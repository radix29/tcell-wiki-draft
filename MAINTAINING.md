# Maintaining the Tcell wiki

A note for whoever maintains these pages, including a stranger with commit rights and no context.
It is committed in the draft repo and is **not** a wiki page: `tools/pages.txt` is the only list that
turns a file into a page, and this file is not on it. If a maintainer ever wants it upstream, it is
offered as content on request and not before (`PLAN.md` Q-2 parks all contact with `gdamore/tcell`).

It assumes you can read `README.md` for the layout of the repo and points at `AGENTS.md` for the
long-form rules. What follows is the four things a maintainer actually does, and what each one costs.

## 1. Add a gallery entry

Append it to the **end** of the matching `##` category in `Gallery.md`. Not alphabetically, not in a
new section you invented, one line, never wrapped:

```markdown
- [project](https://example.com/owner/project) - short lowercase description
- [project](https://example.com/owner/project) - description ([screenshot](https://url.png))
```

` - ` is an ASCII hyphen with one space either side, descriptions carry no trailing period, and
third-party tool names get `_italics_` on first mention (`_nano_`, `_tmux_`). The page is pure ASCII.

Before writing the line, prove it belongs in a *Tcell* gallery: the URL resolves, the project is real
(not a mirror or a fork of something else), and it imports `github.com/gdamore/tcell/v3`. `curl -I` on
the URL; `go.mod` or an import grep settles the rest.

Then record the approval in `tools/gallery-additions.txt`: display name, URL, and the evidence you just
gathered, including whether the author asked for it. That file is what lets `tools/check-gallery.py`
keep `--max-additions 0`: an unrecorded bullet fails the gate, a recorded one passes with its evidence
printed. Never raise the flag in CI to wave an entry through, and never keep a dead link alive by
allow-listing it.

If a project's host died, do not delete the entry and do not invent a URL: find where the project lives
now and **move** the URL, recording old, new and evidence in `tools/gallery-moves.txt`. `cview` and
`cbind` moved to Codeberg that way, because GitHub self-declared as a mirror and the `go.mod` module
path had moved too. A media URL inside an entry (a screenshot, a video) has no home to move to, so it
gets reported rather than moved.

`## Demos in the Repository` is the one section nobody curates: it is generated from the library
checkout by `tools/check-demos.py --markdown`. Re-run the tool and paste what it prints between its
markers; do not edit the lines by hand, and do not add a section like it. A second new `##` on this
page needs a record in `tools/gallery-sections.txt`, which is a plan change, not an edit.

## 2. Add a page

File names become URLs, permanently: ASCII, hyphenated, at most three words, no spaces, no underscores.
`Getting-Started.md` publishes as `/wiki/Getting-Started`, and a typo in a slug is a permanent wrong URL
rather than a rename. Never rename `Home.md` or `Gallery.md`; `../tcell/README.md` links the Gallery by
that URL and Home is the wiki's landing page (GitHub redirects `/wiki/Home` to `/wiki`).

The checklist:

1. Write the file at the repo root: exactly one `#` H1 (GitHub renders the page title itself, so a second
   one shows as a duplicate), blank lines around every heading and list, `_Tcell_` in prose and `tcell`
   only inside code, no trailing periods in headings, no HTML tags, no images hosted in this repo.
2. Add its name to `tools/pages.txt`. That line is what publishes it; a file absent from the manifest is
   invisible to the render wiki no matter how it was committed.
3. Keep the page self-sufficient: no `images/`, no `tools/`, no relative paths, because the text of one
   `.md` is what anyone pasting it into a real wiki receives. Diagrams are Mermaid or ASCII in fences.
4. Link the other pages in a `## See Also` section, without the `.md`: `[Gallery](Gallery)`,
   `[Getting Started](Getting-Started)`, anchors as `Gallery#demos-in-the-repository`. A page nobody links
   is a dead end and `tools/review-checklist.py` says so; `Home` is the hub and needs no link *to* it.
5. Only backtick an API name if this page owns it. Every structural name in the library has exactly one
   owner page, `Function-Reference`, and the gate checks it; environment variables belong to
   `Terminal-Setup`. Elsewhere, write the name in plain prose or show it inside a code fence.
6. Code fences carry markers, and invented ones fail the linter: a bare `go` fence is a whole program the
   harness compiles, `headless=yes` also runs it on the vt emulator, `mode=lib` type-checks a fragment,
   `mode=skip` is not Go, and shell transcripts go in a `console` fence (never in `go`). The library's own
   `demos/` are the examples: link them instead of authoring sample code that rots on the next API change.
