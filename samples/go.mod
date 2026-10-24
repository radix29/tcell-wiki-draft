// S8.1 snippet harness (PLAN.md 8): every code fence that the wiki pages publish is extracted here
// by tools/make-samples.py and compiled against the real library.
//
// The replace points at the sibling checkout ~/go/tcell. Override without editing this file:
//   go mod edit -replace github.com/gdamore/tcell/v3=$TCELL_DIR   (tools/make-samples.py does this
//   automatically when TCELL_DIR is set, so CI can build against a fresh clone anywhere)
module github.com/radix29/tcell-wiki-draft/samples

go 1.26.0

require github.com/gdamore/tcell/v3 v3.0.0

require (
	github.com/clipperhouse/displaywidth v0.11.0 // indirect
	github.com/clipperhouse/uax29/v2 v2.7.0 // indirect
	github.com/gdamore/encoding v1.0.1 // indirect
	github.com/lucasb-eyer/go-colorful v1.4.1 // indirect
	golang.org/x/sys v0.49.0 // indirect
	golang.org/x/term v0.47.0 // indirect
	golang.org/x/text v0.43.0 // indirect
)

replace github.com/gdamore/tcell/v3 => ../../tcell
