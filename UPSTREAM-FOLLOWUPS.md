# Follow-ups for `gdamore/tcell` (prepared, not sent)

**Status: parked (Q-2, 2026-10-24).** Nothing in this file was filed as an issue or a pull request, and
nothing here is wiki page content. It is the F-1 bundle from `PLAN.md` plus what this draft's own
measurements turned up, written so a `gdamore/tcell` maintainer can check each claim in a minute and
decide. Filing any of it is a human job and happens only if the draft owner says so.

Every line number is against `gdamore/tcell` at **`acf267d`** ("perf(cell): reuse the drawn width when
putting back the same text"), the checkout the wiki pages were written against. Each item ends with the
command that re-derives it, because "read the source" is not a measurement.

Three things this draft does **not** propose, so nobody has to decline them: a site-wide `_Sidebar.md`
(D-1 is an upstream call and the draft's own prototype stays in the draft), any support or commercial
links (Q-8 declined them), and any license/branding change (the wiki ships no `LICENSE` file because
upstream's wiki ships none).

## 1. One legacy URL in the README

`README.md:32` points at the old wiki URL form:

```
A number of example are posted up on our [Gallery](https://github.com/gdamore/tcell/wikis/Gallery/).
```

That path is a redirect. `https://github.com/gdamore/tcell/wiki/Gallery` is the current form, and it is
the one the wiki itself links. One line, no content change. (The sentence also reads "A number of example
are"; worth a fix while the line is open, but that is a taste call, not a defect.)

```console
$ grep -n "wikis/" README.md
```

## 2. Two pointers from the repo to the wiki

The wiki links the repo everywhere (Q-4: the repo is canonical for prose the library maintains), so the
only missing direction is repo to wiki. Two insertions would close it:

- `README.md`, beside the Gallery line at `:32`: a "Documentation" line pointing at the wiki's
  `Getting-Started`, `Function-Reference` and `Terminal-Setup`.
- `TUTORIAL.md:3` or `README.md:28` (which already links the tutorial and calls it "still somewhat rough"):
  a line saying the tutorial is step one and `Getting-Started` is the map around it.

Nothing is duplicated by this, which is the whole reason it is cheap: the wiki carries no feature essay
and no re-authored sample code, because `README.md`, `TUTORIAL.md` and `demos/` are what it links.

## 3. Environment variables: link the page, do not write the docs

`README.md` names **5** of the 8 `TCELL_*` variables the library reads - `TCELL_TRUECOLOR` (`:112`),
`TCELL_KEYBOARD_PROTOCOL` (`:128`), `TCELL_NEGOTIATE` (`:130`), `TCELL_MOUSE` (`:132`), `TCELL_ESCDELAY`
(`:134`). No markdown doc names `TCELL_ALTSCREEN`, `TCELL_LINES` or `TCELL_COLS` at all, though the
source comments on two of them do (`tscreen.go:80` describes the alternate-screen override, and
`tty/tty_plan9.go:45` plus `:197` describe the size overrides).

Eleven further names are reader knobs and appear in no doc: `TERM`, `COLORTERM`, `NO_COLOR`,
`TERM_PROGRAM`, `TERM_PROGRAM_VERSION`, `LINES`, `COLUMNS`, `LC_ALL`, `LC_CTYPE`, `LANG`,
`RUNEWIDTH_EASTASIAN`.

**What the draft asks for is a link, not a write-up.** The wiki page `Terminal-Setup` documents all 19 -
the value each one listens for, what it overrules, and what it does *not* affect - and every claim there
was measured on the vt emulator rather than read off the source, so a maintainer can re-run the
measurement instead of trusting the prose. Two of the 19 are worth flagging because they surprise people:
`TCELL_LINES` and `TCELL_COLS` are read by exactly one file, the plan 9 console path, and do nothing on
Linux and macOS where the device reports its own size; and `TCELL_ALTSCREEN=disable` beats a program's
own request, which is why it belongs in user-facing docs at all.

```console
$ grep -rnoP 'TCELL_[A-Z_]+' --include='*.go' . | grep -v _test | grep -v _demos | awk -F: '{print $2}' | sort -u
$ grep -n 'TCELL_' README.md
```

## 4. Three doc comments that do not match the code

1. **`Screen.GetClipboard` names the wrong event.** `screen.go:249-252` says the contents come back "using
   an `EventPaste` with the clipboard content as the `Data()` field". `EventPaste` is a bracketed-paste
   marker with three methods (`paste.go:26-48`: `When`, `Start`, `End`) and no `Data`. The reply is an
   `EventClipboard`, which is the type that has `Data()` (`paste.go:58-69`), posted from the OSC 52
   handler at `input.go:872`, and that is what the shipped demo switches on
   (`demos/clipboard/clipboard.go:106-107`). Two words to fix.

2. **A comment ends mid-word.** `screen.go:99-100` reads "It's an alias for ShowCursor(-1, -1).sim" - the
   `.sim` is stray.

3. **`Colors()` documents only the zero case.** `screen.go:145-148` says "returns the number of colors ...
   if a terminal is monochrome, it will return 0". It also answers `1 << 24` = 16777216 when the terminal
   negotiated 24-bit (`tscreen.go:1358-1364`), and a terminal that replies to the startup queries is
   assumed to have color: a guessed zero becomes 8 on a primary-attributes reply that mentions color
   (`tscreen.go:539-540`). Measured on the vt mock, the same `$TERM` produced 8 with negotiation allowed
   and 0 with `TCELL_NEGOTIATE=disable`, which is a fact a program can branch on and cannot learn from the
   comment.

```console
$ sed -n '245,255p;140,150p;95,101p' screen.go
$ sed -n '24,70p' paste.go; sed -n '868,874p' input.go; sed -n '104,108p' demos/clipboard/clipboard.go
$ sed -n '1356,1366p;535,542p' tscreen.go
```

## 5. A defect: `Fini` after a failed `Init` panics

A program that exits when `Init` fails is fine. A program that cleans up first dies in the library:

```
panic: close of nil channel
github.com/gdamore/tcell/v3.(*tScreen).finish(...) tscreen.go:675
github.com/gdamore/tcell/v3.(*tScreen).Fini(...)    tscreen.go:668
```

`Init` (`tscreen.go:395`) returns at `:410-412` when `initialize()` fails, and `t.quit` is only created
later in the same function at `:488`. `Fini` (`:658`) calls `finish` unconditionally through `finiOnce.Do`
(`:668`), and `finish` (`:671`) closes `t.quit` at `:675` - nil, hence the panic. Guarding the close, or
creating the channel in the constructor, fixes it.

Reproduce it in a directory of its own. Any failure of `Init` will do; the run below is a process with no
controlling terminal, which is what a service manager, `setsid -w`, or a CI runner hands out:

```console
$ cat > main.go <<'EOF'
package main

import (
	"fmt"
	"os"

	"github.com/gdamore/tcell/v3"
)

func main() {
	s, err := tcell.NewScreen()
	if err != nil {
		fmt.Println("NewScreen:", err)
		return
	}
	if e := s.Init(); e != nil {
		fmt.Println("Init:", e)
		if len(os.Args) > 1 && os.Args[1] == "cleanup" {
			s.Fini()
			fmt.Println("Fini returned")
		}
	}
}
EOF
$ go mod init probe && go mod edit -replace github.com/gdamore/tcell/v3=../tcell   # your checkout
$ go mod tidy && go build -o probe .
$ env -i PATH=/usr/bin:/bin HOME=/tmp TERM=xterm-256color ./probe            # exits cleanly
$ env -i PATH=/usr/bin:/bin HOME=/tmp TERM=xterm-256color ./probe cleanup    # panics
```

Measured on 2026-10-26 with the checkout above. `PLAN.md` first recorded this as `tscreen.go:676`; the
panic and the source both say **`:675`**, and the plan carries the correction.

## 6. `TUTORIAL.md`: five thin spots, all mechanical

The file is 330 lines and calls itself rough; these are the specific gaps a reader falls into, each with
its line number. None of them is a rewrite, and the wiki does not restate the tutorial (Q-4), so fixing
them upstream is what makes the wiki's links land better.

1. **No module setup.** Nothing in the file mentions `go mod init`, `go get` or a module path, so the
   first fragment cannot be run from an empty directory.
2. **Order.** The event reference comes first: `## Resize events` (`:16`), `## Key events` (`:29`),
   `## Mouse events` (`:57`), and only then `## Usage` (`:89`), which is where a screen is created. A
   beginner meets `EventResize` twenty lines before `NewScreen`.
3. **Fragments do not compile alone.** The file has exactly one import block, at `:182` inside
   `## Demo application`, and earlier fragments use `fmt` and `logMessage` (`:25`, `:42`, `:71`),
   `log.Fatalf` (`:96`, `:99`), `color.Reset` (`:103`) and `os.Exit` (`:154`). `logMessage` is defined
   only by the demo program, so pasting one early fragment into an empty module is four unresolved
   names plus an undefined function.
4. **`Fini` is shown, never explained.** It appears twice (`:153` inside the `quit` closure in `## Usage`,
   `:273` in the demo) and in no sentence; nothing says the terminal is only restored if it runs. The
   draft's earlier note "only in the demo application" was wrong and is corrected here.
5. **Four features absent.** `grep -ic` for clipboard, title, notification and suspend each return 0,
   while all four are in `Screen` (`GetClipboard`/`SetClipboard`, `SetTitle`, `ShowNotification`,
   `Suspend`/`Resume`) and `demos/clipboard` demonstrates two of them.

```console
$ grep -n '^#' TUTORIAL.md
$ grep -n '^import\|logMessage\|log\.\|color\.\|os\.Exit\|Fini' TUTORIAL.md
$ grep -ic clipboard TUTORIAL.md; grep -ic title TUTORIAL.md; grep -ic notif TUTORIAL.md; grep -ic suspend TUTORIAL.md
```

## 7. Six demos have no doc sentence

`demos/hello` (`hello.go:44`) and `demos/clipboard` (`clipboard.go:65-67`) carry a doc comment above
`main`; `beep`, `boxes`, `colors`, `cursors`, `styles` and `unicode` carry none. The wiki's
`## Demos in the Repository` section is generated from those comments where they exist, which is why the
six descriptions currently on the page are a stranger's prose and the two with comments are quoted
verbatim. One sentence per program, in the same voice as the existing two, and the wiki's generator can
drop the six invented lines and take the library's words instead.

```console
$ for d in demos/*/; do printf '%-12s ' "$d"; grep -c '^// This \(program\|demo\|tool\)' "$d$(basename "$d").go"; done
# 1 for hello and clipboard, 0 for the other six
```

## 8. Two Gallery URL moves the wiki draft already made

`Gallery.md` in this draft differs from upstream's by one addition, one reword and two URL moves (plus a
navigation line). The moves are the ones to re-check before re-publishing them upstream, because they
change where a reader is sent. Both point at a project's own home rather than a mirror, on the evidence
below, and both descriptions were left untouched:

| Entry | Was | Now | Evidence (all of it re-checked 2026-10-26) |
|---|---|---|---|
| `cview` | `https://code.rocketnine.space/tslocum/cview` | `https://codeberg.org/tslocum/cview` | the old host does not resolve; `tslocum/cview` on GitHub describes itself as `THIS IS A MIRROR - SEE LINK B...` and names `https://codeberg.org/tslocum/cview` as its homepage; Codeberg's default branch `go.mod` declares `module codeberg.org/tslocum/cview` |
| `cbind` | `https://code.rocketnine.space/tslocum/cbind` | `https://codeberg.org/tslocum/cbind` | the same four checks: no DNS answer, GitHub description `Key event handling library for tcell - THIS IS A MIRROR - SEE LINK BE...`, homepage and module path both Codeberg |

Also recorded rather than hidden: `goSSMS` was added to `## Productivity & Utilities` **at the author's
request**, and the draft owner is that author, so it is flagged as self-submitted wherever the addition
is written down - upstream should treat it as a request to review, not as a curated entry. The legacy
unlinked first bullet in `## Demonstrations` was reworded so it no longer promises a shipped mouse demo
(the only mouse program left is `_demos/mouse.go`, behind `//go:build ignore`), and its two 2015
screenshot hotlinks were kept because they still answer 200 and Q-7 says hotlinks stay until they 404.

```console
$ getent hosts code.rocketnine.space        # no answer, exit 2
$ curl -s https://api.github.com/repos/tslocum/cview | jq -r '.description, .homepage'
$ curl -s https://codeberg.org/tslocum/cview/raw/branch/master/go.mod | head -1
$ curl -s https://codeberg.org/tslocum/cbind/raw/branch/master/go.mod | head -1
$ grep -n "goSSMS\|mouse demo" Gallery.md   # this repo's Gallery page, not tcell's README
```

## 9. How to check the draft itself

`MAINTAINING.md` in this repo is the short version; `tools/review-checklist.py --offline` runs every gate
in one command against a library checkout (`TCELL_DIR=/path/to/tcell` if it is not a sibling directory).
CI is `.github/workflows/qa.yml`, and the published preview is
`https://github.com/radix29/tcell-wiki-draft/wiki`, which is what a page looks like before anyone
proposes it.
