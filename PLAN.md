# Tcell Wiki Rebuild - Implementation Plan

Status: DRAFT - plan only, nothing implemented
Scope: rewrite `github.com/gdamore/tcell.wiki` from scratch (Home + Gallery + How-To-Use content)
Out of scope (this pass): any change to the `../tcell` library repo, its `README.md`, `TUTORIAL.md`, or code

> **Premise change (2026-10-24, see 4.1 Q-0b).** The person doing this work is **not** a maintainer of
> `gdamore/tcell` or `gdamore/tcell.wiki` and has **no push access to either** (verified: no stored
> credentials for `https://github.com/gdamore/tcell.wiki.git`; `git push --dry-run` fails at auth).
> Everything below was drafted against a *maintainer* model - push to `origin/master`, answer D-1/D-2/D-7/D-8,
> land F-1 in the library repo. Those parts are **pending revision to a contributor model**: author the pages
> in a repo the author owns, then propose them upstream. Not a fork - GitHub offers no Fork for `.wiki` repos
> and a fork of the code repo carries no wiki content at all.
> Chosen vehicle (Q-0c): author in **`radix29/tcell-wiki-draft`** with that repo's own wiki enabled as a
> render preview. Step-by-step setup is in **`AGENTS.md`** ("Runbook"); Phase 0 T0.0 now means "follow it" - steps 1-3 are
> executed (2026-10-24): remotes rewired, `origin`/`render` pushed, `tools/pages.txt` + `.gitignore` committed.

---

## 1. Executive summary

Rebuild the Tcell wiki as a v3-first, task-oriented documentation set with:

1. `Home` - short project description plus two navigation groups (showcase / learn & reference).
2. `Gallery` - full, lossless migration of all 49 current gallery bullets (48 linked), plus a new
   "demos shipped in the repo" subsection.
3. `How-To-Use` content - a tutorial, an architecture document, and functionality documentation in
   one reference page plus a `Terminal-Setup` page (Q-3: the 7 focused topic pages of 5.1 deferred).

**Scope is 6 pages, not 13 (Q-3, see 4.1): `Home`, `Gallery`, `Getting-Started`, `Architecture`,
`Function-Reference`, `Terminal-Setup`.** Total estimate **39-51 focused hours** across 7 phases; the
six page bodies themselves are **31-40 h**, the rest is Phase 0 tooling and Phases 1/7 rails.
Phases 1-4 remain the user-visible minimum (Home + Gallery + Getting-Started tutorial); Phase 6 shrank
from 11-14 h to 6-8 h when the topic pages were deferred to a second milestone.

Two things make this repo unusual and they drive most of the plan:

- **There is no review gate** *at upstream*. A push to a wiki repo changes a rendered page instantly
  and the commit history is the visible page history. Route C moves that moment away from us: we push to
  our own draft repo, and only a manifest-driven mirror to `render` - or a paste into the upstream web
  editor - publishes anything.
- **Wiki repos cannot run CI** (C6): true of `upstream` and of the `render` wiki, not of the draft plain
  repo, which is where `tools/` + Actions live. Verification is those scripts plus manual review
  (section 8, plus the per-phase review gates in section 9).

---

## 2. Verified current state

Wiki repo (`/home/radu/go/tcell.wiki`, remote `gdamore/tcell.wiki.git`, branch `master`):

| Item | Value |
|---|---|
| Files | `Home.md` (4 lines), `Gallery.md` (71 lines) - nothing else |
| Commits | 10, all single-line messages, mostly one-line diffs |
| Gallery bullets | 49 total / 48 with links |
| Category counts | Demonstrations 4 (one unlinked), Editors 3, UI Frameworks 7, Games 13, Productivity & Utilities 21, Miscellaneous 1 |
| Link hosts | github.com 44, code.rocketnine.space 2, 2.bp.blogspot.com 2, youtu.be 1, www.youtube.com 1, user-images.githubusercontent.com 1, termshark.io 1, git.sr.ht 1 |
| Encoding | pure ASCII, `- ` bullets, `_italics_` for third-party names, no trailing periods in descriptions |
| Missing | no sidebar, no other pages, no images stored in the repo, no `.gitignore` |

Library repo (`/home/radu/go/tcell`, source of truth for all technical content):

| Item | Value |
|---|---|
| Module | `github.com/gdamore/tcell/v3`, `go 1.26.0` |
| Non-test LOC | root 7,582 / `vt` 5,556 / `tty` 1,316 / `color` 1,224 / `encoding` 130 |
| Core entry point | `func NewScreen(opts ...TerminfoScreenOption) (Screen, error)` |
| `Screen` interface | 43 methods (Init, Fini, Clear, Fill, FillArea, Put, PutStr, PutStrStyled, Get, SetContent, SetStyle, ShowCursor, HideCursor, SetCursorStyle, GetCursor, Size, EventQ, Enable/DisableMouse, Enable/DisablePaste, Enable/DisableFocus, Colors, Show, Sync, CharacterSet, Register/UnregisterRuneFallback, Resize, Suspend, Resume, Beep, SetSize, LockRegion, Tty, SetTitle, Set/Get/HasClipboard, ShowNotification, KeyboardProtocol, Terminal) |
| `Style` | immutable builder: Foreground, Background, Bold, Dim, Italic, Reverse, Blink, StrikeThrough, Underline, UnderlineStyle, Url, UrlId, Normal, Attributes, Get*/Has* accessors; `StyleDefault` |
| Events | `Event` (With `When()`), EventKey, EventMouse, EventResize, EventPaste, EventFocus, EventError, EventInterrupt, EventTime, EventClipboard; `EventHandler` interface; loop idiom is `ev := <-s.EventQ()` |
| Options | OptAltScreen, OptAdvancedKeys, OptColors, OptControlStringLimit, OptEscapeTimeout, OptKeyboardProtocol, OptNegotiation, OptSanitizeContent, OptTerm |
| Env vars in code | TCELL_ALTSCREEN, TCELL_COLS, TCELL_LINES, TCELL_ESCDELAY, TCELL_KEYBOARD_PROTOCOL, TCELL_MOUSE, TCELL_NEGOTIATE, TCELL_TRUECOLOR |
| Demos | `demos/`: beep, boxes, clipboard, colors, cursors, hello, styles, unicode. `_demos/` (`//go:build ignore`): mouse, notify, setsize, showcolor, sixel, stress |
| Repo docs to reconcile | `README.md`, `TUTORIAL.md` (330 lines, self-described "somewhat rough"), `CHANGESv3.md`, `CHANGESv2.md`, `README-windows.md`, `README-wasm.md`, `README-plan9.md`, `SECURITY.md` |

Documentation gaps found during this audit (candidates for the wiki to close, and for a follow-up
issue in the library repo):

- `TCELL_ALTSCREEN`, `TCELL_COLS`, `TCELL_LINES` exist in code but appear in **no** markdown doc.
- `README.md` still links to the legacy `.../tcell/wikis/Gallery/` URL (redirects today).
- The `mouse demo` bullet in the current Gallery points at a 2015 screenshot and describes a demo
  that is no longer in `demos/` (only `_demos/mouse.go`, `//go:build ignore`).

---

## 3. Platform constraints this plan assumes

Rules that must be designed around (each is marked with how it is settled):

