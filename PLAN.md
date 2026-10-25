# Tcell Wiki Rebuild - Implementation Plan

Status: Phase 0 complete (draft repo, remotes, manifest, baseline, S8 tooling, CI); Phases 1-4 built,
green and **published** - Q-15 removed the ask, so the preview at `radix29/tcell-wiki-draft/wiki` renders
all 7 manifest pages including Phase 2's `Home.md` rewrite, Phase 3's `Gallery.md` (all 49 baseline
entries intact, one recorded addition, the sanctioned `## Demos in the Repository` section, and every URL
on the page answering 200) and Phase 4's `Getting-Started.md` (1,134 prose words, five authored sections,
two measured `console` blocks, zero lines of Go, and 14 external targets all answering 200); Phases 5-7
not started
Scope: rewrite `github.com/gdamore/tcell.wiki` from scratch (Home + Gallery + Getting-Started +
Architecture + Function-Reference + Terminal-Setup - the 6-page build decided by Q-3 and named by Q-5)
Out of scope (this pass): any change to the `../tcell` library repo, its `README.md`, `TUTORIAL.md`, or code

> **Premise change (2026-10-24, see 4.1 Q-0b).** The person doing this work is **not** a maintainer of
> `gdamore/tcell` or `gdamore/tcell.wiki` and has **no push access to either** (verified: no stored
> credentials for `https://github.com/gdamore/tcell.wiki.git`; `git push --dry-run` fails at auth).
> The *maintainer* model this plan was first drafted against is gone; the contributor model is in force (Q-0b,
> Q-0c): author pages in a repo the author owns, then propose them upstream page by page. Not a fork - GitHub
> offers no Fork for `.wiki` repos, and a fork of the code repo carries no wiki content. D-2, D-3, D-6, D-7 and
> D-9 are answered here (Q-4, Q-5, Q-7, Q-8, Q-9), D-1 stays a proposal item, and every F-1 item is an upstream
> ask this draft must not pre-empt.
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
six page bodies themselves are **31-40 h**, the rest is Phase 0 tooling and Phases 1/7 rails. (Q-4 re-cut
Phase 4 from 9-12 h to 4-6 h the same day, which makes the honest total **34-45 h**; section 9 carries the
arithmetic, and Phase 4's record the hours it actually took.)
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
| Link hosts (upstream baseline) | github.com 44, code.rocketnine.space 2 (moved to codeberg.org by Q-11), 2.bp.blogspot.com 2, youtu.be 1, www.youtube.com 1, user-images.githubusercontent.com 1, termshark.io 1, git.sr.ht 1 |
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
| C1 | Publish-on-push, no PRs, anyone with the link can also edit in the web UI | every phase ends with a local review gate; publish only on explicit approval. **Revised by Q-0b: we cannot push at all, so "publish" now means a web-UI edit accepted upstream, or handing content to a maintainer; the review gate moves from "before we push" to "before we propose".** **Revised again by Q-15: for the draft's own two repos the approval is pre-delegated, so C1's protection here is the review gate and the mirror's guards rather than a human answer - and upstream is unchanged, because a proposal stays the only channel there.** |
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
| D-2* | Canonical home for user docs: wiki, or repo `README`/`TUTORIAL.md` with the other pointing here? | **Answered (Q-4): the repo is canonical for prose the library already maintains. `Home` and `Getting-Started` link `README.md` and `TUTORIAL.md` in `gdamore/tcell` and duplicate nothing** | Phase 3, 5 |
| D-3* | Page naming for the "how to use" area: `Getting-Started` + `Function-Reference`, or one big `How-To-Use`? | **Confirmed (Q-5): two pages, and the four new slugs stand as written - `Getting-Started`, `Architecture`, `Function-Reference`, `Terminal-Setup`** | Phase 2 |
| D-4 | Version coverage: v3 only, or v3 + migration notes for v2 users? | **Moot for this build (Q-3): v3-only voice, `Migration-v2-to-v3` deferred; `Home`/`Function-Reference` link the repo `CHANGESv3.md` instead of forking it** | Phase 5 |
| D-5 | Store screenshots in the wiki repo, or keep hotlinks only? | **Answered (pre-settled by Q-0c, restated in 7): hotlinks only - no image files in the page set, so diagrams are Mermaid or ASCII in fenced blocks. Reopens only if a maintainer offers to host files** | Phase 4 |
| D-6 | Drop/keep the legacy unlinked `mouse demo` bullet + 2015 blogspot screenshots? | **Answered (Q-7): keep it, reworded so it does not claim a shipped demo; hotlinks stay until they 404** | Phase 1 |
| D-7 | Should the wiki list community/commercial support (TideLift, Staysail, Discord)? | **Answered (Q-8): no. The wiki carries no support/commercial list at all - readers go to the repo README and `SECURITY.md`** | Phase 2 |
| D-8 | Repo setting: restrict wiki editing to collaborators? | **Closed, nothing to ask (Q-10): the wiki repo is collaborator-only - only the `tcell` maintainer can edit it. That is a platform boundary, not a favour to request** | - |
| D-9 | Authoring language/style: keep `_Tcell_` italics convention used by README + current Gallery? | **Answered (Q-9): `_Tcell_` in prose everywhere**, bare `Tcell` only in headings/file names/paths, `tcell` literal in code - enforced by `check-style.py` rules `name` and `heading-period` | all |

**Whose decision is whose (per Q-0b):** D-1 (site-wide `_Sidebar.md`), D-2 (wiki vs repo as canonical docs
home) and D-7 (whose commercial/community links appear - answered Q-8 as "none of ours") and every F-1 item are
`gdamore` maintainers' calls - we may only *propose* them, and must not pre-implement them in the official
wiki. D-3, D-4, D-5, D-6, D-9 are ours for as long as the work lives in our own draft repo.

### 4.1 Decision record (maintainer answers)

Row IDs are the **decision** IDs (`Q-0`, `Q-0b`, `Q-0c`, `Q-2`, `Q-3`, ...) and they run one behind the
question numbers used out loud in the Q&A, because `Q-0b` and `Q-0c` were follow-ups to `Q-0`. The next
answer is recorded as `Q-16`. Mapping so far: requirements = Q-0, contributor premise = Q-0b, vehicle +
motivation = Q-0c / Q-1, upstream timing = Q-2, scope = Q-3, canonical docs home = Q-4, page naming =
Q-5, coverage gate = Q-6, legacy demo bullet = Q-7, support links = Q-8, name styling = Q-9, wiki
editing boundary = Q-10, dead-host policy = Q-11, publish + preview = Q-12, gallery addition = Q-13,
standing publish rule = Q-14, publish without asking = Q-15.

| ID | Answer | Date | Effect on this plan |
|---|---|---|---|
| Q-0 (requirements) | **§10 is the complete requirements contract** - no deadline, tone/audience, gallery-restructure restriction, or size cap beyond what is already written here | 2026-10-24 | Section 10 upgraded from "traceability of the request" to the authoritative contract; no provenance gap remains |
| Q-3 (scope) | **(b) 6 pages: `Home`, `Gallery`, `Getting-Started`, `Architecture`, `Function-Reference`, `Terminal-Setup`** | 2026-10-24 | Re-estimates the plan at 39-51 h (page bodies 31-40 h). The other 6 topic pages of 5.1 become a **deferred second milestone** (5.1, 6.6, 12), which has three consequences bigger than the hour count: (1) `Function-Reference` absorbs their audience and grows to 1,000-1,400 words, (2) the 100%-symbol-coverage gate now concentrates the whole API into one page - the `pkg.go.dev` mirror tension is now live - open coverage-gate question, see 6.5 - and (3) no built page may link a deferred page (route-C self-containment rule). Also decides nav: `Home` is the hub and `_Sidebar.md` is built as a **droppable prototype mirrored only to our own wiki**, because a site-wide sidebar is an upstream call (D-1) and this keeps it reversible. D-4 (migration page) becomes moot - breaking changes are linked to repo `CHANGESv3.md` instead. |
| Q-2 (upstream timing) | **"Ignore the talk for now, we build it first"** - no issue in `gdamore/tcell`, no upstream contact, until the draft says otherwise | 2026-10-24 | `PLAN.md` Phase 7 marked PARKED (draft stays public so the eventual pitch is just a URL). Plan effects: Phase 7 T7.4 becomes "prepare the proposal package, do not send"; the D-list items that needed upstream (D-2 canonical home, D-1 site-wide sidebar, D-6 wording of a live line, D-7 whose support links) are now **decided as draft-owner questions by us** and separately flagged as "must be asked before it could ever land upstream"; new risk row added. Consequence to hold onto: everything we write must still be paste-able one page at a time, because "build first" must not quietly turn into "a different project with different constraints". |
| Q-0c (vehicle) | **Route C**: author in `radix29/tcell-wiki-draft` (plain repo = source of truth; its own wiki = render preview), propose upstream page by page, GitHub Pages only if upstream declines. Motivation confirmed as "Tcell's docs should be better", not "a project I own end-to-end" | 2026-10-24 | `setup.md` written and referenced from Phase 0 (T0.0); merged into `AGENTS.md` the same day. Consequences: the official wiki becomes a fetch-only remote `upstream` plus a `--push` URL guard; tooling moves from "forever untracked" to committed in the draft repo (`tools/`, `samples/`, `AGENTS.md`, `PLAN.md`), because the C2 "every .md becomes a page" hazard now only exists in the *mirror*, which is driven by `tools/pages.txt`; CI becomes possible in the draft, so C6 reads "no CI **upstream**" and the draft's Actions is our gate while the upstream artefact stays untestable; T5.1's Mermaid probe and any `_Sidebar.md` experiment move to our own wiki, deleting the "push a scratch page to the live official wiki" step; new route-C rule: **a page body may not reference anything outside itself** (no repo-hosted `images/`, no `tools/` links), which pre-answers D-5 as "hotlinks + Mermaid/ASCII only". |
| Q-Ex (examples) | **The wiki links the library's own examples instead of authoring them.** Pages cite `demos/` (8 programs, each with a rendering test) and `TUTORIAL.md` in `gdamore/tcell`; a page fence carries only the fragment under discussion | 2026-10-24 | `samples/smoke/` deleted as an authored example. `tools/check-demos.py` checks the names, URLs, `go run` commands and `_demos/` claims against the checkout and prints the paste-able `## Demos in the Repository` block with `TODO(desc)` where a demo has no doc sentence (6 of 8) rather than inventing prose. Cuts Phase 4 authoring (snippets become small `mode=lib` fragments, still S8.1-compiled and S8.6-run) and turns the Gallery's new section into generated text. Library-side ask for the F-1 package: doc comments on the demos so descriptions come from the library itself. |
| Q-4 (canonical docs home, D-2) | **"link the README and TUTORIAL from tcell, do not duplicate"** - the repo is canonical for prose the library maintains | 2026-10-24 | Reverses the old recommendation (wiki canonical). Effects: (1) `Getting-Started` becomes a routing page - authored sections limited to Install / Run the demos / Before you start / the 5 always-present pieces / Where to go next, everything else links a `TUTORIAL.md` heading, so Phase 4 drops from 9-12 h to 4-6 h and the 300-450 line authoring target is gone; (2) R3 is still met (a tutorial exists; it has one owner) but T4.5's gate becomes "walk the page plus its links"; (3) `Home` keeps 2-3 sentences and links `README.md` instead of mirroring its feature essay, so S5.4's Home row is now link-only for the long form; (4) duplication risk is closed rather than managed, and F-1 shrinks to adding repo->wiki pointers (env vars, Gallery, TUTORIAL->wiki) because the wiki->repo direction needs no edit; (5) new failure mode to watch: `TUTORIAL.md` headings are link targets we do not control, so a rename upstream breaks this page - `tools/check-demos.py` verifies the file exists in the checkout and that every `#anchor` matches a heading it actually has (built and tested 2026-10-24), and Phase 4 T4.1 reads the file end to end first |
| Q-5 (page naming, D-3) | **"confirm"** - `Getting-Started.md`, `Architecture.md`, `Function-Reference.md`, `Terminal-Setup.md` alongside the untouchable `Home.md` / `Gallery.md` | 2026-10-24 | Unblocks Phase 1 T1.1-T1.3 (page stubs + `_Sidebar.md` prototype can now use real slugs) and Phase 2. Consequences: slugs are forever once mirrored, so `check-style.py`'s hyphen/ASCII rules and `check-links.py`'s slug existence checks are the safety net for typos, not for renames; the 6 deferred topic pages of 5.1 keep their drafted names but stay unwritten (Q-3), and no built page may link one (route-C rule); `How-To-Use` is dead, so nothing may hedge by creating it later as a redirect - GitHub wikis have no redirects |
| Q-6 (coverage gate, 6.5) | **Recommendation adopted: structural coverage plus reader-meets prioritization** (options 2 + 3) - gate on the 179 structural names (38 types, 25 funcs, 8 vars, 111 method names) being named by exactly one built page, document the 712 constants **by group** with a `pkg.go.dev` link per group, and use the API in the library's own `TUTORIAL.md`/`README.md`/`CHANGESv3.md`/`demos/` (measured: 130 names) as the priority order inside that gate | 2026-10-24 | Closes the last open exit criterion in 6.5 and 13: `--gate` now enforces this contract (`--gate-kinds type,func,var,method`, constants checked as 14 group tokens), so 100% stops meaning 891 table rows; a page owns a symbol by naming it in backticks on exactly one page, which is also how 5.4's single-owner rule becomes machine-checked (`SHARE` finding on a second owner); the `pkg.go.dev` mirror risk (12's "no auto-generated godoc mirror") is answered structurally rather than by taste. Honest state at the time of writing: gate fails with 5 findings (0 structural names claimed, 14 groups unclaimed) because no content page exists yet, and CI deliberately runs the report, not `--gate`. Verified both directions against a synthetic page that owns the vars and claims the groups - it passes |
| Q-7 (legacy bullet, D-6) | **Option 1: keep the `mouse demo` bullet, reword it, keep the two 2015 blogspot hotlinks until they 404** | 2026-10-24 | `Gallery.md` keeps 49 bullets, so Appendix B's migration contract and `check-gallery.py`'s baseline diff need no amendment (option 2 would have been a recorded deviation with a failing check to match). The wording must stop claiming a shipped demo: the only mouse program left is `_demos/mouse.go` under `//go:build ignore`, while the 8 shipped demos get the generated `## Demos in the Repository` section (Q-Ex), so the bullet becomes a dated historical note rather than a pointer. Approved sentence shape is in 6.2, using only surface-verified names (`EnableMouse`, `MouseFlags`) - not `MouseAllMotions`, which v2 had and v3 does not. Both URLs still return 200 as of 2026-10-24; when one dies, `check-links.py`'s allow-list is where that gets recorded, not a silent deletion of the reader's link. |
| Q-8 (support links, D-7) | **Option 1: nothing.** No Support or Community section on `Home`, and no support links anywhere in the wiki; the option 2 compromise (a one-line pointer to README/`SECURITY.md`) was explicitly declined | 2026-10-24 | Closes D-7, the last D-item that was purely "is this ours to write?" - the answer is no, and unlike a naming call this one is cheap for a maintainer to add themselves, which is why declining it is not a loss. Effects: 6.1 and Phase 2 T2.1 lose their Support section (T2.1 said to include one - now fixed, the second contradiction between an early draft and a later decision); `Home`'s `## Versions`/`## License` lines still carry the pointers a reader legitimately needs (import path, `CHANGESv3.md`, Apache-2.0); the security-contact question stays with `SECURITY.md`, which `../tcell/README.md` already surfaces; and nothing in the proposal package has to ask permission for content we simply do not write. If a maintainer wants support links on the wiki later, that is a 3-line edit they can make directly - no draft work is thrown away. |
| Q-9 (name styling, D-9) | **Option 1: `_Tcell_` in prose everywhere**; bare `Tcell` only in headings, file names and paths, `tcell` literal in code, versions stay `v3` | 2026-10-24 | Cheapest of the open items and the one with the least room for argument: the corpus already decided (`../tcell` writes `_Tcell_` 34:1, the wiki 2:1 with the bare use inside a heading), option 3 would decay the moment a maintainer edits through the web UI, and option 2 would fork style from the docs one click away. Now actually enforced: `check-style.py` gained rules `name` and `heading-period`, tested in both directions. **Two corrections to claims I made earlier in this session and should not have:** (a) I said the linter already had a `name` rule and "verified" it with a grep whose quoting had silently broken - there was no such rule until this commit, and no trailing-period heading rule either; (b) I described `## Demos in the Repository` as something `Gallery.md` has, when 6.2/T3.3 schedule it for Phase 3 and today's Gallery still has only the 6 categories. Both are fixed or stated correctly now. The 2 legacy suppressions in `tools/style-allow.txt` are still 2, so no new page debt was created by the new rules. |
| Q-10 (wiki editing, D-8) | **Not a decision - a platform boundary.** The wiki repo cannot be edited publicly; only the `tcell` maintainer can edit it, so there is nothing to ask for and no process proposal to write | 2026-10-24 | Closes the last "upstream's call" item that was never ours to make, and removes a whole paragraph from the proposal package: the earlier draft asked maintainers to restrict editing and to treat wiki PRs as review-required, which reads as a stranger instructing an owner about their own repository. Two honest caveats: (a) the setting is invisible to us from outside - GitHub sends unauthenticated users to sign-in for `/_new`, so "restricted" here is the owner's word plus the circumstantial evidence that all 10 upstream commits are gdamore's with zero drive-by edits in a decade; (b) what Q-10 *does* change mechanically is our own risk table (row 11 of 11 is rewritten from "defaced pages" to "our draft drifts from upstream"), and it means the proposal package ships as page content plus the D-1 sidebar call and nothing else. Also correcting the record: an earlier patch to the premise block in this file silently no-op'd (a leading-space mismatch defeated the string match while the assert still passed on other replacements), which is why a stale "pending revision to a contributor model" paragraph survived one more round of my claiming it was updated - it is replaced now and re-read raw instead of trusted. |
| Q-11 (dead Gallery hosts - not a D-item; surfaced by the S8.2 link checker) | **Option 2: move the URLs** to the project's real home; descriptions untouched; `tools/gallery-moves.txt` records old -> new plus evidence so the migration contract still reads lossless. Done now, not in Phase 3: `cview` and `cbind` | 2026-10-24 | My recommended target was wrong and the evidence overrode it: I proposed `github.com/tslocum/*`, but the GitHub API describes both repos as `THIS IS A MIRROR - SEE LINK BELOW` with homepage `codeberg.org/tslocum/<repo>`, and each `go.mod` now declares `module codeberg.org/tslocum/<repo>` - so the GitHub link would have made the wiki send readers to a self-declared mirror and the old vanity path is not even an import alias any more. AGENTS' "prefer the project's real home" decided it, not the option text. First content edit ever made to a page body in this draft, so the honest state is: `git diff --stat upstream/master HEAD -- Home.md Gallery.md` is now **2 changed lines**, not empty, and the "byte-identical to upstream" property in 4.2/AGENTS ends here by decision rather than by accident - the diff is the deliverable now, one reviewable URL line per project. `check-gallery.py` gained move support plus three stale-record failures (page still links the old URL; record uses a URL no baseline entry has; move applied to something else), all tested. `tools/link-status-allow.txt` loses both rocketnine entries because nothing unreachable remains on the page, and the file keeps the DNS evidence plus a note that an earlier claim here - "module path unchanged" - was wrong. Allow-listing a dead link to quiet CI is now explicitly not the policy: it deletes the reader's way to reach a living project. |
| Q-12 (publish) | **Option 3: commit, push the draft, publish the render preview** | 2026-10-24 | Executed the same turn: 14 commits pushed to `origin/master` (now `5eee58c`, `d8aa87b..5eee58c` fast-forward, nothing forced or amended), then `tools/mirror-wiki.sh` published `Home.md` + `Gallery.md` to the draft wiki - render HEAD `2ebcbf8` -> `32022f9` (`Preview draft pages`), so the preview at `github.com/radix29/tcell-wiki-draft/wiki` is now something a reader can look at instead of a plan section, and `/wiki/Gallery` renders with the moved Codeberg links. Two facts this turned from prediction into measurement: **CI passed for real** (run `40112709147`, 15/15 steps green including the informational mirror step), which is the first evidence that the gates are not just green on my machine; and the `git diff --stat upstream/master HEAD -- Home.md Gallery.md` check in AGENTS' verify list changed meaning from "must be empty" to "is the deliverable" - today it is 2 lines in `Gallery.md`, 0 in `Home.md`, and any future growth in that number is the review surface. Upstream is still untouched by construction: its push URL is a dead path. Next unblocked step is Phase 1 (`_Sidebar.md` prototype to look at D-1 rendered, plus the Home rewrite skeleton), and Q-13 is whichever question Phase 1 surfaces next. |
| Q-13 (gallery addition) | **Add `goSSMS` to `## Productivity & Utilities`** - the author asked for their own application to be listed | 2026-10-24 | First addition to the Gallery since the baseline, so the contract moved from "49 bullets" to "49 + N recorded additions" (Appendix B allowed exactly that and this is the first time `N` is non-zero). Verified before writing the line: URL answers 200; `radix29/gossms` is Go, not a fork, active; `go.mod` requires `github.com/gdamore/tcell/v3 v3.6.0`, which is what makes it eligible for a *Tcell* gallery at all; the description paraphrases the README ("a terminal-based SQL Server management application", Linux/macOS/Windows) rather than inventing features, and on review drops the README's "single executable" packaging detail - a one-binary note is a distribution fact that ages the moment the project starts shipping packages, which is the same rule that bans star counts and "(new)" markers; appended at the end of the category per AGENTS (never alphabetical); display name keeps the project's own `goSSMS` styling, which the page already tolerates (`myGoAdventure`, `WTF`). Mechanically this is why the addition is legal and everything else still fails: `tools/gallery-additions.txt` holds one record per approved entry (name, URL, evidence) and `check-gallery.py` subtracts those from the addition budget, so `--max-additions` stays 0 in CI and a second unrecorded bullet still fails - tested against a synthetic second entry, a record for an entry that is not on the page, a record whose URL disagrees with the page (both trailing-slash forms, since upstream writes `github.com/zyedidia/micro/` with a slash), and a record approving an entry that is already upstream. Deliberately *not* done: no `demo.gif` media link (the README has one and it resolves, but one URL per entry keeps the migration diff reviewable and media is a maintainer call), and no claim that this was curated - it is author-supplied, recorded as such, and goes into the proposal package (T7.4) flagged the same way. Page state after the edit: 50 bullets, 49 linked, `github.com` 45, `codeberg.org` 2, and `git diff --stat upstream/master HEAD -- Home.md Gallery.md` up from 2 lines to 3. |
| Q-14 (standing publish rule) | **Every push publishes the preview.** `tools/publish.sh` is now the publish path: mirror, then push, then re-check the live wiki | 2026-10-24 | Recorded because "I'll remember to mirror" is how a preview goes stale, and a preview nobody trusts is worse than none: the CI step that used to be `continue-on-error: true` informational is now a real gate (`tools/mirror-wiki.sh --check`, exit 1 when the live wiki does not render the manifest exactly). Order is mirror-then-push, which looks backwards until you notice CI starts on the push - pushing first makes the gate race the mirror, and a gate that fails for no real reason gets ignored the next time it means something. Two side effects worth having: the mirror now **refuses** to publish pages with uncommitted edits (the render tree is a build output of committed text, so publishing a dirty page would put words on a public wiki that no commit and no review ever saw - `FORCE=1` exists for an emergency), and `restore_mirror()` replaced the copy-pasted dry-run cleanup so the check cannot leave the clone dirty. Tested both ways: in-sync preview exits 0; a locally edited page exits 2 at the guard, and with `FORCE=1` exits 1 with the drift diff plus the reminder that a web-UI edit belongs in the repo first. Two things only running it for real found: the script called `mirror-wiki.sh` at the repo root instead of in `tools/` (it has never been anything else, which is what committing an untested script is worth), and an interrupted `--check` - mine died on `SIGPIPE` from `head -3` - left the shared render clone staged, after which the mirror aborted with "commit or clean it first" for a directory nobody has ever edited by hand. That guard now resets the clone and says why, because worktree dirt there can only be this script's own leftovers (a web-UI edit arrives by the pull above and is reported there), and it is a build output of this repo. Also fixed two pieces of stale documentation found while writing this: AGENTS still listed D-2/D-6/D-7/D-8 as "an upstream call" after Q-4/Q-7/Q-8/Q-10 closed them, and it described `tools/link-status-allow.txt` as the place where unreachable URLs are kept, which Q-11 made the opposite of policy. |
| Q-15 (publish authority) | **The agent publishes.** Commit, mirror and push whenever the work needs it - no per-page ask, no per-commit ask | 2026-10-24 | The draft owner's instruction, in their words: "change the agents so you can push, publish and mirror automatically when you need it". Recorded as a decision rather than a mood because the rule it replaces was the strongest one in `AGENTS.md` ("Never `git push` (or `git commit`) unless explicitly asked to. Ask instead."), and removing it moves real risk: the render wiki is public, has no review gate, and publishes instantly, so an unreviewed page can now reach a reader with nobody in the loop. What pays for that is the machinery this plan had already made a gate instead of a courtesy - six GATEs plus the mechanical CHECKs in `tools/review-checklist.py`, `--dry-run` to inspect a publish before it happens, the mirror's refusal to publish a dirty page (Q-14), and CI's `preview` step, which is the reviewer the human "yes" was standing in for. Keeping the ask also contradicted Q-14's own reasoning: a preview nobody trusts is worse than none, and a preview that waits on one word from a human is that - measured here, Phase 1 sat complete and unpublished for a whole phase and Phase 2's hub sat the same way, so the preview rendered a two-page draft while seven pages existed on disk. What did **not** change, because none of it is what Q-15 was about: Q-14's mechanism (mirror, then push, then re-read the live wiki, one command), one logical change per commit with wiki-styled page messages, forward-only history with nothing mirrored ever force-pushed, rebased or amended, `upstream` still unpushable by construction (dead push URL), and Q-2's rule that `gdamore/tcell` is not contacted until the draft owner says so - that one is a human opening an issue on someone else's repo, and pre-authorization on our two repos does not reach it. First run of the authority: `tools/publish.sh` shipped render `39e5378` -> `fa34e5a` (`Preview draft pages`, 6 files, 116 insertions: the rewritten `Home.md`, four Q-3 stubs, `_Sidebar.md`) and pushed `origin/master` `731b430..91a0da9` (17 commits), after which the script's own re-read reported "preview is current ... 7 page(s)". `README.md`'s publishing block now names `tools/publish.sh` beside `--dry-run`, because a front page that shows only the bare mirror script invites a half-publish. |
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
Getting-Started's snippet half broke at Phase 4 and its word half held (1,134 prose words): Q-4 left the
routing page nothing to paste, so it has 0 snippets and 2 `console` blocks - see 6.3's rules line and
Phase 4's T4.3 record for why an honest version of "8-12 snippets" is no snippets.

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
| Tutorial program | repo `TUTORIAL.md` (Q-4) | `Getting-Started` links its sections and adds only what it lacks (install, terminal prerequisites, demos, next steps); never restates its code |
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
  requirement R2), `## How to Use` (four bullets pointing at `Getting-Started`, `Architecture`,
  `Function-Reference` and `Terminal-Setup` - requirement R3. This row said three bullets until Phase 2 was
  built, which was written before Q-3 made `Terminal-Setup` one of the 6 built pages and before 13's "the 6
  built pages are linked from `Home`" became an acceptance item, so the fourth bullet is 13 asking for it
  rather than scope creep, corrected the way T1.2's "five stubs" was corrected), `## Platforms` (1 line each, linking the repo `README-*.md`
  since there is no `Platforms` page in scope), `## License` (Apache-2.0).
  **No Support/Community section (Q-8, closing Q-0b/Q-2: TideLift, Staysail and Discord links are the
  project's to place, not a contributor's; and per Q-4 the wiki does not copy README's list anyway).** Home is also the nav hub (5.5), so these sections carry the links.
- Sources: `../tcell/README.md`, `../tcell/doc.go`, `../tcell/go.mod`, `../tcell/SECURITY.md`.
- Explicitly NOT here: badges, the long color/encodings essays, breaking-change prose.
- Verification: all 3 required elements present (short description, Gallery section, How-to-use
  section); every link checked; word count <= 400.

### 6.2 `Gallery.md`

- Migrate **all 49 bullets verbatim in content** into the existing 6 categories, preserving order
  within categories (append-only history), then:
  - fix the `## UI Frameworks ` trailing space only if the whitespace itself is the fix (D-9 style
    rule: no cosmetic churn) - decision: leave, since it renders identically;
  - rewrite the legacy `mouse demo` bullet per D-6/Q-7 to the approved shape:
    `- mouse demo - the mouse test that shipped with Tcell in 2015 ([screenshot](u1), [screenshot](u2));
    mouse support is now enabled per program with EnableMouse and MouseFlags` - display name, both URLs
    and the bullet count (49) unchanged, `EnableMouse`/`MouseFlags` verified against the surface;
    **as written onto the page in Phase 3 it differs in three places, every one a rule beating the
    template**: `_Tcell_` (Q-9's `name` rule rejects bare `Tcell` in prose), no backticks on the two API
    names (Q-6 gives them to `Function-Reference`, and no other Gallery entry carries a backtick), and
    **one** screenshot URL rather than `u1`+`u2` - the shape assumed both 2015 blogspot images sat on this
    bullet, and the second has always been the `govisor` entry's, which the 49-bullet count depends on;
  - add `## Demos in the Repository` with the 8 `demos/` programs and a one-line description of
    each, plus a note that `_demos/` files are `//go:build ignore` and how to run them.
- New subsection under each category only if a future entry genuinely needs it (no one-off sections).
- Entry format frozen: `- [name](url) - short description` (ASCII `- `, no trailing period),
  optional ` ([screenshot](url))` / `([video](url))`; `_italics_` for third-party tool names.
- Verify (lossless migration): per-category counts before/after must match the S2 checklist;
  `grep -c '^- ' Gallery.md` before = 49 (or 49 + deliberate changes recorded in the checklist).
- Verify every external URL with `curl` (S8.2); record the 2 blogspot + 3 video URLs status in the
  migration checklist; never delete an entry because of a 404 - report it instead.
- **An entry we add is a decision, not an edit (Q-13).** New projects are appended to the end of their
  category and are only legal while `tools/gallery-additions.txt` carries their name, URL and evidence
  (URL resolves, project is real, it actually depends on Tcell, author-supplied if it was). That file,
  not `--max-additions`, is what approves them, so CI keeps a zero budget for everything unrecorded and
  a second bullet without its own record still fails.
- **A dead host is not a dead entry (Q-11).** When the host is gone but the project is alive, move the
  URL to where the project actually lives (checked against its own description, homepage field,
  `go.mod` module path and tag SHAs - a repo that labels itself `THIS IS A MIRROR` is not a home) and
  record the move, with evidence, in `tools/gallery-moves.txt`. That file is what lets
  `check-gallery.py` call the line the same entry instead of one lost plus one added. A 404 on a
  *screenshot or video* is different: those are historical artefacts with no other home, so they get
  reported (D-6/Q-7), not moved.
- De-duplication: two `go-tetris` entries exist (different owners) - keep both, and add owner
  disambiguation to the description if the maintainer agrees (D-list item to fold into D-6 review).

### 6.3 `Getting-Started.md` (the tutorial)

- **Q-4 rule: this page teaches by linking, not by retelling.** `../tcell/TUTORIAL.md` holds the
  tutorial prose (330 lines, v3-current, maintained with the API); the page routes a reader through it
  and carries only what it does not cover. A `go` fence on this page is a <= 10-line fragment that
  illustrates the one API under discussion, never a restated TUTORIAL or demo program.
- Authored here: `## Install` (Go version policy, `go get`, module setup), `## Run the demos` (the 8
  programs in `demos/`, `go run ./demos/hello`, generated list per Q-Ex), `## Before you start`
  (TERM/terminfo pointer to `Terminal-Setup`), `## What a Tcell program always contains` (5 pieces, one
  line each + a link to the TUTORIAL section that walks through them), `## Where to go next`
  (`Function-Reference`, `Architecture`, `Gallery`, `pkg.go.dev`).
- Link-only (do not restate): the hello program, the cell grid and `Size`, `Put`/`PutStr`/`PutStrStyled`
  and the grapheme-width return values, the wrap loop, `Style` chaining, `EventQ` + `select`,
  `EventResize` -> `Sync()`, mouse events, clipboard/notifications/title/suspend - all sections of
  `TUTORIAL.md`, named in the order a reader should meet them.
  **Corrected at T4.1, which read the file instead of trusting this list:** `Style` chaining is not a
  section (it is two values inside the demo application), and clipboard / notifications / title / suspend
  are not in `TUTORIAL.md` at all (the closest it comes is `EnablePaste` in the demo), so those four are
  routed to `Function-Reference`, whose 6.5 scope already owns them. The width claim is also wrong: of the
  three calls named here only `Put` returns anything (`(string, int)`, `screen.go:55`); `PutStr` and
  `PutStrStyled` return nothing (`screen.go:59`, `screen.go:63`), which is why the page says "the one that
  draws a single grapheme at a time". The reading order this line asked for is on the page, and it is not
  the file's own order - see T4.1.
- Sources: `../tcell/TUTORIAL.md` (reuse prose/samples where already v3-correct: drawText loop,
  event loop), `../tcell/demos/hello`, `../tcell/demos/styles`, `../tcell/demos/cursors`,
  `CHANGESv3.md` (event-model changes), `go doc` output.
- Rules: every snippet compiles as-is (S8.1); no `v2` API in any snippet (`PollEvent`,
  `ChannelEvents`, `PostEvent`, `SimulationScreen`, `StyleNormal`, `Attribute`, `Color(ForegroundX)`
  forms are all banned - they are v2/v1 and were removed); every code fence tagged `go`; snippets
  <= 30 lines, with the full program assembled once at the end.
  **(Phase 4: the v2 ban was enforced and is clean; the other two clauses are pre-Q-Ex prose that the
  page did not need - it has no snippet at all, so nothing is <= 10 lines and nothing is assembled, and
  its two fences are `console` because they are shell. "Assembled once at the end" became "named once at
  the end": the section closes by sending the reader to the Usage section, to `demos/hello` and to the
  demo application. Rationale in Phase 4's T4.3 record.)**
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
- **Coverage contract (answered by Q-6, enforced by `tools/symbol-coverage.py --gate`):** the
  **structural surface** - 38 exported types, 25 funcs, 8 vars, 111 method names at `acf267d` (179
  names) - is named in backticks by **exactly one** built page; the **712 constants** are documented by
  group (`Color*`, `Key*`, `Rune*`, `Mod*`, `Button*`, `Attr*`, `CursorStyle*`, `Underline*`, `Kitty*`,
  `Encoding*`, `Mouse*`, `Wheel*`, `Xterm*`, plus an `other*` catch-all) with one row and one
  `pkg.go.dev` link per group, and a page claims a group by naming its token in backticks. Exit
  criterion: `--gate` clean. Nothing in this contract asks for a row per constant, which is what kept
  the page inside its word budget and away from the `pkg.go.dev` mirror 12 forbids.
- **Priority order inside the gate:** the API named by the library's own `TUTORIAL.md`, `README.md`,
  `CHANGESv3.md` and the 8 demos (130 names today) is documented first and most carefully; the tool
  prints how many of those a page still misses, so the tail of the structural surface never crowds out
  what a reader actually meets.
- Coverage stays a **report** in CI (`.github/workflows/qa.yml` runs the tool without `--gate`) until
  `Function-Reference` exists in Phase 6; flipping the flag on is then a one-word CI change, not a
  redesign.

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

**Frozen as the style guide (T1.3, 2026-10-24).** This section *is* the style guide: `tools/check-style.py`
and the two `tools/*allow*.txt` files are its mechanical half, so a new rule moves the tool in the same
commit and a legacy exception is recorded with a reason instead of being argued in a review. It was
frozen here rather than copied out into a `STYLE.md` because a second copy of the rules can only disagree
with the linter, because the rendered content set is 6 pages by Q-3/Q-5 and a 7th content page would be
a page a reader has to be told about, and because a page may not link a file that is not itself (5.5)
- so the guide a writer reads has to be the doc that already carries the decisions behind the rules.

- Voice: present tense, second person sparingly, no marketing adjectives, v3-only by default.
- Naming (Q-9): **`_Tcell_` in prose everywhere** - the library docs use it 34 times against 1 bare
  mention, and the two pages agree with it, so this is one convention across both repos rather than a
  coin flip. Bare `Tcell` is reserved for headings, file names and paths; `tcell` stays literal inside
  code and backticks because that is the package name; versions stay `v3`. Enforced by
  `tools/check-style.py` rules `name` and `heading-period` (both verified against clean and dirty
  sample pages; `Gallery.md`'s existing `# Gallery of Tcell Examples` H1 is exempt as a heading).
  File names stay ASCII, hyphenated, <= 3 words.
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
| S8.3 | symbol coverage auditor: exported surface parsed from the checkout (`tools/apiface`) vs symbols named in the pages, plus the `TCELL_*` env audit and a hallucinated-API gate. Since Phase 3 a backticked **path** (`_demos/mouse.go`, `vt/emulate.go`) is a path and not an API claim - pages are supposed to cite files (6.4) and S8.2b is the tool that can check a path against the checkout | the Q-6 coverage contract in 6.5 (`--gate`), and Appendix A's ownership table |
| S8.4 | gallery diff/counter: per-category bullet counts + set-of-URLs diff between old and new `Gallery.md`, bent only by the three decision files it reads and prints: `tools/gallery-moves.txt` (Q-11 URL moves), `tools/gallery-additions.txt` (Q-13 entries) and, since Phase 3, `tools/gallery-sections.txt` (6.2's one new section, whose generated entries are exempt from the additions budget and still shape-checked) | migration is provably lossless (S2) |
| S8.5 | style linter (small script): non-ASCII in prose, trailing whitespace, `*emph*`, `*.md)` internal links, missing fence tags, wrapped bullets | house style (S7) enforced mechanically |
| S8.6 | **PASSED and built (2026-10-24).** The spike ran `Screen.Init` against `vt.MockTerm` + `tcell.NewTerminfoScreenFromTty` + `tcell.ShimScreen` (the recipe from `demos/hello/hello_test.go`) and a program drew and quit headlessly in 0.3 s, so snippets can be *run*, not just compiled | snippets do more than compile | implemented as opt-in `headless=yes` inside S8.1 (a fence that asks for it is executed on the emulator and must exit on ESC); `mode=lib` + `headless` is a label error |
**Status (2026-10-24): S8.1-S8.5, S8.7 and a demo checker (S8.2b, `tools/check-demos.py`) are
implemented under `tools/` and run on every push in `.github/workflows/qa.yml`, together with a
`preview` step (`tools/mirror-wiki.sh --check`) that fails when the live render wiki does not render the
pushed pages - the mechanical half of Q-14.**

| S8.7 | **Built (2026-10-24):** `tools/review-checklist.py` runs every other tool as a GATE, adds the mechanical CHECKs (v2 leakage vs the real surface, resize prose naming `EventResize`, orphan pages, duplicated `##` topics, non-self-contained diagrams) and prints the ASK lines a human must answer. Since Phase 2 it prints **both** word counts per page - `wikilib.prose_words()` (fences, link targets, inline code and markup out) for 5.1's budgets and the raw `split()` count for 6.1's cap, because they are two different questions and printing one number invited grading the page by whichever was convenient (Phase 2's record has the reasoning, and the function's docstring lists the ten shapes it was checked against) | consistent manual review | verified both ways: clean pages exit 0; a page with `PollEvent`/`StyleNormal`/unnamed-resize exits 1 with three named findings |

Review gates: each phase ends with (a) scripts green, (b) second read of raw markdown, then a single
publish commit per page. **(c) used to be "explicit maintainer approval"; Q-15 replaced it with
pre-authorization, which is only safe in the order written here - (a) and (b) are the review, and the
publish that follows is `tools/publish.sh` refusing to ship a dirty page, not a bare `git push`. A red gate
is a stop, never a way to ask CI.**

---

## 9. Phased execution plan

Estimates are focused hours for one author who has the source tree checked out. Phase totals are the
sum of that phase's tasks. Recomputed after Q-3: **39-51 h** (Phase 0 3-4, 1 2-3, 2 3-4, 3 4-5,
4 9-12, 5 8-10, 6 6-8, 7 4-5). Q-4 then cut Phase 4 to 4-6 h, so the set is **34-45 h** (0 3-4, 1 2-3,
2 3-4, 3 4-5, 4 4-6, 5 8-10, 6 6-8, 7 4-5), and Phase 4 landed near the bottom of its range. The 44-57 h
figure an earlier revision of section 1 carried predates both of those cuts.

### Phase 0 - Decisions and safety rails (3-4 h) - *blocks everything*

**Status: COMPLETE 2026-10-24.** The rails exist and run rather than being planned: draft repo
`radix29/tcell-wiki-draft` with `origin` / `render` / read-only `upstream` (push URL
`NO-PUSH-official-wiki-is-read-only`), the manifest at `Home.md` + `Gallery.md`, `baseline/` committed in
`7a5223a`, S8.1-S8.7 built and green locally (`tools/review-checklist.py --offline` exits 0) and in CI,
the render preview published (`39e5378`), and the page diff vs upstream treated as the deliverable instead
of a violation: 1 file changed, 3 insertions, 2 deletions (Q-11's two URL moves plus Q-13's one addition).
Spend landed under the 3-4 h estimate because most of Phase 0 was the draft owner answering questions in
one sitting rather than research. **Phase 1 is unblocked:** T1.1's sidebar prototype and T1.2's four stubs
(the count in T1.2 said five, which it was not - see the Phase 1 record) need nothing from upstream, and
D-1 is the only `D`-item whose final answer is still somebody else's.

- T0.0 **Executed 2026-10-24** (runbook now in `AGENTS.md`): created public `radix29/tcell-wiki-draft` and
  enabled its wiki (render branch `master`), rewired remotes so the official wiki is fetch-only
  `upstream` with a dead push URL, committed `tools/pages.txt`, `tools/mirror-wiki.sh`, the `README.md`
  unofficial disclaimer and `.github/workflows/qa.yml`, and landed `git push -u origin master`. *(0.5 h)*
- T0.1 **Closed by the 4.1 decision log.** Every `D`-item now carries an answer or an explicit reason it
  has none to give: D-1 draft-owner answer with the upstream call still open (Q-3), D-2 Q-4, D-3 Q-5,
  D-4 moot for this build (Q-3), D-5 Q-0c/7, D-6 Q-7, D-7 Q-8, D-8 closed as a platform boundary (Q-10),
  D-9 Q-9. "Answered" still means *for as long as this lives in our own draft repo* (Q-0b): anything that
  touches the official wiki - D-1's site-wide sidebar, an F-1 change to the library repo - stays a
  proposal. Disclosure: three earlier attempts to apply this correction silently no-op'd (escaped quotes,
  then a misplaced period, then a `**` inside the quoted sentence) while the file-wide assert still
  passed, which is how this stale sentence survived; multi-line rewrites now splice by line structure and
  every replacement is asserted on its own.
  *(0.5 h)*
- T0.2 **Superseded by Q-0c (exclude nothing): committed, not ignored.** `PLAN.md`, `AGENTS.md`, `README.md`,
  `tools/` and `.gitignore` are **committed** in the draft repo, because C2's "every `.md` becomes a
  page" hazard exists only where a push renders - and that is the manifest, now. *(done 2026-10-24)*
- T0.3 Fetch `upstream`; record `git rev-parse upstream/master` and copy the current `Home.md` /
  `Gallery.md` into `baseline/`, **committed in the draft** (recovery point + the copy CI's S8.4 diff
  reads), not an untracked dir. **Executed 2026-10-24:** `baseline/Home.md` + `baseline/Gallery.md` are
  byte-identical to `upstream/master` (`8e83ce1`), with `baseline/RECORD.txt` holding the SHAs,
  checksums and the 49-bullet count, **committed in `7a5223a`**, so CI's S8.4 diff reads a tracked file and not an
  untracked dir. *(0.5 h)*
- T0.4 **Executed 2026-10-24:** S8.1-S8.5 + S8.7 built (see 8's status line), plus `tools/check-demos.py`
  for the linked-examples rule (Q-Ex). The S8.6 spike ran and passed, so it shipped as opt-in
  `headless=yes` inside S8.1 rather than being parked. *(2 h)*
- Exit (**met 2026-10-24**): decisions recorded in 4.1 (17 logged `Q-` rows; all nine `D`-items marked
  answered, closed, or explicitly upstream), scripts green against the *current* 2-page wiki
  (`tools/review-checklist.py --offline` exits 0, and CI runs the same set), baseline captured **and
  committed** (`7a5223a`). What deliberately does not close here, because Phase 0 could not decide it:
  D-1's site-wide `_Sidebar.md` (upstream's call; T1.1 makes it concrete instead of arguing it), every
  F-1 library-repo change, and all upstream contact (Q-2).

### Phase 1 - Skeleton and nav (2-3 h)

**Status: built and green locally on 2026-10-24 - not published, and that is the only thing left.** The
four new page files plus `_Sidebar.md` exist, `tools/pages.txt` lists all seven names in Appendix D's
order, every S8 gate passes over them (`tools/review-checklist.py --offline` exits 0 with only ASK lines
left; `tools/check-links.py` with network: 60 external URLs all 200, 7 internal links resolving, 0
broken; `symbol-coverage.py` reports "0 page-cited symbol(s) checked", which is the right answer for
pages that promise scope and assert no API), and `tools/mirror-wiki.sh --dry-run` stages exactly those
seven files - five added, `Home`/`Gallery` unchanged - against the live render wiki at `39e5378`, and
publishes nothing. Two of the three exit criteria are therefore still open, and they are one
act: nothing has been pushed, so `radix29/tcell-wiki-draft/wiki` still renders the two Phase 0 pages.
`tools/mirror-wiki.sh --check` said exactly that (exit 1, "preview is BEHIND the draft", 5 files and 44
insertions pending), which is also the answer to "just `git push` then": CI's `preview` step runs that
same check, so pushing `origin` without mirroring first turns the run red on purpose (Q-14). The
remaining act is `tools/publish.sh`, and it is one command: mirror, push, re-read the live wiki.
`AGENTS.md` makes an unprompted push the one thing this repo never does, and Q-14 settled *how* a push
publishes, not when one is allowed - so the draft owner's ask is the missing input. **[Closed the same day:
Q-15 took the ask out of the loop and `tools/publish.sh` ran, so this act is recorded under Phase 2 and in
4.1, and the preview carries both pages and all seven.]**
Landed inside the 2-3 h estimate; none of it was research. Phase 2 is unblocked for authoring, but note
what the mirror does to a deferred publish: it publishes the whole manifest, not one file, so T2.3 would
ship these seven files whether or not anyone wanted them shipped yet - waiting makes the next publish
larger, not safer.

- T1.1 **Done.** `_Sidebar.md` is D-1 made concrete: three groups using 5.2's own nav words (Start here /
  Reference / Showcase), all six pages, no sixth invention, plus one line saying this wiki is an
  unofficial draft rewrite and pointing at `gdamore/tcell/wiki` and the library - a public preview that
  reads as official is the exact failure Q-0b worried about. It is in the manifest, so the mirror is
  what publishes it, and it is linked by no page, so dropping it would edit no page text (5.5's
  reversibility test). `review-checklist.py` reports `_Sidebar` as a page "nothing links to"; that ASK
  is the design talking, and the wrong fix is to link it from a page, which T1.1 forbids.
- T1.2 **Done, with the count in this task corrected: four stubs, not five.** 5.1 builds 6 pages and
  `Home` + `Gallery` already exist, so there was never a fifth stub to write; the missing four are
  `Getting-Started`, `Architecture`, `Function-Reference`, `Terminal-Setup`. Each one is a single H1
  (following `Gallery.md`'s one-H1 precedent, PLAN 7), a purpose sentence written in 5.3's reader-intent
  voice, the planned scope taken from 6.3-6.6 rather than invented, and one pointer to what a reader can
  actually read today - the library `TUTORIAL.md`, `CHANGESv3.md`, `README-windows.md`, or `pkg.go.dev`
  - because "honest" and "not a dead end" are the same property here. The stub notice is draft
  scaffolding on purpose: it is what keeps a preview honest, and T7.4's proposal package sends a page
  that has content or sends it not at all, so no stub sentence is quietly on its way upstream (Q-2 parks
  that day anyway). What is deliberately absent:
  backticked API, the eight demo names, and every `TCELL_*` variable. A stub that names `Screen` or
  `EventResize` in backticks claims ownership of it under Q-6 and pre-empts the page that is supposed to
  own it, and `check-demos.py`/`symbol-coverage.py` would then be grading four pages on promises they
  never meant to make. The stubs stay out of the deferred list too: no page links a deferred topic, so
  nothing here names `Screen-and-Rendering` or `Migration-v2-to-v3` even as a forward reference.
- T1.3 **Done.** The manifest is now the 6 content pages plus the droppable `_Sidebar.md`, with a comment
  at the top saying the manifest is the only thing the mirror copies and a comment over the sidebar line
  saying why it can be deleted without touching a page; `check-style.py` and `check-style.py --all` are
  both clean (still exactly the 2 legacy suppressions, no new debt). "Freeze the style guide file" was
  read as *freeze S7*, which is where the rules already live: a status line was added under its heading
  and no `STYLE.md` was created - see the note at S7 for the three reasons. One changelog wart to own:
  the sidebar file and its manifest line landed in two commits, because a scripted manifest rewrite
  dropped the line the file-adding commit should have carried; nothing was pushed or mirrored in between,
  and the choice was to add the line forward rather than amend a commit that is one publish away from
  being reader-visible history.
- Found, and it belongs to T5.1: `tools/review-checklist.py` fails any page containing the word
  `mermaid` anywhere in its text, fences included. Verified with a throwaway page holding a legal
  ` ```mermaid ` fence, which is exactly what T5.4 is scheduled to write into `Architecture`, and that
  CHECK would then be a FAIL on the plan's own diagram rule (PLAN 6.4, PLAN 7, D-5). The CHECK was
  written for `images/foo.png` references, so before T5.4 draws anything the CHECK has to ignore fenced
  blocks and fence lines, and be tested both ways like every other CHECK. Stub text works around it for
  now by not naming the diagram format at all, which is why no stub mentions diagrams in prose.
- Exit **partly met (2026-10-24):** zero broken internal links is met - 7 internal links, every one
  pointing at a manifest slug, checked by `check-links.py` and by `check-style.py`'s `link-md` /
  `self-contained` rules. "`Home` nav + prototype sidebar both render sensibly in the draft wiki" and
  "commit set pushed to `origin`" are both still open and both are `tools/publish.sh`. `Home.md` was
  deliberately not touched: its nav is T2.1's rewrite, and touching it here would spend Phase 2's work
  twice and grow the one diff upstream is actually being offered - which after this phase is still
  `Gallery.md`, 3 lines, Q-11 plus Q-13, because four new pages are additions to a draft and not a
  change to the official wiki. Nothing was pushed to `upstream`, which cannot be pushed at all. **[Both
  open items closed the same day by Q-15's publish; the SHAs are in Phase 2's "Published" note.]**

### Phase 2 - Home rewrite (3-4 h)

**Status: built, green, committed on `master`, published (Q-15).** `Home.md` is the page 6.1 spec'd:
`# Tcell` plus seven `##` sections in 6.1's order (Why,
Versions, Install, Gallery, How to Use, Platforms, License), no Support/Community section (Q-8), 330 prose
words against 5.1's 250-350 budget and 395 counting code and markup against 6.1's "<= 400" cap. All six
GATEs pass (`style`, `links`, `gallery`, `demos`, `snippets`, `symbols`) and `review-checklist.py` is clean
with Home the only page reporting nothing to ask. For one commit it was also unpublished: `AGENTS.md` still
said an unprompted push was the one thing this repo never does, so the preview was on `39e5378` (the two
Phase 0 pages), `tools/mirror-wiki.sh --check` said "BEHIND", and `--dry-run` refused outright because the
page was dirty - which is Q-14's guard doing its job and is the practical reason the page is committed
rather than parked in the working tree. Q-14 had made the publish half one command; Q-15 took the waiting
out of it, and the run is recorded below. A publish ships 7 files, because the mirror copies the manifest
and not the commit, so Phase 1's "waiting makes the next publish larger, not safer" held, and the next
publish carried a rewritten hub with it.

**Published (2026-10-24, the first act under Q-15).** `tools/publish.sh` mirrored, pushed and re-read: render
HEAD `39e5378` -> `fa34e5a` (`Preview draft pages`, 6 files, 116 insertions - the rewritten `Home.md`, the
four Q-3 stubs and `_Sidebar.md`), `origin/master` `731b430..91a0da9` (17 commits, fast-forward, nothing
forced or amended), and the script's own verification step then reported *"preview is current ... renders
exactly the 7 page(s) in tools/pages.txt"*. Two things that only a real run can settle: Phase 1's exit
criterion - "`Home` nav + prototype sidebar both render sensibly in the draft wiki" - is met now rather
than promised, because the sidebar and the rewritten hub are on the same rendered page for anyone to look
at; and the deferred publish really did just grow the one publish, since six pages and 17 commits went out
together with no merge conflicts, no drift and no lost work, which is the argument Phase 1 made in prose
and this made in shas. Landed inside the 3-4 h estimate; the fact-checking was the work, the writing was
fast, and the publish itself was one command and about a minute of waiting for the re-read.

- T2.1 **Done.** The page 6.1 describes, with four things worth stating because they were decisions and
  not transcription:
  - **It claims no API.** There is no backticked symbol anywhere on Home, so `symbol-coverage.py` still
    reports "0 page-cited symbol(s) checked": `NewScreen`, `Init` and `Fini` appear only inside the `go`
    fence, which the tool deliberately does not read as a claim of ownership. That keeps Q-6's single-owner
    contract intact for Phase 6, where `Function-Reference` owns those three names in a Lifecycle table and
    a second owner would be a `SHARE` failure. The two import paths in backticks (both on the Versions
    line; the one in the `go get` line is inside a fence, so it is not a claim either) resolve through the
    `pkg:github` entry already in `tools/api-allow.txt`, so the invented-API gate saw
    zero claims and stayed green rather than being quieted.
  - **The `NewScreen` one-liner 6.1 asks for is a real program, and is deliberately not `headless=yes`.**
    A plain ` ```go ` fence must be a complete program (S8.1's label rule), so the fence carries its
    `package`/`import`/`func main` and builds and links gofmt-clean in the harness; marking it `headless=yes`
    would be a label lie dressed as extra rigor, because the S8.6 emulator asserts a *non-blank* screen and
    a fence that only opens a screen draws nothing - and making it draw is precisely how a Home page starts
    becoming the second tutorial Q-4 forbids. The `go get` line sits in a `console` fence so the harness is
    never asked to compile a shell command.
  - **Nav only, no second content.** Six internal links over five distinct pages: Gallery, plus all four
    other built pages, with `Getting-Started` reached twice (from Install and from How to Use).
    `## Gallery` and `## How to Use` are the two lists 5.5 says carry navigation. No link to any of the six
    deferred topic pages, no `Prev | Up | Next` footer, no "See also" block: for the hub page 6's per-page
    "See also" and 6.1's nav sections are the same list, and a second copy of it on the same page would need
    a second owner. Each `## How to Use` line is that page's *own* stub purpose sentence compressed, so Home
    makes no completion claim about a stub - a reader who clicks through finds the page saying what Home said
    it was for.
  - **The draft disclaimer is not on this page.** Q-0b's honesty (unofficial, not affiliated, official wiki
    over there) lives in `README.md`, which is never mirrored, and in `_Sidebar.md`, which renders beside the
    preview's Home and is droppable. A page body that upstream adopted must not contain a sentence that turns
    false on adoption, and Home is the one page upstream is most likely to adopt. Found in this phase, decided
    in this phase, and it belongs in T7.4's package as an explicit line rather than as a surprise.
- T2.2 **Done, and it is where the phase went.** Every claim on the page traces to the library, the
  non-obvious ones traced to source rather than to prose: "only the changed cells are sent" is
  `tscreen.go`'s `drawCell`, which returns early when `cells.Dirty(x, y)` is false (and whose comment says
  most cells are clean); "titles ... when offered" is `tScreen.SetTitle`, which does nothing unless
  `t.setTitle != ""`, i.e. unless the terminal has the capability at all; notifications are OSC 777 only per
  the `ShowNotification` doc comment; "the current and previous _Go_ releases" is README's stated support
  policy; the four platform lines are README's own platform list plus what `README-windows.md` (modern VT
  console API, and it is the one that names the minimum version), `README-wasm.md` (build flags plus support
  files) and `README-plan9.md` (best-effort) actually contain. Two claims were *cut* rather than checked:
  v3's freedom from the terminal database is real but is `Terminal-Setup`'s to make, and "pure _Go_" stays a
  portability bullet rather than growing an OS list that duplicates `## Platforms`. Version claims are
  README's own v3/v2/v1 note, and it is why Home gives v2's import path and not v1's: printing an import path
  for the release the sentence calls unmaintained advertises the thing the sentence warns about.
  Links: `check-links.py` with network is 64 external URLs and 12 internal links, 0 broken; Home's seven are
  six links into the library repo (`README.md`, `CHANGESv3.md`, `README-windows.md`, `README-wasm.md`,
  `README-plan9.md`, `LICENSE`) plus `pkg.go.dev` for the package root, and all seven answer 200 today.
  `check-demos.py` additionally verifies
  the six library-file links exist in the checkout on the *detected* default branch (`main`, via
  `git ls-remote --symref`), which is the check that catches an upstream rename instead of a reader finding it.
