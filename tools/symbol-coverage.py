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
ENV_LIST = W.ROOT / "tools" / "tcell-env-vars.txt"
# Things a page legitimately backticks that are not root-package API: Go builtins, prose shorthands,
# env vars, file names. Format: one pattern per line (fnmatch), '#' comments, with a reason after '#'.
BUILTIN = {"true", "false", "nil", "iota", "int", "rune", "byte", "string", "error", "any", "bool",
           "make", "new", "len", "cap", "append", "panic", "recover", "close", "delete", "copy",
           "main", "init", "context", "fmt", "os", "go", "defer", "range", "chan", "struct", "interface"}
IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
# A backticked path is a claim about the repository, never about the API, and PLAN.md 6.4 wants pages
# to cite files by name (`tscreen.go`, `vt/emulate.go`, `color/fit.go`). Reading those as symbol claims
# would push a writer toward plain text for a file name or toward an allow-list entry per file, and both
# are worse than fixing the tokenizer: the tool that *can* check a path is tools/check-demos.py, and it
# already fails a page that names a demo or a `_demos` file the checkout does not have.
SOURCE_SUFFIX = (".go", ".md", ".yml", ".yaml", ".txt", ".json", ".png", ".mod", ".sum")


def path_like(base: str) -> bool:
    """True for a backticked token that reads as a file or directory rather than a Go identifier."""
    return "/" in base or base.endswith(SOURCE_SUFFIX)

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


def env_names_in_source(tcell: pathlib.Path) -> set:
    """Every environment name the buildable library reads, whatever its prefix (T6.2's list audit).

    Measured the way PLAN.md Appendix C measures: a call of Getenv/LookupEnv/envInt naming it. `_demos`
    and `_test.go` are excluded because neither is built, which is what keeps $SHELL (read by a tagged
    demo program) out of a list whose rule is "what the library honors".
    """
    pat = re.compile(r"\b(?:Getenv|LookupEnv|envInt)\(\s*\"([A-Z][A-Z0-9_]+)\"")
    out = set()
    for path in sorted(tcell.rglob("*.go")):
        rel = path.relative_to(tcell).as_posix()
        if "/testdata/" in f"/{rel}" or path.name.endswith("_test.go") or rel.startswith("_"):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        out.update(pat.findall(text))
    return out


def read_env_list():
    """The reader knobs tools/tcell-env-vars.txt claims, in order, with their reasons."""
    if not ENV_LIST.is_file():
        return None, {}
    names, reasons = [], {}
    for line in ENV_LIST.read_text(encoding="utf-8").splitlines():
        name, _, why = line.partition("#")
        name = name.strip()
        if not name:
            continue
        names.append(name)
        reasons[name] = why.strip()
    return names, reasons


