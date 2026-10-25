# Getting Started

The learn path through _Tcell_: install it, run the demo programs that ship in the library, and write a first program that draws cells, reads a key press, and quits on purpose.

The walk-through itself is the library's [tutorial](https://github.com/gdamore/tcell/blob/main/TUTORIAL.md), which is kept with the code and corrected when the API moves. This page is the way in: what to install, what to run first, what every program contains, and what to read next. It repeats no part of the tutorial, deliberately, because a second copy of a walk-through is a second thing to keep correct.

## Install

_Tcell_ is an ordinary _Go_ library: one requirement line, in a module of your own, in a directory you made.

```console
$ mkdir hello
$ cd hello
$ go mod init example.com/hello
$ go get github.com/gdamore/tcell/v3
```

Write main.go beside go.mod, then `go run .`: the go command reads the import, builds the library and runs the program. What goes into main.go is the tutorial's subject, and the next section puts a program on the screen before there is any code to write. The `go get` line above takes the latest release; the [README](https://github.com/gdamore/tcell/blob/main/README.md) states the _Go_ releases the library supports, the current and the previous one, and the library's own go.mod names the oldest release it builds with. If your toolchain is older, the go command downloads one that fits, unless GOTOOLCHAIN says local, in which case it stops and prints the version it wanted.

## Run the Demos

The library ships eight demo programs, and one command runs the smallest of them from the module you just made, with nothing to clone:

```console
$ go run github.com/gdamore/tcell/v3/demos/hello
```

It centers a greeting, colors it, sets the window title, and quits on ESC. The eight programs, each with a line about what it shows, are listed in [Demos in the Repository](Gallery#demos-in-the-repository), which also gives the commands for running them from a clone of the library.

Read [hello](https://github.com/gdamore/tcell/blob/main/demos/hello/hello.go) as well as run it: it is the shortest of the eight, and every piece in the list below is in it. The library keeps a rendering test for each of the eight, so those programs are code somebody has to keep working, which a copy of one on a wiki never is.

## Before You Start

- A screen needs a terminal that is really there. Opening one is the first thing a program does, and with input and output redirected (a background job, an editor's Run button, a CI job) it fails before drawing anything, with a message naming /dev/tty on the systems that have one. Run the program in a terminal you are looking at.
- Ctrl+C does not stop the program. While a screen is open the terminal is in raw mode, so Ctrl+C arrives as a key press like any other and the program has to decide to quit: the loop in the tutorial quits on ESC and on Ctrl+C.
- The first event is a resize. The screen reports a usable size as soon as Init returns, which is what the demo programs draw from, and a resize event arrives anyway: once at the start, then every time the reader drags the window edge. Draw from the size the screen reports and repaint on that event, so that nothing in the program has to know a number like 80x24.
- What the terminal can do is settled as the screen opens: how many colors it has, and which keyboard protocol it speaks. When either answer is not the one you wanted, [Terminal Setup](Terminal-Setup) is where this wiki covers what a program asks and what the reader can answer from the shell.

## What a Tcell Program Always Contains

Five pieces, in the order a program needs them. The [Usage](https://github.com/gdamore/tcell/blob/main/TUTORIAL.md#usage) section of the tutorial walks every one of them, and the [Demo application](https://github.com/gdamore/tcell/blob/main/TUTORIAL.md#demo-application) is all five in one program that also draws boxes.

- A screen to draw on. Ask the library for one, then open it, and check both results, because a failure here is the terminal rather than the program. Those are the first two calls in the Usage section, and the first two in [hello](https://github.com/gdamore/tcell/blob/main/demos/hello/hello.go) too.
- A style. One default for all text, then one value for each kind of text, made by adding to the default rather than replacing it. [demos/styles](https://github.com/gdamore/tcell/tree/main/demos/styles) is every text style at once, and [demos/colors](https://github.com/gdamore/tcell/tree/main/demos/colors) is the color a style can reach.
- Cells, written into a buffer rather than to the terminal. The drawing calls take a coordinate, some text and a style, and the one that draws a single grapheme at a time hands back whatever is left of the string and the width it used, which is what lets a render function wrap text without measuring it a second time; that function is in the Usage section, and the comment inside it names the case to handle, a grapheme at the end of the string that never finished arriving.
- A loop. Show sends the terminal what changed, and waiting on the event channel returns what came next: a key press, a paste, or an EventResize. A resize means the whole screen has to be drawn again, and that is the whole of [Resize events](https://github.com/gdamore/tcell/blob/main/TUTORIAL.md#resize-events). Nothing arrives from the mouse until the program asks for mouse events ([Mouse events](https://github.com/gdamore/tcell/blob/main/TUTORIAL.md#mouse-events)).
- A way out that leaves the terminal usable. Giving the terminal back is one call, and the hard part is making sure it runs when the program is not quitting on purpose: the Demo application does it behind a recover and raises again afterwards, so that a crash does not hand the reader back a shell in the wrong mode.

In that order the five pieces are a whole program: explained in the tutorial's Usage section, running and tested in [hello](https://github.com/gdamore/tcell/blob/main/demos/hello/hello.go), and drawn with a box to drag in the Demo application.

## Where to Go Next

- Finish the tutorial in this order: [Usage](https://github.com/gdamore/tcell/blob/main/TUTORIAL.md#usage), then the [Demo application](https://github.com/gdamore/tcell/blob/main/TUTORIAL.md#demo-application), then the two sections it leaves for later, [Key events](https://github.com/gdamore/tcell/blob/main/TUTORIAL.md#key-events) and [Mouse events](https://github.com/gdamore/tcell/blob/main/TUTORIAL.md#mouse-events), with the [button table](https://github.com/gdamore/tcell/blob/main/TUTORIAL.md#mouse-buttons) beside them once the program has a mouse.
- [Key event restrictions](https://github.com/gdamore/tcell/blob/main/TUTORIAL.md#key-event-restrictions) says what a terminal cannot tell a program. Read it before writing something that depends on what a key can mean, because it is cheaper to read early than to discover late.
- [Function Reference](Function-Reference) is this wiki's map of what the library provides, by the task in front of you, including the clipboard, the window title, notifications and suspend, none of which the tutorial reaches.
- [Architecture](Architecture) is how a drawing call becomes the fewest bytes this terminal will accept, and how the bytes coming back become the event you waited for.
- [Terminal Setup](Terminal-Setup) covers the terminal itself, and [Gallery](Gallery) is where to find a program like yours, starting with the eight that ship with the library.
- [pkg.go.dev](https://pkg.go.dev/github.com/gdamore/tcell/v3) is the API as the source states it, and [Breaking changes in v3](https://github.com/gdamore/tcell/blob/main/CHANGESv3.md) is the file to open when the program being fixed was written against version 2.