| # | Constraint | Consequence |
|---|---|---|
| C1 | Publish-on-push, no PRs, anyone with the link can also edit in the web UI | every phase ends with a local review gate; publish only on explicit approval. **Revised by Q-0b: we cannot push at all, so "publish" now means a web-UI edit accepted upstream, or handing content to a maintainer; the review gate moves from "before we push" to "before we propose".** |
| C2 | GitHub wikis expose **any** `.md` file as a public page | **Settled by Q-0c + `AGENTS.md` Runbook: it only bites where a push renders.** Pages reach a wiki solely through `tools/pages.txt`, so `PLAN.md`/`AGENTS.md`/`README.md` are committed in the draft and never mirrored; `upstream` stays fetch-only |
| C3 | Slugs come from file names: `Getting-Started.md` -> `/wiki/Getting-Started`; spaces become `_` | prefer hyphenated, <= 3 word ASCII file names; internal links omit `.md` |
| C4 | Nested/subdirectories are not reliably rendered as sub-pages | assume a **flat** page set; hierarchy via `_Sidebar.md` and Home nav only |
| C5 | `_Sidebar.md` / `_Footer.md` apply to every page | **Settled by Q-3/Q-0b: we build it as a droppable prototype in our own draft wiki only (5.5) and never propose it unsolicited - a site-wide sidebar is an upstream call (D-1).** Pages never depend on it |
| C6 | No CI in wiki repos | verification is scripts + manual checklists run locally (S8) |
| C7 | Rewriting published history is not possible to unwind | one logical change per commit, wiki-style messages (`Created X (markdown)`, `Updated X (markdown)`), no force-push ever |
| C8 | Existing deep links matter: `/wiki/Home`, `/wiki/Gallery`, and the README pointer | keep `Home` and `Gallery` file names exactly; never rename them |
| C9 | Mermaid support in the wiki renderer is *assumed* but unproven here | probe task T5.1 in **our own draft wiki** before writing Architecture diagrams; fallback is ASCII art in fenced blocks. Q-0c removed the old "push a scratch page to the live official wiki" step entirely |
| C10 | Hotlinked third-party images (2 blogspot URLs from 2015) can rot | verify status, keep URLs (do not silently drop content), and raise hosting option as D-6 |

---

## 4. Decisions needed from the maintainer (blocking items marked *)

| ID | Question | Recommendation | Blocks |
|---|---|---|---|
| D-1* | Add `_Sidebar.md` for navigation across all pages? | **Draft-owner answer (Q-3): build it, mirror it only to `radix29/tcell-wiki-draft`, keep it droppable; it stays an upstream ask, never an unsolicited change** | Phase 1 |
| D-2* | Canonical home for user docs: wiki, or repo `README`/`TUTORIAL.md` with the other pointing here? | Wiki canonical for tutorials/reference; repo keeps a 1-paragraph overview + link. Repo-side edit is a separate follow-up (F-1) | Phase 3, 5 |
| D-3* | Page naming for the "how to use" area: `Getting-Started` + `Function-Reference`, or one big `How-To-Use`? | `Getting-Started` (learn path) + `Function-Reference` (find-the-API) - two different reader intents, two pages | Phase 2 |
| D-4 | Version coverage: v3 only, or v3 + migration notes for v2 users? | **Moot for this build (Q-3): v3-only voice, `Migration-v2-to-v3` deferred; `Home`/`Function-Reference` link the repo `CHANGESv3.md` instead of forking it** | Phase 5 |
| D-5 | Store screenshots in the wiki repo, or keep hotlinks only? | Keep hotlinks; add repo-hosted images only for the 3-4 diagrams we author ourselves | Phase 4 |
| D-6 | Drop/keep the legacy unlinked `mouse demo` bullet + 2015 blogspot screenshots? | Keep the bullet, rewrite wording so it does not claim a shipped demo; keep URLs until they 404 | Phase 1 |
| D-7 | Should the wiki list community/commercial support (TideLift, Staysail, Discord)? | Yes, short "Support" section on Home only (mirrors README) | Phase 2 |
| D-8 | Repo setting: restrict wiki editing to collaborators? | Worth checking in repo Settings; changes spam risk, not content | Phase 7 |
| D-9 | Authoring language/style: keep `_Tcell_` italics convention used by README + current Gallery? | Yes, keep for consistency with the existing Gallery and library READMEs | all |

**Whose decision is whose (per Q-0b):** D-1 (site-wide `_Sidebar.md`), D-2 (wiki vs repo as canonical docs
home), D-7 (whose commercial/community links appear), D-8 (restricting wiki editing) and every F-1 item are
`gdamore` maintainers' calls - we may only *propose* them, and must not pre-implement them in the official
wiki. D-3, D-4, D-5, D-6, D-9 are ours for as long as the work lives in our own draft repo.

### 4.1 Decision record (maintainer answers)

Row IDs are the **decision** IDs (`Q-0`, `Q-0b`, `Q-0c`, `Q-2`, `Q-3`, ...) and they run one behind the
question numbers used out loud in the Q&A, because `Q-0b` and `Q-0c` were follow-ups to `Q-0`. The next
answer is recorded as `Q-4`. Mapping so far: requirements = Q-0, contributor premise = Q-0b, vehicle +
motivation = Q-0c / Q-1, upstream timing = Q-2, scope = Q-3.

