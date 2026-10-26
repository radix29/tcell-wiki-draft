# Gallery of Tcell Examples

Here's a gallery of applications and libraries that were built using _Tcell_:

To write a program like these, [Getting Started](Getting-Started) starts from an empty directory, and [Home](Home) maps the rest of this wiki.

## Demonstrations

- mouse demo - the mouse test that shipped with _Tcell_ in 2015 ([screenshot](http://2.bp.blogspot.com/-fWvW5opT0es/VhIdItdKqJI/AAAAAAAAATE/7Ojc0L1SpB0/s1600/Screen%2BShot%2B2015-10-04%2Bat%2B11.47.13%2BPM.png)); mouse support is now enabled per program with EnableMouse and MouseFlags
- [gomatrix](https://github.com/gdamore/gomatrix) - converted from Termbox
- [gomandelbrot](https://github.com/rgm3/gomandelbrot) - Mandelbrot!
- [ascii-fluid](https://github.com/esimov/ascii-fluid) - fluid simulation controlled by webcam

## Editors

- [micro](https://github.com/zyedidia/micro/) - lightweight text editor with syntax-highlighting and themes
- [gonano](https://github.com/jbaramidze/gonano) - editor, mimics _nano_
- [aretext](https://github.com/aretext/aretext) - minimalist text editor with _vim_ key bindings

## UI Frameworks 

- [tview](https://github.com/rivo/tview/) - rich interactive widgets
- [cview](https://codeberg.org/tslocum/cview) - user interface toolkit (fork of _tview_)
- [awesome gocui](https://github.com/awesome-gocui/gocui) - Go Console User Interface
- [gowid](https://github.com/gcla/gowid) - compositional widgets for terminal UIs, inspired by _urwid_
- [gruid-tcell](https://github.com/anaseto/gruid-tcell) - driver for the grid based UI and game framework
- [lil](https://github.com/andrievsky/lil) - A simple and flexible interface for any service by implementing only list and get operations
- [cbind](https://codeberg.org/tslocum/cbind) - key event encoding, decoding and handling

## Games

- [proxima5](https://github.com/gdamore/proxima5) - space shooter ([video](https://youtu.be/jNxKTCmY_bQ))
- [go-life](https://github.com/sachaos/go-life) - Conway's Game of Life
- [tpong](https://github.com/spinzed/tpong) - old-school Pong
- [memoryalike](https://github.com/Bios-Marcel/memoryalike) - memorization game
- [uchess](https://github.com/tmountain/uchess) - UCI chess client
- [gokeybr](https://github.com/bunyk/gokeybr) - deliberately practice your typing
- [gosnakego](https://github.com/liweiyi88/gosnakego) - a snake game
- [hero.go](https://github.com/barisbll/hero.go) - 2d monster shooter ([video](https://user-images.githubusercontent.com/40062673/277157369-240d7606-b471-4aa1-8c54-4379a513122b.mp4))
- [go-tetris](https://github.com/aaronriekenberg/go-tetris) - simple tetris game for native terminal and WASM using github actions+pages
- [oddshub](https://github.com/dos-2/oddshub) - A TUI designed for analyzing sports betting odds
- [go-tetris](https://github.com/MichaelS11/go-tetris) - Go Tetris with AI option
- [tiles](https://github.com/16point7/tiles) - a lightweight implementation of 2048
- [myGoAdventure](https://github.com/jagottsicher/myGoAdventure) - Atari2600 "Adventure"-like game for the terminal with Go

## Productivity & Utilities

- [WTF](https://github.com/senorprogrammer/wtf) - personal information dashboard
- [browsh](https://github.com/browsh-org/browsh) - modern web browser ([video](https://www.youtube.com/watch?v=HZq86XfBoRo))
- [godu](https://github.com/viktomas/godu) - utility to discover large files/folders
- [aerc](https://git.sr.ht/~sircmpwn/aerc) - email client
- [tblogs](https://github.com/ezeoleaf/tblogs) - development blogs reader
- [spinc](https://github.com/lallassu/spinc) - _irssi_ inspired chat application for Cisco Spark/WebEx
- [gorss](https://github.com/lallassu/gorss) - RSS/Atom feed reader
- [lf](https://github.com/gokcehan/lf) - file manager
- [goful](https://github.com/anmitsu/goful) - CUI file manager
- [min](https://github.com/a-h/min) - Gemini browser
- [ov](https://github.com/noborus/ov) - file pager
- [tmux-wormhole](https://github.com/gcla/tmux-wormhole) - _tmux_ plugin to transfer files
- [sync](https://github.com/kyprifog/sync) - GitHub repo synchronization tool
- [statusbar](https://github.com/kyprifog/statusbar) - statusbar motivation tool for tracking periodic tasks/goals
- [todo](https://github.com/kyprifog/todo) - simple todo app
- [gbb](https://github.com/sdemingo/gbb) - A classical bulletin board app for tildes or public unix servers
- [fzf](https://github.com/junegunn/fzf) - command-line fuzzy finder
- [termshark](https://termshark.io) - interface for _tshark_, inspired by Wireshark, built on _gowid_
- [keydex](https://github.com/shikaan/keydex) - Terminal-based password manager for KeePass databases
- [tiki](https://github.com/boolean-maybe/tiki) - Markdown workspace for tasks, docs, prompts, and notes stored in your git repo
- [goless](https://github.com/gdamore/goless) - Text file viewer like less, designed for customization and embeddable library
- [goSSMS](https://github.com/radix29/gossms) - SQL Server management studio for Linux, macOS and Windows

## Miscellaneous

- [govisor](https://github.com/gdamore/govisor) - service management UI ([screenshot](http://2.bp.blogspot.com/--OsvnfzSNow/Vf7aqMw3zXI/AAAAAAAAARo/uOMtOvw4Sbg/s1600/Screen%2BShot%2B2015-09-20%2Bat%2B9.08.41%2BAM.png))

## Demos in the Repository

Each program lives in [demos](https://github.com/gdamore/tcell/tree/main/demos) and can be run straight from a clone of the library:

```console
$ git clone https://github.com/gdamore/tcell
$ cd tcell
$ go run ./demos/hello
```

- [beep](https://github.com/gdamore/tcell/tree/main/demos/beep) - rings the terminal bell every three seconds, and on the B key
- [boxes](https://github.com/gdamore/tcell/tree/main/demos/boxes) - draws randomly placed colored boxes and reports the average drawing time per box
- [clipboard](https://github.com/gdamore/tcell/tree/main/demos/clipboard) - demonstrates access to the clipboard
- [colors](https://github.com/gdamore/tcell/tree/main/demos/colors) - cycles the background of a box through the RGB color cube
- [cursors](https://github.com/gdamore/tcell/tree/main/demos/cursors) - sets the cursor style and color from the 0 to 6 keys
- [hello](https://github.com/gdamore/tcell/tree/main/demos/hello) - just prints "Hello, World!"
- [styles](https://github.com/gdamore/tcell/tree/main/demos/styles) - prints one line per text style, including the underline styles and a hyperlink
- [unicode](https://github.com/gdamore/tcell/tree/main/demos/unicode) - prints a month name in several scripts, plus combining marks, emoji and double-wide characters

The `_demos/` directory (mouse.go, notify.go, setsize.go, showcolor.go, sixel.go, stress.go) holds `//go:build ignore` programs: they are not part of the module, so nothing above builds or runs them; to run one, name the file: `go run _demos/mouse.go`. As shipped, `sixel.go` imports `github.com/mattn/go-sixel`, which the module does not require.
