#!/usr/bin/env python3
"""S8.3 symbol coverage auditor - PLAN.md 8 and 6.5.

Usage: tools/symbol-coverage.py [--tcell DIR] [--report FILE] [--list-uncovered] [--gate]
                                [--gate-kinds type,func,var] [--verbose] [page ...]

Two jobs, deliberately separated:

  GATE (on by default)  Every capitalized identifier a page puts in backticks must exist in the
      root package of ../tcell. This is the cheap, high-value direction: it catches an invented API
      (`TerminfoScreen`, `Style.SetUnderline`, `TCELL_FOO`) at commit time instead of at review time.
      PLAN.md Appendix A singles out exactly this failure mode ("do not invent one on a page").

  REPORT (off by default)  How much of the exported surface the pages actually mention. PLAN.md 6.5
      wants 100% of root-package exported symbols owned by exactly one page, and that is the open
      coverage-gate question: the real surface is ~1000 names, 600+ of them palette and key
      constants (Color*, Key*, Rune*). Run this with --gate only once a maintainer answers that
      question; --gate-kinds lets the gate start at types/funcs/vars and leave constant tables out.

The API list comes from tools/apiface (go/parser over ../tcell, no network, no module download).
Exit 0 = gate satisfied, 1 = a page names a symbol that does not exist (or coverage below the gate
when --gate is on), 2 = usage/environment problem (no Go, no checkout).
"""
from __future__ import annotations

import argparse
import collections
import os
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import wikilib as W

APIFACE = W.ROOT / "tools" / "apiface"
ALLOW = W.ROOT / "tools" / "api-allow.txt"
# Things a page legitimately backticks that are not root-package API: Go builtins, prose shorthands,
# env vars, file names. Format: one pattern per line (fnmatch), '#' comments, with a reason after '#'.
BUILTIN = {"true", "false", "nil", "iota", "int", "rune", "byte", "string", "error", "any", "bool",
           "make", "new", "len", "cap", "append", "panic", "recover", "close", "delete", "copy",
           "main", "init", "context", "fmt", "os", "go", "defer", "range", "chan", "struct", "interface"}
IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
# Constants are where the API surface explodes (Color*, Key*, Rune*...), so they are reported in
# buckets instead of as one number - that split is what the open coverage-gate question turns on.
CONST_PREFIXES = ("Color", "Key", "Rune", "Mod", "Button", "Attr", "CursorStyle", "Underline",
                  "Mouse", "Wheel", "Opt", "Kitty", "Xterm", "Encoding", "System", "Style")


def run_apiface(tcell: pathlib.Path):
    if not APIFACE.is_dir():
        print("tools/apiface is missing", file=sys.stderr)
        return None
    if not tcell.is_dir():
        print(f"error: Tcell checkout not found at {tcell}\n"
              "       PLAN.md assumes the sibling checkout ../tcell; set TCELL_DIR to override.",
              file=sys.stderr)
        return None
    if subprocess.run(["bash", "-lc", "command -v go"], capture_output=True).returncode != 0:
        print("error: go not on PATH; S8.3 needs it to read the API surface", file=sys.stderr)
        return None
    out = subprocess.run(["go", "run", ".", str(tcell)], cwd=APIFACE, capture_output=True, text=True)
    if out.returncode != 0:
        print(f"error: tools/apiface failed:\n{out.stderr}", file=sys.stderr)
        return None
    return out.stdout


def parse_surface(dump: str):
    """(symbols, methods, subpackages, rows) where symbols/methods are name sets."""
    symbols, methods, rows = set(), collections.defaultdict(set), []
    subpkgs = set()
    for line in dump.splitlines():
        parts = line.split("\t")
        if len(parts) < 4:
            continue
        kind, owner, name, doc = parts[0], parts[1], parts[2], parts[3]
        rows.append((kind, owner, name, doc))
        if kind == "subpkg":
            subpkgs.add(owner)
        elif kind == "method":
            methods[owner].add(name)
            symbols.add(name)
        else:
            symbols.add(name)
    return symbols, methods, subpkgs, rows


def group(kind: str, name: str) -> str:
    if kind != "const":
        return kind
    for prefix in CONST_PREFIXES:
        if name.startswith(prefix):
            return f"const {prefix}*"
    return "const other"


def load_allow():
    """tools/api-allow.txt: one name per line, '<name>  # reason'; 'pkg:<dir> # ...' whitelists a package
    prefix for `pkg.Symbol` references we cannot resolve from the root package (stdlib, third-party)."""
    ok = set(BUILTIN)
    reasons = {}
    extra_pkgs = set()
    if not ALLOW.exists():
        return ok, reasons, extra_pkgs
    for raw in ALLOW.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        name, _, reason = line.partition("#")
        name = name.strip()
        if not name:
            continue
        if name.startswith("pkg:"):
            extra_pkgs.add(name[4:].strip())
            continue
        ok.add(name)
        if reason.strip():
            reasons[name] = reason.strip()
    return ok, reasons, extra_pkgs