| ID | Answer | Date | Effect on this plan |
|---|---|---|---|
| Q-0 (requirements) | **§10 is the complete requirements contract** - no deadline, tone/audience, gallery-restructure restriction, or size cap beyond what is already written here | 2026-10-24 | Section 10 upgraded from "traceability of the request" to the authoritative contract; no provenance gap remains |
| Q-3 (scope) | **(b) 6 pages: `Home`, `Gallery`, `Getting-Started`, `Architecture`, `Function-Reference`, `Terminal-Setup`** | 2026-10-24 | Re-estimates the plan at 39-51 h (page bodies 31-40 h). The other 6 topic pages of 5.1 become a **deferred second milestone** (5.1, 6.6, 12), which has three consequences bigger than the hour count: (1) `Function-Reference` absorbs their audience and grows to 1,000-1,400 words, (2) the 100%-symbol-coverage gate now concentrates the whole API into one page - the `pkg.go.dev` mirror tension is now live - open coverage-gate question, see 6.5 - and (3) no built page may link a deferred page (route-C self-containment rule). Also decides nav: `Home` is the hub and `_Sidebar.md` is built as a **droppable prototype mirrored only to our own wiki**, because a site-wide sidebar is an upstream call (D-1) and this keeps it reversible. D-4 (migration page) becomes moot - breaking changes are linked to repo `CHANGESv3.md` instead. |
| Q-2 (upstream timing) | **"Ignore the talk for now, we build it first"** - no issue in `gdamore/tcell`, no upstream contact, until the draft says otherwise | 2026-10-24 | `PLAN.md` Phase 7 marked PARKED (draft stays public so the eventual pitch is just a URL). Plan effects: Phase 7 T7.4 becomes "prepare the proposal package, do not send"; the D-list items that needed upstream (D-2 canonical home, D-1 site-wide sidebar, D-6 wording of a live line, D-7 whose support links) are now **decided as draft-owner questions by us** and separately flagged as "must be asked before it could ever land upstream"; new risk row added. Consequence to hold onto: everything we write must still be paste-able one page at a time, because "build first" must not quietly turn into "a different project with different constraints". |
| Q-0c (vehicle) | **Route C**: author in `radix29/tcell-wiki-draft` (plain repo = source of truth; its own wiki = render preview), propose upstream page by page, GitHub Pages only if upstream declines. Motivation confirmed as "Tcell's docs should be better", not "a project I own end-to-end" | 2026-10-24 | `setup.md` written and referenced from Phase 0 (T0.0); merged into `AGENTS.md` the same day. Consequences: the official wiki becomes a fetch-only remote `upstream` plus a `--push` URL guard; tooling moves from "forever untracked" to committed in the draft repo (`tools/`, `samples/`, `AGENTS.md`, `PLAN.md`), because the C2 "every .md becomes a page" hazard now only exists in the *mirror*, which is driven by `tools/pages.txt`; CI becomes possible in the draft, so C6 reads "no CI **upstream**" and the draft's Actions is our gate while the upstream artefact stays untestable; T5.1's Mermaid probe and any `_Sidebar.md` experiment move to our own wiki, deleting the "push a scratch page to the live official wiki" step; new route-C rule: **a page body may not reference anything outside itself** (no repo-hosted `images/`, no `tools/` links), which pre-answers D-5 as "hotlinks + Mermaid/ASCII only". |
| Q-Ex (examples) | **The wiki links the library's own examples instead of authoring them.** Pages cite `demos/` (8 programs, each with a rendering test) and `TUTORIAL.md` in `gdamore/tcell`; a page fence carries only the fragment under discussion | 2026-10-24 | `samples/smoke/` deleted as an authored example. `tools/check-demos.py` checks the names, URLs, `go run` commands and `_demos/` claims against the checkout and prints the paste-able `## Demos in the Repository` block with `TODO(desc)` where a demo has no doc sentence (6 of 8) rather than inventing prose. Cuts Phase 4 authoring (snippets become small `mode=lib` fragments, still S8.1-compiled and S8.6-run) and turns the Gallery's new section into generated text. Library-side ask for the F-1 package: doc comments on the demos so descriptions come from the library itself. |
| Q-0b (premise) | **We are not a maintainer of `tcell` or `tcell.wiki`.** Work happens in a repo the author owns, not in a fork of `tcell`; upstream contribution is by proposal, not by push | 2026-10-24 | Biggest single edit this plan has had. Affects: C1 + C9 (above), the D-list split into ours vs upstream's (above), D-7 dropped from our draft, Phase 0 (add: create draft repo + point `origin` at it, keep the official wiki as read-only `upstream`), Phase 7 (T7.5 "publish" becomes "propose + hand over per-page markdown"), T5.1 (probe on our own wiki), and §12 (GitHub Pages becomes a real fallback if upstream declines). Draft README must state *unofficial / not affiliated / official wiki at ...*; the wiki repo carries no `LICENSE` file, so attribution and Gallery URLs are preserved and no license is implied. |

(Answers are recorded one row at a time as the plan is walked through; `Q1..Q16` map to the
question set raised in session `01a16d5c`, not to the `D-*` decision IDs above.)

---

## 5. Target information architecture

### 5.1 Page set for the build (flat pages; nav lives in `Home` per 5.5)

```
Home                    short description + two nav groups
Gallery                 showcase (migrated) + in-repo demos
Getting-Started         the tutorial: install -> first app -> input -> polish  (learn path)
Architecture            how it is put together: layers, backends, data flow    (understand path)
Function-Reference      map of the provided functionality, by task and symbol   (reference path)
Terminal-Setup          TERM, options, env vars (incl. the 3 undocumented), colors, negotiation

DEFERRED (Q-3) - built only if the first 6 land well; do not link to these from a built page:
Screen-and-Rendering    Screen lifecycle, drawing, damage, Show/Sync, resize, suspend
Styles-and-Color        Style, AttrMask, color models, 24-bit, palettes, theme respect
Events-and-Input        event channel, keys, key protocols, mouse, paste, focus, clipboard, errors
Unicode-and-Encodings   grapheme clusters, width, fallbacks, charsets, encoding subpackage
Platforms               POSIX / Windows / WASM / Plan 9 (short pages that link out to repo READMEs)
Migration-v2-to-v3      breaking changes summary + mechanical fix table
```

Page budgets (so the set stays maintainable by one person): Home 250-350 words, Gallery 0 prose
(new prose: 2 sentences + subsection intros only), Getting-Started 900-1,400 words + 8-12 snippets,
Architecture 900-1,300 words + 3-4 diagrams, Function-Reference 1,000-1,400 words + tables (it absorbs
what the deferred topic pages would have carried, which is why it grows past the original 700-1,000),
Terminal-Setup 700-1,100 words. 6 pages built + 6 deferred vs 2 today; see 5.5 for the nav shape.

### 5.2 Navigation actually used: `Home` as the hub (sidebar is a droppable prototype)

Fold navigation into `Home` (three explicit lists: "Start here", "Reference", "Showcase") and add a
one-line `Prev | Up | Next` footer to each page. Cost: nav must be updated by hand whenever a page
is added; ~10 min of extra work per new page and a standing risk of stale nav.

### 5.3 Reader-intent mapping (used to keep pages from drifting into each other)

| Reader wants | Lands on | Should NOT have to read |
|---|---|---|
| "is this library right for me" | Home | API details |
| "show me a working program" | Getting-Started | internals |
| "why is my resize not repainting" | Getting-Started (Resize section) -> Function-Reference (Drawing / Lifecycle rows) | platform docs |
| "what can Tcell do at all" | Function-Reference | prose |
| "how do I stop Tcell from negotiating at startup" | Terminal-Setup | tutorial |
| "port my v2 app" | repo `CHANGESv3.md` + Function-Reference (deferred page `Migration-v2-to-v3`) | tutorial |
| "what is built on Tcell" | Gallery | anything else |

### 5.4 Content ownership table (single source of truth, to prevent duplication drift)

| Topic | Owner | Wiki treatment |
|---|---|---|
| One-paragraph "what is Tcell" | Home | 2-3 sentences, no feature essay (README keeps the long version) |
| Feature list (Unicode, mouse, colors, keys, perf) | Home (condensed bullets) | 1 line each + link to the `Function-Reference` / `Terminal-Setup` section that has detail (Q-3: no topic pages) |
| Env var reference | wiki `Terminal-Setup` | authoritative; `../tcell/README.md` should later link here (F-1) |
| Tutorial program | wiki `Getting-Started` | snippets must be real, tested (S8.1); repo `TUTORIAL.md` later becomes a pointer |
| Breaking changes lists | repo `CHANGESv2.md` / `CHANGESv3.md` | wiki summarizes + links; never fork the full list |
| Windows/WASM/Plan 9 setup detail | repo `README-*.md` | `Function-Reference` has a short platform block that links out; never copy the WASM setup steps (Q-3: no `Platforms` page) |
| API signatures | `pkg.go.dev` + `go doc` | wiki never copies signature blocks verbatim beyond one line; links `pkg.go.dev` per symbol group |
| Showcase list | wiki `Gallery` | authoritative (repo README already links here) |

### 5.5 Nav shape and page-independence rules for the 6-page build (Q-3 + route C)

