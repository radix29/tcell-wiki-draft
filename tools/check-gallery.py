#!/usr/bin/env python3
"""S8.4 Gallery migration checker - proves the rewrite is lossless (PLAN.md S2, R2, Appendix B).

Usage: tools/check-gallery.py [--gallery F] [--baseline F] [--sections FILE]
                              [--allow-new-section S] [--max-additions N] [--verbose]

Compares Gallery.md against baseline/Gallery.md (the live wiki as fetched, see baseline/RECORD.txt):

  lossless   every baseline entry (name + URL) still exists, in the same category, in the same
             relative order (append-only, so a re-sorted category looks like a rewrite);
  structure  the 6 baseline categories still exist and stay in baseline order; a new section needs a
             record in tools/gallery-sections.txt (or --allow-new-section for a one-off run), because
             PLAN.md 6.2 sanctions exactly one ("## Demos in the Repository") and forbids one-off
             sections per entry. A record approves the *section*, and with it the entries inside it:
             their content is generated from the library checkout by tools/check-demos.py --markdown,
             so the additions budget (which is about new *projects*) does not apply to them, while the
             shape and ASCII rules below still do. What no checker can know is what *belongs* in a
             generated section - the reviewer's check on that content is to re-run the tool and diff
             it, which is also why an approved section whose heading has disappeared is an error: a
             dropped section is a regression, and a record nobody needs is a silent lie.
  shape      every bullet matches the frozen entry format of PLAN.md 6.2 / AGENTS.md
             ("- [name](url) - lowercase description", ASCII ' - ', no trailing period, no star
             counts, dates or "(new)" markers);
  counts     total bullets per Appendix B: 49, or 49 + N additions, which are always listed;
             a URL corrected in tools/gallery-moves.txt (dead host -> the project's real home, with
             evidence) counts as the same entry, and is reported so the reviewer sees it;
  moves      every move record must point at a baseline entry that exists and a URL that is now on
             the page - a stale move is an error, because a silent URL drift is exactly what the
             lossless contract exists to catch;
  additions  an entry the baseline does not have (a new project in the Gallery) is legal only while
             tools/gallery-additions.txt carries its name, its URL and the evidence for adding it -
             --max-additions is then the budget for anything *beyond* those records, so raising it in
             CI is never how an unrecorded entry gets through.

Exit 0 = migration is provably lossless, 1 = something a reviewer has to explain, 2 = usage error.
"""
from __future__ import annotations

import argparse
import collections
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import wikilib as W

BULLET_RE = re.compile(r"^(?P<indent> *)-\s+(?P<body>.*)$")
ENTRY_RE = re.compile(r"^\[(?P<name>[^\]]+)\]\((?P<url>[^)\s]+)\)(?P<rest>.*)$")
LINK_ONLY_RE = re.compile(r"^\[(?P<name>[^\]]+)\]\((?P<url>[^)\s]+)\)$")
MEDIA_RE = re.compile(r"^ \((?:\[(?P<label>screenshot|video|screenshot/video)\]\((?P<url>[^)\s]+)\))\)$")
PLAIN_RE = re.compile(r"^(?P<name>[^\[\]]+?) - (?P<desc>.*)$")
BAD_MARKER_RE = re.compile(r"(\(\s*new\s*\)|\bstars?\b|\u2605|\bnew!\b|,\s*\d{4}\b|\(\d{4}\)|\bv\d+(\.\d+)*\b)", re.I)
# Only a literal full stop counts: "written for sr.ht" or "a .go CLI" must not fire.
TRAILING_PERIOD_RE = re.compile(r"\.$")
CATEGORY_ORDER_NOTE = "PLAN.md 6.2 keeps the 6 baseline categories and their order"
MOVES = W.ROOT / "tools" / "gallery-moves.txt"
ADDITIONS = W.ROOT / "tools" / "gallery-additions.txt"
SECTIONS = W.ROOT / "tools" / "gallery-sections.txt"