def env_vars_in_source(tcell: pathlib.Path) -> set:
    """TCELL_* strings the library actually reads (Appendix C does this with grep; same rule here)."""
    out = set()
    for path in sorted(tcell.rglob("*.go")):
        if "/testdata/" in str(path.as_posix()):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        out.update(re.findall(r"TCELL_[A-Z0-9_]+", text))
    return out


def mentions(paths):
    """Collect backticked identifiers per page: {page: {token: [lineno, ...]}}."""
    out = collections.defaultdict(lambda: collections.defaultdict(list))
    tok_re = re.compile(r"`([^`\n]+)`")
    for path in paths:
        text = W.read(path)
        spans = W.fence_ranges(text)
        for n, line in enumerate(text.splitlines(), 1):
            if W.in_fence(n, spans):
                continue
            for raw in tok_re.findall(line):
                for piece in re.split(r"[ ,;()\[\]{}]|->|=>", raw):
                    piece = piece.strip().strip(".").strip()
                    if piece:
                        out[path.name][piece].append(n)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="S8.3 symbol coverage auditor")
    ap.add_argument("pages", nargs="*", help="pages to scan (default: tools/pages.txt)")
    ap.add_argument("--tcell", default=None, help="path to the tcell checkout (default $TCELL_DIR or ../tcell)")
    ap.add_argument("--report", metavar="FILE", help="write the full coverage table to FILE")
    ap.add_argument("--list-uncovered", action="store_true", help="print uncovered symbol names")
    ap.add_argument("--gate", action="store_true",
                    help="FAIL on incomplete coverage (PLAN.md 6.5's 100%% gate; needs the open "
                         "coverage-gate question answered first)")
    ap.add_argument("--gate-kinds", default="type,func,var",
                    help="which buckets --gate measures (default type,func,var; methods/consts are the "
                         "600-name tail that the coverage question is about)")
    ap.add_argument("--strict-dots", action="store_true",
                    help="treat pkg.Symbol references to unknown packages as errors, not warnings")
    args = ap.parse_args()

    tcell_dir = pathlib.Path(args.tcell or os.environ.get("TCELL_DIR") or (W.ROOT.parent / "tcell"))
    dump = run_apiface(tcell_dir)
    if dump is None:
        return 2

    symbols, methods, subpkgs, rows = parse_surface(dump)
    allow, reasons, allow_subpkgs = load_allow()
    root_subpkgs = len(subpkgs)
    subpkgs |= allow_subpkgs
    by_bucket = collections.defaultdict(set)
    for kind, owner, name, _doc in rows:
        if kind == "subpkg":
            continue
        by_bucket[group(kind, name)].add(name)

    paths = W.page_paths(args.pages or None)
    missing = [p for p in paths if not p.exists()]
    if missing:
        for p in missing:
            print(f"{p}: listed file does not exist", file=sys.stderr)
        return 2
    found = mentions(paths)
    all_tokens = collections.defaultdict(list)
    for page, tokens in found.items():
        for token, lines in tokens.items():
            all_tokens[token].extend((page, n) for n in lines)

    # --- gate: does every claimed symbol exist? ---
    errors = []
    warnings = []
    claimed = 0
    for token, where in sorted(all_tokens.items()):
        base = token.split("(")[0].strip()
        if base in allow or base in BUILTIN or reasons.get(base):
            continue
        if "." in base:
            head, _, rest = base.partition(".")
            leaf = rest.split(".")[-1].split("(")[0]
            if head[:1].islower():
                # pkg.Symbol: a tcell subpackage, an allow-listed prefix, or nothing we can resolve.
                if head in subpkgs or base in subpkgs:
                    continue
                msg = (f"'{base}' looks like a package reference, but '{head}' is neither a tcell "
                       "subpackage nor an allow-listed prefix (tools/api-allow.txt)")
                (errors if args.strict_dots else warnings).append((token, where, msg))
                continue
            # Type.Member or a chain like pkg.Type.Member: without type info we can only ask whether
            # the leaf name exists anywhere in the package. `Style.SetUnderline` (does not exist
            # anywhere) is caught; `EventKey.Key` (a field, and also a real type name) is not.
            if leaf in symbols or base.split("(")[0] in symbols:
                continue
            claimed += 1
            where_txt = ", ".join(f"{p_}:{n}" for p_, n in where[:3])
            errors.append((token, where, f"'{leaf}' does not exist anywhere in the root package, so "
                           f"'{base}' cannot be right (PLAN.md Appendix A: do not invent API) "
                           f"- cited at {where_txt}"))
            continue
        if not IDENT_RE.match(base) or not base[:1].isupper() or base.isupper():
            continue  # prose, shell words, env vars like TCELL_ALTSCREEN (checked by hand/Phase 6)
        if base in ("Tcell", "TCell", "TCELL"):
            continue
        claimed += 1
        if base in symbols:
            continue
        # A name the library has but not in the root package? (e.g. moved into a subpackage)
        hints = [n for n in symbols if n.lower() == base.lower()]
        where_txt = ", ".join(f"{p}:{n}" for p, n in where[:3])
        errors.append((token, where, f"'{base}' is not an exported symbol of github.com/gdamore/tcell/v3 "
                       + (f"(did you mean '{hints[0]}'?)" if hints else "(no close match in the root package)")
                       + f" - cited at {where_txt}"))

    # --- report: coverage of the surface ---
    total_syms = total_cov = 0
    table = []
    for bucket in sorted(by_bucket):
        names = by_bucket[bucket]
        cov = {n for n in names if n in all_tokens}
        table.append((bucket, len(names), len(cov), sorted(names - cov)))
        total_syms += len(names)
        total_cov += len(cov)

    print(f"surface  {tcell_dir}  ({len(symbols)} exported names in the root package, "
          f"{root_subpkgs} subpackages, {len(allow_subpkgs)} allow-listed package prefix(es))")
    for bucket, n, c, _missing in table:
        bar = f"{100.0 * c / n:5.1f}%" if n else "  n/a"
        print(f"  {bucket:<18} {c:>4}/{n:<4} {bar}")
    print(f"  {'TOTAL':<18} {total_cov:>4}/{total_syms:<4} {100.0 * total_cov / total_syms:5.1f}%"
          f"   ({claimed} page-cited symbol(s) checked)")

    if args.list_uncovered:
        for bucket, _n, _c, miss in table:
            if miss and bucket in ("type", "func", "var"):
                print(f"\nuncovered {bucket}s: {', '.join(miss)}")
            elif miss and bucket not in ("type", "func", "var"):
                print(f"\nuncovered {bucket}: {len(miss)} name(s), first 30: {', '.join(miss[:30])}")

    # --- env var audit (PLAN.md 2: TCELL_ALTSCREEN/TCELL_COLS/TCELL_LINES are implemented but
    # documented nowhere; 8 TCELL_* vars total are a Definition-of-Done item in PLAN.md 13) ---
    implemented = env_vars_in_source(tcell_dir)
    cited_env = {t for t in all_tokens if re.fullmatch(r"TCELL_[A-Z0-9_]+", t)}
    cited_env |= {m for t in all_tokens for m in re.findall(r"TCELL_[A-Z0-9_]+", t)}
    undoc = sorted(implemented - cited_env)
    invented = sorted(cited_env - implemented)
    print(f"env      {len(implemented)} TCELL_* var(s) implemented in the source, "
          f"{len(cited_env & implemented)} documented by these pages")
    if undoc:
        print(f"  undocumented by any page (PLAN.md 13 wants all of them): {', '.join(undoc)}")
    if invented:
        errors.append(("env", [(p_, 0) for p_ in ["(source)"]],
                       f"page(s) document {', '.join(invented)} which the tcell source does not read"))

    # duplicate ownership (PLAN.md 5.4 single-source-of-truth rule)
    dupes = {t: sorted({p for p, _ in where}) for t, where in all_tokens.items()
             if len({p for p, _ in where}) > 1 and t in symbols}
    if dupes:
        print(f"\nnote: {len(dupes)} symbol(s) documented on more than one page (PLAN.md 5.4 wants one owner):")
        for t, pages in sorted(dupes.items()):
            print(f"  {t}: {', '.join(pages)}")

    if args.report:
        out = pathlib.Path(args.report)
        lines = ["# S8.3 symbol coverage - generated by tools/symbol-coverage.py",
                 f"# tcell checkout: {tcell_dir}", "# columns: bucket<TAB>covered<TAB>total", ""]
        lines += [f"{b}\t{c}\t{n}" for b, n, c, _ in table]
        lines += ["", "# uncovered names", ""]
        for b, _n, _c, miss in table:
            for name in miss:
                lines.append(f"{b}\t{name}")
        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"report: {out}")

    for token, where, msg in warnings:
        where_txt = ", ".join(f"{p}:{n}" for p, n in where[:3])
        print(f"WARN  {token}: {msg} - cited at {where_txt}")
    for token, where, msg in errors:
        print(f"BAD SYMBOL  {token}: {msg}")
    if errors:
        print(f"\n{len(errors)} symbol reference(s) a page claims that the library does not have.")
        return 1

    if args.gate:
        kinds = {k.strip() for k in args.gate_kinds.split(",") if k.strip()}
        n = sum(len(names) for b, names in by_bucket.items() if b in kinds)
        c = sum(len({x for x in names if x in all_tokens}) for b, names in by_bucket.items() if b in kinds)
        if n and c < n:
            print(f"COVERAGE  {c}/{n} of {'/'.join(sorted(kinds))} documented; PLAN.md 6.5 wants 100% "
                  "once the coverage-gate question is answered")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
