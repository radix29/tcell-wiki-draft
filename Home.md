# Tcell

_Tcell_ is a cell-based terminal user interface library for _Go_, inspired by _termbox_. A program gets the terminal as a grid of styled cells; the terminal's replies arrive as events. It is low-level: cells, keys, colors, no widgets.

## Why Tcell

- Portable: pure _Go_, no _cgo_.
- Unicode: wide characters and grapheme clusters.
- Keyboard: a modern key protocol makes CTRL-I and TAB different keys.
- Mouse: motion, click-drag and wheel, not only button presses.
- Color: 24-bit, or 8 colors on an old terminal.
- Clipboard, notifications, titles and bracketed paste, when offered.
- Output: only the changed cells are sent.

The library [README](https://github.com/gdamore/tcell/blob/main/README.md) is the long form of that list, and [pkg.go.dev](https://pkg.go.dev/github.com/gdamore/tcell/v3) is the API as the source states it.

## Versions

This wiki documents _Tcell_ v3, imported as `github.com/gdamore/tcell/v3`. Version 3 breaks compatibility with versions 1 and 2, and [Breaking changes in v3](https://github.com/gdamore/tcell/blob/main/CHANGESv3.md) lists what to use instead. Version 2 stays available as `github.com/gdamore/tcell/v2`; version 1 is unmaintained and should not be used.

## Install

Add the library to your own module (_Tcell_ supports the current and previous _Go_ releases).

```console
$ go get github.com/gdamore/tcell/v3
```

Every program starts by opening a screen:

```go
package main

import (
	"log"

	"github.com/gdamore/tcell/v3"
)

func main() {
	s, err := tcell.NewScreen()
	if err != nil {
		log.Fatal(err)
	}
	if err := s.Init(); err != nil {
		log.Fatal(err)
	}
	defer s.Fini()
}
```

See [Getting Started](Getting-Started) for drawing, events and quitting.

## Gallery

The [Gallery](Gallery) lists what people build with _Tcell_, each entry linked to its own repository. It is where to find a real program to read.

## How to Use

- [Getting Started](Getting-Started) - install, the demos that ship in the library, and a first program
- [Architecture](Architecture) - how drawing becomes the fewest bytes a terminal accepts, and how replies become events
- [Function Reference](Function-Reference) - what the library provides, by task not alphabet
- [Terminal Setup](Terminal-Setup) - what a program says as it opens a screen, and what the reader can say from the shell

## Platforms

- POSIX (Linux, FreeBSD, macOS, Solaris): pure _Go_, mainstream systems first.
- Windows: modern Windows on the console VT API, in [README-windows](https://github.com/gdamore/tcell/blob/main/README-windows.md).
- WASM: extra build flags and support files, in [README-wasm](https://github.com/gdamore/tcell/blob/main/README-wasm.md).
- Plan 9: best-effort, in [README-plan9](https://github.com/gdamore/tcell/blob/main/README-plan9.md).

## License

_Tcell_ is free software under the [Apache License 2.0](https://github.com/gdamore/tcell/blob/main/LICENSE) the library ships.