def load_records(path: pathlib.Path, shape: str, key_ok, val_ok=lambda v: v.startswith("http")):
    """Shared parser for the decision files that let the migration contract bend.

    '<key>\t<value>\t[evidence]', one decision per line, # comments allowed. The files exist so a
    reviewer sees *which* deviation was approved and why, which is also why a malformed line is
    reported instead of skipped: a silently dropped record means the check stops defending the thing
    it was written for. `val_ok` is what makes a URL record refuse a value that is not a URL; a
    section record carries prose evidence in that field, so it accepts anything non-empty.
    """
    out = {}
    if not path.exists():
        return out
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [f.strip() for f in raw.split("\t")]
        if len(parts) < 2 or not key_ok(parts[0]) or not parts[1] or not val_ok(parts[1]):
            print(f"{path.name}:{n}: expected '{shape}', got: {raw}", file=sys.stderr)
            continue
        out[parts[0]] = (parts[1], parts[2] if len(parts) > 2 else "(no evidence recorded)")
    return out


def load_moves(path: pathlib.Path = MOVES):
    """tools/gallery-moves.txt: old URL -> (new URL, evidence). See Q-11 in PLAN.md 4.1."""
    return load_records(path, "<old-url>\t<new-url>\t[evidence]", lambda k: k.startswith("http"))


def load_additions(path: pathlib.Path = ADDITIONS):
    """tools/gallery-additions.txt: display name -> (URL, evidence). Entries the baseline does not
    have are allowed one by one, never in bulk: a second addition needs its own approved record."""
    return load_records(path, "<name>\t<url>\t[evidence]", lambda k: bool(k) and not k.startswith("http"))


def load_sections(path: pathlib.Path = SECTIONS):
    """tools/gallery-sections.txt: section heading -> (evidence for approving the whole section). A
    *section* approval, for the one new `##` PLAN.md 6.2 sanctions; the entries it carries are
    generated from the library checkout, so they are governed by the shape rules and not by the
    additions budget, which is the record of approved new *projects*."""
    return load_records(path, "<section>\t[evidence]", lambda k: bool(k) and not k.startswith("http"),
                        val_ok=lambda v: bool(v))


class Entry:
    def __init__(self, lineno, category, raw):
        self.lineno = lineno
        self.category = category
        self.raw = raw
        self.name = ""
        self.url = ""
        self.kind = "plain"  # entry | plain
        self.problems = []
        self._parse()

    def _parse(self):
        m = ENTRY_RE.match(self.raw)
        if m:
            self.kind = "entry"
            self.name = m.group("name")
            self.url = m.group("url")
            rest = m.group("rest")
            if not rest.startswith(" - "):
                self.problems.append(f"after the link use ' - ' (ASCII hyphen, single spaces), got {rest[:12]!r}")
                tail = rest
            else:
                tail = rest[3:]
            media = MEDIA_RE.search(tail)
            desc = tail[:media.start()] if media else tail
            self.media_url = media.group("url") if media else ""
            self.desc = desc
            if desc.strip().startswith("- "):
                self.problems.append("double ' - ' separator")
            if TRAILING_PERIOD_RE.search(desc.strip()):
                self.problems.append(f"description ends with a period: {desc.strip()[-12:]!r}")
            return
        m = LINK_ONLY_RE.match(self.raw)
        if m:
            self.kind = "entry"
            self.name, self.url = m.group("name"), m.group("url")
            self.desc = ""
            self.media_url = ""
            self.problems.append("entry has no ' - description' part")
            return
        m = PLAIN_RE.match(self.raw)
        if m:
            self.kind = "plain"
            self.name, self.url = m.group("name"), ""
            self.desc = m.group("desc")
            self.media_url = ""
            if not re.search(r"\]\(", self.raw) and not TRAILING_PERIOD_RE.search(self.desc.strip()):
                # An unlinked legacy bullet (the 'mouse demo' line) is allowed but flagged for D-6.
                return
            if TRAILING_PERIOD_RE.search(self.desc.strip()):
                self.problems.append(f"unlinked entry description ends with a period: {self.desc.strip()[-12:]!r}")
            return
        self.kind = "malformed"
        self.problems.append("entry matches none of the frozen shapes "
                             "('- [name](url) - description', with optional ' ([screenshot](url))')")

    @property
    def key(self):
        return (self.name.strip(), self.url)


