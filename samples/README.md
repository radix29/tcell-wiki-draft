# samples/ - snippet compile harness (S8.1)

This directory is **not** a source of examples and holds no committed example programs. The wiki
links Tcell's own examples instead of re-authoring them:

    The library ships eight runnable programs under `demos/` in github.com/gdamore/tcell, each with a
    rendering test. The Gallery lists them by name and link (`tools/check-demos.py` checks the names,
    URLs and run commands against the checkout, and `go build ./demos/...`); the tutorial and
    `Function-Reference` link a demo beside the API it demonstrates. Code that lives only in a wiki
    fence rots on the next API change - v3 renamed `PutStr`, `SetContent` and `EventKey.Rune`, and the
    first version of this harness caught all three in a page snippet within one run.

What this module is for: the **fragments** a page still needs (a 6-line event-loop skeleton, the one
`Style` call under discussion). `tools/make-samples.py` extracts every `go` fence from the pages that
publish, copies `go.mod`/`go.sum` into a throwaway sandbox, writes the fragments under `gen/`,
retargets the `github.com/gdamore/tcell/v3` dependency at the sibling checkout (or `$TCELL_DIR`, which
is how CI uses a fresh clone), then runs `gofmt -l`, `go vet ./...` and a real link per program.
Nothing is generated into this directory, so there is nothing to keep in sync and nothing to
gitignore.

## Fence markers a page may use

| Fence | Meaning | Checked by |
|---|---|---|
| ` ```go ` | a complete program: `package main` + `func main` | `go vet` + `go build -o bin/...` (link included) |
| ` ```go snippet=name ` | one part of snippet `name`; all fences with the same name concatenate in document order | same, once |
| ` ```go mode=lib ` | a fragment; type-checked, never linked. A fragment without a `package` clause gets `package main` prepended so a page can show a bare function | `go vet ./...` |
| ` ```go mode=skip ` | not Go at all: terminal transcripts, v2-vs-v3 sketches, pseudo-code | nothing (that is the point) |
| ` ```go headless=yes ` | `mode=program` only: after it links, **run it** on the vt emulator (S8.6) | `go test` with `vt.NewMockTerm` + `tcell.ShimScreen`, asserting a non-blank screen and an ESC exit |

`tools/check-style.py` rejects unknown markers, so `mode=libe` or `headless=maybe` fails at commit time
instead of being silently skipped, and `mode=lib headless=yes` is a label error because a fragment has
no `main()` to run. The headless recipe is the library's own (`../tcell/demos/hello/hello_test.go`):
`ShimScreen` makes the mock the screen `tcell.NewScreen()` returns, so a snippet runs unmodified - the
spike behind PLAN.md S8.6 measured 0.3 s per program, and a snippet with no ESC arm fails with that
named as the reason, because a reader must be able to quit it. PLAN.md 7 additionally requires every snippet to be `gofmt`-clean and to **show its
imports**: a `mode=lib` fragment that references `tcell.Screen` without an import block is a page bug,
and the harness says so with that advice.

## Running it

    tools/make-samples.py --list          # what the pages declare, without building
    tools/make-samples.py                 # build everything (CI does exactly this)
    tools/make-samples.py --keep -v       # keep the sandbox and print its path for debugging
    tools/make-samples.py --tcell ../tcell

`go.mod` keeps `replace github.com/gdamore/tcell/v3 => ../../tcell` for local work; the harness
overwrites that replace inside the sandbox, so the repo file stays untouched and `TCELL_DIR` needs no
edit. Do not add a `LICENSE` here (the upstream wiki ships none, so this draft implies none) and do not commit
generated programs - `go.sum` is committed because the sandbox verifies dependency hashes offline.

## Known API facts this harness has already verified against v3

Recorded so nobody re-adds them to a page: `color.Green1` does not exist (v2 name; v3 has
`color.Green`), `PutStr(x, y, string, style)` does not exist (use `PutStrStyled`), `SetContent`
returns no value, `EventKey.Rune()` does not exist (use `EventKey.Str()`, defined when `Key() ==
KeyRune`), `Style` has `Underline(params ...any)` and no `SetUnderline`.
