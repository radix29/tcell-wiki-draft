# Terminal Setup

For the reader whose terminal misbehaves: how _Tcell_ decides what a terminal can do, what a program can say when it opens a screen, and what the reader can say from the shell to overrule it. Read it when colors come out wrong, when the mouse is ignored, when a lone Escape is slow, or when a program starts slowly enough to notice.

## How a Screen Decides

A screen answers three questions before it draws anything. The options a program passes when it builds the screen set the floor. Opening the screen then reads the environment, which can still change the answer. Last comes one conversation with the terminal, which lasts at most a second and ends as soon as the device attributes reply: whatever arrives replaces the guess, so a terminal that mentions color turns a count of zero into eight, and one that mentions OSC 52 makes the clipboard a real capability instead of a hope.

There is no terminal database in v3, and therefore no file for a reader to repair. `$TERM` sorts terminals into families, the escapes they need are built in, and two terminals introduce themselves through their own environment variable before anything is asked. What follows is everything left to set, and who wins when two settings disagree.

## The Nine Options

A program passes these to NewScreen and to its two siblings. None of them is a preference stored for later: each one decides something before the first frame.

| Option | What it decides | If you say nothing |
|---|---|---|
| OptColors | how many colors exist, where 0 means none at all | the environment and the terminal decide together |
| OptTerm | which terminal this is, instead of trusting `$TERM` | `$TERM` is believed, and an unknown name is guessed |
| OptAltScreen | whether the alternate screen buffer is used | it is used |
| OptSanitizeContent | whether control characters are stripped out of text before it is drawn | text is drawn as it was handed over |
| OptAdvancedKeys | whether keys may carry a release, a repeat count and a physical key | CTRL letters arrive as CTRL keys and Shift-Tab as Backtab |
| OptKeyboardProtocol | which keyboard protocol to insist on | one is negotiated; naming the zero value insists on the legacy one |
| OptNegotiation | whether the startup conversation happens at all | it happens |
| OptEscapeTimeout | how long a lone Escape waits for company | 50 ms, or 125 ms on Windows |
| OptControlStringLimit | the largest answer a terminal may send back in one control string | 64 KiB, and a program that passes 0 removes the limit |

Two of these are worth knowing before a program needs them. OptSanitizeContent is the difference between drawing text and drawing text from an untrusted file, and it costs a pass over every string. OptKeyboardProtocol with its zero value is a real instruction, not an absence, so a program that means "let the terminal choose" should pass nothing.

## The Eight Variables

Everything here is read when the screen opens, which is after the options above have been applied. That is the whole reason the environment wins most of the time.

| Variable | The value it listens for | What it overrules |
|---|---|---|
| `TCELL_ALTSCREEN` | disable, and only that word | a program's choice, including the default of using the buffer |
| `TCELL_TRUECOLOR` | disable | the 24-bit answer; the palette count stays where it was |
| `TCELL_NEGOTIATE` | disable, or auto to force the conversation on | the option, in whichever direction it went |
| `TCELL_MOUSE` | disable | a program's request for mouse events, silently |
| `TCELL_KEYBOARD_PROTOCOL` | legacy, kitty, win32, xterm, or auto to hand it back | the protocol a program asked for; a value nobody recognizes changes nothing |
| `TCELL_ESCDELAY` | a positive whole number of milliseconds | the program's own timeout and the platform default |
| `TCELL_LINES`, `TCELL_COLS` | rows and columns | nothing, unless you are on plan 9, where they are asked first |

The last row is the trap. Those two are read by one file, the plan 9 console code, and by nothing else: setting them on Linux or macOS changes nothing, because there the device itself reports its size. Plan 9 asks these first, then `LINES` and `COLUMNS`, then settles for 24 rows of 80 columns. `TCELL_ESCDELAY` is counted in milliseconds where its matching option is a duration, which is worth remembering when a setting comes out a thousand times too long.

## Other Variables the Reader Sets

These are not _Tcell_'s inventions; the library follows conventions that exist with or without it.