7. Commit the page alone with GitHub's own message: `Created <Page> (markdown)`, or
   `Updated <Page> (markdown)` for an edit. One logical change per commit, single-line message under
   about 60 characters, no `Co-authored-by:` or tooling trailers: page history is the reader-facing
   changelog. `Home` goes last, so the hub never links a page that does not exist yet.

## 3. Run the checks

One command, and it is the one CI runs (`.github/workflows/qa.yml`, workflow `qa`):

```console
$ tools/review-checklist.py --offline     # six gates plus the per-page review questions
$ tools/check-links.py                    # the same, with the external URLs actually probed
```

Six GATEs: `check-style.py` (house style), `check-links.py` (slugs, anchors, URLs), `check-gallery.py`
(the 49 inherited entries are all still there, in order), `check-demos.py` (the demos and `TUTORIAL.md`
headings the pages link really exist), `make-samples.py` (every `go` fence compiles; the `headless=yes`
one runs), `symbol-coverage.py --gate` (no invented API; every structural name the checkout exports owned
by exactly one
page; 14 constant groups; the environment audit). Then ASK lines: review questions a script cannot
settle, answered in the plan record for the phase rather than on a page.

Exit codes are the contract: 0 clean, 1 something needs a page edit, 2 the environment is wrong
(no library checkout: `TCELL_DIR=/path/to/tcell` fixes that). Every tool prints one summary line.

Spot checks no script does for you, all of them cheap:

```console
$ curl -sS https://github.com/radix29/tcell-wiki-draft/wiki/Architecture | grep -c 'data-type="mermaid"'
$ curl -sS https://github.com/radix29/tcell-wiki-draft/wiki/Function-Reference | grep -c '<table'
$ lynx -dump -nolist -width=80 https://github.com/radix29/tcell-wiki-draft/wiki/Architecture | less
$ node tools/viewport-probe.cjs https://github.com/radix29/tcell-wiki-draft/wiki/Terminal-Setup --control
```

The first two ask the live renderer whether a published diagram or table is still really drawn (today:
3 and 12). The third reads a page as a text browser does, which is what an upstream paste hands a
maintainer who greps the raw markdown. The fourth loads a live page in a real browser at a phone
viewport and reports whether anything escapes the column (it needs Chrome, and it is a spot check, not
a gate).

## 4. What publish-on-push means here

A GitHub wiki has no review gate: saving a page changes what readers see, and the commit history becomes
the page history anyone can read. This repo keeps that hazard at arm's length, and the rules follow:

- `tools/publish.sh` is the publish path. It mirrors the manifest into the draft wiki, pushes `origin`,
  then re-reads the live wiki to prove it. A bare `git push` leaves the preview rendering an older
  commit, and CI's `preview` step fails on exactly that.
- `tools/mirror-wiki.sh --dry-run` shows what a publish would ship and publishes nothing. Use it before
  anything that touches a page.
- The mirror refuses to publish a page with uncommitted edits, because the render tree is a build output
  of *committed* text. `FORCE=1` exists for an emergency, not as a habit.
- Published history is never rewritten. No force-push, no rebase, no amend, no revert of anything already
  mirrored: corrections are new forward commits, one per logical change.
- Pushing the plain repo changes nothing a reader sees (`PLAN.md`, `AGENTS.md`, `tools/`, this file are
  not in the manifest). The render wiki and the official wiki are the only publishers, and the official
  one is unreachable from here by design: `upstream`'s push URL is a dead string, and proposals to it go
  through a human and an issue.

## 5. When a gate goes red after an upstream release

The symbols step tracks the library's default branch on purpose. A new exported name upstream, or a new
environment variable the library starts reading, turns it red: `symbol-coverage.py --gate` fails when a
structural name has no owner page, and the env audit fails when a name is on the list, missing from the
pages, or read by the library but not listed at all.

That is the failure the lists exist to make loud. The response is to write the table row or the list line,
not to widen a gate. The alternative is the failure this guard was written for: `TCELL_ALTSCREEN` existed
in the code, was named in no documentation, and was only findable by reading source.

The same rule covers the allow-lists, and they are few: `tools/style-allow.txt` (one inherited cosmetic
defect), `tools/link-status-allow.txt` (statuses someone investigated and decided to keep),
`tools/api-allow.txt` (non-API package prefixes). `tools/tcell-env-vars.txt` is not an allow-list and has
no exceptions in it: it is a claim about what the library reads, and the auditor fails the pages when the
claim and the source stop agreeing. Never add a line to any of them to silence a finding you do not
understand.

One more red that is not a defect: CI's link probe can be answered a 5xx by GitHub for a URL that is
plainly live. Re-run the job. Do not move the URL, do not allow-list it, do not soften the sentence - the
last time this happened the re-run went green at the same commit unchanged.
