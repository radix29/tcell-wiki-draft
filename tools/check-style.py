#!/usr/bin/env python3
"""S8.5 style linter - PLAN.md 7 house rules, enforced mechanically.

Usage: tools/check-style.py [--all] [file ...]        (default: the pages in tools/pages.txt)

Page rules (files listed in tools/pages.txt) are strict, because a page is text that gets pasted
into somebody else's wiki. Non-page docs (PLAN.md, README.md, AGENTS.md) get the subset
that still matters with --all: tabs, trailing whitespace, unclosed fences, single H1.

Known legacy exceptions live in tools/style-allow.txt and are counted in the summary, so a
suppressed rule never becomes invisible. Exit 0 = clean, 1 = findings, 2 = bad usage.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import wikilib as W

ALLOW = W.ROOT / "tools" / "style-allow.txt"
H_RE = re.compile(r"^(?P<hashes>#{1,6})\s")
BULLET_RE = re.compile(r"^(?P<indent> *)[-*+]\s")
HTML_RE = re.compile(r"<[A-Za-z/!?][^>\n]*>")
EMU_RE = re.compile(r"(?<![\w*`])\*(?!\s)[^*\n]*?\*(?![\w*`])")
IMAGE_EXT = re.compile(r"\.(png|jpe?g|gif|webp|bmp|svg)$", re.I)
LOCAL_PAGE_LINK = re.compile(r"\.md$")


class Findings:
    def __init__(self, allow=None):
        self.items = []
        self.suppressed = 0
        self.allow = allow if allow is not None else []

    def add(self, path, lineno, rule, message, *, line="", page=True):
        if _allowed(self.allow, path, rule, line):
            self.suppressed += 1
            return
        self.items.append(f"{_rel(path)}:{lineno}: [{rule}] {message}")

    def report(self, show_stale: bool = True):
        self.items.sort(key=lambda s: (s.split(":", 1)[0], int(re.match(r"^[^:]*:(\d+)", s).group(1))))
        for item in self.items:
            print(item)
        if self.items:
            print(f"\n{len(self.items)} finding(s) in {len({i.split(':')[0] for i in self.items})} file(s).")
        if self.suppressed:
            print(f"({self.suppressed} finding(s) suppressed by tools/style-allow.txt - that is the legacy "
                  "list, not a clean bill of health)")
        stale = [e for e in self.allow if not e["used"]] if show_stale else []
        if stale:
            print(f"note: {len(stale)} allow-list entr(y/ies) matched nothing and are stale:")
            for e in stale:
                print(f"  tools/style-allow.txt:{e['line']}: {e['file']}\t{e['rule']}\t{e['needle']}")
            print("  (a page rewrite should delete them; that is the point of listing them at all)")
        return 1 if self.items else 0


def _rel(path: pathlib.Path) -> str:
    try:
        return str(path.resolve().relative_to(W.ROOT))
    except ValueError:
        return str(path)


def load_allow():
    """tools/style-allow.txt lines are: <file-tab><rule><tab><needle|*>. Returns mutable entries so
    the summary can also report entries that matched nothing (a stale allow list is a silent lie)."""
    entries = []
    if not ALLOW.exists():
        return entries
    for n, raw in enumerate(ALLOW.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip() or raw.startswith("#"):
            continue
        parts = raw.split("\t")
        if len(parts) != 3:
            print(f"tools/style-allow.txt:{n}: expected 3 tab-separated fields, got: {raw}", file=sys.stderr)
            continue
        entries.append({"line": n, "file": parts[0].strip(), "rule": parts[1].strip(),
                        "needle": parts[2].strip(), "used": False})
    return entries


def _allowed(entries, path: pathlib.Path, rule: str, line: str) -> bool:
    name = _rel(path)
    hit = False
    for e in entries:
        if e["file"] in (name, "*") and e["rule"] in (rule, "*") and (e["needle"] == "*" or e["needle"] in line):
            e["used"] = True
            hit = True
    return hit


def lint(path: pathlib.Path, page: bool, out: Findings) -> None:
    text = W.read(path)
    lines = text.splitlines()
    spans = W.fence_ranges(text)

    # --- rules that apply everywhere ---
    for n, line in enumerate(lines, 1):
        # Tabs are only a problem in prose: gofmt *requires* tab-indented Go inside a fence
        # (PLAN.md 7 wants gofmt-clean code), so the whole block is exempt.
        if "\t" in line and not W.in_fence(n, spans):
            out.add(path, n, "tabs", "tab character in prose; markdown indents are spaces "
                    "(tabs are fine inside a code fence - that is what gofmt writes)", line=line, page=page)
        if line != line.rstrip():
            out.add(path, n, "trailing-space", "trailing whitespace", line=line, page=page)
    if text and not text.endswith("\n"):
        out.add(path, len(lines), "final-newline", "file does not end with a newline",
                line=lines[-1] if lines else "", page=page)
    if "\r\n" in text:
        out.add(path, 1, "crlf", "CRLF line endings; the wiki repo is LF", page=page)

    blocks = list(W.fence_blocks(text))
    for open_lineno, info, _body in blocks:
        if info is None:
            out.add(path, open_lineno, "fence-unclosed", "code fence is never closed", page=page)
            continue
        if not page:
            continue  # the tag vocabulary below is a page rule; tooling docs use bash/markdown/json
        tag, _, rest = info.partition(" ")
        if not tag:
            out.add(path, open_lineno, "fence-tag", "code fence has no language tag "
                    f"(one of {sorted(W.FENCE_TAGS)}) - ASCII art uses `text`, diagrams `mermaid`", page=page)
        elif tag not in W.FENCE_TAGS:
            out.add(path, open_lineno, "fence-tag", f"unknown fence language `{tag}` "
                    f"(allowed: {sorted(W.FENCE_TAGS)})", page=page)
        for attr in filter(None, rest.split()):
            key = attr.split("=", 1)[0]
            if key not in W.SNIPPET_KEYS:
                out.add(path, open_lineno, "fence-attr", f"unknown fence marker `{attr}`; snippet markers are "
                        f"{sorted(W.SNIPPET_KEYS)} (tools/make-samples.py, tools/check-style.py docstring)", page=page)
            elif "=" not in attr:
                out.add(path, open_lineno, "fence-attr", f"fence marker `{attr}` needs a value", page=page)

    if not page:
        return

    h1 = [n for n, line in enumerate(lines, 1) if line.startswith("# ")]
    if len(h1) > 1:
        out.add(path, h1[1], "h1", f"{len(h1)} H1 headings; the wiki already renders the page title, so "
                "a page has at most one (PLAN.md 7, AGENTS.md)", page=page)

    # --- page-only rules (a page is paste-able on its own, so it may not lean on this repo) ---
    # Which lines are bullets / wrapped continuations of bullets. A bullet plus its continuations is
    # one list run, so a wrapped bullet is reported once (wrapped-bullet) and not twice (blank-before).
    is_bullet = [bool(BULLET_RE.match(line)) for line in lines]
    is_cont = []
    for i, line in enumerate(lines):
        inside = bool(re.match(r"^\s+\S", line)) and not is_bullet[i]
        is_cont.append(inside and i > 0 and (is_bullet[i - 1] or is_cont[i - 1]))
    in_list = [b or c for b, c in zip(is_bullet, is_cont)]
    list_start = [b and not (i > 0 and in_list[i - 1]) for i, b in enumerate(is_bullet)]

    for n, line in enumerate(lines, 1):
        if W.in_fence(n, spans):
            continue
        prose = W.strip_inline_code(line)
        for bad in prose:
            if ord(bad) > 126:
                out.add(path, n, "ascii", f"non-ASCII {bad!r} (U+{ord(bad):04X}) in prose; the wiki pages "
                        "are pure ASCII - Unicode belongs inside code spans/blocks", line=line, page=page)
                break
        if EMU_RE.search(prose):
            out.add(path, n, "emphasis", "*emphasis* found; this wiki uses _emphasis_", line=line, page=page)
        if HTML_RE.search(prose):
            out.add(path, n, "html", "HTML tag; GitHub wikis render markdown only here (PLAN.md 7)", line=line, page=page)
        # blank line around headings and lists
        if H_RE.match(line) and n > 1 and lines[n - 2].strip():
            out.add(path, n, "blank-before", "heading needs a blank line above it", line=line, page=page)
        if H_RE.match(line) and n < len(lines) and lines[n].strip() and not lines[n].startswith("#"):
            out.add(path, n, "blank-after", "heading needs a blank line below it", line=line, page=page)
        if (list_start[n - 1] and n > 1 and lines[n - 2].strip() and not W.in_fence(n - 1, spans)
                and not H_RE.match(lines[n - 2])):
            # (a heading directly above a list is already reported by blank-after, not twice here)
            out.add(path, n, "blank-before", "list needs a blank line above it", line=line, page=page)
        # wrapped bullets: continuation line under a bullet (PLAN.md 7: one bullet per line, unwrapped,
        # because the published wiki diff should stay one line per entry)
        if is_cont[n - 1] and not W.in_fence(n, spans):
            out.add(path, n, "wrapped-bullet", "continuation of a bullet; keep each entry on one "
                    "unwrapped line so wiki diffs stay one-line", line=line, page=page)

    for lineno, _text, target, is_image in W.link_targets(text):
        slug = W.slug_of(target)
        if slug == "":
            continue  # external or pure anchor; handled by check-links.py and by rule below
        if slug.startswith("/") or "/" in slug or slug.startswith(".."):
            out.add(path, lineno, "self-contained", f"link target '{target}' points outside the page; a wiki "
                    "page may only link other pages by slug, or absolute URLs (AGENTS.md, PLAN.md 5.5)", page=page)
        elif LOCAL_PAGE_LINK.search(slug):
            out.add(path, lineno, "link-md", f"'{target}' names a file; internal links omit the extension: "
                    f"'{slug[:-3]}'", page=page)
        if is_image and not W.is_external(target):
            out.add(path, lineno, "image-hosting", f"image '{target}' would have to live in the wiki repo; "
                    "diagrams are Mermaid or ASCII (D-5, PLAN.md 7)", page=page)
        if not is_image and IMAGE_EXT.search(slug):
            out.add(path, lineno, "image-link", f"'{target}' is an image; link it as a screenshot instead", page=page)


def main() -> int:
    ap = argparse.ArgumentParser(description="S8.5 wiki style linter")
    ap.add_argument("files", nargs="*", help="files to lint (default: tools/pages.txt)")
    ap.add_argument("--all", action="store_true", help="also lint the non-page docs (subset of rules)")
    ap.add_argument("--page", action="append", default=[], help="force page rules for a file")
    args = ap.parse_args()

    force = {pathlib.Path(p).resolve().name for p in args.page}
    paths = W.page_paths(args.files or None)
    if args.all:
        extra = [p for p in sorted(W.ROOT.glob("*.md")) if p not in paths]
        paths = paths + extra
    if not paths:
        print("nothing to lint", file=sys.stderr)
        return 2

    out = Findings(load_allow())
    for path in paths:
        if not path.exists():
            out.items.append(f"{_rel(path)}:0: [missing] listed file does not exist")
            continue
        lint(path, W.is_page(path) or path.name in force, out)
    if not out.items:
        names = ", ".join(_rel(p) for p in paths)
        print(f"style: clean - {names}")
    return out.report(show_stale=not args.files)


if __name__ == "__main__":
    sys.exit(main())
