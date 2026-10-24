#!/usr/bin/env python3
"""S8.2 link checker - PLAN.md 8: no dead external links, no broken internal links.

Usage: tools/check-links.py [--offline] [--verbose] [--report FILE] [file ...]

Internal links are checked against tools/pages.txt: a file that exists in this repo but is not in
the manifest is still a *broken link in the render*, because the mirror publishes the manifest and
nothing else. That is also how a page would link one of the 6 deferred pages by accident, which
PLAN.md 5.5 forbids. Anchors are checked against the headings of the target page (GitHub slug rules).

External links are probed with an HTTP HEAD through curl (AGENTS.md already uses curl for this),
retried as a range GET because several hosts answer 403/405 to HEAD, plus one transport retry. A URL
that is genuinely gone is recorded, never deleted (PLAN.md 6.2: "never delete an entry because of a
404 - report it instead"): write the table with --report, and accept a status deliberately in
tools/link-status-allow.txt (needle<TAB>statuses<TAB>reason).

Exit 0 = everything resolves or is deliberately accepted; 1 = a broken link or a route-C internal
link; 2 = bad usage.
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import wikilib as W

ALLOW = W.ROOT / "tools" / "link-status-allow.txt"
TIMEOUT = 12
UA = "curl/8 (tcell-wiki-draft QA link checker; one-shot, low volume)"
# GitHub and friends answer 403/405 to HEAD; a ranged GET is the polite probe that gets through.
RETRY_STATUS = {400, 401, 403, 405, 406, 415, 429, 500, 501, 503}
ERR = "ERR"
OK_MIN, OK_MAX = 200, 400


def _curl(url: str, *, head: bool) -> str:
    cmd = ["curl", "-sS", "-o", "/dev/null", "-m", str(TIMEOUT), "-A", UA,
           "-w", "%{http_code}", "-L", "--max-redirs", "5"]
    if head:
        cmd.append("-I")
    else:
        cmd += ["-r", "0-2047"]
    cmd.append(url)
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT + 10)
    except subprocess.TimeoutExpired:
        return ERR
    lines = out.stdout.strip().splitlines()
    code = lines[-1] if lines else ERR
    return code if re.fullmatch(r"\d{3}", code) else ERR


def probe(url: str) -> str:
    """HTTP status string for a URL, or ERR after two transport failures."""
    code = _curl(url, head=True)
    if code == ERR:
        code = _curl(url, head=True)
    if code == ERR:
        return ERR
    if int(code) in RETRY_STATUS:
        got = _curl(url, head=False)
        if got != ERR:
            code = got
    return code




def load_allow():
    """tools/link-status-allow.txt: <needle><TAB><accepted statuses, comma separated><TAB><reason>."""
    rules = []
    if not ALLOW.exists():
        return rules
    for n, raw in enumerate(ALLOW.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip() or raw.startswith("#"):
            continue
        parts = raw.split("\t")
        if len(parts) != 3:
            print(f"tools/link-status-allow.txt:{n}: expected 3 tab-separated fields: {raw}", file=sys.stderr)
            continue
        rules.append((n, parts[0].strip(), {s.strip() for s in parts[1].split(",")}, parts[2].strip()))
    return rules


def acceptance(rules, url: str, code: str):
    for lineno, needle, codes, reason in rules:
        if needle in url and code in codes:
            return lineno, reason
    return None


def rel_of(path: pathlib.Path) -> str:
    try:
        return str(path.resolve().relative_to(W.ROOT))
    except ValueError:
        return str(path)


def main() -> int:
    ap = argparse.ArgumentParser(description="S8.2 link checker")
    ap.add_argument("files", nargs="*", help="files to check (default: tools/pages.txt)")
    ap.add_argument("--offline", action="store_true", help="check internal links only (no network)")
    ap.add_argument("--verbose", "-v", action="store_true", help="print every external URL and its status")
    ap.add_argument("--report", metavar="FILE", help="write the full external status table to FILE")
    args = ap.parse_args()

    paths = [p for p in W.page_paths(args.files or None)]
    missing = [p for p in paths if not p.exists()]
    if missing:
        for p in missing:
            print(f"{rel_of(p)}: listed file does not exist", file=sys.stderr)
        return 2

    slugs = {name[:-3] for name in W.manifest_pages() if name.endswith(".md")}
    rules = load_allow()
    text_of = {rel_of(p): W.read(p) for p in paths}
    anchors = {name: W.anchors_in(text) for name, text in text_of.items()}

    internal_bad = []
    external = collections.OrderedDict()
    internal_count = 0
    for name, text in text_of.items():
        for lineno, _link, target, _image in W.link_targets(text):
            if W.is_external(target):
                external.setdefault(target, set()).add(f"{name}:{lineno}")
                continue
            internal_count += 1
            slug, _, anchor = target.partition("#")
            if not slug:
                if anchor and anchor not in anchors[name]:
                    internal_bad.append((name, lineno, target, f"anchor '#{anchor}' matches no heading here"))
                continue
            if slug.endswith(".md"):
                internal_bad.append((name, lineno, target, "internal link names a file; drop the '.md'"))
                continue
            if "/" in slug or slug.startswith("."):
                internal_bad.append((name, lineno, target, "internal link uses a path; wiki links are bare slugs"))
                continue
            if slug not in slugs:
                internal_bad.append((name, lineno, target,
                                     f"'{slug}' is not a published page (tools/pages.txt is the gate; "
                                     "PLAN.md 5.5 forbids linking a deferred page)"))
                continue
            if anchor and anchor not in anchors.get(slug + ".md", set()):
                internal_bad.append((name, lineno, target, f"anchor '#{anchor}' matches no heading in {slug}.md"))

    codes = {}
    if external and not args.offline:
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            futures = {pool.submit(probe, url): url for url in external}
            for fut in concurrent.futures.as_completed(futures):
                codes[futures[fut]] = fut.result()
    elif external:
        print(f"note: --offline, {len(external)} external URL(s) not probed", file=sys.stderr)

    problems = []
    report_rows = []
    for url, where in external.items():
        code = "offline" if args.offline else codes.get(url, ERR)
        note = acceptance(rules, url, code)
        row = f"{code}\t{url}\t{', '.join(sorted(where))}"
        if note:
            row += f"\tACCEPTED ({note[1]})"
        report_rows.append(row)
        ok = code.isdigit() and OK_MIN <= int(code) < OK_MAX
        if ok or note or args.offline:
            if args.verbose:
                print(f"{code}  {url}" + (f"   [{note[1]}]" if note else ""))
            continue
        problems.append((url, code, sorted(where)))

    # A CI runner with no egress would otherwise look like "49 dead URLs": if nearly every probe
    # failed to speak HTTP at all, that is a network fault in the runner, so say so and stop (exit 2)
    # instead of reporting broken links.
    noconn = [url for url in external if not args.offline and codes.get(url, "") in ("", ERR, "000")]
    if not args.offline and external and len(noconn) >= max(2, int(0.9 * len(external))):
        print(f"error: {len(noconn)}/{len(external)} URLs returned no HTTP status at all - this looks like "
              "no network egress, not broken links", file=sys.stderr)
        return 2

    for url, code, where in sorted(problems, key=lambda item: item[1]):
        print(f"BROKEN {code}  {url}  <- {', '.join(where)}")
    for name, lineno, target, why in internal_bad:
        print(f"BROKEN link  {name}:{lineno}: [{target}] {why}")

    if args.report:
        out = pathlib.Path(args.report)
        out.write_text(
            "# S8.2 external URL status - generated by tools/check-links.py, do not edit by hand\n"
            "# columns: status<TAB>url<TAB>where[<TAB>note]\n"
            + "\n".join(sorted(report_rows)) + "\n", encoding="utf-8")
        print(f"report: {out} ({len(report_rows)} URL(s))")

    if problems or internal_bad:
        print(f"\n{len(problems) + len(internal_bad)} broken link(s): {len(problems)} external, "
              f"{len(internal_bad)} internal (of {len(external)} external, {internal_count} internal)")
        return 1
    print(f"links: clean - {len(external)} external URL(s), {internal_count} internal link(s), "
          f"{len(text_of)} file(s) checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
