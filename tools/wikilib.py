"""Shared helpers for the Tcell wiki draft QA scripts (PLAN.md 8, `AGENTS.md` Tooling).

Everything here is stdlib-only: the scripts run the same way on a laptop and in
`.github/workflows/qa.yml`, and a docs repo must never need a package install.
"""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "tools" / "pages.txt"

# Fenced-block languages a page may use (PLAN.md 7: code is go-tagged, diagrams are Mermaid or
# ASCII). Anything else is a typo we want to hear about.
FENCE_TAGS = {"go", "mermaid", "text", "console"}
# Optional key=value markers a fence may carry for the S8.1 snippet harness (tools/make-samples.py).
SNIPPET_KEYS = {"snippet", "mode", "headless"}


def _manifest_lines() -> list[tuple[int, str]]:
    out = []
    for n, line in enumerate(MANIFEST.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        out.append((n, line))
    return out


def manifest_pages() -> list[str]:
    """Page file names this repo publishes (the only thing tools/mirror-wiki.sh will copy)."""
    return [name for _, name in _manifest_lines()]


def page_paths(paths: list[str] | None = None, *, missing: bool = True) -> list[pathlib.Path]:
    """Manifest pages by default; explicit arguments override (so CI can lint one changed file)."""
    if paths:
        out = []
        for p in paths:
            path = pathlib.Path(p)
            if not path.is_absolute():
                path = ROOT / path
            if missing or path.exists():
                out.append(path)
        return out
    return [ROOT / name for name in manifest_pages()]


def is_page(path: pathlib.Path) -> bool:
    try:
        return path.resolve().name in manifest_pages() and path.resolve().parent == ROOT
    except OSError:
        return False


def is_ascii(text: str) -> bool:
    """Pages must stay pure ASCII (PLAN.md 7, AGENTS.md); non-page docs are exempt."""
    return all(ord(c) < 127 for c in text)


def read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


# --- markdown structure -------------------------------------------------------------------------
FENCE_RE = re.compile(r"^(?P<indent> {0,3})(?P<fence>`{3,}|~{3,})[ \t]*(?P<info>[^`]*)$")
LINK_RE = re.compile(r"!\[(?P<text>[^\]]*)\]\((?P<target>[^)\s]+)(?:[ \t]+\"[^\"]*\")?\)|"
                     r"\[(?P<link>[^\]]*)\]\((?P<linktarget>[^)\s]+)(?:[ \t]+\"[^\"]*\")?\)")
SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*:")
INLINE_CODE_RE = re.compile(r"(`+)(?:.|\n)*?\1")


def fence_blocks(text: str):
    """Yield (open_lineno, info_string, body_lines) for every fenced block, in order.

    An unclosed block yields (open_lineno, None, []) so the linter can complain about it; body_lines
    excludes the two fence lines. Used by the style linter (tag validation) and by the S8.1 snippet
    harness (which only wants `go` blocks).
    """
    lines = text.splitlines()
    open_at, char, length = None, "", 0
    for n, line in enumerate(lines, 1):
        m = FENCE_RE.match(line)
        if not m:
            continue
        if open_at is None:
            open_at = n
            char, length = m.group("fence")[0], len(m.group("fence"))
            continue
        if m.group("fence")[0] == char and len(m.group("fence")) >= length and not m.group("info").strip():
            info = lines[open_at - 1]
            info = FENCE_RE.match(info).group("info").strip()
            yield (open_at, info, lines[open_at:n - 1])
            open_at = None
    if open_at is not None:
        yield (open_at, None, [])


def fence_ranges(text: str) -> list[range]:
    """Line-number ranges (1-based, inclusive of both fence lines) for every fenced block."""
    spans = []
    open_at = None
    fence_char, fence_len = "", 0
    for n, line in enumerate(text.splitlines(), 1):
        m = FENCE_RE.match(line)
        if not m:
            continue
        if open_at is None:
            open_at = n
            fence_char, fence_len = m.group("fence")[0], len(m.group("fence"))
        elif m.group("fence")[0] == fence_char and len(m.group("fence")) >= fence_len and not m.group("info").strip():
            spans.append(range(open_at, n + 1))
            open_at = None
    if open_at is not None:
        spans.append(range(open_at, len(text.splitlines()) + 1))
    return spans


def in_fence(lineno: int, spans: list[range]) -> bool:
    return any(lineno in span for span in spans)


def strip_inline_code(line: str) -> str:
    """Blank out `code` spans so prose rules do not fire on literals (PLAN.md 7 allows Unicode and
    odd characters inside code)."""
    return INLINE_CODE_RE.sub(lambda m: " " * len(m.group(0)), line)


def link_targets(text: str, *, skip_code: bool = True):
    """Yield (lineno, link_text, target, is_image) for every inline link in a page."""
    spans = fence_ranges(text) if skip_code else []
    for n, line in enumerate(text.splitlines(), 1):
        if skip_code and in_fence(n, spans):
            continue
        for m in LINK_RE.finditer(line):
            if m.group("linktarget") is not None:
                yield n, m.group("link"), m.group("linktarget"), False
            else:
                yield n, m.group("text"), m.group("target"), True


def slug_of(target: str) -> str:
    """Wiki page name a link target points at ('' for pure anchors and external URLs)."""
    target = target.split("#", 1)[0]
    if not target or SCHEME_RE.match(target) or target.startswith("//"):
        return ""
    return target


def github_slug(text: str) -> str:
    """GitHub's heading-anchor rule: strip markdown links, lowercase, drop punctuation, spaces to '-'.
    Shared by check-links.py (internal anchors) and check-demos.py (library-doc anchors), because two
    copies of a renderer's quirk-free version of an anchor rule is how false passes happen."""
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text).strip().lower()
    s = re.sub(r"[^\w\- ]", "", s, flags=re.UNICODE)
    return s.replace(" ", "-")