- T2.3 **Review gate met, and published (Q-15).** The page was read raw as well as through the
  tools, then rendered in the head of a first-time reader: "is this the library for me" is answered by the
  lede plus Why without scrolling, "what do I run first" by Install, "where is the reference" by How to Use -
  5.3's three reader intents, three sections, no backtracking. The commit is `Updated Home (markdown)`,
  wiki-styled per `AGENTS.md`, single-line, single-purpose; five commits follow it (the tool measure, the
  retired style suppression, the two runbook docs, closing the phase, the Q-15 rule change), the publish
  pushed every one of them, and nothing was force-pushed, amended or rebased.
- Found here, and it belongs to the tools rather than the page: 6.1's "word count <= 400" and 5.1's
  "Home 250-350 words" measure different things, and `review-checklist.py` printed one number for both -
  `len(text.split())`, which counts a 60-character URL, eight fence delimiters and fifteen bullet dashes as
  words. Home is 330 prose words and 395 raw, so it clears both, but `Getting-Started` with 8-12 snippets
  and `Function-Reference` with tables would have had the two measures diverge hard, and a budget graded by
  the wrong number is a budget that gets argued with. Fixed forward: `wikilib.prose_words()` (fences, link
  targets, inline code, table pipes and `#`/`-` markers out) is printed next to the raw count, tested on
  ten shapes (prose, links, a fence, bullets, a heading, table rows with both delimiter-row spellings, a
  thematic break, inline code, empty); those shapes are written into the function's docstring rather than
  into a test file, because `tools/` commits no test file and a docstring can be re-run by hand by whoever
  touches it next. `AGENTS.md`'s Tooling list
  says so too, since a reviewer reading the tool list should know which of the two numbers to compare to 5.1.
