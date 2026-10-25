#!/usr/bin/env python3
"""S8.7 review checklist runner - PLAN.md 8: "consistent manual review" made repeatable.

Usage: tools/review-checklist.py [--offline] [--verbose] [page ...]

Three kinds of line, on purpose:

  GATE  runs a sibling tool and reports PASS/FAIL. This is what CI runs, and what a reviewer should
        run once instead of remembering six commands.
  CHECK a cheap local check of a review question we can answer mechanically: v2 API leakage, whether
        a page that talks about resizing names `EventResize`, orphan pages, duplicated `##` topics.
  ASK   a question that needs a human. It never fails the run, because "did you check env
        precedence?" is not decidable from text - but printing it every time is the difference
        between a review and a re-read.

Each page's line prints two word counts, because PLAN.md 5.1's budgets and 6.1's "<= 400 words" are
checked against different things: `prose_words` (fences, link targets, inline code and markup out) is
what a reader reads and what a budget like "Home 250-350 words" means, and the raw `split()` count is
the page's size on disk, which is what a cap like "<= 400" was written against. A page is inside its
budget and under the cap when both numbers say so; printing one invites grading it by the other.

Pages default to tools/pages.txt, so the checklist covers exactly what publishes. Exit 0 = no GATE or
CHECK failure, 1 = something to fix, 2 = bad usage/environment.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import wikilib as W

# PLAN.md T4.4's banned list. Every name here was re-checked against the real v3 surface
# (tools/apiface) and is absent from it, which is what makes it a CHECK and not an opinion.
V2_BANNED = ("PollEvent", "ChannelEvents", "PostEvent", "SimulationScreen", "StyleNormal",
             "Attribute", "ColorForeground", "ColorBackground")

# Route C's self-containment rule (PLAN.md 7, D-5): upstream receives the text of one .md file, so a
# page may not point at a file that lives in this repo. Only *references* are a defect, so the two
# patterns below name a file or a repo directory, and nothing else. `mermaid`/`text` fences are the
# diagram formats D-5 asks for and are already excluded (`body` has every fence line removed).
EXTERNAL_URL_RE = re.compile(r"[A-Za-z][A-Za-z0-9+.\-]*://\S+")  # a hotlink is D-5's answer, not a defect
IMAGE_FILE_RE = re.compile(r"(?<![\w./\\-])((?:[\w.+-]+/)*[\w.+-]+\.(?:png|jpe?g|gif|webp|bmp|svg))(?![\w])", re.I)
REPO_DIR_RE = re.compile(r"(?<![\w./\\-])((?:images?|img|assets|media|graphics|screenshots?|docs?)/[\w.+-]*)")


def repo_file_refs(body: str):
    r"""Every reference in non-fenced text to a file that would have to live in this repo.

    Tested both ways against the shapes the page set actually contains (PLAN.md Phase 1's "Found" row
    scheduled this for T5.1, because the CHECK before it failed the *word* `mermaid` anywhere in a page
    and therefore failed PLAN 6.4's own diagram rule):
      "```mermaid\nflowchart LR\n  a-->b\n```"                    -> no finding (a fence is a diagram)
      "diagrams are mermaid or ASCII in fenced blocks" -> no finding (a word is not a file)
      "![d](images/arch.png)" and "see images/arch.png"               -> 1 finding each (repo-hosted file)
      "([screenshot](http://2.bp.blogspot.com/a/b/2015.png))"         -> no finding (Gallery.md line 7)
    The URL pass blanks `scheme://...` spans first, which is what makes that last one clean: an external
    hotlink and a repo-relative path both end in `.png`, and only one of them needs a file this repo
    does not have.
    """
    text = EXTERNAL_URL_RE.sub(lambda m: " " * len(m.group(0)), body)
    seen, out = set(), []
    for rx in (IMAGE_FILE_RE, REPO_DIR_RE):
        for m in rx.finditer(text):
            ref = m.group(1)
            if ref.lower() not in seen:
                seen.add(ref.lower())
                out.append(ref)
    return out


GATES = (
    ("style", "check-style.py", ()),
    ("links", "check-links.py", ()),
    ("gallery", "check-gallery.py", ()),
    ("demos", "check-demos.py", ()),
    ("snippets", "make-samples.py", ()),
    ("symbols", "symbol-coverage.py", ("--gate",)),
)


def run_gate(name: str, script: str, extra, offline: bool):
    argv = [sys.executable, str(pathlib.Path(__file__).resolve().parent / script)]
    argv += [a for a in extra] + (["--offline"] if script == "check-links.py" and offline else [])
    p = subprocess.run(argv, capture_output=True, text=True)
    out = (p.stdout + p.stderr).strip().splitlines()
    return p.returncode, (out[-1] if out else ""), out


def prose_pages(paths):
    return [(p.stem, W.read(p) if p.exists() else "") for p in paths]


def check_page(page: str, text: str, built: set, links_out: dict, headings: dict):
    """Mechanical part of the review, per page. Returns (fails, asks)."""
    fails, asks = [], []
    spans = W.fence_ranges(text)
    lines = text.splitlines()
    body = "\n".join(line for n, line in enumerate(lines, 1) if not W.in_fence(n, spans))
    code = "\n".join(line for n, line in enumerate(lines, 1) if W.in_fence(n, spans))

    for name in V2_BANNED:
        hit = [n for n, line in enumerate(text.splitlines(), 1)
               if re.search(rf"\b{re.escape(name)}\b", line)]
        if hit:
            where = "fence" if any(re.search(rf"\b{name}\b", c or "") for c in [code]) else "prose"
            fails.append(f"v2 leakage: `{name}` in {where} at line {hit[0]} "
                         f"(not in the v3 surface; PLAN.md T4.4 bans it - say what replaced it)")
    if re.search(r"\bresize", body, re.I) and "EventResize" not in code + body:
        fails.append("talks about resizing but never names `EventResize` - a reader copy-pasting the "
                     "old `Screen.Resized()`/poll pattern gets nothing (v3: `case *tcell.EventResize`)")

    if not links_out.get(page):
        asks.append("no link to another built page: does this page own its topic, and where does the "
                    "reader go next? (PLAN.md 5.4 single-owner rule; an orphan page is a dead end)")
    for other, seen in headings.items():
        if other != page and seen & set(h for h in re.findall(r"^## (.+)$", text, re.M)):
            asks.append(f"repeats a `##` topic also in {other} - one of the two pages should link "
                        "instead of restating it (PLAN.md 5.4)")
    if "TCELL_" in text:
        asks.append("documents TCELL_* vars: did you check the precedence order (flag > env > "
                    "terminfo > built-in default) and say it out loud? PLAN.md 13 wants all of them")
    refs = repo_file_refs(body)
    if refs:
        fails.append("page references " + ", ".join(refs[:3]) + " outside a fenced block - route C says "
                     "self-contained only, so a diagram is a `mermaid` or `text` fence and a picture is a "
                     "hotlink, never a file in this repo (D-5, PLAN.md 7)")
    if not re.search(r"^```go", text, re.M):
        asks.append("page has no `go` fence yet: if it is supposed to show code, snippets must go "
                    "through tools/make-samples.py (S8.1) and headless ones `headless=yes` (S8.6)")
    return fails, asks


def main() -> int:
    ap = argparse.ArgumentParser(description="S8.7 review checklist runner")
    ap.add_argument("pages", nargs="*", help="pages to review (default: tools/pages.txt)")
    ap.add_argument("--offline", action="store_true", help="skip external URL probes in the links gate")
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()

    paths = W.page_paths(args.pages or None)
    missing = [p for p in paths if not p.exists()]
    for p in missing:
        print(f"{p}: listed file does not exist", file=sys.stderr)
    if missing:
        return 2

    built = {p.stem for p in paths}
    texts = dict(prose_pages(paths))
    links_out, headings = {}, {}
    for page, text in texts.items():
        targets = [t for _, _, t, _img in W.link_targets(text)]
        links_out[page] = sorted({W.slug_of(t) for t in targets
                                  if t and not W.is_external(t) and W.slug_of(t) in built
                                  and W.slug_of(t) != page})
        headings[page] = set(re.findall(r"^## (.+)$", text, re.M))

    print(f"pages     {', '.join(sorted(built))} (from tools/pages.txt)")
    print("\nGATES")
    bad = 0
    env_line = ""
    for name, script, extra in GATES:
        rc, last, lines = run_gate(name, script, extra, args.offline)
        if name == "symbols":
            env_line = next((l for l in lines if "undocumented by any page" in l), "")
            if not env_line:
                # Every TCELL_* name is documented from Phase 6 on, so the line this tool printed when a
                # variable went undocumented has nothing left to say; print the audit's own count instead.
                env_line = next((l for l in lines if l.startswith("envlist ")), "")
        mark = "PASS" if rc == 0 else "FAIL"
        bad += rc != 0
        if rc != 0 or args.verbose:
            print(f"  [{mark}] {name:<9} {last}")
        else:
            print(f"  [{mark}] {name}")
    # Home is the hub (PLAN.md 5.5) and GitHub renders it as the wiki landing page, so "nothing links
    # to Home" is the designed state, not a defect.
    orphans = sorted(p for p in built if p != "Home" and not any(p in v for v in links_out.values()))
    if orphans:
        print(f"\nCHECK")
        for p in orphans:
            print(f"  [ASK] {p}: nothing links to it (nav lives in `Home` per PLAN.md 5.5 - "
                  f"is it reachable from there?)")

    print("\nPER PAGE")
    for page in sorted(texts):
        text = texts[page]
        fails, asks = check_page(page, text, built, links_out, headings)
        words = len(text.split())
        prose = W.prose_words(text)
        print(f"  {page} ({prose} prose words, {words} counting code and markup, "
              f"{len(re.findall(r'^##', text, re.M))} sections)")
        for f in fails:
            bad += 1
            print(f"    [FAIL] {f}")
        for a in asks:
            print(f"    [ASK]  {a}")
        if not fails and not asks:
            print("    [ok]   nothing mechanical to fix and nothing to ask - suspicious for a page; "
                  "read it once as a first-time reader")

    if env_line:
        print(f"\nENV\n  {env_line.strip()}")
    print(f"\nchecklist  {'clean - answer the ASK lines before proposing a page upstream' if not bad else f'{bad} thing(s) to fix'}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