# A blockquote marker at the start of a line, possibly nested or padded. GitHub renders the markup it
# quotes, so '> ## Demos in the Repository' (Gallery.md's generated section, PLAN 6.2) is still an h2 and
# still gets the anchor: the published page carries href="#demos-in-the-repository", measured on the
# render wiki on 2026-10-25. Until this was stripped, `[demos](Gallery#demos-in-the-repository)` - a link
# that works for a reader - was reported BROKEN, which is the false failure this module warns about.
QUOTE_PREFIX_RE = re.compile(r"^(?:\s*>\s*)+")


def anchors_in(text: str) -> set:
    """Every heading anchor a reader could link to in this markdown, fences excluded.

    Blockquoted headings count, because GitHub gives them one (see QUOTE_PREFIX_RE); everything else
    about this is the same deliberate approximation as github_slug.
    """
    out = set()
    spans = fence_ranges(text)
    for n, line in enumerate(text.splitlines(), 1):
        if in_fence(n, spans):
            continue
        m = re.match(r"^#{1,6}\s+(.*)$", strip_inline_code(QUOTE_PREFIX_RE.sub("", line)))
        if m:
            out.add(github_slug(m.group(1)))
    return out


def is_external(target: str) -> bool:
    return bool(SCHEME_RE.match(target)) or target.startswith("//")


BULLET_MARKER_RE = re.compile(r"^(?P<indent> *)(?:[-*+]|\d+[.)])[ \t]+")
HEADING_MARKER_RE = re.compile(r"^#{1,6}[ \t]+")
# A markdown table's delimiter row (|---|:--|), a thematic break (---, ***, ___) and a bare rule are all
# markup with no words in them, so they must not be counted; every other pipe on a page is table syntax
# here too (PLAN.md 6.5's tables are the only pipes this page set uses), so '|' is treated as whitespace.
MARKUP_ONLY_RE = re.compile(r"^[|:*_.\- ]+$")


def prose_words(text: str) -> int:
    r"""The words a reader reads, for the budgets in PLAN.md 5.1 and the '<= 400 words' in 6.1.

    What comes out, and why: fenced blocks (code is not prose, and a page carrying a dozen snippets
    must not be graded on them), the target of each markdown link (a 60-character URL is one 'word' to
    str.split() and zero to a reader; the link *text* stays), inline code, and the `#` / `-` markers that
    are markup rather than words. What stays is heading text, prose and list text, which is what a person
    reads top to bottom.

    `len(text.split())` is still worth printing next to this (it is the cheap size proxy, and 6.1's cap
    was written against it), so callers show both: a page can only be inside its budget on the first
    measure and under the cap on the second at the same time, and printing one number invites reading
    the budget as the other.

    Shapes it was checked against when it was written (PLAN.md Phase 2's record; `tools/` commits no test
    file, so these are the reproducible form of that check, each expecting the comment's number):
      "three four words" -> 3          a plain line is unchanged
      "see [Gallery](Gallery) and [long](https://ex.com/a/b/c) ok" -> 5   link text stays, target goes
      "prose here\n\n```go\npackage main\n\nfunc main() {}\n```\n\nmore prose" -> 4   raw is 11
      "- one two\n- three four five" -> 5                       markers are markup, not words
      "## Why Tcell" -> 2
      "| Sym | What |\n|---|---|\n| a | b |" -> 4               raw is 11 (delimiter row is not prose)
      "| --- | --- |\n| a | b |" -> 2                          the spaced delimiter row spelling too
      "---\n***" -> 0                                           thematic breaks
      "use `tcell.NewScreen` here" -> 2                        inline code is code, not prose
      "" -> 0
    """
    spans = fence_ranges(text)
    lines = [line for n, line in enumerate(text.splitlines(), 1) if not in_fence(n, spans)]
    out = []
    for line in lines:
        line = LINK_RE.sub(lambda m: m.group("link") if m.group("link") is not None else (m.group("text") or ""),
                           line)
        line = strip_inline_code(line)
        if MARKUP_ONLY_RE.match(line.strip(" \t")):
            continue
        line = line.replace("|", " ")
        line = HEADING_MARKER_RE.sub("", line)
        line = BULLET_MARKER_RE.sub("", line)
        out.append(line)
    return len(" ".join(out).split())