def reader_meets(tcell: pathlib.Path, symbols: set):
    """Which exported API names the library's own prose and demos put in front of a reader.

    TUTORIAL.md, README.md, CHANGESv3.md and every demos/ program - the material a reader reaches for
    next, so it is the priority list inside the structural gate (PLAN.md 6.5, Q-6) rather than a second
    standard. Names are matched against the real surface, so a typo in a doc is not "API a reader met".
    """
    where = collections.defaultdict(set)
    docs = [tcell / "TUTORIAL.md", tcell / "README.md", tcell / "CHANGESv3.md"]
    docs += sorted((tcell / "demos").glob("*/*.go"))
    for doc in docs:
        if not doc.is_file():
            continue
        text = doc.read_text(encoding="utf-8", errors="replace")
        for name in set(re.findall(r"\b[A-Z][A-Za-z0-9]{2,}\b", text)):
            if name in symbols:
                where[name].add(doc.name)
    return where


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
                    help="enforce PLAN.md 6.5 as answered by Q-6: every structural name (types, funcs, "
                         "vars, methods) named by exactly one page, every constant group owned by group")
    ap.add_argument("--gate-kinds", default="type,func,var,method",
                    help="which buckets --gate measures (default type,func,var,method = the structural "
                         "names, as many as the checkout exports today and no fixed number to keep; "
                         "constants are covered by group, never one row per name)")
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
        if path_like(base):
            continue  # a repository path or a source file name, checked by tools/check-demos.py
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

    kinds = {k.strip() for k in args.gate_kinds.split(",") if k.strip()}
    if args.list_uncovered:
        for bucket, _n, _c, miss in table:
            if not miss:
                continue
            if bucket in kinds:
                print(f"\nuncovered {bucket}s: {', '.join(miss)}")
            else:
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

    # --- the reader-knob list (T6.2's guardrail, designed during Phase 5 and landed with its page) ---
    # Three checks, one per direction of the rot PLAN.md 2 records: the source gains a knob nobody names,
    # a knob stops being read and stays documented, a documented knob never made it onto the list.
    listed, env_why = read_env_list()
    if listed is None:
        print(f"envlist  {ENV_LIST.relative_to(W.ROOT)} is missing, so the reader-knob list is unchecked",
              file=sys.stderr)
        return 2
    read = env_names_in_source(tcell_dir)
    documented = {n for n in listed if n in all_tokens}
    print(f"envlist  {len(listed)} reader knob(s) listed, {len(read)} read by the library, "
          f"{len(documented)} documented by these pages")
    if len(listed) != len(set(listed)):
        dups = sorted({n for n in listed if listed.count(n) > 1})
        errors.append(("envlist", [(ENV_LIST.name, 0)],
                       f"{', '.join(dups)} appear twice in the reader-knob list"))
    for name in sorted(set(listed) - read):
        errors.append(("envlist", [(ENV_LIST.name, 0)],
                       f"{name} is listed as a reader knob but the library reads no such variable - "
                       "either the source stopped reading it or the list has a typo"))
    for name in sorted(read - set(listed)):
        errors.append(("envlist", [(ENV_LIST.name, 0)],
                       f"the library reads {name} and tools/tcell-env-vars.txt does not list it, so no "
                       "page is required to document it and it will go the way of TCELL_ALTSCREEN"))
    for name in sorted(set(listed) - documented):
        errors.append(("envlist", [(ENV_LIST.name, 0)],
                       f"{name} is listed ({env_why.get(name, 'no reason given')}) but no built page "
                       "names it in backticks, which is how this tool counts a documented variable"))
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
    gate_dupes = {t: v for t, v in dupes.items()
                  if any(t in names for b, names in by_bucket.items() if b in kinds)}

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
    sym_errs = [e for e in errors if e[0] not in ("env", "envlist")]
    env_errs = [e for e in errors if e[0] in ("env", "envlist")]
    for token, where, msg in sym_errs:
        print(f"BAD SYMBOL  {token}: {msg}")
    for _token, _where, msg in env_errs:
        print(f"BAD ENVVAR  {msg}")
    if errors:
        parts = []
        if sym_errs:
            parts.append(f"{len(sym_errs)} symbol reference(s) a page claims that the library does not have")
        if env_errs:
            parts.append(f"{len(env_errs)} environment finding(s) against tools/tcell-env-vars.txt and "
                         "the built pages")
        print("\n" + "; ".join(parts) + ".")
        return 1

    meets = reader_meets(tcell_dir, symbols)
    print(f"reader   {len(meets)} of the API names appear in the library's own TUTORIAL/README/CHANGES/"
          f"demos - that is the priority list inside the gate (Q-6), missing from pages: "
          f"{len([n for n in meets if n not in all_tokens])}")

    if args.gate:
        print("gate      PLAN.md 6.5 as answered by Q-6: structural names owned by exactly one page, "
              "constant groups owned by group")
        bad = []
        for bucket in sorted(kinds & set(by_bucket)):
            names = by_bucket[bucket]
            miss = sorted(n for n in names if n not in all_tokens)
            if miss:
                bad.append(f"STRUCT  {bucket}: {len(miss)}/{len(names)} named by no page "
                           f"(first 20: {', '.join(miss[:20])})")
        for t, pages in sorted(gate_dupes.items()):
            bad.append(f"SHARE   {t} is owned by {len(pages)} pages ({', '.join(pages)}); 6.5 wants one")
        groups = {b: names for b, names in by_bucket.items() if b.startswith("const ")}
        owned = set()
        for path in paths:
            text = W.read(path)
            for token in re.findall(r"`([A-Za-z][A-Za-z0-9]*)\*`", text):
                owned.add(token)
        unowned = sorted(g for g in groups
                         if re.sub(r"\*$", "", g.split(" ", 1)[1]) not in owned)
        if unowned:
            bad.append(f"GROUP   {len(unowned)}/{len(groups)} constant group(s) no page claims by group "
                       f"(a page must name the group in backticks, e.g. `{unowned[0].split()[1]}...`): "
                       f"{', '.join(g.split()[1] for g in unowned)})")
        for line in bad:
            print(line)
        if bad:
            print(f"\n{len(bad)} gate problem(s). Q-6: 100% of the structural surface, constants by group; "
                  "the 712-name tail is documented by group and linked, never row by row.")
            return 1
        print(f"gate      clean - {sum(len(by_bucket[b]) for b in kinds if b in by_bucket)} structural "
              f"name(s) owned exactly once, {len(groups)} constant group(s) claimed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