- **`Home` is the nav hub** (the old "Option B"), with its `## How to Use` / `## Gallery` sections doing
  the linking. No `Prev | Up | Next` footers: they are per-page chrome that goes stale and they would
  have to be deleted again if upstream ever took a sidebar.
- **`_Sidebar.md` is built and tracked, but mirrored only to our own draft wiki**, so its look can be
  evaluated (C5) without being load-bearing. It is not part of the upstream proposal (D-1 is a site-wide
  change and the maintainers' call) and deleting it must never require editing a page - which is true
  today because no page links to it or depends on it.
- **A page must be paste-able alone** (`AGENTS.md` Runbook): no links to the 6 deferred pages, no `Prev/Next`,
  no `images/` from our repo, no `tools/` paths, no relative paths. Internal links point only at the
  other 5 built pages; everything else is an absolute URL to `../tcell` docs, `pkg.go.dev`, or a demo.

---

## 6. Page-by-page specification

Each spec lists: sections, required source files, verification. All pages additionally get:
one-sentence purpose at the top and a "See also" list of links to the other built pages only (5.5:
no `Prev/Up/Next` footers, no links to deferred pages).

### 6.1 `Home.md`

- Sections: `# Tcell` (lede, 2-3 sentences: cell-based terminal UI library for Go, inspired by
  termbox, v3), `## Why Tcell` (6-8 bullets: portability incl. no-cgo, Unicode/graphemes, key
  protocols incl. CTRL-I vs TAB, mouse incl. motion/drag/wheel, 24-bit color, clipboard +
  notifications, bracketed paste, performance), `## Versions` (v3 current + import path; v2/v1
  availability + "v1 unmaintained"; link the repo `CHANGESv3.md`, not a wiki migration page (Q-3)),
  `## Install` (one `go get` block + `NewScreen` one-liner), `## Gallery` (2 sentences + link -
  requirement R2), `## How to Use` (3 bullets pointing at `Getting-Started`, `Architecture`,
  `Function-Reference` - requirement R3), `## Platforms` (1 line each, linking the repo `README-*.md`
  since there is no `Platforms` page in scope), `## License` (Apache-2.0).
  **No Support/Community section (Q-0b/Q-2: TideLift, Staysail and Discord links are the project's to
  place, not a contributor's).** Home is also the nav hub (5.5), so these sections carry the links.
- Sources: `../tcell/README.md`, `../tcell/doc.go`, `../tcell/go.mod`, `../tcell/SECURITY.md`.
- Explicitly NOT here: badges, the long color/encodings essays, breaking-change prose.
- Verification: all 3 required elements present (short description, Gallery section, How-to-use
  section); every link checked; word count <= 400.

### 6.2 `Gallery.md`

- Migrate **all 49 bullets verbatim in content** into the existing 6 categories, preserving order
  within categories (append-only history), then:
  - fix the `## UI Frameworks ` trailing space only if the whitespace itself is the fix (D-9 style
    rule: no cosmetic churn) - decision: leave, since it renders identically;
  - rewrite the legacy `mouse demo` bullet per D-6;
  - add `## Demos in the Repository` with the 8 `demos/` programs and a one-line description of
    each, plus a note that `_demos/` files are `//go:build ignore` and how to run them.
- New subsection under each category only if a future entry genuinely needs it (no one-off sections).
- Entry format frozen: `- [name](url) - short description` (ASCII `- `, no trailing period),
  optional ` ([screenshot](url))` / `([video](url))`; `_italics_` for third-party tool names.
- Verify (lossless migration): per-category counts before/after must match the S2 checklist;
  `grep -c '^- ' Gallery.md` before = 49 (or 49 + deliberate changes recorded in the checklist).
- Verify every external URL with `curl` (S8.2); record the 2 blogspot + 3 video URLs status in the
  migration checklist; never delete an entry because of a 404 - report it instead.
- De-duplication: two `go-tetris` entries exist (different owners) - keep both, and add owner
  disambiguation to the description if the maintainer agrees (D-list item to fold into D-6 review).

### 6.3 `Getting-Started.md` (the tutorial)

- Sections: `## Install` (Go version policy from README; `go get`), `## Hello, terminal` (minimal
  complete program: NewScreen -> Init -> defer Fini -> SetStyle -> Clear -> PutStr -> Show -> event
  loop -> EventKey quit), `## Anatomy of a Tcell program` (the 5 always-present pieces),
  `## The screen is a cell grid` (coordinates, width in cells, `Size`), `## Drawing text`
  (`Put` vs `PutStr` vs `PutStrStyled`, return values `(string, int)` and why to use the width,
  wide runes/emoji at the last column, the wrap loop from `TUTORIAL.md`), `## Styles` (StyleDefault,
  chained builder, foreground/background/attr), `## Input` (`EventQ` channel + `select` with a
  timer - the v3 story), `## Resize` (`EventResize` -> `Sync()`, why not `Clear()`),
  `## Mouse`, `## Beyond the basics` (clipboard, notifications, title, cursor styles, suspend),
  `## Next steps` (links to `Function-Reference`, `Architecture`, demos, `demos/hello`).
- Sources: `../tcell/TUTORIAL.md` (reuse prose/samples where already v3-correct: drawText loop,
  event loop), `../tcell/demos/hello`, `../tcell/demos/styles`, `../tcell/demos/cursors`,
  `CHANGESv3.md` (event-model changes), `go doc` output.
- Rules: every snippet compiles as-is (S8.1); no `v2` API in any snippet (`PollEvent`,
  `ChannelEvents`, `PostEvent`, `SimulationScreen`, `StyleNormal`, `Attribute`, `Color(ForegroundX)`
  forms are all banned - they are v2/v1 and were removed); every code fence tagged `go`; snippets
  <= 30 lines, with the full program assembled once at the end.
- Deliverable side-effect: the compile-harness fixture directory (S8.1) is created alongside.

### 6.4 `Architecture.md`

- Sections: `## Two layers` (public `tcell` package = model + API; internals = terminal dialect
  handling), `## The screen model` (logical cell buffer -> damage -> minimal diff -> output
  sequences; `CellBuffer`, `LockRegion`, `Show` vs `Sync`), `## Backends` (single `Screen`
  interface; tty abstraction `tty` package: raw mode, signals, resize notify, drain, UTF-16 on
  Windows; POSIX unix / Windows console / WASM / Plan 9 variants table),
  `## Terminal capability handling` (what replaced terminfo in v3 - the `vt` package, cited by
  file: `vt.Attr` (attr.go), `vt.Backend`/`vt.Blitter` (backend.go), `vt.Coord`/`vt.Col`
  (coord.go), `vt.CursorStyle` (cursor.go), `vt.Emulator`/`vt.NewEmulator` (emulate.go),
  `vt.KeyEvent`/`vt.MouseEvent` (event.go), `vt.Key`/`vt.BaseKey`/`vt.Modifier`/
  `vt.KeyboardState`/`vt.DeadKey` (key.go), `vt.Layout`/`vt.GetLayout` (layout.go +
  `layouts/{all,us}`), `vt.ModeStatus`/`vt.PrivateMode`/`vt.MouseReporting`/
  `vt.AdvancedKeyboard` (mode.go), `vt.MockTerm`/`vt.NewMockTerm`/`vt.MockBackend` (mock.go)),
  `## Input pipeline` (bytes -> InputProcessor (internal since v3) ->
  grapheme/width aware decoder -> Event on `EventQ`; escape-delay tradeoff, `TCELL_ESCDELAY`),
  `## Keyboard protocols` (legacy vs kitty vs win32 vs xterm; negotiation, `KeyProtocol`,
  `KittyKbdMode`, `XtermKbdMode`, override precedence: env > option > auto),
  `## Output pipeline` (grapheme -> width -> alternate charset -> color fitting via `color.Find` /
  `color.PaletteColor`, 24-bit vs 256 vs 8, theme-respecting `color.Reset`),
  `## Unicode & width` (`internal/widthutil`, `eastasian.go`, `RuneFallbacks`, `width.go`),
  `## Concurrency model` (single-owner `Screen`, `LockRegion`/`Lock` contract, event channel is the
  sync point), `## Where to look in the source` (file -> responsibility table for
  `screen.go`, `tscreen.go`, `cell.go`, `style.go`, `event.go`, `key.go`, `mouse.go`, `runes.go`,
  `vt/vt.go`, `vt/emulate.go`, `tty/tty_*.go`, `color/fit.go`).
- Diagrams (3-4): layer stack, frame/damage lifecycle sequence, input pipeline, backend/platform
  matrix. Mermaid if T6.1 proves it renders; otherwise ASCII in fenced blocks (always acceptable).
- Sources: LOC/package inventory above + reading the named files. **No API opinions** - describe
  what the code does, cite file names so pages stay fixable when code moves.

### 6.5 `Function-Reference.md`

- Organized by task, not by alphabet: `## Lifecycle`, `## Drawing`, `## Reading content back`,
  `## Styles & color`, `## Cursors`, `## Input & events`, `## Mouse`, `## Clipboard & title &
  notifications`, `## Terminal introspection` (`Colors`, `Terminal`, `CharacterSet`,
  `KeyboardProtocol`, `Tty`), `## Advanced hooks` (`NewTerminfoScreenFromTty`, `ShimScreen`,
  `NewDevTty*`, `NewStdIoTty`, `RegisterRuneFallback`, `SetEncodingFallback`, `GetEncoding`/
  `RegisterEncoding`, `LockRegion`, `SetSize`, `Suspend`/`Resume`, `Beep`),
  `## Subpackages` (one paragraph each: `color`, `encoding`, `tty`, `vt` - with "used by applications
  only if..." framing).
- Each area = 3-column table: `Symbol | What it does | See (page section)`. One-line rows only, so
  wiki diffs stay small when APIs change.
- **Coverage requirement:** an audit script (S8.3) diffs exported symbols from
  `go doc -all github.com/gdamore/tcell/v3` (currently 2,023 lines of output; 38 exported types,
  17 `New*` constructors plus 4 color helpers, 43 Screen methods, ~27 Style methods) against
  symbols named in the wiki pages.
  Exit criterion: 100% of root-package exported symbols appear in exactly one of the **6 built pages**
  (a page section or the tables), with an explicit `internal/advanced/deprecated` label for the rest.
  **Caveat, pending the coverage-gate question (open, next to be asked): with only 6 pages this gate
  forces `Function-Reference` toward a `pkg.go.dev` mirror, which 12 lists as a non-goal.**

### 6.6 Topic pages - **only `Terminal-Setup` is built; the other 6 are deferred (Q-3)**

Deferred to a second milestone: `Screen-and-Rendering`, `Styles-and-Color`, `Events-and-Input`,
`Unicode-and-Encodings`, `Platforms`, `Migration-v2-to-v3`. They stay specced below as the backlog, and
their audience is served in the meantime by `Function-Reference` tables + `Getting-Started` sections.
Nothing in the 6-page build may link to them (`AGENTS.md`: a page must be self-contained).

`Terminal-Setup` (built, one of the 6) and every deferred page follow this shape:

- Purpose sentence, "when you need this", concept prose (<= 300 words), API table, worked example
  (<= 25 lines), environment/option table where relevant,
  "Common pitfalls" (e.g. adjacent cell of a wide rune is undefined; colors and themes;
  `TCELL_NEGOTIATE=disable`; escape delay vs standalone Escape).
- `Terminal-Setup` must document **all 8** `TCELL_*` variables (including
  `TCELL_ALTSCREEN`, `TCELL_COLS`, `TCELL_LINES` which no doc covers today - read their handling in
  source first) plus every `Opt*` type, and state the precedence rule (env beats option).
- `Migration-v2-to-v3` is generated from `CHANGESv3.md` sections (Cell/Contents APIs, events, key
  events, termbox compat removal, terminfo removal, color/attr bit sizes, underline, capability
  queries, Windows console API, InputProcessor, SimulationScreen) as a "v2 code -> v3 code" table.

---

## 7. Cross-cutting editorial standards

- Voice: present tense, second person sparingly, no marketing adjectives, v3-only by default.
- Naming: `_Tcell_` in prose (matches README + current Gallery), `Tcell` in headings, file names
  ASCII/hyphenated/<= 3 words.
- Prose stays **ASCII only** (existing convention); Unicode is allowed inside fenced code blocks
  and inside inline code where the example needs it (e.g. CJK/emoji width demos).
- Links: internal `[Getting Started](Getting-Started)` (no `.md`, no path); external always the
  canonical URL; `pkg.go.dev` symbol links use the `.../v3@main#Section` form and must be verified.
- Every page: one H1 max (rendered page title already duplicates it - follow `Gallery.md`'s
  precedent of a single H1), blank line around lists/headings, one bullet per line, no wrapping
  (keeps wiki diffs one-line), no HTML tags, no `*emphasis_` mixing.
- Images: **no files in the page set (Q-0c pre-answers D-5).** Diagrams are Mermaid (if the T5.1 probe
  renders it in our draft wiki) or ASCII in fenced blocks, because a page must survive being pasted into
  someone else's wiki on its own (5.5). Third-party screenshots stay hotlinked where they already exist.
- Code: `gofmt`-clean, `go` fence tag, tested (S8.1), no license headers in snippets, imports shown.
- Never edit a published page by rewriting history; corrections are new commits.
- `PLAN.md` / `AGENTS.md` / `README.md` are tracked in the **draft** repo but never mirrored into the
  render tree and never proposed upstream (C2 applies to the mirror, `tools/pages.txt` is the gate).

---

## 8. Verification & QA tooling (no CI available)

Small scripts, **committed under `tools/` and `samples/`** in the draft repo (`AGENTS.md` Runbook), so they run
both locally and as Actions CI there - the one thing a real wiki repo can never have. Nothing in
`tools/` can publish: the mirror copies only what `tools/pages.txt` lists:

| ID | Tool | What it proves |
|---|---|---|
| S8.1 | `samples/` Go module with `replace github.com/gdamore/tcell/v3 => ../tcell`; one `main.go` per wiki snippet, extracted from the `.md` files | every doc snippet builds against current v3 (`go vet ./...`, `go build`) |
| S8.2 | link checker: extract all `](url)` from `*.md`, `curl -sS -o /dev/null -w '%{http_code}' -I`, plus internal-slug existence check against `ls *.md` | no dead external links, no broken internal links |
| S8.3 | symbol coverage auditor: `go doc -all` symbol list vs symbols mentioned in wiki text | the 100% reference coverage gate (S6.5) |
| S8.4 | gallery diff/counter: per-category bullet counts + set-of-URLs diff between old and new `Gallery.md` | migration is provably lossless (S2) |
| S8.5 | style linter (small script): non-ASCII in prose, trailing whitespace, `*emph*`, `*.md)` internal links, missing fence tags, wrapped bullets | house style (S7) enforced mechanically |
| S8.6 | **PASSED and built (2026-10-24).** The spike ran `Screen.Init` against `vt.MockTerm` + `tcell.NewTerminfoScreenFromTty` + `tcell.ShimScreen` (the recipe from `demos/hello/hello_test.go`) and a program drew and quit headlessly in 0.3 s, so snippets can be *run*, not just compiled | snippets do more than compile | implemented as opt-in `headless=yes` inside S8.1 (a fence that asks for it is executed on the emulator and must exit on ESC); `mode=lib` + `headless` is a label error |
**Status (2026-10-24): S8.1-S8.5, S8.7 and a demo checker (S8.2b, `tools/check-demos.py`) are
implemented under `tools/` and run on every push in `.github/workflows/qa.yml`.**

| S8.7 | **Built (2026-10-24):** `tools/review-checklist.py` runs every other tool as a GATE, adds the mechanical CHECKs (v2 leakage vs the real surface, resize prose naming `EventResize`, orphan pages, duplicated `##` topics, non-self-contained diagrams) and prints the ASK lines a human must answer | consistent manual review | verified both ways: clean pages exit 0; a page with `PollEvent`/`StyleNormal`/unnamed-resize exits 1 with three named findings |

**Status (2026-10-24): S8.1-S8.5, S8.7 and a demo checker (S8.2b, `tools/check-demos.py`) are
implemented under `tools/` and run on every push in `.github/workflows/qa.yml.**

Review gates: each phase ends with (a) scripts green, (b) second read of raw markdown, (c) explicit
maintainer approval, then a single publish commit per page.

---

## 9. Phased execution plan

Estimates are focused hours for one author who has the source tree checked out. Phase totals are the
sum of that phase's tasks. Recomputed after Q-3: **39-51 h** (Phase 0 3-4, 1 2-3, 2 3-4, 3 4-5,
4 9-12, 5 8-10, 6 6-8, 7 4-5). The 44-57 h figure in section 1 predates the Q-3 scope cut.

### Phase 0 - Decisions and safety rails (3-4 h) - *blocks everything*
- T0.0 **Executed 2026-10-24** (runbook now in `AGENTS.md`): created public `radix29/tcell-wiki-draft` and
  enabled its wiki (render branch `master`), rewired remotes so the official wiki is fetch-only
  `upstream` with a dead push URL, committed `tools/pages.txt`, `tools/mirror-wiki.sh`, the `README.md`
  unofficial disclaimer and `.github/workflows/qa.yml`, and landed `git push -u origin master`. *(0.5 h)*
- T0.1 Get answers to D-1, D-2, D-3 (blocking), plus D-4..D-9 preferences. **Per Q-0b, D-1, D-2, D-7 and
  D-8 are maintainers' calls - "answered" for us means "we know what to propose", not "decided".**
  *(0.5 h)*
- T0.2 **Superseded by Q-0c (exclude nothing): committed, not ignored.** `PLAN.md`, `AGENTS.md`, `README.md`,
  `tools/` and `.gitignore` are **committed** in the draft repo, because C2's "every `.md` becomes a
  page" hazard exists only where a push renders - and that is the manifest, now. *(done 2026-10-24)*
- T0.3 Fetch `upstream`; record `git rev-parse upstream/master` and copy the current `Home.md` /
  `Gallery.md` into `baseline/`, **committed in the draft** (recovery point + the copy CI's S8.4 diff
  reads), not an untracked dir. **Executed 2026-10-24:** `baseline/Home.md` + `baseline/Gallery.md` are
  byte-identical to `upstream/master` (`8e83ce1`), with `baseline/RECORD.txt` holding the SHAs,
  checksums and the 49-bullet count. Commit them with the next tooling commit. *(0.5 h)*
- T0.4 **Executed 2026-10-24:** S8.1-S8.5 + S8.7 built (see 8's status line), plus `tools/check-demos.py`
  for the linked-examples rule (Q-Ex). The S8.6 spike ran and passed, so it shipped as opt-in
  `headless=yes` inside S8.1 rather than being parked. *(2 h)*
- Exit: decisions recorded in section 4 of this file (**D-1, D-2, D-3 remain open and gate Phase 1**),
  scripts green against the *current* 2-page wiki (done: `tools/review-checklist.py` exits 0), baseline
  saved (done; committing it is the one loose end in Phase 0).

### Phase 1 - Skeleton and nav (2-3 h)
- T1.1 Draft `_Sidebar.md` for the 6-page tree of 5.1 as the **droppable prototype** (5.5): mirrored to
  our draft wiki, never linked to from a page, never in the upstream proposal. *(0.5 h)*
- T1.2 Create stubs for the **5 not-yet-written built pages only** (H1 + purpose sentence + "planned"
  note) so `Home`'s links resolve from the first mirror push. No stubs for deferred pages - nothing may
  link to them anyway (5.5). Keep stubs honest - no empty-looking pages in the render tree. *(1 h)*
- T1.3 Freeze the style guide file (from S7) and run S8.5 over the stubs; add all 6 pages +
  `_Sidebar.md` to `tools/pages.txt` so the mirror is exercised from day one. *(0.5 h)*
- Exit: `Home` nav + prototype sidebar both render sensibly in the draft wiki; zero broken internal
  links; commit set pushed to `origin` (the draft), never to `upstream`.

### Phase 2 - Home rewrite (3-4 h)
- T2.1 Draft `Home.md` per S6.1 (<= 400 words) including the required Gallery and "How to use"
  sections and the Support section. *(2 h)*
- T2.2 Cross-check every factual claim against `../tcell` source/README; verify links (S8.2). *(0.5 h)*
- T2.3 Review gate + publish: `Updated Home (markdown)`. *(0.5 h)*
- Exit: R1 met (description + >= 2 navigation sub-sections); Home links to Gallery and to all three
  how-to pages.

### Phase 3 - Gallery (4-5 h)
- T3.1 Run S8.4 to snapshot the 49 bullets + URL set as the migration contract. *(0.5 h)*
- T3.2 Reformat/migrate into the frozen entry shape; apply D-6 wording fix; keep category order. *(1.5 h)*
- T3.3 Add `## Demos in the Repository` (8 demos + `_demos` note) - read each demo's purpose from
  source so descriptions are truthful. *(1 h)*
- T3.4 Verify all 53 URLs (48 project links + 5 media: 2 blogspot screenshots, 2 YouTube, 1
  GitHub-hosted video) with S8.2; write the 404 report for the maintainer instead of deleting
  entries. *(1 h)*
- T3.5 Lossless check + review + publish: `Updated Gallery (markdown)`. *(0.5 h)*
- Exit: R2 met - all prior information present, count report shows zero unexplained losses.

### Phase 4 - Tutorial (`Getting-Started`) (9-12 h) - *largest single deliverable*
- T4.1 Outline + map the 8-12 snippets to source examples (`TUTORIAL.md`, `demos/hello|styles|
  cursors|colors|clipboard`). *(1.5 h)*
- T4.2 Write sections per S6.3 (Install -> Next steps). *(4-5 h)*
- T4.3 Build the S8.1 harness; make every snippet build; fix until green. *(2-3 h)*
- T4.4 v2-API-leak sweep (grep the banned-symbol list across pages); ASCII/style sweep. *(1 h)*
- T4.5 Dry-run the tutorial on a real terminal (`TERM=xterm-256color`, tmux, Windows Terminal or
  the closest available) and note friction in a review note; adjust. *(1 h)*
- T4.6 Review + publish: `Created Getting-Started (markdown)`. *(0.5 h)*
- Exit: R3a met - a reader can go from empty module to a running, resizing, quit-able program using
  only this page.

### Phase 5 - Architecture (8-10 h)
- T5.1 Renderer probe: confirm mermaid in **our own draft wiki** (push to the mirror, look at it, no
  official wiki involved) or fall back to ASCII for all diagrams. *(0.5-1 h)*
- T5.2 Read the named source files; produce the "where to look" file->responsibility table first
  (it is the spine of the page). *(2-3 h)*
- T5.3 Draft the sections in S6.4 with file citations. *(3-4 h)*
- T5.4 Diagrams (3-4) in the chosen format. *(1.5 h)*
- T5.5 Fact-check pass: each claim cites a file or type name; flag anything speculative or drop it. *(1 h)*
- T5.6 Review + publish: `Created Architecture (markdown)`. *(0.5 h)*
- Exit: R3b met - Architecture page covers layers, backends, input/output pipelines, keyboard
  protocols, Unicode/width, concurrency, with pointers into the source tree.

### Phase 6 - Functionality documentation - **2 pages (6-8 h) after Q-3**
- T6.1 `Function-Reference.md`: hub + area tables (S6.5), absorbing the material the 6 deferred topic
  pages would have carried, as one-line table rows + a short block per area. *(4-5 h)*
- T6.2 `Terminal-Setup.md`: all 8 `TCELL_*` vars + all 9 `Opt*` options + precedence rule, including
  reading the 3 never-documented vars (`TCELL_ALTSCREEN`, `TCELL_COLS`, `TCELL_LINES`) in source first.
  *(1.5-2 h)*
- T6.3 Run S8.3 symbol auditor; iterate until every exported symbol is owned by one of the 6 built
  pages; put the coverage report in the review note, not on a page. *(0.5-1 h, gate re-opened by Q-9)*
- T6.4 Snippets for both pages through the S8.1 harness; review; one commit per page.
- Exit: R3c met **at hub level** - provided functionality documented by task and by symbol across the
  6 built pages; topic pages explicitly listed as the deferred remainder.
- Cut from this phase by Q-3 (backlog, do not build): `Screen-and-Rendering`, `Styles-and-Color`,
  `Events-and-Input`, `Unicode-and-Encodings`, `Platforms`, `Migration-v2-to-v3`.

### Phase 7 - Integration, polish, handoff (4-5 h)
- T7.1 Full-set passes: S8.2 links, S8.5 style, S8.3 coverage, S8.7 per-page checklist. *(1.5 h)*
- T7.2 Nav/sidebar completeness; "See also" graph has no orphans; mobile/terminal rendering spot
  check of tables (wide tables are the usual casualty). *(1 h)*
- T7.3 Maintenance note for the maintainer: a committed file in the draft (not a page, so it is not in
  `tools/pages.txt`), proposed as upstream content only if asked: how to add a gallery entry, how to add
  a page, which scripts to run, what "publish-on-push" implies. *(0.5 h)*
- T7.4 Follow-up list for `../tcell` (F-1: README/TUTORIAL pointers to the wiki, fix the legacy
  `wikis/Gallery` URL, document the 3 undocumented env vars, note the stale `mouse demo` claim);
  file as issues/PRs **only if asked**. **Q-2: parked - prepare this package, do not send it.** *(0.5 h)*
- T7.5 Publish final touches; confirm public result page by page; record published commit SHAs. *(1 h)*

Dependency graph: P0 -> P1 -> P2 -> P3 -> P4 -> P5 -> P6 -> P7. P3 is independent of P4/P5 content
but shares the style/nav work; T6.3 (symbol audit) depends on P4+P5 existing so cross-links and owner
pages resolve.

---

## 10. Requirements traceability

Maintainer confirmed on 2026-10-24 (see 4.1) that this table is the **complete** contract -
nothing in the original request is unrepresented, and no deadline, audience, or size constraint
applies beyond the page budgets in S5.1.

| ID | Requirement (from the request) | Where it is satisfied | Verified by |
|---|---|---|---|
| R1 | Top document: short description of the project | Home `# Tcell` lede + `## Why Tcell` | T2.2, S8.7 |
| R1b | Top document has at least 2 sub-sections incl. Gallery and "How to use" | Home `## Gallery`, `## How to Use` (plus Why/Versions/Install/Platforms/Support) | T2.1 checklist |
| R2 | Gallery keeps all current information | `Gallery.md` migrated 1:1 (+ demos section) | S8.4 URL/bullet diff, T3.5 |
| R3 | "How to use" includes a tutorial | `Getting-Started.md` | T4.6 runnable-program gate |
| R3b | ... and an Architecture document | `Architecture.md` | T5.5 citation check |
| R3c | ... and documentation of provided functionality | `Function-Reference.md` + `Terminal-Setup.md` (Q-3: 6 topic pages deferred, so this is satisfied at hub level) | S8.3 coverage report |
| R4 | Naming may be improved | D-3 decision, S5.1 file names | D-3 sign-off |

---

## 11. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Duplication drift: wiki vs repo `README`/`TUTORIAL`/`CHANGES*` | stale, contradictory docs | S5.4 ownership table; wiki links instead of copying; F-1 follow-up to add pointers |
| Documenting v2 habits as v3 (PollEvent, StyleNormal, Attribute, SimulationScreen, `Color` consts) | readers write broken code | banned-symbol grep (T4.4); all snippets through the compile harness (S8.1) |
| Mermaid support in the wiki renderer fails (C9) | rework of all diagrams | T5.1 probe in our own draft wiki before any diagram is written; fallback is ASCII art in fenced blocks |
| A publish mistake goes live instantly | public misinformation | per-page review gate; baseline copies (T0.3); forward-fix commits only (C7) |
| Loss of a gallery entry during migration (49 bullets, hand-edited) | visible content loss | S8.4 machine diff of bullets + URL sets before publishing |
| Dead/legacy hotlinked screenshots (2 blogspot URLs) | broken images on the showcase | verify, report, propose D-5/D-6; do not silently drop |
| Undocumented env var semantics guessed wrong | wrong user advice | read the handling in source and cite the file; if ambiguous, ask before documenting |
| Wiki is publicly editable (spam/vandalism) | defaced pages | D-8 setting check; keep baseline + periodic `git pull --ff-only` + S8.4-style content diffs |
| Scope creep into rewriting library code/README | plan never finishes | those are F-1 follow-ups, explicitly out of scope |
| **No external signal until the draft is finished** (Q-2 defers all upstream contact): 6 pages of docs nobody asked for, built against guessed answers to D-1/D-2/D-6 | rework, or a public draft that diverges from what the project would accept | every page stays self-contained and paste-able (route-C rule, `AGENTS.md`, 5.5); keep 3 decisions separable and reversible in the draft - one file for `_Sidebar.md` (D-1) so it can be dropped without touching pages, `Home`/`Gallery` never renamed, support links (D-7) never written by us; the draft README states the project is a proposal; re-read this row before starting Phase 5 |
| 6 built pages + 6 deferred ones become a maintenance burden | rot returns in a year | page budgets (S5.1), one-owner-per-topic rule, tables one-line-per-row, maintenance note (T7.3), and the deferred set stays unwritten until the built set survives a month of API churn |

---

## 12. Explicit non-goals / follow-ups

- **Deferred milestone, not abandoned (Q-3):** the 6 topic pages of 5.1 (`Screen-and-Rendering`,
  `Styles-and-Color`, `Events-and-Input`, `Unicode-and-Encodings`, `Platforms`, `Migration-v2-to-v3`)
  and any `_Footer.md`. They are the natural second milestone once the 6-page build renders well in the
  draft wiki; keep their names reserved by not using the names for anything else.
- No changes to the library repo in this pass (F-1 bundles: README pointer + legacy URL fix,
  `TUTORIAL.md` pointer, env var docs, stale demo claim, sidebar naming if a `_Footer.md` is wanted).
- No v1 content, no v1 migration page (v1 is unmaintained).
- No auto-generated godoc mirror - the wiki explains, `pkg.go.dev` references.
- No translations, no PDF/Pub output, no static-site generator migration (out of scope unless the
  maintainer wants it: a real docs site would fix sidebar/diagram/CI limits in C4-C6).
- No third-party screenshots added to the repo (licensing unclear).
- No re-license/rebrand decisions (badges, Stand-With-Ukraine banner, commercial support wording are
  Home-level links only, sourced from the repo README).

---

## 13. Definition of Done (final acceptance checklist)

- [ ] `Home.md` has a short project description and at least the Gallery + How-to-use sub-sections, <= 400 words.
- [ ] `Gallery.md` contains all 48 linked entries + the 1 legacy bullet (or a recorded, approved
      deviation), every URL status recorded, new demos section present.
- [ ] The 6 built pages (`Home`, `Gallery`, `Getting-Started`, `Architecture`, `Function-Reference`,
      `Terminal-Setup`) exist and are linked from `Home`; no page links to a deferred page. (Q-3)
- [ ] Every code fence in the wiki is `go`-tagged, `gofmt`-clean and builds in the S8.1 harness.
- [ ] Symbol coverage report shows 100% of root-package exported symbols owned by exactly one of the 6
      built pages (gate wording pending the open coverage-gate question).
- [ ] All 8 `TCELL_*` env vars and all 9 `Opt*` options documented, with precedence stated.
- [ ] S8.2/S8.3/S8.4/S8.5 all green immediately before each publish commit.
- [ ] The mirrored render tree contains exactly the 6 pages + the droppable `_Sidebar.md` prototype;
      `PLAN.md`, `AGENTS.md`, `README.md`, `tools/` are never mirrored (`tools/pages.txt` is the gate).
- [ ] Every page reviewed in raw markdown **and** as rendered in our draft wiki at
      `https://github.com/radix29/tcell-wiki-draft/wiki/<slug>` (Q-0b: the official wiki is read-only,
      so "reviewed where it is published" means the mirror until upstream accepts something).
- [ ] Maintainer explicitly approved each publish; nothing force-pushed; history is forward-only.

---

## Appendix A - Symbol inventory to be assigned to owner pages

From `go doc -all github.com/gdamore/tcell/v3` (2,023 lines): 38 exported types including
`AttrMask`, `ButtonMask`, `CellBuffer`, `CursorStyle`, `Color`, `EncodingFallback`, `Event`,
`EventHandler`, `Key`, `KeyProtocol`, `KittyKbdMode`, `ModMask`, `MouseFlags`, `Opt*` (9),
`Screen`, `Style`, `TerminfoScreenOption`, `Tty`, `UnderlineStyle`, `WindowSize`, `XtermKbdMode`;
events `EventClipboard/Error/Focus/Interrupt/Key/Mouse/Paste/Resize/Time`;
constructors `NewScreen`, `NewTerminfoScreen`, `NewTerminfoScreenFromTty`, `NewDevTty(FromDev)`,
`NewStdIoTty`, `NewEvent*` (9), `NewHexColor`, `NewRGBColor`, `FromImageColor`, `PaletteColor`,
`GetColor`, `FindColor`; vars `ColorNames`, `ColorValues`, `KeyNames`, `RuneFallbacks`,
`StyleDefault`, the `AttrMask` constants (`AttrBold`, `AttrBlink`, `AttrReverse`, `AttrDim`,
`AttrItalic`, `AttrStrikeThrough`, `AttrNone`, `AttrInvalid` - note there is **no** underline
attribute constant; underline is `UnderlineStyle` + `Style.Underline()`), and the key/rune
constant blocks; funcs `GetEncoding`, `RegisterEncoding`, `SetEncodingFallback`, `ShimScreen`.
Note: there is no exported `TerminfoScreen` type in v3 (only `NewTerminfoScreen` and the
`TerminfoScreenOption` type) - do not invent one on a page.
(The exact list is regenerated by S8.3 at implementation time; this appendix is a sizing guide.)

## Appendix B - Gallery migration contract (recomputed at T3.1)

Demonstrations 4 / Editors 3 / UI Frameworks 7 / Games 13 / Productivity & Utilities 21 /
Miscellaneous 1 = 49 bullets, 48 with links, 44 on github.com. Hosts and counts in S2.
Post-migration rule: same 49 or `49 + N` with `N` approved additions; every delta listed in the
review note with its commit message.

## Appendix C - Commands to re-derive every fact in this plan

```bash
# wiki state
git -C /home/radu/go/tcell.wiki log --format=%s
awk '/^## /{if(s!="")print s": "c; s=$0; c=0; next} /^- /{c++} END{print s": "c}' /home/radu/go/tcell.wiki/Gallery.md

# library API surface
cd /home/radu/go/tcell && go doc -all . > /tmp/tcell-doc.txt
sed -n '/^type Screen interface/,/^}/p' /tmp/tcell-doc.txt | grep -oP '^\t[A-Z][A-Za-z]*'

# env vars actually implemented vs documented
grep -rhoP 'TCELL_[A-Z_]+' --include='*.go' . | sort -u
grep -hoP  'TCELL_[A-Z_]+' *.md | sort -u
```

## Appendix D - Commit / paste sequence (Q-3 + Q-0b revised: we push to the draft, never upstream)

In the **draft** repo, one commit per page so the draft's own history reads like a changelog, in the
order the pages get written: `Getting-Started`, `Architecture`, `Function-Reference`, `Terminal-Setup`,
then `Updated Home` last, so the hub never links to a page that does not exist yet. `_Sidebar.md` goes
in its own commit and lands last (it is droppable, 5.5).

If upstream ever accepts pages (Q-2 parked), the same order is the **paste order** in the wiki web
editor, with GitHub's own messages (`Created <Page> (markdown)`, `Updated Home (markdown)`): one page
per paste, never two pages in one edit, because the wiki page history is the reader-facing changelog
and a maintainer reviews it as such. Home still goes last.
