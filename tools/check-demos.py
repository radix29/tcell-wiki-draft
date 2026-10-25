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
  _demos     whether each _demos/<file>.go still compiles when named directly (`go build
             _demos/mouse.go`, which is what the library's own CI does) - because the Gallery note
             tells a reader to do exactly that, and an earlier draft of this tool said the file had to
             be copied out of the directory first, which was a guess. Measured whenever --build or
             --markdown asks for a claim; a page that names a file that no longer builds is a failure.
  citations  every demos/<name> or .../tree/<branch>/demos/<name> reference a page makes resolves to
             a real demo - a wiki page linking demos/whatever is asserting that a stranger can run it;
  links      the URL form we link (default branch of the library repo) is detected, not guessed, via
             git ls-remote --symref;
  build      optional --build runs `go build ./demos/...` in the checkout, which is the cheapest
             proof that "run this demo" is still true, and the per-file _demos check above.

--markdown prints the paste-able Gallery block. Descriptions come from each demo's own doc comment;
where a demo has none the line is emitted with a TODO marker, because inventing a description for
someone else's program is exactly the kind of thing this project must not do. The `_demos` note the
block ends with is generated from the build measurement above, so the block never contradicts the
checkout it was generated from (that is why --markdown measures too, and why a paste is a measurement
and not a memory).

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
# A URL into a library file (`blob`/`raw` + branch + path + optional #anchor). Q-4 makes these
# load-bearing, so they are checked against the checkout rather than trusted.
DOC_URL_RE = re.compile(r"github\.com/gdamore/tcell/(?:blob|raw)/(?P<branch>[^/\s]+)/"
                        r"(?P<path>[^#\s?)]+)(?:#(?P<frag>[^\s)]*))?")
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


def _clean(text: str, limit: int = 90) -> str:
    """One ASCII, markdown-safe clause from a compiler message (it is going on a public page)."""
    text = re.sub(r"[`()*_]", "", text.strip().splitlines()[0] if text.strip() else "")
    text = "".join(ch for ch in text if 32 <= ord(ch) < 127)
    text = re.sub(r"\s+", " ", text).strip(" .,:;")
    return text[:limit].strip()


def build_undemos(tcell: pathlib.Path, undemos):
    """{name without .go: '' or a verb-first reason} - does naming the file build it, as the note claims?

    The go tool skips a directory beginning with '_' for package patterns, which is the whole point of
    the name, but an explicit file argument is still a buildable program - the library proves this on
    itself in .github/workflows/webasm.yml (`go build _demos/mouse.go`). So the claim worth measuring
    is per file, and "needs no copy-out" is only half of it: a file that imports a module the checkout
    does not require is a build error a reader meets, and a page should say so rather than be surprised.
    """
    out = {}
    for u in undemos:
        p = subprocess.run(["go", "build", "-o", "/dev/null", f"_demos/{u['name']}"],
                           cwd=str(tcell), capture_output=True, text=True)
        if p.returncode == 0:
            out[u["name"][:-3]] = ""
            continue
        err = (p.stderr or p.stdout or "").strip()
        m = re.search(r"no required module provides package (\S+)", err)
        if m:
            # The compiler writes "... package github.com/x/y; to add it:" - the trailing punctuation
            # belongs to its sentence, not to the import path we are naming on a public page.
            pkg = m.group(1).rstrip(';,."\'` ')
            why = f"imports `{pkg}`, which the module does not require"
        else:
            why = f"fails to build: {_clean(err)}" if _clean(err) else "fails to build silently"
        out[u["name"][:-3]] = why
    return out


def citations(pages):
    """Every citation a page makes into the library repo.

    Three kinds, all with {page, line, branch, raw}: demos (kind=demo), the not-shipped `_demos` pile
    (kind=under), and library docs (kind=doc: a `blob/<branch>/<path>` URL plus optional `#frag`).
    Q-4 makes the doc kind load-bearing - `Getting-Started` teaches by linking `TUTORIAL.md` headings it
    does not own - so an upstream rename must fail a check here instead of breaking a reader.
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
            for m in DOC_URL_RE.finditer(line):
                if m.group("path").startswith(("demos/", "_demos/")):
                    continue  # the demo regexes below know what a demo URL is
                claimed.append((m.start(), m.end()))
                out.append({"kind": "doc", "page": rel, "line": n, "path": m.group("path"),
                            "frag": (m.group("frag") or "").split("?")[0], "under": False, "name": "",
                            "branch": m.group("branch"), "raw": m.group(0)})
            for m in DEMOS_URL_RE.finditer(line):
                if any(a <= m.start() < b for a, b in claimed):
                    continue
                claimed.append((m.start(), m.end()))
                out.append({"kind": "under" if m.group("dir") == "_demos" else "demo", "page": rel,
                            "line": n, "name": m.group("name").removesuffix(".go"),
                            "under": m.group("dir") == "_demos", "branch": m.group("branch"),
                            "raw": m.group(0)})
            for m in DEMOS_BARE_RE.finditer(line):
                if any(a <= m.start() < b for a, b in claimed):
                    continue
                raw = m.group("full")
                name = raw.split("/", 1)[1]
                out.append({"kind": "under" if raw.startswith("_") else "demo", "page": rel, "line": n,
                            "name": name.removesuffix(".go"), "under": raw.startswith("_"),
                            "branch": "", "raw": raw})
    return out


def check_doc(cit, tcell, seen):
    """Does the library file a page links exist, and does the heading it names still exist there?"""
    where = f"{cit['page']}:{cit['line']}"
    target = tcell / cit["path"]
    try:
        target.resolve().relative_to(tcell.resolve())
    except ValueError:
        return [f"{where}: {cit['raw']!r} points outside the library repo"]
    if target.is_dir():
        return []
    if not target.is_file():
        return [f"{where}: the library has no {cit['path']} at this commit - under Q-4 a page name *is* "
                "the tutorial, so a renamed file must be caught here, not by a reader"]
    frag = cit["frag"]
    if not frag or target.suffix != ".md":
        return []
    if frag not in seen.setdefault(str(target), W.anchors_in(W.read(target))):
        return [f"{where}: #{frag} matches no heading in {cit['path']} (it has: "
                f"{', '.join(sorted(seen[str(target)])) or 'none'}) - name a heading the library owns"]
    return []


def main() -> int:
    ap = argparse.ArgumentParser(description="S8.2b tcell demo/link checker")
    ap.add_argument("pages", nargs="*", help="pages to scan (default: tools/pages.txt)")
    ap.add_argument("--tcell", default=os.environ.get("TCELL_DIR") or str((W.ROOT.parent / "tcell").resolve()))
    ap.add_argument("--build", action="store_true",
                    help="run `go build ./demos/...`, and each _demos/*.go by name, in the checkout")
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

    # The _demos build check is the evidence behind the note the Gallery block ends with, so it runs
    # whenever a run is asked to make that claim (--build asks for build facts, --markdown prints the
    # sentence). It costs about five seconds warm, which is why the plain citation run does not pay it.
    underbuild = {}
    if args.build or args.markdown:
        underbuild = build_undemos(tcell, undemos)
        failed = {n: why for n, why in underbuild.items() if why}
        if failed:
            detail = "; ".join(f"{n}.go {why}" for n, why in sorted(failed.items()))
            print(f"_demos     {len(underbuild) - len(failed)} of {len(underbuild)} file(s) build by "
                  f"naming them; {len(failed)} {'does' if len(failed) == 1 else 'do'} not as shipped "
                  f"({detail})")
        else:
            print(f"_demos     all {len(underbuild)} file(s) build by naming them "
                  "(go build _demos/<name>.go)")
    pages = W.page_paths(args.pages or None)
    missing = [p for p in pages if not p.exists()]
    if missing:
        for p in missing:
            print(f"{p}: listed file does not exist", file=sys.stderr)
        return 2

    cited = citations(pages)
    demo_cited = {c["name"] for c in cited if c["kind"] == "demo"}
    docs = [c for c in cited if c["kind"] == "doc"]
    seen = {}
    print(f"citations {len(docs)} library file link(s) (Q-4), {len([d for d in docs if d['frag']])} "
          f"with a heading anchor, verified against {tcell}")
    for c in cited:
        if c.get("branch") and c["branch"] != branch:
            problems.append(f"{c['page']}:{c['line']}: links branch '{c['branch']}' "
                            f"(the library default is '{branch}'); PLAN.md 2 already records one stale "
                            "wiki URL of exactly this kind - use the default branch or a tag")
        if c["kind"] == "doc":
            problems += check_doc(c, tcell, seen)
            continue
        if c["under"]:
            stem = c["name"] if c["name"].endswith(".go") else c["name"] + ".go"
            if stem not in under:
                problems.append(f"{c['page']}:{c['line']}: cites _demos/{c['name']} which the checkout "
                                f"does not have ({', '.join(sorted(under))})")
                continue
            if underbuild and c["name"] in underbuild and underbuild[c["name"]]:
                problems.append(f"{c['page']}:{c['line']}: names _demos/{c['name']}, which does not "
                                f"build as shipped ({underbuild[c['name']]}) - a page may tell a reader "
                                "to run a program the checkout cannot compile")
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
        # The provenance note goes *outside* the block, because the block is what a person pastes: an
        # HTML comment on a wiki page breaks PLAN.md 7 ("no HTML tags") and would name this repo's
        # tooling to a reader of the wiki, which route C forbids (5.5). A block that cannot be pasted
        # without editing it is a broken generator, so the warning is printed for the human instead.
        print("\nnote: the block between the ```markdown markers is paste-able as it stands; the names, "
              "URLs and run commands are facts from the checkout, every TODO(desc) line needs a human "
              "sentence written from the program, and the `_demos` paragraph closing the block is the "
              "build measurement taken above. Do not hand-edit the block - re-run this tool.")
        print("\n```markdown")
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
            listed = ", ".join(sorted(u["name"] for u in undemos))
            runnable = sorted(n for n, why in underbuild.items() if not why)
            note = (f"\nThe `_demos/` directory ({listed}) holds `//go:build ignore` programs: they are "
                    "not part of the module, so nothing above builds or runs them")
            if not underbuild:
                # Not measured (the caller asked for no build check), so the note says nothing about
                # running them - an unmeasured promise about someone else's build is the thing this
                # tool exists to stop.
                note += ", and this run did not check whether any of them compiles"
            elif runnable:
                note += f"; to run one, name the file: `go run _demos/{runnable[0]}.go`."
            else:
                note += (", and none of them compiles on this checkout, so the wiki lists none of them "
                         "as runnable from here")
            failed = {n: why for n, why in underbuild.items() if why}
            if failed:
                # One shape for one file and for several: each reason is already a clause with the file
                # name as its subject, so there is no singular/plural sentence to get wrong.
                note += (" As shipped, " + "; ".join(f"`{n}.go` {why}"
                                                     for n, why in sorted(failed.items())) + ".")
            print(note)
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