| Variable | What _Tcell_ does with it |
|---|---|
| `TERM` | names the terminal when no option does, and sorts it: `vt` prefixes and `linux` and `ansi` are treated as old, names containing `mono` as colorless, `st` as a terminal worth knowing about before asking |
| `COLORTERM` | `truecolor`, `direct` or `24bit` buys 24-bit color, and any value containing 256 buys 256 colors |
| `NO_COLOR` | any non-empty value answers zero colors, on the theory that a reader who sets this wants no color |
| `TERM_PROGRAM` | two terminals are recognized from it before any question is asked: Apple_Terminal and WezTerm, each given a working configuration rather than a conversation |
| `TERM_PROGRAM_VERSION` | the version reported beside the name, for a program that says what it thinks it is running on |
| `LINES`, `COLUMNS` | the size of last resort: consulted when the device reports no size of its own, and only then; failing those, 80 columns and 25 rows |
| `LC_ALL`, `LC_CTYPE`, `LANG` | the first one that is set names the codeset text is encoded in, in that order; `C` and `POSIX` mean US-ASCII, a locale with no codeset after the dot means UTF-8, and an unrecognizable codeset is reported back through CharacterSet |
| `RUNEWIDTH_EASTASIAN` | `1`, `true` or `yes` declares an East Asian setup, which changes how wide ambiguous characters count |

Windows and plan 9 report UTF-8 and read none of the locale variables, so a misconfigured locale there is not a _Tcell_ problem. A program can ask what codeset it ended up with, and that answer is the fastest way to see whether the locale was understood; `demos/unicode` draws it on the screen at startup.

## Which Setting Wins

The promise that the environment beats a program is true for most knobs and false for two of them, and the split is not arbitrary: what a reader sets from the shell describes the terminal, and what a program passes describes its own needs.

- The environment wins for the alternate screen, the mouse, the keyboard protocol, whether to negotiate at all, and the escape delay, because all five are read after the options were applied. Setting `auto` for the keyboard protocol hands the decision back to negotiation, which is the escape hatch for a reader who wants to undo a program's insistence.
- The program wins for the terminal name and the color count, because both are only consulted when no option supplied them: an option beating `NO_COLOR`, `COLORTERM` and `$TERM` at once, and no way for a reader to argue past it.
- Nothing wins over a terminal that answers, except a refusal to ask: the replies arrive last, and one of them is the number of colors a program will be told.

A reader who needs the last word has `TCELL_NEGOTIATE=disable` and `TCELL_ALTSCREEN=disable`, and the cost of both is that the program is being told less, not more.

## A Run Worth Copying

```console
$ go run ./demos/clipboard
   Your terminal (WezTerm 20240203) claims to allow clipboard access.
$ TCELL_NEGOTIATE=disable go run ./demos/clipboard
   Your terminal (unidentified) does NOT claim to allow clipboard access.
$ go run ./demos/colors
$ NO_COLOR=1 go run ./demos/colors
$ TCELL_TRUECOLOR=disable go run ./demos/colors
$ TERM=xterm-256color go run ./demos/colors
$ TCELL_LINES=10 TCELL_COLS=40 go run ./demos/hello
```

The two lines of output are the whole sentence the clipboard demo builds, and the second is what it says when nobody was asked: the name, the version and the clipboard claim all come from the startup conversation. The color lines each change one thing: the palette as the terminal described it, a count of zero, 24-bit turned off while the palette stays, and a name that promises 256. The last line does nothing on Linux and macOS; run it on plan 9 and it is the size you get.

## Common Pitfalls

- A color count of zero is not always monochrome. A terminal that answers the startup questions gets eight colors where the guess said zero, so a program that branches on a count of zero may never take that branch in a real terminal.
- `NO_COLOR` is honored and is not a command. A program that names a color count beats it, so a reader fighting over a theme with a program has to find the program's own switch.
- A lone Escape is a coin flip between being a key and being the start of a sequence. The wait is short by design; a terminal that splits sequences across reads wants a longer `TCELL_ESCDELAY` and a program that never uses a bare Escape does not care.
- `TCELL_NEGOTIATE=disable` does not make a terminal conservative, it makes it silent: no name, no version, no clipboard, no advanced keyboard, and no correction to whatever `$TERM` claimed.
- A program asking for mouse events can be refused without knowing it. `TCELL_MOUSE=disable` swallows the request rather than failing it, so a mouse-driven program that behaves like a keyboard-driven one should be checked against the shell it was started from.
- Text drawn from an untrusted file is drawn as text. Unless the program asked for its content to be sanitized, an escape sequence inside that file reaches the terminal.

## See Also

- [Function Reference](Function-Reference) - the options and the introspection calls by name, which this page does not repeat
- [Terminal Introspection](Function-Reference#terminal-introspection) - what a program can ask about the answers on this page
- [Architecture](Architecture) - why the startup conversation is one second long and what it asks for
- [Getting Started](Getting-Started) - the demo programs used above, and how to run them
- [Windows notes](https://github.com/gdamore/tcell/blob/main/README-windows.md) - what the Windows console contributes of its own