- Found here too, and left alone: `_Sidebar.md`'s blurb and Home's lede now open with nearly the same
  sentence, which is visible on the rendered preview where both appear at once. Not fixed, because the
  sidebar has to stand alone on the other six renders (5.5: droppable, load-bearing for nothing) and
  rewording a reviewed Phase 1 artifact for a duplication only the preview shows is not Phase 2's call. It is
  a T7.2 nav-completeness item, and if upstream ever takes both files together they will trim one of them.
- Exit **met (2026-10-24, publish included per Q-15):** R1 is met - a short project description plus seven
  navigation sub-sections including the required `## Gallery` and `## How to Use`, inside both word budgets -
  and Home links the Gallery and all four other built pages, which is 13's "the 6 built pages are linked from
  `Home`" satisfied a full phase before four of those pages have any content in them - with the one wrinkle
  that 13 phrases it as all six, and `Home` is the page it cannot link itself: that is why
  `review-checklist.py` exempts `Home` from the orphan CHECK, and why `_Sidebar.md` links it even though no
  page may depend on the sidebar (5.5). Phase 3 is unblocked,
  and Phase 3 is where the lossless-migration contract (Appendix B) has to be met rather than described.

### Phase 3 - Gallery (4-5 h)

**Status: built, green, committed, published (Q-15).** `Gallery.md` is the page 6.2 describes: all 49
baseline bullets are present, in their own categories, in baseline order (`tools/check-gallery.py` proves
that on every run), `goSSMS` is still the one recorded addition, the legacy bullet is reworded per Q-7,
and the one new section PLAN 6.2 sanctions is on the page carrying the library's own 8 demo programs.
Nothing was deleted and nothing is dead, so the "404 report" T3.4 asks for is a status table with an
empty broken column: 63 URLs on the page, every one answering 200, and the 5 media URLs checked past the
status code to a content type or a page title. Spend landed inside 4-5 h; writing the sentences was the
small part, and the two tool defects the new section exposed were the work - both fixed forward in the
tools, nowhere around in the page.