def parse(path: pathlib.Path):
    """Return (categories, entries) from a Gallery file."""
    if not path.exists():
        raise SystemExit(f"{path}: no such file (baseline/Gallery.md comes from PLAN.md T0.3)")
    cats = []
    entries = []
    current = "(top of page)"
    for n, line in enumerate(W.read(path).splitlines(), 1):
        if line.startswith("## "):
            current = line[3:].strip()
            cats.append(current)
            continue
        m = BULLET_RE.match(line)
        if m:
            if m.group("indent"):
                entries.append(Entry(n, current, m.group("body")))
                entries[-1].problems.insert(0, "indented bullet; gallery entries are flat")
            else:
                entries.append(Entry(n, current, m.group("body")))
    return cats, entries


def main() -> int:
    ap = argparse.ArgumentParser(description="S8.4 Gallery lossless-migration checker")
    ap.add_argument("--gallery", default="Gallery.md")
    ap.add_argument("--baseline", default="baseline/Gallery.md")
    ap.add_argument("--allow-new-section", action="append", default=[],
                    metavar="SECTION", help="approve one new category name for this run only "
                    "(the standing approval is a record in tools/gallery-sections.txt)")
    ap.add_argument("--max-additions", type=int, default=0, metavar="N",
                    help="allow at most N entries that are not in the baseline (default 0 = pure migration)")
    ap.add_argument("--moves", default=str(MOVES),
                    help="recorded URL-move file (default tools/gallery-moves.txt)")
    ap.add_argument("--additions", default=str(ADDITIONS),
                    help="recorded approved-addition file (default tools/gallery-additions.txt)")
    ap.add_argument("--sections", default=str(SECTIONS),
                    help="recorded approved-section file (default tools/gallery-sections.txt)")
    ap.add_argument("--verbose", "-v", action="store_true",
                    help="print every category, addition and move record")
    args = ap.parse_args()

    gallery = pathlib.Path(args.gallery)
    baseline = pathlib.Path(args.baseline)
    base_cats, base_entries = parse(baseline)
    cats, entries = parse(gallery)

    errors = []
    notes = []

    # A URL the page still points at, that a move record claims to have moved, means the move was
    # reverted but the record survived (or the record names a project that no longer exists).
    moves = load_moves(pathlib.Path(args.moves))
    additions = load_additions(pathlib.Path(args.additions))
    sections = load_sections(pathlib.Path(args.sections))
    # A --allow-new-section flag is the same approval for one run, tagged so the note cannot be read
    # as a record that outlives the command line it came from.
    approved = {}
    for name, rec in sections.items():
        # A section record is '<heading>\t<evidence>'. load_records hands back (value, evidence)
        # because the other two decision files have a URL in the middle slot, so the one field a
        # section carries is folded into the evidence the note prints rather than printed twice.
        evidence = rec[0] if rec[1] in ("", "(no evidence recorded)") else f"{rec[0]} ({rec[1]})"
        approved[name] = (evidence, pathlib.Path(args.sections).name)
    for name in args.allow_new_section:
        approved.setdefault(name, ("approved on the command line for this run only", "--allow-new-section"))
    page_urls = {e.url for e in entries}
    for old, (new, _why) in moves.items():
        if old in page_urls:
            errors.append(f"tools/gallery-moves.txt claims {old} moved to {new}, but the page still links "
                          "the old URL - either apply the move or delete the record")
        elif old not in {b.url for b in base_entries}:
            errors.append(f"tools/gallery-moves.txt has a record for {old}, which no baseline entry uses "
                          "- stale move records are as misleading as stale allow-list entries")
        elif new not in page_urls:
            errors.append(f"tools/gallery-moves.txt claims {old} -> {new}, but nothing on the page links "
                          f"{new} - the entry's URL was changed to something else, or not at all")
    # Upstream writes some URLs with a trailing slash and some without (github.com/zyedidia/micro/ is
    # real), so records match on the URL modulo a trailing slash - otherwise a cosmetic difference
    # turns an approved entry into an "unapproved addition" and a stale record into a clean one.
    def same_url(a: str, b: str) -> bool:
        return a.rstrip("/") == b.rstrip("/")

    for name, (url, _why) in additions.items():
        if any(b.name == name and same_url(b.url, url) for b in base_entries):
            errors.append(f"tools/gallery-additions.txt approves '{name}' at {url}, which is already in "
                          "the baseline - an approved addition is by definition an entry we did not "
                          "have; delete the record")
            continue
        where = [e for e in entries if e.name == name]
        if not any(same_url(e.url, url) for e in where):
            hint = (f" - the page has '{name}' at {where[0].url} instead" if where else
                    ", and no entry of that name on the page")
            errors.append(f"tools/gallery-additions.txt approves '{name}' at {url}, but the page does "
                          f"not carry it{hint} - delete the record or apply the entry, do not leave it "
                          "looking approved")

    # --- structure -------------------------------------------------------------
    kept = [c for c in base_cats if c in cats]
    order_in_gallery = [c for c in cats if c in base_cats]
    if order_in_gallery != kept:
        errors.append(f"baseline categories were reordered: {' -> '.join(order_in_gallery)} "
                      f"({CATEGORY_ORDER_NOTE})")
    for missing in [c for c in base_cats if c not in cats]:
        errors.append(f"category '{missing}' disappeared ({CATEGORY_ORDER_NOTE})")
    for extra in [c for c in cats if c not in base_cats]:
        if extra not in approved:
            errors.append(f"new category '{extra}' is not approved; PLAN.md 6.2 sanctions exactly one "
                          "new section and forbids one-off sections per entry, so a second one is a "
                          "plan change and not an edit. A sanctioned one needs a record in "
                          f"{SECTIONS.relative_to(W.ROOT)} (or --allow-new-section '{extra}' to test it)")
        else:
            notes.append(f"approved new category: '{extra}' [{approved[extra][1]}] ({approved[extra][0]})")
    for name in [n for n in sections if n not in cats]:
        errors.append(f"tools/{SECTIONS.name} approves the section '{name}', which the page no longer "
                      "has - a sanctioned section that disappears is a content loss (R2), and a "
                      "record nobody needs is a stale lie; fix the page or delete the record")

    # --- lossless + order ------------------------------------------------------
    by_cat_now = collections.defaultdict(list)
    for e in entries:
        by_cat_now[e.category].append(e)
    base_by_cat = collections.defaultdict(list)
    for e in base_entries:
        base_by_cat[e.category].append(e)

    for cat, b_list in base_by_cat.items():
        now = by_cat_now.get(cat, [])
        now_keys = [e.key for e in now]
        for b in b_list:
            rec = moves.get(b.url)
            if rec and any(e.name == b.name and e.url == rec[0] and e.category == b.category for e in now):
                # A recorded URL correction (dead host -> real home): same entry, same place.
                notes.append(f"recorded URL move: '{b.name}' {b.url} -> {rec[0]} ({rec[1]})")
                continue
            if b.key not in now_keys:
                # Same URL elsewhere? Then it moved; same name elsewhere? Renamed.
                elsewhere = [e for e in entries if e.key == b.key]
                if elsewhere:
                    errors.append(f"'{b.name}' moved out of category '{cat}' (baseline append-only order); "
                                  f"it is now in '{elsewhere[0].category}'")
                    continue
                same_url = [e for e in entries if b.url and e.url == b.url]
                if same_url:
                    errors.append(f"URL of '{b.name}' survived but the display name changed to "
                                  f"'{same_url[0].name}'; record that as a deliberate edit (PLAN.md 6.2)")
                    continue
                same_name = [e for e in entries if e.name == b.name and b.name]
                if same_name:
                    errors.append(f"entry '{b.name}' survived but its URL changed from {b.url} to "
                                  f"{same_name[0].url}; never drop a URL silently (PLAN.md 6.2)")
                    continue
                errors.append(f"LOST entry '{b.name}' ({b.url}) from category '{cat}' at baseline line "
                              f"{b.lineno} - the migration must be lossless")
                continue
        # relative order inside the category must be preserved (append-only)
        surviving = [e for e in now if e.key in {b.key for b in b_list}]
        if [e.key for e in surviving] != [b.key for b in b_list if b.key in now_keys]:
            errors.append(f"entries inside category '{cat}' were reordered; keep baseline order and "
                          "append (AGENTS.md: add entries to the end of the matching section)")

    def recorded_move(e):
        """An entry whose URL a tools/gallery-moves.txt record moved to exactly this one."""
        return any(b.name == e.name and b.url in moves and moves[b.url][0] == e.url for b in base_entries)

    # An approved section is outside the additions contract: that budget counts new *projects* added to
    # the inherited categories, while the entries of a sanctioned section are generated text about the
    # library's own programs (PLAN.md 6.2, tools/check-demos.py). They stay under the shape rules below.
    in_sections = [e for e in entries if e.category in approved
                   and e.key not in {b.key for b in base_entries}]
    new_entries = [e for e in entries
                   if e.key not in {b.key for b in base_entries} and not recorded_move(e)
                   and e.category not in approved]
    if in_sections:
        notes.append(f"{len(in_sections)} entry(ies) sit in the approved section "
                     f"'{in_sections[0].category}' and are exempt from the additions budget; their "
                     "content is generated, so the check on them is to re-run tools/check-demos.py "
                     "--markdown and diff it")
    approved = []
    for e in list(new_entries):
        rec = additions.get(e.name)
        if rec and rec[0].rstrip("/") == e.url.rstrip("/"):
            approved.append(e)
            notes.append(f"approved addition: '{e.name}' {e.url} in '{e.category}' ({rec[1]})")
            new_entries.remove(e)
    moved_in = [e for e in entries if e.key in {b.key for b in base_entries}
                and any(b.key == e.key and b.category != e.category for b in base_entries)]
    if new_entries and args.verbose:
        for e in new_entries:
            print(f"ADDITION  {gallery}:{e.lineno}: [{e.name}]({e.url}) in '{e.category}'")
    if moved_in:
        notes.append(f"{len(moved_in)} entry(ies) appear in a different category than the baseline")
    if len(new_entries) > args.max_additions:
        errors.append(f"{len(new_entries)} new entr(ies) but --max-additions {args.max_additions}; "
                      "Appendix B needs every addition approved before it lands "
                      + ("(run with --verbose to list them)" if not args.verbose else ""))

    # --- shape -----------------------------------------------------------------
    for e in entries:
        for p in e.problems:
            errors.append(f"{gallery}:{e.lineno}: [{e.category}] {p}")
        if BAD_MARKER_RE.search(e.desc or ""):
            errors.append(f"{gallery}:{e.lineno}: entry carries a date/star-count/'(new)'-style marker "
                          f"({BAD_MARKER_RE.search(e.desc).group(0)!r}); AGENTS.md forbids these")
        if not W.is_ascii(e.raw):
            bad = next(ch for ch in e.raw if ord(ch) > 126)
            errors.append(f"{gallery}:{e.lineno}: non-ASCII {bad!r} in an entry; pages are pure ASCII")
    urls = [e.url for e in entries if e.url]
    for url, count in collections.Counter(urls).items():
        if count > 1:
            errors.append(f"URL {url} appears {count} times in the gallery")
    names = collections.defaultdict(list)
    for e in entries:
        if e.name:
            names[e.name].append(e.url)
    for name, url_list in names.items():
        if len(url_list) > 1:
            notes.append(f"duplicate display name '{name}' x{len(url_list)} (tolerated by AGENTS.md when the "
                         "URLs differ; check it is not an accident)")

    # --- counts (Appendix B contract) ------------------------------------------
    total_now = len(entries)
    linked_now = len([e for e in entries if e.url])
    base_total = len(base_entries)
    print(f"counts   baseline {base_total} bullets ({len([e for e in base_entries if e.url])} linked) "
          f"-> now {total_now} ({linked_now} linked) in {len(cats)} categories")
    for cat in base_cats + [c for c in cats if c not in base_cats]:
        b = len(base_by_cat.get(cat, []))
        n = len(by_cat_now.get(cat, []))
        flag = "" if b == n else f"  <-- {'+' if n > b else ''}{n - b}"
        if args.verbose or b != n:
            print(f"  {cat:<28} baseline {b:>2}  now {n:>2}{flag}")
    unlinked_now = [e for e in entries if not e.url]
    if len(unlinked_now) != len([e for e in base_entries if not e.url]):
        errors.append("the number of entries without a link changed; the one legacy unlinked bullet "
                      "(mouse demo) is handled by D-6 wording, not by dropping or adding links")

    for note in notes:
        print(f"note: {note}")
    if errors:
        print()
        for err in errors:
            print(f"MIGRATION  {err}")
        print(f"\n{len(errors)} migration problem(s). Nothing here may be 'fixed' by deleting a URL "
              "(PLAN.md 6.2).")
        return 1
    print(f"gallery: lossless - all {base_total} baseline entries present, order preserved, "
          f"{len(new_entries)} addition(s) within --max-additions {args.max_additions}"
          + (f" (+{len(approved)} approved and recorded in tools/gallery-additions.txt)" if approved else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
