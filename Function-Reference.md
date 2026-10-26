# Function Reference

The reference path through _Tcell_: what the library provides, grouped by the task in front of you rather than by alphabet. Every name the root package exports is here once, with the file that declares it, so the page is a map of the API and a way into the source.

The middle column says what a row is for, not what its Go declaration reads: [pkg.go.dev](https://pkg.go.dev/github.com/gdamore/tcell/v3@main#pkg-index) is the signatures, generated from the same source. The last column names the file a name is declared in, and a row lists two files when a name is both an interface method and the implementation behind it. The [demos](https://github.com/gdamore/tcell/tree/main/demos) are the eight programs that use these names and the [tutorial](https://github.com/gdamore/tcell/blob/main/TUTORIAL.md) walks the common ones.

This page owns the names. [Architecture](Architecture) and [Terminal Setup](Terminal-Setup) write them in plain prose, and a name inside a code fence is code rather than a claim, so a fence on another page is not a second owner.

## Lifecycle

A program that draws anything starts by getting a screen and opening it. What these return is what the rest of this page is written against; what they take is the nine options Terminal Setup owns.

| Symbol | What it does | Where it lives |
|---|---|---|
| `NewScreen` | returns the screen this terminal can give you, taking the options below | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go) |
| `NewTerminfoScreen` | the same screen, for code that wants its dependence on `$TERM` said out loud | [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `NewTerminfoScreenFromTty` | builds that screen on a Tty of your own, which is how a mock or a named device becomes the screen | [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `TerminfoScreenOption` | the type both constructors take the options as, one method deep and closed to anything outside the package | [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `OptColors` | says how many colors there are instead of letting the environment or the reader say, where 0 means none and any count above 256 is how a program asks for 24-bit color | [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `OptTerm` | says what terminal this is instead of reading `$TERM`, which is what a test or an exotic box needs | [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `OptAltScreen` | turns the alternate screen buffer off, on by default, and the reader can still overrule it | [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `OptSanitizeContent` | strips control characters out of text before drawing it, which is slower and harder to attack | [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `OptAdvancedKeys` | asks for the richer key reporting, where CTRL letters and Shift-Tab arrive with different fields filled in | [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `OptKeyboardProtocol` | picks the keyboard protocol instead of negotiating one, and its zero value picks the legacy one | [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `OptNegotiation` | turns the startup conversation with the terminal off, on by default | [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `OptEscapeTimeout` | says how long a lone Escape waits before being called a key | [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `OptControlStringLimit` | caps how much a terminal may send back in one control string | [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `Screen` | the interface every program holds: 43 methods, and the rest of these tables are mostly those | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go) |
| `Init` | opens the screen, and the conversation with the terminal happens here, so draw only after it says yes | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `Fini` | gives the terminal back; a program that never reaches it hands the reader a shell in raw mode | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `Size` | width and height in cells, asked of a screen, of a cell buffer and of a resize event | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [cell.go](https://github.com/gdamore/tcell/blob/main/cell.go), [resize.go](https://github.com/gdamore/tcell/blob/main/resize.go) |
| `Resize` | does nothing on a screen, because a program may not ask a window to change size; `SetSize` tries | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [cell.go](https://github.com/gdamore/tcell/blob/main/cell.go) |
| `ErrNoScreen` | what a constructor answers when there is no terminal to open, redirected input being the usual cause | [errors.go](https://github.com/gdamore/tcell/blob/main/errors.go) |
| `ErrNoCharset` | when the locale names a codeset with no encoder registered; never under UTF-8 | [errors.go](https://github.com/gdamore/tcell/blob/main/errors.go) |
| `ErrEventQFull` | declared for a full event queue, and returned by nothing in v3, so matching on it matches nothing | [errors.go](https://github.com/gdamore/tcell/blob/main/errors.go) |

The failure worth handling is `Init`: a program started with no terminal behind it, from a CI job or a detached shell, gets `ErrNoScreen` there rather than at the first draw.

```go headless=yes
package main

import (
	"log"

	"github.com/gdamore/tcell/v3"
	"github.com/gdamore/tcell/v3/color"
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

	style := tcell.StyleDefault.Foreground(color.GreenYellow).Bold(true)
	for _, line := range []string{"hello", "world"} {
		s.PutStrStyled(1, 1, line, style)
	}
	s.Show()

	for ev := range s.EventQ() {
		switch ev := ev.(type) {
		case *tcell.EventResize:
			w, h := ev.Size()
			s.PutStrStyled(0, h-1, "resized", style)
			s.Show()
			_ = w
		case *tcell.EventKey:
			if ev.Key() == tcell.KeyEsc {
				return
			}
		}
	}
}
```

That is the whole shape of a program, and it is the smallest thing this page can publish that the harness also runs. [Getting Started](Getting-Started) is where the eight demo programs are listed and worth reading instead of writing more here.

## Drawing

Nothing reaches the terminal until Show is asked for it, which is what lets a program write a frame in any order. The buffer is logical state: what it holds is what will be displayed, which is not necessarily what is displayed now.

| Symbol | What it does | Where it lives |
|---|---|---|
| `Put` | writes the first grapheme of a string at a cell and hands back the rest of the string and the width it used | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [cell.go](https://github.com/gdamore/tcell/blob/main/cell.go) |
| `PutStr` | writes a string in the default style, clipped to the screen | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go) |
| `PutStrStyled` | the same with a style given, which is the call most of the demos actually use | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go) |
| `SetContent` | writes one cell from a primary rune plus any combining runes, for code building cells by hand | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go) |
| `Clear` | erases the logical screen, the short form of filling it with spaces in the default style | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go) |
| `Fill` | fills every cell with one rune and style, the other half of what Clear is a shortcut for | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [cell.go](https://github.com/gdamore/tcell/blob/main/cell.go) |
| `FillArea` | fills a rectangle and ignores whatever falls outside the screen, so a box may overflow on purpose | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [cell.go](https://github.com/gdamore/tcell/blob/main/cell.go) |
| `SetStyle` | sets the style used for clearing and whatever `StyleDefault` means here | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `Show` | sends the changed cells, in the least disruptive way the library can manage | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `Sync` | Show for a screen believed corrupt: redraws every cell instead of only the changed ones | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |

A wide grapheme takes two cells and writing into the cell beside it has undefined results; started in the last column it becomes a space on output. [demos/cursors](https://github.com/gdamore/tcell/tree/main/demos/cursors) writes single graphemes with `Put` on purpose, and its resize handler is the reason `Sync` exists.

## Reading Content Back

A screen answers questions about what it holds. These are logical reads: they report what the next Show would send, not what the terminal is showing.

| Symbol | What it does | Where it lives |
|---|---|---|
| `Get` | the string, style and cell width at a position, and empty values when the position is off screen | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [cell.go](https://github.com/gdamore/tcell/blob/main/cell.go) |
| `Dirty` | whether this cell has to be sent again, the comparison the drawing loop makes per cell | [cell.go](https://github.com/gdamore/tcell/blob/main/cell.go) |
| `SetDirty` | records that a cell was or was not sent, for code that draws on the screen's behalf | [cell.go](https://github.com/gdamore/tcell/blob/main/cell.go) |
| `Invalidate` | marks every cell dirty, which is what a resize and `Sync` do before redrawing | [cell.go](https://github.com/gdamore/tcell/blob/main/cell.go) |
| `CellBuffer` | the grid of cells behind a screen, exported for screen implementations rather than for programs | [cell.go](https://github.com/gdamore/tcell/blob/main/cell.go) |

A program is never handed a screen's buffer: `GetCells` is not on the Screen interface, and it is named below with the rest of that group.

## Styles and Color

A style is a value you declare once and copy by changing one thing. Every setter returns a new style, so a program keeps its look in a handful of package-level values instead of threading colors through every call.

| Symbol | What it does | Where it lives |
|---|---|---|
| `Style` | what a cell carries: two colors, the attributes, an underline and perhaps a link | [style.go](https://github.com/gdamore/tcell/blob/main/style.go) |
| `StyleDefault` | the zero style, meaning whatever this terminal thinks text looks like until told | [style.go](https://github.com/gdamore/tcell/blob/main/style.go) |
| `Foreground` | returns a style with the text color changed | [style.go](https://github.com/gdamore/tcell/blob/main/style.go) |
| `Background` | returns a style with the background color changed | [style.go](https://github.com/gdamore/tcell/blob/main/style.go) |
| `Normal` | drops every attribute and keeps both colors | [style.go](https://github.com/gdamore/tcell/blob/main/style.go) |
| `Bold` | bold, which some terminals draw heavier and others brighter | [style.go](https://github.com/gdamore/tcell/blob/main/style.go) |
| `Blink` | blink, which many terminals ignore and some render as bright | [style.go](https://github.com/gdamore/tcell/blob/main/style.go) |
| `Dim` | faint text | [style.go](https://github.com/gdamore/tcell/blob/main/style.go) |
| `Italic` | italic | [style.go](https://github.com/gdamore/tcell/blob/main/style.go) |
| `Reverse` | swap the two colors | [style.go](https://github.com/gdamore/tcell/blob/main/style.go) |
| `StrikeThrough` | crossed-out text | [style.go](https://github.com/gdamore/tcell/blob/main/style.go) |
| `Underline` | underline, taking a bool for a plain one, an underline shape, or a color, in any combination | [style.go](https://github.com/gdamore/tcell/blob/main/style.go) |
| `Url` | attaches a link to text, for terminals that render hyperlinks | [style.go](https://github.com/gdamore/tcell/blob/main/style.go) |
| `UrlId` | the same link by id, with the URL registered elsewhere | [style.go](https://github.com/gdamore/tcell/blob/main/style.go) |
| `HasBold`, `HasBlink`, `HasReverse`, `HasItalic`, `HasDim`, `HasStrikeThrough`, `HasUnderline` | asks a style which attributes it has, one predicate per attribute | [style.go](https://github.com/gdamore/tcell/blob/main/style.go) |
| `GetForeground`, `GetBackground`, `GetUnderlineStyle`, `GetUnderlineColor`, `GetUrl` | reads a style back: two colors, the underline's shape and color, and the link with its id | [style.go](https://github.com/gdamore/tcell/blob/main/style.go) |
| `UnderlineStyle` | the shapes an underline comes in: none, solid, double, curly, dotted, dashed | [style.go](https://github.com/gdamore/tcell/blob/main/style.go) |
| `AttrMask` | the bit set the attributes are stored as, on a type whose own comment tells applications not to use it | [attr.go](https://github.com/gdamore/tcell/blob/main/attr.go) |
| `Attributes` | sets several attributes at once from a mask, and is deprecated because the mask is | [style.go](https://github.com/gdamore/tcell/blob/main/style.go) |
| `GetAttributes` | reads them back the same way, for the same deprecated reason | [style.go](https://github.com/gdamore/tcell/blob/main/style.go) |
| `Color` | the color value a style takes, declared in the color subpackage and aliased here | [color.go](https://github.com/gdamore/tcell/blob/main/color.go) |
| `NewRGBColor` | a color from three channels, one of the four deprecated ways to name one | [color.go](https://github.com/gdamore/tcell/blob/main/color.go) |
| `NewHexColor` | a color from one 24-bit value, the form that reads like a CSS hex triple | [color.go](https://github.com/gdamore/tcell/blob/main/color.go) |
| `PaletteColor` | a color from a palette index below 256 | [color.go](https://github.com/gdamore/tcell/blob/main/color.go) |
| `FromImageColor` | a color from an image color, for a program that already has pixels | [color.go](https://github.com/gdamore/tcell/blob/main/color.go) |
| `GetColor` | a color from a W3C name such as tomato, or from a hex string | [color.go](https://github.com/gdamore/tcell/blob/main/color.go) |
| `FindColor` | the nearest color in a palette you supply, which is how an RGB value gets fitted to eight colors | [color.go](https://github.com/gdamore/tcell/blob/main/color.go) |
| `ColorNames` | the map from a name to a color | [color.go](https://github.com/gdamore/tcell/blob/main/color.go) |
| `ColorValues` | the map from a color to its red, green and blue | [color.go](https://github.com/gdamore/tcell/blob/main/color.go) |

The whole root-level color API is deprecated, this page's rows included: the file says so at its top and the color constants repeat it block by block. New code takes colors from [color](https://github.com/gdamore/tcell/tree/main/color) and there is nothing to convert.

## Cursors

Four calls and one type, and shapes are the part of a terminal most likely to ignore you.

| Symbol | What it does | Where it lives |
|---|---|---|
| `ShowCursor` | puts the cursor at a cell, and hides it if the position is off screen or is -1, -1 | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `HideCursor` | hides it, which the doc comment calls an alias for showing it at -1, -1 | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `GetCursor` | where it was last told to be; a negative pair reads back as -1, -1, which is all HideCursor does, while an off-screen position comes back exactly as it was given and is hidden only on output | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `SetCursorStyle` | asks for a shape, a blink state and a color, and does nothing on a terminal that cannot | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go) |
| `CursorStyle` | the shapes: block, bar or underline, each one steady or blinking | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go) |

[demos/cursors](https://github.com/gdamore/tcell/tree/main/demos/cursors) draws every shape with its name beside it, which is the quickest way to find out what your own terminal supports.

## Input and Events

One channel, one select, one type switch. Events are values, so a program decides what it cares about instead of installing callbacks, and the tutorial's [Demo application](https://github.com/gdamore/tcell/blob/main/TUTORIAL.md#demo-application) is this loop with a box to drag.

| Symbol | What it does | Where it lives |
|---|---|---|
| `EventQ` | the channel every event arrives on, open until Fini and never to be written to after it | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `Event` | the interface all of them satisfy, which is how a select reads them | [event.go](https://github.com/gdamore/tcell/blob/main/event.go) |
| `When` | when an event happened, carried by the events that have a stamp at all | [event.go](https://github.com/gdamore/tcell/blob/main/event.go), [paste.go](https://github.com/gdamore/tcell/blob/main/paste.go) |
| `EventTime` | the base event that holds that stamp, embeddable in an event of your own | [event.go](https://github.com/gdamore/tcell/blob/main/event.go) |
| `SetEventTime` | sets a stamp, for a program queueing its own events | [event.go](https://github.com/gdamore/tcell/blob/main/event.go) |
| `SetEventNow` | sets it to now, which every constructor in the library calls | [event.go](https://github.com/gdamore/tcell/blob/main/event.go) |
| `EventHandler` | for code that takes an event and says whether it consumed it | [event.go](https://github.com/gdamore/tcell/blob/main/event.go) |
| `HandleEvent` | that one method, taking the event and answering true or false | [event.go](https://github.com/gdamore/tcell/blob/main/event.go) |
| `EventInterrupt` | a wakeup a program posts to itself to leave a blocking select | [interrupt.go](https://github.com/gdamore/tcell/blob/main/interrupt.go) |
| `EventError` | an error carried as an event, so a failure inside a goroutine reaches the loop | [errors.go](https://github.com/gdamore/tcell/blob/main/errors.go) |
| `Error` | lets an `EventError` satisfy the error interface too, reading as its payload's message | [errors.go](https://github.com/gdamore/tcell/blob/main/errors.go) |
| `Unwrap` | the payload again, so errors.Is and errors.As work through the event | [errors.go](https://github.com/gdamore/tcell/blob/main/errors.go) |
| `EventKey` | a key press or release, what most programs switch on | [key.go](https://github.com/gdamore/tcell/blob/main/key.go) |
| `Key` | the virtual key code, and the method on a key event that answers with it | [key.go](https://github.com/gdamore/tcell/blob/main/key.go) |
| `Str` | the text a key produced, defined only when the key is `KeyRune` | [key.go](https://github.com/gdamore/tcell/blob/main/key.go) |
| `Name` | the key's printable name, such as F3 or Enter, for echoing and for config files | [key.go](https://github.com/gdamore/tcell/blob/main/key.go) |
| `KeyNames` | the map the library ships those names in, for a program writing a key binding file | [key.go](https://github.com/gdamore/tcell/blob/main/key.go) |
| `Physical` | which physical key was pressed, which is a different question from what it typed | [key.go](https://github.com/gdamore/tcell/blob/main/key.go) |
| `Pressed` | press or release; legacy keyboards only ever report presses | [key.go](https://github.com/gdamore/tcell/blob/main/key.go) |
| `Repeat` | how many repeats this event covers; legacy keyboards send one event per repeat instead | [key.go](https://github.com/gdamore/tcell/blob/main/key.go) |
| `Modifiers` | which modifiers came with a key or a mouse report, on both of those event types | [key.go](https://github.com/gdamore/tcell/blob/main/key.go), [mouse.go](https://github.com/gdamore/tcell/blob/main/mouse.go) |
| `ModMask` | the type a modifier set is stored as, on a page that cannot promise every bit arrives | [key.go](https://github.com/gdamore/tcell/blob/main/key.go) |
| `KeyProtocol` | which keyboard protocol the terminal agreed to, which decides what the five rows above can say | [key.go](https://github.com/gdamore/tcell/blob/main/key.go) |
| `KittyKbdMode` | the kitty protocol's own mode bits, for a program that has to ask for one of them | [input.go](https://github.com/gdamore/tcell/blob/main/input.go) |
| `XtermKbdMode` | the same idea for xterm's modifyOtherKeys, with fewer bits to choose from | [input.go](https://github.com/gdamore/tcell/blob/main/input.go) |
| `EventResize` | the screen changed size, the one event a program has to answer by redrawing | [resize.go](https://github.com/gdamore/tcell/blob/main/resize.go) |
| `PixelSize` | the new size in pixels rather than cells, which is what a program drawing boxes wants | [resize.go](https://github.com/gdamore/tcell/blob/main/resize.go) |
| `WindowSize` | the two sizes together, the type a resize event is built out of | [resize.go](https://github.com/gdamore/tcell/blob/main/resize.go) |
| `EventPaste` | the start or end marker around a bracketed paste | [paste.go](https://github.com/gdamore/tcell/blob/main/paste.go) |
| `Start` | true on the event that opens a paste | [paste.go](https://github.com/gdamore/tcell/blob/main/paste.go) |
| `End` | true on the one that closes it, the two being one method's two answers | [paste.go](https://github.com/gdamore/tcell/blob/main/paste.go) |
| `EnablePaste` | asks for paste boundaries, without which a pasted file arrives as typing | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `DisablePaste` | stops asking for them | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `EventFocus` | the terminal window or tab gained or lost focus | [focus.go](https://github.com/gdamore/tcell/blob/main/focus.go) |
| `EnableFocus` | asks for those events, which a program that pauses in the background wants | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `DisableFocus` | stops asking | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `NewEventKey` | builds a key event from a captured sequence, for a program replaying recorded input | [key.go](https://github.com/gdamore/tcell/blob/main/key.go) |
| `NewEventKeyEx` | the same with the extended fields: press state, physical key, repeat count | [key.go](https://github.com/gdamore/tcell/blob/main/key.go) |
| `NewEventResize` | builds a resize event from a size in cells | [resize.go](https://github.com/gdamore/tcell/blob/main/resize.go) |
| `NewEventPaste` | builds one half of a paste pair | [paste.go](https://github.com/gdamore/tcell/blob/main/paste.go) |
| `NewEventFocus` | builds a focus event in either direction | [focus.go](https://github.com/gdamore/tcell/blob/main/focus.go) |
| `NewEventError` | wraps an error as an event | [errors.go](https://github.com/gdamore/tcell/blob/main/errors.go) |
| `NewEventInterrupt` | builds a wakeup, optionally carrying a payload | [interrupt.go](https://github.com/gdamore/tcell/blob/main/interrupt.go) |

```go mode=lib snippet=events
package main

import (
	"github.com/gdamore/tcell/v3"
)

// The loop every _Tcell_ program has, with the two events most programs answer.
func loop(s tcell.Screen) bool {
	select {
	case ev := <-s.EventQ():
		switch ev := ev.(type) {
		case *tcell.EventResize:
			s.Clear()
		case *tcell.EventKey:
			if ev.Key() == tcell.KeyEsc {
				return false
			}
		}
	}
	return true
}
```

The queue is 128 events deep and, once it is full, the library waits rather than dropping anything, so a program that stops reading also stops its own input. Every Screen method takes the screen's lock, which is what makes drawing from another goroutine allowed; writing into the channel after Fini is not, and that is the deadlock [the tutorial](https://github.com/gdamore/tcell/blob/main/TUTORIAL.md#demo-application) warns about.

## Mouse

Nothing arrives from a mouse until it is asked for, and how much arrives depends on the terminal more than on the flags. The library ships no mouse program to run: the old mouse test is `_demos/mouse.go` under a build tag, and the [Gallery](Gallery#demos-in-the-repository) note says what that costs.

| Symbol | What it does | Where it lives |
|---|---|---|
| `EnableMouse` | turns mouse reporting on, and reports everything when given no flag | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `DisableMouse` | turns it off again | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `MouseFlags` | which events to report: presses, drags, all motion, or coordinates in pixels | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go) |
| `EventMouse` | one report, carrying buttons, modifiers and a position | [mouse.go](https://github.com/gdamore/tcell/blob/main/mouse.go) |
| `Position` | where the mouse was, in cells unless pixel mode was asked for, counted from the top left | [mouse.go](https://github.com/gdamore/tcell/blob/main/mouse.go) |
| `Buttons` | which buttons are down, or which wheel step arrived | [mouse.go](https://github.com/gdamore/tcell/blob/main/mouse.go) |
| `ButtonMask` | the type a set of buttons and wheel directions is stored as | [mouse.go](https://github.com/gdamore/tcell/blob/main/mouse.go) |
| `NewEventMouse` | builds a report at a position with buttons and modifiers, mostly for screen implementations | [mouse.go](https://github.com/gdamore/tcell/blob/main/mouse.go) |

```go mode=lib snippet=mouse
package main

import (
	"github.com/gdamore/tcell/v3"
)

// Drags need a button held down, so the two lower flags are what most programs want.
func ask(s tcell.Screen) {
	s.EnableMouse(tcell.MouseButtonEvents, tcell.MouseDragEvents)
	defer s.DisableMouse()
}
```

Most terminals cannot report more than one button at a time and several report no motion unless a button is held, so a program that reacts to hovering works in some terminals and not others.

## Clipboard, Title and Notifications

Three things a terminal may refuse, each worth a fallback because the answer belongs to the terminal and not to the program.

| Symbol | What it does | Where it lives |
|---|---|---|
| `SetClipboard` | posts bytes to the system clipboard, any bytes, an empty one clearing it | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `GetClipboard` | asks for the clipboard, the answer arriving later as its own event | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `HasClipboard` | whether the screen claims to have one, which is a weak answer in both directions | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `EventClipboard` | the clipboard's contents, which arrive in reply to a request | [paste.go](https://github.com/gdamore/tcell/blob/main/paste.go) |
| `Data` | the bytes inside it, which need not be text, on this event and on a wakeup | [paste.go](https://github.com/gdamore/tcell/blob/main/paste.go), [interrupt.go](https://github.com/gdamore/tcell/blob/main/interrupt.go) |
| `NewEventClipboard` | builds one around a payload | [paste.go](https://github.com/gdamore/tcell/blob/main/paste.go) |
| `SetTitle` | sets the window title, which a terminal may be configured to ignore | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `ShowNotification` | raises a desktop notification, and only terminals with OSC 777 can raise one | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `Beep` | sounds the alarm, answering with an error when the system cannot | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |

Reading the clipboard can be refused for security even where writing works, and plenty of terminals that can read it do not say so, so `HasClipboard` answering false settles nothing. [demos/clipboard](https://github.com/gdamore/tcell/tree/main/demos/clipboard) is the one program that asks for both directions.

## Terminal Introspection

Five questions about the terminal the program is standing in. The answers are settled while Init runs and do not change underneath a program afterwards.

| Symbol | What it does | Where it lives |
|---|---|---|
| `Colors` | how many colors this terminal has, where zero means monochrome and 16777216 means 24-bit color is what this screen sends, which no other call tells a program | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `Terminal` | the terminal's name and version, either one empty when it never said | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `Tty` | the device underneath, when this screen is a terminal at all | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [tty.go](https://github.com/gdamore/tcell/blob/main/tty.go) |
| `CharacterSet` | the locale's codeset, for diagnostics: text is translated to UTF-8 either way | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `KeyboardProtocol` | which keyboard protocol is in force, and therefore what a key event can distinguish | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |

`Colors` is the answer a style needs before choosing between a truecolor value and a palette index, and [Terminal Setup](Terminal-Setup) is where a reader can overrule it.

## Advanced Hooks

The parts of a screen a normal program never reaches for, each listed because something that is not a normal program needs it.

| Symbol | What it does | Where it lives |
|---|---|---|
| `Suspend` | hands the terminal back to the reader, to run a sub-shell and then come again | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `Resume` | takes it back, switching the modes on from what Init already learned | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `SetSize` | tries to resize the window, which the modern Windows Terminal refuses | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `LockRegion` | stops a rectangle of cells from ever being drawn, for a picture written straight at the terminal | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go) |
| `LockCell` | the same rule one cell at a time, the cell marked clean so nothing is sent to it | [cell.go](https://github.com/gdamore/tcell/blob/main/cell.go) |
| `UnlockCell` | takes the rule off and marks the cell dirty, so the next Show puts it back | [cell.go](https://github.com/gdamore/tcell/blob/main/cell.go) |
| `ShimScreen` | replaces the screen NewScreen returns, which is how all eight demo tests run with nobody watching | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go) |
| `NewDevTty` | opens the process's own terminal as a Tty, which a screen normally does for itself | [tty](https://github.com/gdamore/tcell/tree/main/tty) |
| `NewDevTtyFromDev` | opens a named device instead, and answers with an error on Windows, where there is no such thing | [tty](https://github.com/gdamore/tcell/tree/main/tty) |
| `NewStdIoTty` | opens standard input and output as a Tty, for a screen with no device behind it | [tty](https://github.com/gdamore/tcell/tree/main/tty) |
| `Read`, `Write`, `Close`, `Start`, `Stop`, `Drain`, `NotifyResize` | the seven a Tty adds, once you have one: raw mode on and off, bytes both ways, and a resize nudge | [tty/tty.go](https://github.com/gdamore/tcell/blob/main/tty/tty.go) |
| `RegisterRuneFallback` | says what to draw for a glyph this terminal may lack, ASCII replacements being the point | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `UnregisterRuneFallback` | removes one, implicit ones included, and an unmapped glyph becomes a question mark | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `RuneFallbacks` | the map of implicit fallbacks the library ships, which a program may change | [runes.go](https://github.com/gdamore/tcell/blob/main/runes.go) |
| `RegisterEncoding` | adds a codeset for a locale that is not UTF-8, which is the fix for an old or exotic system | [encoding.go](https://github.com/gdamore/tcell/blob/main/encoding.go) |
| `GetEncoding` | looks a codeset up, and answers nil for UTF-8 and ASCII because those need no encoder | [encoding.go](https://github.com/gdamore/tcell/blob/main/encoding.go) |
| `SetEncodingFallback` | says what to do when the locale names a codeset nobody registered | [encoding.go](https://github.com/gdamore/tcell/blob/main/encoding.go) |
| `EncodingFallback` | the three available answers: fall back to UTF-8, fall back to ASCII, or fail | [encoding.go](https://github.com/gdamore/tcell/blob/main/encoding.go) |

```go mode=lib snippet=mock
package main

import (
	"github.com/gdamore/tcell/v3"
	"github.com/gdamore/tcell/v3/vt"
)

// A screen built for a test instead of for a reader: the emulator is the Tty.
func mock() (tcell.Screen, error) {
	mt := vt.NewMockTerm(vt.MockOptColors(8))
	s, err := tcell.NewTerminfoScreenFromTty(mt, tcell.OptColors(8), tcell.OptTerm("ansi"))
	if err != nil {
		return nil, err
	}
	tcell.ShimScreen(s)
	return s, nil
}
```

That recipe is the library's own, taken from a demo test, and it is what a wiki snippet needs to be run rather than merely compiled.

## Names No Program Calls

Eleven names are in the exported surface and reachable by nothing a program can write: the interface that holds three of them carries a comment saying those are not part of the Screen API. They are listed anyway, because a coverage report that skipped them would describe a smaller library than the one a program imports.

| Symbol | What it does | Where it lives |
|---|---|---|
| `GetCells` | hands the buffer to the layer above a screen implementation, and is not on the Screen interface | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `StopQ` | a channel Fini closes and Suspend leaves open, which is how the loops are stopped | [screen.go](https://github.com/gdamore/tcell/blob/main/screen.go), [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `SetCursor` | the cursor call underneath SetCursorStyle, taking one style and one color instead of a slice | [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `Print` | writes to the terminal without converting a string to bytes first, for the startup bursts | [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `Printf` | formats into the terminal buffer, which is how titles and sequences get sent | [tscreen.go](https://github.com/gdamore/tcell/blob/main/tscreen.go) |
| `Scan` | runs the parser over bytes already read, the main loop's half of the work | [input.go](https://github.com/gdamore/tcell/blob/main/input.go) |
| `ScanUTF8` | the same over a UTF-8 buffer, the path a UTF-8 terminal takes | [input.go](https://github.com/gdamore/tcell/blob/main/input.go) |
| `SetEscapeTimeout` | gives the parser how long to wait for bytes that may follow an Escape | [input.go](https://github.com/gdamore/tcell/blob/main/input.go) |
| `SetKeyboardProtocol` | tells the parser which protocol to read the replies as | [input.go](https://github.com/gdamore/tcell/blob/main/input.go) |
| `SetPixelMouse` | switches the parser to reading mouse reports as pixel coordinates | [input.go](https://github.com/gdamore/tcell/blob/main/input.go) |
| `WaitDuration` | how long the parser may hold an incomplete sequence before giving up on it | [input.go](https://github.com/gdamore/tcell/blob/main/input.go) |

A program that wants the first two can reach the same door through `Tty` and the event channel; a program that wants the last six is writing a screen, and [vt](https://github.com/gdamore/tcell/tree/main/vt) is where that work already lives.

## Constants by Group

712 constants, and no reader studies 712 rows. Each group is one row: what the names are for, and where the list of them is kept. This is the section that owns the groups, so a page that says something about a group says it here.

| Symbol | What it does | Where it lives |
|---|---|---|
| `Color*` | the 392 named colors: sixteen ANSI and bright variants, the 216-color cube, the grey ramp, then the W3C names over the top | [pkg.go.dev](https://pkg.go.dev/github.com/gdamore/tcell/v3@main#pkg-constants) |
| `Key*` | 214 virtual key codes: printable aliases, function keys, editing keys, physical key names, the legacy CTRL letters | [pkg.go.dev](https://pkg.go.dev/github.com/gdamore/tcell/v3@main#Key) |
| `Rune*` | 32 box-drawing and graphical glyphs, named after the terminfo strings they stand in for | [pkg.go.dev](https://pkg.go.dev/github.com/gdamore/tcell/v3@main#pkg-constants) |
| `Mod*` | 16 modifier bits, every one of them either plain or left and right variants | [pkg.go.dev](https://pkg.go.dev/github.com/gdamore/tcell/v3@main#ModMask) |
| `Button*` | eight mouse buttons including the thumb buttons, as the mask a mouse report carries | [pkg.go.dev](https://pkg.go.dev/github.com/gdamore/tcell/v3@main#ButtonMask) |
| `Wheel*` | the four wheel directions, declared in the same block as the buttons and reported the same way | [pkg.go.dev](https://pkg.go.dev/github.com/gdamore/tcell/v3@main#ButtonMask) |
| `Attr*` | the eight attribute bits behind the deprecated mask calls, where underline is deliberately not one of them | [pkg.go.dev](https://pkg.go.dev/github.com/gdamore/tcell/v3@main#AttrMask) |
| `CursorStyle*` | the seven cursor shapes, six of them one shape in two blink states | [pkg.go.dev](https://pkg.go.dev/github.com/gdamore/tcell/v3@main#pkg-constants) |
| `Underline*` | the six underline shapes, from none and solid up through curly and dashed | [pkg.go.dev](https://pkg.go.dev/github.com/gdamore/tcell/v3@main#pkg-constants) |
| `Mouse*` | the four mouse flags: three levels of events, plus pixel coordinates as a modifier on them | [pkg.go.dev](https://pkg.go.dev/github.com/gdamore/tcell/v3@main#pkg-constants) |
| `Kitty*` | the kitty protocol's mode bits, and the protocol's own entry in the KeyProtocol list | [pkg.go.dev](https://pkg.go.dev/github.com/gdamore/tcell/v3@main#pkg-constants) |
| `Xterm*` | xterm modifyOtherKeys modes, a shorter list with the same job | [pkg.go.dev](https://pkg.go.dev/github.com/gdamore/tcell/v3@main#pkg-constants) |
| `Encoding*` | the three things GetEncoding can do when it has nothing to hand out | [pkg.go.dev](https://pkg.go.dev/github.com/gdamore/tcell/v3@main#pkg-constants) |
| `other*` | the three KeyProtocol values left over once the prefixes are sorted, named here because the grouping puts them alone | [pkg.go.dev](https://pkg.go.dev/github.com/gdamore/tcell/v3@main#KeyProtocol) |

Two groups are documented on pkg.go.dev beside the type they belong to rather than in the flat list, and the `Color*` block carries a deprecation over the whole of it, the same notice the color rows above carry.

## Subpackages

Four packages sit under the root one, and none of them is what an application reaches for first.

`color` is where colors are actually declared, the root package's color API being an alias with a deprecation over it: take color values, `color.Names` and the palette fitting of `color.Find` from here, and import one package less than a program that needs `tcell` for a color would.

`encoding` exists so that a locale which is not UTF-8 can be served at all; `encoding.Register` adds every codeset the _golang.org/x/text_ tables hold, which is the difference between a binary that runs anywhere and one that runs on a modern system.

`tty` holds the device interface and the three ways to open one: the process terminal, a named device, or standard input and output. A program needs it to write a screen for something that is not a terminal, or to test one.

`vt` is a terminal emulator: coordinates, colors, modes, cells, a parser and a backend interface, plus `vt.MockTerm`, the mock the eight demo tests are drawn on. An application uses it to test what it draws, and nothing else in the package set is worth reaching into as rarely.

A surface dumper counts five, because `internal/widthutil` is also a directory of Go files. It holds the display-width helper the root package measures text with, and the RUNEWIDTH_EASTASIAN toggle [Terminal Setup](Terminal-Setup) documents is read there; nothing can import an internal package from outside the module, which is why this page lists four.

## See Also

- [Getting Started](Getting-Started) - the same API as a walk-through, and where the eight demo programs are listed
- [Architecture](Architecture) - why a drawing call costs the terminal only what actually changed
- [Terminal Setup](Terminal-Setup) - the nine options named above, and what a reader can say from the shell instead
- [Gallery](Gallery) - programs built with all of it