- T3.1 **Done.** Appendix B is recomputed below and carries both the inherited contract and the state the
  phase produced. One property of the contract is worth writing down here because it changed what T3.4
  was for: `check-gallery.py` compares **(display name, entry URL) pairs**, so an entry's *media* URL is
  outside the lossless contract entirely - the 5 screenshot/video URLs can change without any migration
  check noticing, and only `check-links.py` (which probes every URL on the page, media included) is
  guarding them. That is not a defect to fix here - a screenshot has no home to "move" to the way a dead
  project host does (Q-11 vs D-6/Q-7) - but it is why the table below is a review record and not a flag.
  The 2015 blogspot scheme question in T3.4 is deliberately a note and not a diff for exactly this reason.
  *(0.5 h)*
- T3.2 **Done, and it was one line.** Every inherited entry already matched the frozen entry shape - the
  checker was green on the upstream text before this phase touched it - so the only reformatting T3.2
  could legitimately do was the D-6/Q-7 wording fix: `- mouse demo - the mouse test that shipped with
  _Tcell_ in 2015 ([screenshot](...)); mouse support is now enabled per program with EnableMouse and
  MouseFlags`. Display name unchanged, one screenshot URL unchanged, still the un-numbered 49th bullet,
  still the only entry on the page without a link. Three deviations from the shape 6.2 printed, each one
  a rule beating a template: **`_Tcell_` instead of `Tcell`** (Q-9's `name` rule rejects the plan's own
  literal shape text - the shape was written before that rule was enforced, and a page may not carry a
  style finding), and **no backticks** on `EnableMouse`/`MouseFlags` (Q-6 gives a symbol to exactly one
  page, and those two belong to `Function-Reference`'s Mouse table in Phase 6; Gallery is not an API page
  and no other entry on it carries a backtick), and **one screenshot, not the two the shape shows** - the
  shape's `([screenshot](u1), [screenshot](u2))` assumed both blogspot images sat on this bullet, and the
  second has always belonged to the `govisor` entry, which 6.2's own bullet count of 49 depends on.
  Left alone deliberately: four inherited descriptions that open with a capital ("A simple and flexible
  interface...", "A TUI designed...", "A classical bulletin board app...", "Text file viewer like
  less...") against AGENTS' "short lowercase description" rule, and the trailing slashes upstream wrote on
  `micro`/`tview`. They are the published page's own words, the checker accepts them, and lowercasing
  somebody's text is the cosmetic churn D-9 exists to stop. *(1.5 h)*
- T3.3 **Done.** `## Demos in the Repository` is appended after `## Miscellaneous` (append-only, so the
  baseline category order the checker polices is untouched) and is the `tools/check-demos.py --markdown`
  block pasted as generated (its commands sit in one `console` fence - the marker PLAN 7 requires for raw
  shell, which `Home.md` has used since Phase 2 and this page had never needed, and which the snippet
  harness skips as non-Go, so the page promises no compilable snippet it cannot build), with the two
  doc-sentence descriptions the library carries (`clipboard`,
  `hello`) and six this phase wrote from reading each program: `beep` beeps on a three second countdown
  and on B, `boxes` draws randomly placed colored boxes and prints the average drawing time per box, and
  then `colors` (RGB cube fade), `cursors` (the 0-6 cursor styles, each with a color), `styles` (one line
  per text style, the four underline variants and a hyperlink) and `unicode` (one month name in six
  languages, plus combining marks, ZWJ emoji and double-wide CJK). No description is inferred from a file
  name, which is the whole reason the tool prints `TODO(desc)` instead of a sentence. Two things the
  generated block said that the checkout does not support, both fixed in the generator so the next paste
  cannot re-put them on a page: **the `_demos` note claimed those files "run only after copying the file
  out", which is false** - naming the file works, and the library's own CI does exactly that
  (`.github/workflows/webasm.yml` runs `go build _demos/mouse.go`), so the note now says `go run
  _demos/mouse.go` and the tool *measures* it (`build_undemos`, run by `--build` and `--markdown`): 5 of
  the 6 files build that way and `sixel.go` does not, because it imports `github.com/mattn/go-sixel` which
  the module does not require, and the note says so because a reader will try. A page that names a
  `_demos` file that no longer builds now fails S8.2b. And **the block began with an HTML comment**
  ("GENERATED by tools/check-demos.py..."), which PLAN 7 forbids on a page and route C forbids twice over
  since it names this repo's tooling to a reader - so the provenance warning now prints *outside* the
  block and what sits between the markers pastes with no edits at all.
  The section also needed an approval the checker could see: 8 new bullets that are not in the baseline
  are, to a lossless-migration checker, 8 unapproved additions. Raising `--max-additions` would have
  approved *any* 8 new projects, which is the opposite of what `tools/gallery-additions.txt` was built for,
  so the approval is now per section in **`tools/gallery-sections.txt`** (`<heading>\t<evidence>`, same
  shape and same stale-record rule as the other two decision files): an approved section's entries are
  exempt from the additions budget and still under every shape, ASCII and duplicate-URL rule, the report
  prints which entries it exempted and why, and a record whose section has disappeared from the page is an
  error rather than a shrug. Tested both ways: section without a record fails (and reports the additions
  too), record without a section fails, a trailing period on a demo line inside an approved section still
  fails, and a malformed record line is reported instead of skipped. The record lands in the same commit as
  the section it approves, because added earlier it would have reddened every check until the page caught
  up. Why a file and not the existing `--allow-new-section` flag: `review-checklist.py` and CI both call
  the checker bare, so a flag is two more call sites to keep in step, and a policy that CI cannot see is a
  policy that fails the day it is needed. *(1 h, over by the tool work)*
- T3.4 **Done: 63 URLs, 0 broken, nothing to report to the maintainer except that nothing is broken.**
  The page grew from 54 URLs to 63: github.com went from 45 project links to 54 (the 8 demo programs plus
  the `demos` directory itself), and the rest is unchanged - 2 codeberg.org from Q-11, 2 blogspot, and one
  each on youtu.be, www.youtube.com, user-images.githubusercontent.com, termshark.io, git.sr.ht. The 5 media
  URLs, measured here rather than assumed:
  - `mouse demo` screenshot (2.bp.blogspot.com, `Screen+Shot+2015-10-04...png`) - 200, `image/png`, 54,791 bytes
  - `govisor` screenshot (2.bp.blogspot.com, `Screen+Shot+2015-09-20...png`) - 200, `image/png`, 142,509 bytes
  - `proxima5` video (`youtu.be/jNxKTCmY_bQ`) - 200, and the page it resolves to titles itself "Proxima5 v0.1"
  - `browsh` video (`www.youtube.com/watch?v=HZq86XfBoRo`) - 200, titles "browsh - Modern Text-Based Browser - Linux TUI"
  - `hero.go` video (`user-images.githubusercontent.com/.../277157369-...mp4`) - 200, `video/mp4`, 1,183,593 bytes

  A 200 from YouTube is what an unavailable video also returns, so the titles above are the part of this a
  link checker cannot do; that is a T7.3 maintenance-note line ("re-run the media URLs by hand, look at
  what comes back"), not a new gate. One finding for the proposal package: **both blogspot URLs are
  `http:`**, and Blogger serves byte-identical `image/png` over `https:` (measured: same sizes, same types),
  so a maintainer who cares that a wiki served over HTTPS points at plaintext image requests has a
  two-character-each change available at any time. We do not make it: Q-7 says these hotlinks stay until
  they 404, Q-11's "move the URL" policy is about a dead *project* host with a real new home, and a media
  URL is the thing a maintainer is likeliest to replace with a hosted screenshot (D-6) - which would make
  our edit a piece of churn in a page-diff history nobody can rewrite. `tools/link-status-allow.txt` gains
  nothing, because there is no status to accept: allow-listing is for URLs we keep *despite* a status, and
  every URL on this page has the good one. *(0.5 h)*
- T3.5 **Review gate met, and published (Q-15).** The page was re-read raw (entry shapes, section order,
  the one added section's fence and blank lines) and as the 49 bullets plus 1 addition plus 8 generated
  lines the count report says they are, then through every gate: style clean (still the one legacy
  suppression), links 73 URLs across all pages / 63 on this page / 0 broken, gallery lossless with the
  exemption note printed, demos 8 of 8 cited and `go build ./demos/...` clean, snippets clean, symbols
  clean, `review-checklist.py` exits 0 with only ASK lines left. Commits, in order: `Reword the legacy
  mouse demo entry`, `Let the symbol gate read file paths as paths`, `Updated Gallery (markdown)`, plus
  the tooling that made those green (`Record an approved gallery section, not a bigger budget`,
  `Measure the _demos claim instead of asserting it`, `Print an approved section record as its evidence`).
  The one ASK the page still carries - "no link to another built page" - is answered here rather than
  fixed: Gallery is a leaf (Home links it, `_Sidebar.md` links it, `../tcell/README.md` links it), PLAN 6's
  per-page "See also" has no section to live in on this page because 6.2 sanctions exactly one new section
  and the machine-generated block owns it - an authored See-also sentence inside that block is deleted by
  the next re-generation. So the See-also graph stays a T7.2 item, where it belongs with the other four
  stubs that also link nothing yet. `git diff --stat upstream/master HEAD -- Home.md Gallery.md` is now
  **Gallery 24 insertions / 3 deletions** (2 Q-11 URL moves, 1 Q-13 addition, 1 Q-7 reword, 20 lines of
  new section) and Home 72/3, which is still the whole review surface for a future upstream paste.
  *(0.5 h)*
- Found, and fixed in the right place: `tools/symbol-coverage.py` read a backticked **file path** as an
  API claim. The new section's `go run _demos/mouse.go` produced `BAD SYMBOL: '_demos/mouse.go' ... 'go'
  does not exist anywhere in the root package` (the dotted-token branch took `go` from `mouse.go` as the
  leaf), and `sixel.go` produced a package-reference warning. The two tempting wrong answers were plain
  text for a file name - which is how a page stops being able to name `tscreen.go` in code font - and an
  `api-allow.txt` entry per file, which AGENTS forbids and 6.4 makes worthless: the Architecture page is
  specced to cite `vt/emulate.go`, `color/fit.go` and a dozen more, so Phase 5 would have hit this on
  scale. The tokenizer now treats a token with a `/` or a source-file suffix as a path, and the path that
  *can* be checked (does this demo / `_demos` file exist and build) is checked by S8.2b, which already
  failed a page naming `_demos/nosuch`. Tested both ways: paths quiet, `TerminfoScreen` and
  `Style.SetUnderline` still `BAD SYMBOL`.
- Found, and it is a design note rather than a bug: `review-checklist.py` runs every gate with no
  arguments, so had the new section's approval been a command-line flag, both the checklist and CI would
  have gone red the day the section landed and green again only by teaching every caller about it. That is
  the argument for decision files over flags, and it was invisible until a change needed it.
- Exit **met (2026-10-24, publish included per Q-15):** R2 is met - all prior information is present and
  provably so, `check-gallery.py` reports zero unexplained losses and prints every deviation it knows
  about (2 recorded URL moves, 1 recorded addition, 1 approved section exempting 8 generated entries), and
  every URL status on the page is recorded above: the 54 URLs the page carried into this phase plus the 9
  it added, 63 in all, answering 200. PLAN 13's Gallery line is satisfied on all three clauses (all entries, every URL status
  recorded, demos section present) and its box stays unticked until T7.1 re-verifies it, which is how the
  Phase 2 record left Home's line too. Phase 4 is unblocked: `Getting-Started` can now point a reader at
  the demos section instead of promising it, because the section exists and every command in it runs.

### Phase 4 - Tutorial (`Getting-Started`) (4-6 h) - *re-estimated by Q-4, was 9-12 h*

**Status: built, green, committed, published (Q-15).** `Getting-Started.md` is the routing page Q-4 asked
for: 1,134 prose words against 5.1's 900-1,400, five `##` sections in 6.3's order (Install, Run the
Demos, Before You Start, What a Tcell Program Always Contains, Where to Go Next), 19 external links over
14 distinct targets answering 200, 6 internal links over 4 built pages including one anchor into
`Gallery#demos-in-the-repository`, and **zero lines of Go**: the page contains no code a reader pastes, so
there is nothing on it that can rot on the next API change, which is what Q-Ex and Q-4 were for. Every
non-obvious claim on the page was measured before it was written (the list is in T4.2). Two tools changed,
one because the page caught the link gate being wrong about an anchor the page publishes (T4.4), the other
by leaving a gate silent rather than lying (T4.3). Spend about 3 h of the 4-6 h: the measurements were the
work, the writing was one pass, and the only CHECK that fired on the page's own substance was the one that
was right (T4.5's note on `EventResize`).

**Published (2026-10-25, under Q-15).** `tools/publish.sh` mirrored, pushed and re-read: render HEAD
`ca574fc` -> `95fd1d6` (`Preview draft pages`, 1 file, 53 insertions / 2 deletions - the Phase 1 stub
replaced by the page), `origin/master` `1e9aecf..4ec1443` (fast-forward, nothing forced or amended), then
the script's own re-read reported "preview is current ... 7 page(s)". `git diff --stat upstream/master
HEAD -- Home.md Gallery.md` is unchanged by this phase, because `Getting-Started.md` is a new file: the
review surface a future upstream paste sees is still Home 72/3 and Gallery 24/3, plus a 55-line page that
does not exist upstream at all. That publish carried the page and nothing else; `tools/publish.sh` ran
again for the gate fix and these records, and the standing claim this note has to keep true is the one
AGENTS states as a session exit: `git rev-list --count origin/master..HEAD` is 0 and the mirror is clean.

- T4.1 **Done first, and the link map became the page's structure.** `TUTORIAL.md` read end to end (330
  lines). Its headings in *file* order are Resize events, Key events, Key event restrictions, Mouse
  events, Mouse buttons, Usage, Demo application: the three event-reference sections sit before the
  section that opens a screen and the loop that reads the events they describe, which is fine as a
  document and wrong as a first read, so the page states a reading order (Usage, then the demo
  application, then Key and Mouse events, then restrictions "cheaper to read early than to discover
  late") instead of inheriting the file's. Where it is thin (all of it is F-1 now, none of it page
  content): 6.3's link list expected sections for `Style` chaining and for clipboard / title /
  notifications / suspend and the file has no such sections - chaining exists only as two values inside
  the demo application, and those four topics are simply absent (`grep` for `SetTitle`, `Suspend`,
  `clipboard`, `notif`: the only hit in the file is `EnablePaste` in the demo), which is why the page
  sends a reader who needs them to `Function-Reference`, whose 6.5 scope already owns them; there is no
  module setup anywhere in it; its fragments reference `log`, `os`, `fmt` and `color` with no import
  block, which PLAN 7 forbids on a page and which costs a reader three compile errors if they paste one
  into an empty module; `Fini` first appears in the demo application, three pages after the screen is
  opened. One thing that looked like a defect and is not: a fence in the Usage section is closed with
  four backticks where it opens with three, which is legal CommonMark (a closing fence may be longer), so
  it renders and stays.
  *(1 h)*
- T4.2 **Done. Five authored sections, and the facts in them are measurements.** What was measured, in
  the order it was run: (1) empty directory -> `go mod init` -> `go get github.com/gdamore/tcell/v3`
  resolves v3.6.0 and writes `go.sum` -> `go run github.com/gdamore/tcell/v3/demos/hello` draws "Hello,
  World!" on a pty and exits 0 on ESC, in a directory with **no .go file and nothing cloned**. That
  command is the page's own contribution to the reader's first minute, and it is why `## Run the Demos`
  does not duplicate the Gallery's clone block: 6.3 asked for `go run ./demos/hello`, which is the clone
  route the generated Gallery section already carries, and the module-path route needs no clone. (2)
  `GOTOOLCHAIN`: with the default (`auto`) the go command downloads a toolchain matching the library's go
  directive, and with `GOTOOLCHAIN=local` it stops with "go.mod requires go >= X (running go Y;
  GOTOOLCHAIN=local)", so the version sentence describes a flag's behaviour it has seen. (3) No
  terminal: `NewScreen` succeeds and `Init` fails with `open /dev/tty: no such device or address`, which
  is the first "Before You Start" bullet, hedged to "the systems that have one" because Windows words the
  same failure differently. (4) Raw mode: a program on a 30x100 pty logged `Ctrl+C` (0x03) arriving as an
  `EventKey` rather than as a signal, then ESC, then exit 0 after `Fini`, which is bullet two. (5) Size:
  on a 120x40 pty, `Size()` right after `Init` already reports 120x40 and the first event off `EventQ` is
  an `EventResize`, so bullet three can tell the reader they do not have to wait for an event before
  drawing - the TUTORIAL says the event arrives, and the "size is already right" half is what this run
  added. (6) `demos/hello` is the shortest of the eight (77 lines, next is `beep` at 82) and all eight
  carry a `_test.go` (`check-demos.py` prints 8/8), which is what "the library keeps a rendering test for
  each of the eight" claims and means. (7) The tutorial's demo application compiles unchanged against
  v3.6.0, draws, and quits on ESC with status 0 - so the page's strongest claim about a link target ("all
  five in one program") was tested rather than assumed. What the page deliberately does not say: anything
  about `TERM`, terminfo or color depth. Measured and left unsaid: with `TERM` unset the demo still
  opened a screen, and the bytes at `Init` are a negotiation (DA1, DA2, kitty, mode queries) rather than a
  terminfo lookup. "v3 does not need the terminal database" is `Terminal-Setup`'s sentence to say - T2.2
  turned that down for `Home` for the same reason and it turns it down here. *(2 h)*
- T4.3 **Done, and empty on purpose - the one task this phase did not need.** There are no fragments to
  put through the harness. 6.3 says a `go` fence here is a "<= 10-line fragment that illustrates the one
  API under discussion", Q-Ex says the library's own programs *are* the examples, and a routing page has
  no API under discussion: every fragment it could paste is either the TUTORIAL's code (which Q-4 forbids
  it to restate) or a demo (which the library tests, 8 of 8). So the page pastes shell instead, and both
  `console` blocks are commands that were run - the same argument `Home.md` made in Phase 2 for the
  `go get` line and `Gallery.md` made in Phase 3 for the clone block. `make-samples.py` still runs over
  the page set and reports Home's one program building and linking, which is the whole `go` surface of
  this wiki today. Consequence recorded rather than hidden: `review-checklist.py` prints "page has no
  `go` fence yet" as an ASK on `Getting-Started` (and on `Gallery` and the three stubs). The ASK stays -
  it is the check that catches a page pasting untested Go, the one failure mode this repo cannot review
  its way out of - and the answer is this bullet. `headless=yes` is unused for the same reason: T4.3 asks
  for it "where a fragment is a whole program", and this page has no whole program, so marking Home's
  open-a-screen fence with it would be the label lie Phase 2 already declined to tell. *(0 h, was 0.5)*
- T4.4 **Done, and it found a bug in the gate instead of a bug in the page.** The eight banned v2 names
  (`V2_BANNED` in `review-checklist.py`) appear on no page, and a manual sweep finds no v2 idiom either;
  `check-style.py` is clean over all 7 files with the one legacy suppression and no new one; every page is
  still pure ASCII (`wikilib.is_ascii` over the manifest). Then `check-links.py --verbose Getting-Started.md`
  came back **BROKEN** on the one internal link this page adds that no page had reason to make before:
  `[...](Gallery#demos-in-the-repository)`, "anchor matches no heading in Gallery.md". The page was right
  and the gate was wrong, twice over, and the fix is commit `5e2706c`:
  **(a)** `anchors_in()` was handed whole files while its own doc comment asks for a body, so each target
  page's duplicate in-file `#` H1 entered the anchor set. Nothing broke, which was the problem - PLAN 7
  says GitHub drops that H1, so a link to a page's own title anchor would have been a green PASS and a 404
  for the reader, exactly the false pass Phase 1 wrote out of `check-gallery.py`.
  **(b)** It could not see a heading inside a blockquote, and PLAN 6.2 puts Gallery's `## Demos in the
  Repository` heading inside one, so the anchor the generated section owns was invisible. Before touching
  the rule I checked the renderer instead of reasoning about it: `curl` of the published `Gallery` page on
  the render wiki carries `href="#demos-in-the-repository"` - GitHub renders the quoted heading and gives
  it the anchor - so the link ships and the gate was taught, not the page bent. `anchors_in()` now gets the
  body with the H1 line removed and strips a leading `>` before matching a heading; the regression probe is
  four assertions, in the commit's own argument: the blockquoted anchor resolves, the six ordinary Gallery
  headings still resolve, a wrong anchor (`demos-in-the-repo`, `nope`) still FAILS, and no anchor is
  invented out of the fenced clone block. One honesty note on **(a)**: dropping the H1 from the anchor set
  rests on PLAN 7's reading of the renderer, not on a measurement, because no page on this wiki links a
  page title anchor - the change is inert today and would only bite a future link, which is the right
  direction for an unmeasured rule (fail the link, not the reader).
  `check-demos.py` is green and is now load-bearing rather than advisory: 21 library-file links across the
  pages, 13 of them this page's, 10 carrying a heading anchor and every one of those 10 here, each checked
  against a file that exists in the checkout and a heading the file actually has - the Q-4 rename guard,
  working for the first time on the page that needed it. *(0.5 h, plus the gate fix)*
- T4.5 **Done as a run, not a re-read.** Fresh directory, page open, nothing else: init, get, run the
  demo, ESC, program gone, terminal intact; then `hello.go` read against the five pieces (all five are
  in it, in order); then the tutorial by the order the page gives, with the demo application built and
  run to check the page was not pointing at something broken. Friction found, and all four fixes went
  into the page rather than into the reader's habits: (a) Install told the reader to write a main.go the
  page does not contain, so it now says plainly that main.go is the tutorial's subject and moves on,
  because the next section gets a program onto the screen with no code at all; (b) an earlier draft said
  the drawing calls "return how wide that text came out", which is true of `Put` and false of `PutStr`
  and `PutStrStyled`, and the cause was 6.3's own summary line rather than a misreading - the page now
  says "the one that draws a single grapheme at a time", and 6.3 carries the correction where somebody
  repeating the mistake will find it; (c) "the eight are listed with their descriptions next to the
  commands" overread what the Gallery block actually holds (one example command, not eight), so the
  sentence now asks it for the list and the clone commands and nothing more; (d) three back-references
  reading "the section walked above" / "named above" became the plain words Usage and Demo application,
  each linked once at the head of its section, because a reader should not have to hunt for what "above"
  means. One naming decision the walk settled: `review-checklist.py`'s resize CHECK wants the literal
  string `EventResize` on any page that says "resize", and this page writes it in **plain prose** rather
  than backticks - the CHECK is a substring test and passes either way, which is the right outcome,
  because that CHECK is about not teaching a v2 polling pattern while Q-6 is about who owns a symbol, and
  plain prose answers only the first. *(1 h)*
- T4.6 **Review gate met, and published (Q-15).** Read raw twice, then as the reader path above, then
  with every gate: `review-checklist.py --offline` exits 0 (6 GATEs PASS, only ASK lines left), and with
  network `check-links.py` reports 81 external URLs and 18 internal links across the page set, 0 broken,
  every one of this page's 14 external targets 200. Commit `Created Getting-Started (markdown)`, single
  line, single file, first page commit in Appendix D's order because Home still goes last. Then
  `tools/publish.sh`, whose output is in the Published note above. *(0.5 h)*
- Exit **met (2026-10-25, publish included per Q-15):** R3a in its Q-4 form - a reader with an empty
  directory ends up with a module, a dependency, a running program on their screen and a route to their
  own first program, using this page and the links it names, and the page carries no second tutorial: it
  has no Go in it at all. Nothing in the page links a deferred topic page (5.5), nothing references a
  file in this repo, and the whole page is paste-able into the upstream web editor as it stands. Phase 5
  is unblocked, and can now assume the reader has run something: `Architecture` answers why it repaints
  the way it does, which is the question this page deliberately did not answer.

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
  `wikis/Gallery` URL, document the `TCELL_*` vars the source reads but no doc names - Q-6's audit
  counts 8, note the stale `mouse demo` claim, and list the 2 URL moves Q-11 made so a maintainer can
  re-check the evidence and re-publish them upstream); **plus the `TUTORIAL.md` thin spots found reading
  it end to end at T4.1** (no module setup or `go get`; the three event-reference sections sit before the
  section that creates the screen and the loop that reads them, so a beginner meets `EventResize` before
  `NewScreen`; its fragments use `log`/`os`/`fmt`/`color` with no import block, so pasting one into an
  empty module is three compile errors; `Fini` appears only in the demo application, three pages after
  the screen is opened; nothing on the clipboard, the title, notifications or suspend) **and one library
  defect measured during T4.5** (calling `Fini` on a screen whose `Init` failed panics with `close of nil
  channel` in `tScreen.finish`, `tscreen.go:676`, so a program that exits on a failed `Init` is fine and
  one that cleans up first is not); none of it is page content and none of it is sent (Q-2);  file as
  issues/PRs **only if asked**. **Q-2: parked - prepare this package, do not send it.** *(0.5 h)*
- T7.5 Publish final touches; confirm public result page by page; record published commit SHAs - by
  Q-14 that is `tools/publish.sh` plus reading the rendered page, not a manual `git push`. *(1 h)*

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
| R3 | "How to use" includes a tutorial | `Getting-Started.md` linking repo `TUTORIAL.md` (Q-4: one tutorial, one owner) | T4.5 walkthrough-from-empty-module gate |
| R3b | ... and an Architecture document | `Architecture.md` | T5.5 citation check |
| R3c | ... and documentation of provided functionality | `Function-Reference.md` + `Terminal-Setup.md` (Q-3: 6 topic pages deferred, so this is satisfied at hub level) | S8.3 coverage report |
| R4 | Naming may be improved | D-3 decision, S5.1 file names | D-3 sign-off |

---

## 11. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Duplication drift: wiki vs repo `README`/`TUTORIAL`/`CHANGES*` | stale, contradictory docs | **Settled by Q-4, not merely mitigated: the wiki may not restate repo prose**, S5.4 names one owner per topic, `check-demos.py`/`check-style.py` keep the links real; F-1 (repo-side pointers to the wiki) is now the only remaining direction of travel |
| Documenting v2 habits as v3 (PollEvent, StyleNormal, Attribute, SimulationScreen, `Color` consts) | readers write broken code | banned-symbol grep (T4.4); all snippets through the compile harness (S8.1) |
| Mermaid support in the wiki renderer fails (C9) | rework of all diagrams | T5.1 probe in our own draft wiki before any diagram is written; fallback is ASCII art in fenced blocks |
| A publish mistake goes live instantly | public misinformation | per-page review gate; baseline copies (T0.3); forward-fix commits only (C7) |
| Loss of a gallery entry during migration (49 bullets, hand-edited) | visible content loss | S8.4 machine diff of bullets + URL sets before publishing |
| Dead/legacy hotlinked screenshots (2 blogspot URLs) | broken images on the showcase | verify, report, propose D-6/Q-7; do not silently drop. (Q-11 covers *project* URLs, which have a home to move to; a 2015 screenshot does not) |
| Undocumented env var semantics guessed wrong | wrong user advice | read the handling in source and cite the file; if ambiguous, ask before documenting |
| ~~Wiki is publicly editable~~ **closed by Q-10:** upstream wiki is collaborator-only | was: defaced pages | residual risk moved where it belongs: our own draft repo and drift from upstream - keep the baseline and the periodic `git pull --ff-only` + S8.4 content diff for *that* |
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
      (Phase 2 onward: shell commands live in `console` fences, which PLAN 7 and `check-style.py` accept
      and the harness skips by design, so the honest reading of this box is "every `go` fence ..."; if it
      is still worded this way at T7.1, tick it against that reading and say so in the note.)
- [ ] `tools/symbol-coverage.py --gate` is clean: all 179 structural names owned by exactly one of the 6
      built pages, all 14 constant groups claimed by group, no structural symbol with two owners (Q-6).
- [ ] All 8 `TCELL_*` env vars and all 9 `Opt*` options documented, with precedence stated.
- [ ] S8.2/S8.3/S8.4/S8.5 all green immediately before each publish commit.
- [ ] The mirrored render tree contains exactly the 6 pages + the droppable `_Sidebar.md` prototype;
      `PLAN.md`, `AGENTS.md`, `README.md`, `tools/` are never mirrored (`tools/pages.txt` is the gate).
- [ ] Every page reviewed in raw markdown **and** as rendered in our draft wiki at
      `https://github.com/radix29/tcell-wiki-draft/wiki/<slug>` (Q-0b: the official wiki is read-only,
      so "reviewed where it is published" means the mirror until upstream accepts something).
