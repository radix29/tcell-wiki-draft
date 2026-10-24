#!/usr/bin/env python3
"""S8.2b demo checker - the wiki links Tcell's own examples, it never re-authors them (route C).

Usage: tools/check-demos.py [--build] [--markdown] [--verbose] [page ...]

The Gallery is a list of things built with Tcell, and PLAN.md 6.2 adds one new subsection,
"## Demos in the Repository". The eight programs under ../tcell/demos ARE the examples page: the
library ships them, ships a rendering test for each one, and CI in the library repo keeps them
working. So the wiki's job is to name them and link them - not to copy their code into a fence,
where it would rot on the next API change (v3 already renamed PutStr/SetContent/EventKey.Rune).

What this checks:

  discovery  the demos that actually exist in the checkout (authoritative list, refreshed each run),
             whether each has a _test.go, and the //go:build ignore status of the _demos/ files the
             Gallery note describes (PLAN.md 6.2);
  citations  every demos/<name> or .../tree/<branch>/demos/<name> reference a page makes resolves to
             a real demo - a wiki page linking demos/whatever is asserting that a stranger can run it;
  links      the URL form we link (default branch of the library repo) is detected, not guessed, via
             git ls-remote --symref;
  build      optional --build runs `go build ./demos/...` in the checkout, which is the cheapest
             proof that "run this demo" is still true.

--markdown prints the paste-able Gallery block. Descriptions come from each demo's own doc comment;
where a demo has none the line is emitted with a TODO marker, because inventing a description for
someone else's program is exactly the kind of thing this project must not do.

Exit 0 = every citation resolves, 1 = a page cites a demo that does not exist (or a claim about
_demos/ is wrong), 2 = environment (no checkout).
"""
from __future__ import annotations

import argparse
import os
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import wikilib as W

REPO = "https://github.com/gdamore/tcell"
DOC_SENTENCE = re.compile(r"^//[ \t]*(This (?:program|demo|tool)[^.]*\.)", re.M)
# Two citation forms: a URL into the library repo (which carries a branch name we can verify), and a
# bare path like `demos/hello` or `_demos/mouse.go`. Inline code counts on purpose - a path in
# backticks is exactly the assertion worth checking, unlike the prose rules in check-style.py.
DEMOS_URL_RE = re.compile(r"github\.com/gdamore/tcell/(?:tree|blob)/(?P<branch>[^/\s]+)/"
                          r"(?P<dir>_?demos)/(?P<name>[\w.-]+)")
DEMOS_BARE_RE = re.compile(r"(?<![\w./-])(?P<full>_?demos/[\w.-]+)")


def default_branch() -> str:
    """The library's default branch - detected, never assumed (links depend on it)."""
    try:
        out = subprocess.run(["git", "ls-remote", "--symref", REPO, "HEAD"],
                             capture_output=True, text=True, timeout=25).stdout
    except (OSError, subprocess.SubprocessError):
        return "main"
    m = re.search(r"ref:\s+refs/heads/(\S+)\s+HEAD", out)
    return m.group(1) if m else "main"


def discover(tcell: pathlib.Path, branch: str):
    demos, undemos = [], []
    for d in sorted((tcell / "demos").glob("*")) if (tcell / "demos").is_dir() else []:
        if not d.is_dir():
            continue
        src = sorted(p for p in d.glob("*.go") if not p.name.endswith("_test.go"))
        if not src:
            continue
        text = src[0].read_text(encoding="utf-8", errors="replace")
        m = DOC_SENTENCE.search(text)
        desc = re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
        demos.append({
            "name": d.name,
            "files": [p.name for p in src],
            "test": any(p.name.endswith("_test.go") for p in d.glob("*.go")),
            "run": f"go run ./demos/{d.name}",
            "url": f"{REPO}/tree/{branch}/demos/{d.name}",
            "desc": desc,
        })
    for f in sorted((tcell / "_demos").glob("*.go")) if (tcell / "_demos").is_dir() else []:
        head = "\n".join(f.read_text(encoding="utf-8", errors="replace").splitlines()[:8])
        tag = re.search(r"^//go:build\s+(\S+)", head, re.M)
        undemos.append({"name": f.name, "tag": tag.group(1) if tag else ""})
    return demos, undemos