- [ ] Every publish went through `tools/publish.sh` with the gates green and the raw markdown re-read (Q-15
      pre-delegated the "maintainer explicitly approved" this line used to require; a proposal to upstream
      still needs a human, per Q-2); nothing force-pushed; history is forward-only.

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
review note with its commit message. After Phase 3 the rule has a second clause with the same shape: one
approved **section** (`tools/gallery-sections.txt`, PLAN 6.2's "## Demos in the Repository") whose
generated entries are exempt from the additions budget and visible in the checker's own report.

**Current draft state (N = 1, Q-13):** Demonstrations 4 / Editors 3 / UI Frameworks 7 / Games 13 /
Productivity & Utilities **22** / Miscellaneous 1 = **50 bullets, 49 with links**, the extra one being
`goSSMS` (author-supplied, recorded with evidence in `tools/gallery-additions.txt`, appended to its
category). URL hosts on the page now: github.com 45, codeberg.org 2 (Q-11), 2.bp.blogspot.com 2,
youtu.be 1, www.youtube.com 1, user-images.githubusercontent.com 1, git.sr.ht 1, termshark.io 1 = 54.
`tools/check-gallery.py` proves the 49 baseline entries are still all present and in order.

**After Phase 3 (N = 1, plus one approved section):** the 6 inherited categories exactly as above, plus
`## Demos in the Repository` with 8 entries (the library's own `demos/` programs, generated) = **58
bullets, 57 with links** (the 57th unlinked one is still the legacy `mouse demo` bullet, Q-7). URL hosts
on the page now: github.com 54 (45 project links, the `demos` directory, 8 demo programs), codeberg.org 2
(Q-11), 2.bp.blogspot.com 2, youtu.be 1, www.youtube.com 1, user-images.githubusercontent.com 1,
termshark.io 1, git.sr.ht 1 = 63, all answering 200 on 2026-10-24 and the 5 media URLs verified to a
content type or a page title (PLAN Phase 3's T3.4 record). Deletions upstream would have to review: 3
lines, the 2 Q-11 URL moves and the 1 Q-7 reword; the other 24 insertions are the addition and the new
section. `tools/check-gallery.py` still proves all 49 baseline entries are present, in their categories,
in baseline order - which is the property R2 is actually about.

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