def citations(pages):
    """Every demo citation on the pages: {page, line, name, under, branch, raw}.

    `under` marks a citation into _demos/ (the not-shipped pile), `branch` is the branch a URL links
    (so a link to tree/master/... is visible even though the repo default is main).
    """
    out = []
    for path in pages:
        text = W.read(path)
        try:
            rel = path.resolve().relative_to(W.ROOT).as_posix()
        except ValueError:
            rel = path.name
        spans = W.fence_ranges(text)
        for n, line in enumerate(text.splitlines(), 1):
            if W.in_fence(n, spans):
                continue
            claimed = []
            for m in DEMOS_URL_RE.finditer(line):
                claimed.append((m.start(), m.end()))
                out.append({"page": rel, "line": n, "name": m.group("name").removesuffix(".go"),
                            "under": m.group("dir") == "_demos", "branch": m.group("branch"),
                            "raw": m.group(0)})
            for m in DEMOS_BARE_RE.finditer(line):
                if any(a <= m.start() < b for a, b in claimed):
                    continue
                raw = m.group("full")
                name = raw.split("/", 1)[1]
                out.append({"page": rel, "line": n, "name": name.removesuffix(".go"),
                            "under": raw.startswith("_"), "branch": "", "raw": raw})
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="S8.2b tcell demo/link checker")
    ap.add_argument("pages", nargs="*", help="pages to scan (default: tools/pages.txt)")
    ap.add_argument("--tcell", default=os.environ.get("TCELL_DIR") or str((W.ROOT.parent / "tcell").resolve()))
    ap.add_argument("--build", action="store_true", help="run `go build ./demos/...` in the checkout")
    ap.add_argument("--markdown", action="store_true", help="print the paste-able Gallery block")
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()

    tcell = pathlib.Path(args.tcell).resolve()
    if not (tcell / "demos").is_dir():
        print(f"error: {tcell} has no demos/ directory (PLAN.md assumes the sibling checkout ../tcell; "
              "set TCELL_DIR to override)", file=sys.stderr)
        return 2

    branch = default_branch()
    demos, undemos = discover(tcell, branch)
    names = {d["name"] for d in demos}
    under = {u["name"] for u in undemos}
    problems = []

    print(f"demos     {len(demos)} program(s) in {tcell}/demos, "
          f"{len([d for d in demos if d['test']])} with a _test.go; "
          f"{len(undemos)} file(s) in _demos, "
          f"{len([u for u in undemos if u['tag'] == 'ignore'])} marked //go:build ignore; "
          f"library default branch: {branch}")
    for d in demos:
        note = "" if d["desc"] else "  TODO(desc): the demo has no doc sentence - do not invent one"
        if args.verbose or not d["desc"]:
            print(f"  {d['name']:<10} test={'yes' if d['test'] else 'NO '}  {d['run']:<28} "
                  f"{d['desc'][:58]}{note}")
    for u in undemos:
        if u["tag"] != "ignore":
            problems.append(f"_demos/{u['name']} has //go:build {u['tag'] or 'nothing'}, not ignore; "
                            "PLAN.md 6.2 wants the Gallery note to say 'ignore'")

    pages = W.page_paths(args.pages or None)
    missing = [p for p in pages if not p.exists()]
    if missing:
        for p in missing:
            print(f"{p}: listed file does not exist", file=sys.stderr)
        return 2

    cited = citations(pages)
    demo_cited = {c["name"] for c in cited if not c["under"]}
    for c in cited:
        if c.get("branch") and c["branch"] != branch:
            problems.append(f"{c['page']}:{c['line']}: links branch '{c['branch']}' "
                            f"(the library default is '{branch}'); PLAN.md 2 already records one stale "
                            "wiki URL of exactly this kind - use the default branch or a tag")
        if c["under"]:
            stem = c["name"] if c["name"].endswith(".go") else c["name"] + ".go"
            if stem not in under:
                problems.append(f"{c['page']}:{c['line']}: cites _demos/{c['name']} which the checkout "
                                f"does not have ({', '.join(sorted(under))})")
            continue
        if c["name"] not in names:
            problems.append(f"{c['page']}:{c['line']}: cites demos/{c['name']}, but the library ships "
                            f"{', '.join(sorted(names))} - a page may not promise a demo that does not exist")
    unlinked = sorted(names - demo_cited)
    if unlinked:
        print(f"note: {len(unlinked)} of the {len(names)} demos are not linked from these page(s): "
              f"{', '.join(unlinked)}")
        print("      PLAN.md 6.2 lists all of them under '## Demos in the Repository' (T3.2); until then "
              "this is a to-do, not a defect")

    if args.build:
        p = subprocess.run(["go", "build", "./demos/..."], cwd=str(tcell), capture_output=True, text=True)
        if p.returncode != 0:
            problems.append("`go build ./demos/...` failed in the checkout (the examples are the wiki's "
                            "promise, so this blocks publishing a demos section):\n"
                            + (p.stdout + p.stderr).strip())
        else:
            print("build     go build ./demos/... clean")

    if args.markdown:
        print("\n```markdown")
        print("<!-- GENERATED by tools/check-demos.py --markdown from the library checkout: the names, "
              "URLs and run commands are facts, any TODO(desc) line needs a human sentence. Do not "
              "hand-edit this block - re-run the tool. -->")
        print("## Demos in the Repository\n")
        print(f"Each program lives in [demos]({REPO}/tree/{branch}/demos) and can be run straight from a "
              "clone of the library:\n")
        print("```console")
        print("$ git clone https://github.com/gdamore/tcell")
        print("$ cd tcell")
        print("$ go run ./demos/hello")
        print("```\n")
        for d in demos:
            if not d["desc"]:
                print(f"- [{d['name']}]({d['url']}) - TODO(desc): {d['files'][0]} carries no doc "
                      "sentence; write one from reading the program, never from the file name")
                continue
            # Derived from the demo's own comment: drop the "This program" preamble so the line reads
            # like a Gallery entry, keep every other word verbatim.
            desc = re.sub(r"^This (program|demo|tool)\s+", "", d["desc"]).rstrip(".")
            desc = re.sub(r"\s+", " ", desc)
            print(f"- [{d['name']}]({d['url']}) - {desc}")
        if undemos:
            print(f"\nThe `_demos/` directory ({', '.join(sorted(u['name'] for u in undemos))}) holds "
                  "`//go:build ignore` programs: they are not part of the module and run only after "
                  "copying the file out, so the wiki does not list them as runnable demos.")
        print("```")

    for p in problems:
        print(f"DEMO  {p}")
    if problems:
        return 1
    if args.markdown:
        return 0
    print(f"demos: clean - {len(names)} shipped demo(s), {len(demo_cited)} cited by these pages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
