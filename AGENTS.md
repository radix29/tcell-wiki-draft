# Repository Overview

This is the **Tcell wiki draft** — `radix29/tcell-wiki-draft`, an unofficial rewrite of
`https://github.com/gdamore/tcell/wiki`. The clone started from the published wiki
(`.../gdamore/tcell.wiki.git`, remote `upstream`) and kept its 10 commits as provenance, so `master` is
the live wiki *plus* the draft's own commits on top. `PLAN.md` is the plan; this file is the runbook.

- Three remotes, three trust levels: `upstream` is the official wiki and is **fetch-only** (its push
  URL is deliberately `NO-PUSH-official-wiki-is-read-only`, so nothing here can publish there by
  accident); `origin` is the draft plain repo, where tooling/issues/CI live (no `LICENSE` file: the upstream wiki ships none, so the draft implies none); `render` is the draft's own
  wiki, written **only** by `tools/mirror-wiki.sh`, which copies exactly
  the files listed in `tools/pages.txt`.
- That topology is the whole safety model: **a file is safe to commit the moment it is absent from
  `tools/pages.txt`.** `PLAN.md`, `AGENTS.md`, `README.md`, `tools/`, `samples/` are tracked on purpose
  and never render as pages; the upstream artefact is the text of one page `.md`, pasted one page at a
  time into someone else's wiki.
- Page bodies sit at the repo root as plain `.md` - the 6 pages of Q-3: `Home.md` (the nav hub since
  Phase 2, and the last page in Appendix D's commit order), `Gallery.md`, `Getting-Started.md` (the
  Phase 4 page: five authored sections, two `console` blocks, no `go` fence and no Go on it at all), and
  the three that are still honest stubs from Phase 1 - `Architecture.md`, `Function-Reference.md`,
  `Terminal-Setup.md` - each one a purpose sentence, the planned scope, a pointer to what to read today,
  and no API claimed in backticks, which Q-6 reserves for the page that owns the symbol. `_Sidebar.md` sits
  beside them as D-1's droppable prototype: it is in the manifest, it is not a content page, and no page
  links it. `tools/` (QA scripts), `samples/` (snippet compile harness) and `.github/workflows/qa.yml`
  (CI) exist; see Tooling below.
- This wiki repo shares no history with the library repo — never cherry-pick, merge, or branch
  across the two. All three remotes are HTTPS, so a push may need credentials (`gh auth setup-git`)
  even when `../tcell` pushes fine.
- The Tcell library itself lives in a sibling checkout (`../tcell`). Its `README.md` points
  readers at this wiki's Gallery, so the Gallery is the canonical list of Tcell-based projects.
- Page file names decide the slug (`PLAN.md` C3): ASCII, hyphenated, at most three words, no spaces and
  no underscores - `Home.md`, `Gallery.md`, and per Q-3 `Getting-Started.md`, `Architecture.md`,
  `Function-Reference.md`, `Terminal-Setup.md`. All four Q-3 slugs exist from Phase 1 and are in the
  manifest, so from the next publish a typo in one of them is a permanent wrong URL, not a rename.

# Runbook (setup executed 2026-10-24)

Remotes and what they are for:

```text
upstream  https://github.com/gdamore/tcell.wiki.git            fetch only; push URL is a dead string
origin    https://github.com/radix29/tcell-wiki-draft.git      this repo; draft source of truth
render    https://github.com/radix29/tcell-wiki-draft.wiki.git pages only, via tools/mirror-wiki.sh
```

Done: draft repo + wikis enabled (render branch is `master`; render HEAD moves with every publish, so
read it with `git ls-remote --symref render HEAD` rather than trusting this sentence, whose history runs
`2ebcbf8` GitHub's `Initial Home page` placeholder -> `32022f9` first real page preview -> `39e5378` second
preview, all three on 2026-10-24), `origin/master` was pushed once with CI green on it
(`.github/workflows/qa.yml`, run `40112709147`, 15/15 steps), remotes rewired,
`tools/pages.txt` + `.gitignore` + tooling + `README.md` +
`.github/workflows/qa.yml` committed, `baseline/` captured (`upstream/master` = `8e83ce1`, 49 Gallery
bullets). `master` deliberately diverges from `upstream/master` - that divergence is route C - so
rolling a page back is `git checkout upstream/master -- Home.md Gallery.md`, never
`git reset --hard upstream/master` (that would also drop tooling commits). Rollback of the whole
experiment: delete the `origin`/`render` remotes and the two GitHub repos.

Publishing is a command, not an approval step (Q-15): `tools/publish.sh` mirrors, pushes and re-reads the
live wiki in one call, and nothing waits on a human saying yes. So
`git rev-list --count origin/master..HEAD`
is 0 at the end of a session and `tools/mirror-wiki.sh --check` is clean; if either is not true the
session stopped mid-work, and the fix is to finish and publish, not to leave a green phase in a local
branch. What a publish ships is whatever `tools/pages.txt` lists, because the mirror copies the manifest
and not the commit, so a preview can never lag behind one page by accident - and `--dry-run` shows the
pending file list without publishing anything.

Verify a session against this repo (all seven must pass; CI runs the same set):

```bash
tools/review-checklist.py --offline    # all gates at once, plus per-page review questions
git diff --stat upstream/master HEAD -- Home.md Gallery.md   # the deliverable; today: Gallery 24
                                                            # insertions / 3 deletions (2 URL moves Q-11,
                                                            # 1 addition Q-13, 1 reword Q-7, and the new
                                                            # `## Demos in the Repository` section), plus
                                                            # the Phase 2 Home rewrite
git ls-remote --symref render HEAD     # render wiki HEAD; a non-ff mirror push means web-UI edits
```

# Publishing Model (Read Before Pushing)

Pushing `origin/master` changes **only the draft** — that is the point of route C, and it is harmless.
What used to be true of this clone is now true of the mirror and of upstream's web editor: **copying a
page into a wiki repo and pushing it changes a rendered wiki instantly**, with no review gate, and the
commit history becomes the visible page revision history. So page bodies still get the discipline below,
and the two things `PLAN.md` 4 still leaves upstream (D-1's site-wide `_Sidebar.md` and every F-1 change
to the library repo) stay proposals, not an edit - `PLAN.md` Q-2 parks it: no contact with
`gdamore/tcell` until the draft owner says so.

- **Publishing is pre-authorized (Q-15, 2026-10-24, draft owner): commit, mirror and push when the work
  needs it, without asking first.** The rule that used to sit here - "never `git push` (or `git commit`)
  unless explicitly asked to" - was costing a human one word per green phase while a preview nobody
  publishes is the exact failure Q-14 was written against, so the ask is gone and the discipline is what
  is left. Authorization is about *whether to publish*, never about *how*: `origin` takes ordinary
  commits, the `render` wiki is written only by the mirror script, `upstream` cannot be pushed at all (its
  push URL is a dead string and Q-15 changes none of that), and every bullet below still binds. Publish
  when there is something a reader could use - a finished page, a phase exit, a fix to a live page - and
  not to make a red gate look busy: a red `tools/review-checklist.py` is a reason to stop, not a reason to
  let CI be the reviewer. What Q-15 does **not** buy is the official wiki or the library repo: `upstream`
  stays unpushable, and Q-2's "no contact with `gdamore/tcell` until the draft owner says so" is about a
  human opening an issue or a PR, which no amount of pre-authorization here touches.
- **A push is not finished until the preview shows it (Q-14, standing rule from the draft owner).**
  Run `tools/publish.sh`, which mirrors and then pushes and then re-reads the live wiki to prove it;
  pushing with bare `git push` leaves `radix29/tcell-wiki-draft/wiki` rendering an older commit, and
  CI's `preview` step fails on exactly that. Mirror-then-push is deliberate: CI starts on the push, so
  pushing first makes the gate race the mirror and a flaky gate gets ignored.
  `tools/mirror-wiki.sh` also refuses to publish pages with uncommitted edits (the render tree is a
  build output of *committed* text); `FORCE=1` exists for an emergency, not as habit.
- Never force-push, rebase, amend, or revert anything **published**: the official wiki (unreachable by
  design) and the `render` wiki carry permanent, reader-visible revision history, and rewriting them
  desyncs this clone from GitHub's wiki HEAD and from other clones - every correction is a new forward
  commit. Unrendered tooling commits on `origin` may still be squashed, but never a page commit
  (`PLAN.md` Appendix D wants page history to read as a changelog) and never anything already mirrored.
- One commit per logical page edit. History is one-entry-per-commit for exactly this reason —
  wiki diffs stay a single added/changed line, so keep each list item on one unwrapped line even
  when it exceeds 80 columns.
- Match the existing commit message style (it mirrors GitHub's wiki UI). `Updated <Page> (markdown)`
  for edits to an existing page, `Created <Page> (markdown)` for a new page, `Added <project>` /
  `Add <project>` for gallery additions, or a short sentence such as `Minor markup fix.` /
  `New gallery from README.` History mixes `Added`/`Add` with and without a trailing period; pick
  one style. All 10 existing messages are a single line with no body — keep it that way, under
  ~60 chars, no `Co-authored-by:`/AI trailers. Those wiki-shaped messages are for **page** commits, so
  the pasted page history stays readable; tooling/plan commits (impossible upstream, normal here) use a
  plain imperative one-liner, same single-line and ~60-char rules.

# Gallery.md Structure

Categories are `##` sections in this order; add entries to the end of the matching section, not
alphabetically, and never create a one-off section for a single project:

`## Demonstrations` · `## Editors` · `## UI Frameworks` · `## Games` ·
`## Productivity & Utilities` · `## Miscellaneous` · `## Demos in the Repository`

The seventh is PLAN 6.2's one sanctioned new section and it is **generated, not curated**: do not add a
project to it, do not reword its lines by hand, and do not add another section like it. A new `##` on
this page is approved only by a record in `tools/gallery-sections.txt` (heading, evidence), which is what
lets `tools/check-gallery.py` treat the section's entries as outside the additions budget while still
shape-checking every line of it; the checker prints the exemption on every run, and a record whose section
has disappeared from the page is an error. A second new section would be a plan change, not an edit.

Entry format — exactly this shape, one line each:

```markdown
- [project](https://example.com/owner/project) - short lowercase description
- [project](https://example.com/owner/project) - description ([screenshot](https://url.png))
- [project](https://example.com/owner/project) - description ([video](https://youtu.be/id))
```

- ` - ` is an ASCII hyphen with single spaces. `Gallery.md` and `Home.md` are entirely ASCII
  (only `AGENTS.md` uses em dashes); keep new wiki text ASCII.
- No trailing period on descriptions. Italicize third-party tool/library names with underscores
  on first mention in an entry: `_nano_`, `_vim_`, `_tmux_`, `_tshark_`, `_gowid_`.
- Prefer the project's real home, including non-GitHub hosts (`codeberg.org`, `git.sr.ht`,
  `termshark.io`). Check the URL actually resolves before adding it (`curl` below, or
  `tools/check-links.py`, which re-checks every URL on the page locally and in CI).
- When an inherited URL's host died, follow Q-11: find where the project lives now and **move the
  URL**, recording old, new and evidence in `tools/gallery-moves.txt` — that is what keeps
  `tools/check-gallery.py` calling it the same entry instead of a lost one. Evidence, not taste: a
  repository whose own description says `THIS IS A MIRROR` is not a home (GitHub's `tslocum/*` are
  mirrors; Codeberg is the home and the `go.mod` module path), so check description, homepage,
  `go.mod` and tag SHAs before relinking. Never keep a dead link by allow-listing it, and never
  delete the entry — the allow-list file is for statuses we *keep*, and it says so.
- Adding an entry that upstream does not have (Q-13) needs a record in `tools/gallery-additions.txt`
  first: display name, URL, and the evidence - URL resolves, project is real, it genuinely depends on
  Tcell, and whether the request came from the author. `tools/check-gallery.py` reads that file, so
  `--max-additions` stays 0 and an unrecorded bullet still fails; do not raise the flag in CI to wave
  one through, and do not add a new project without checking it imports `tcell` (this is the Tcell
  gallery). Verified entry for reference: `goSSMS` -> `github.com/radix29/gossms`.
- Duplicate display names are tolerated when the URLs differ (`go-tetris` appears twice for two
  different repos). Search for the project name and URL before adding; prefer extending or
  consolidating an existing entry over adding a near-duplicate.
- Don't add dates, star counts, version/compatibility notes, or "(new)" markers to entries — no
  entry carries one, and they rot immediately since nothing here is regenerated.
- `## Demos in the Repository` lists the 8 programs in `../tcell/demos` with their `go run ./demos/<name>`
  commands, six descriptions written from reading the programs and two from the library's own doc comments,
  plus the `_demos/` note that names a file instead of promising a copy-out (`go run _demos/mouse.go`;
  `sixel.go` needs a module the checkout does not require). Regenerate the section with
  `tools/check-demos.py --markdown` and paste what sits between the markers unedited — it measures the
  demos, the library's default branch, the `_demos` build status and the sixel caveat, so a hand-edited
  line is a claim the next run silently drops. Six of the eight descriptions are this draft's prose and may
  be rewritten from the source; run `--verbose` first, because a description the library starts shipping as
  a doc comment comes from the library from then on.
- The migration contract compares **(display name, entry URL)** pairs, so a *media* URL inside an entry is
  not policed by `tools/check-gallery.py` at all — a screenshot link can change with no check noticing.
  `tools/check-links.py` is the gate that probes those URLs (all 5 media URLs were verified to a content
  type or a page title on 2026-10-24, and a YouTube 200 is not proof a video plays, so read the title). A
  dead media URL gets reported (D-6/Q-7), not moved: unlike a dead project host it has no home to move to
  (Q-11), and the two 2015 blogspot images serve byte-identical `image/png` over `https:` if a maintainer
  ever wants that.
- The first `## Demonstrations` bullet has no link (`mouse demo - the mouse test that shipped with _Tcell_
  in 2015 ...; mouse support is now enabled per program with EnableMouse and MouseFlags`). It is legacy,
  from when Tcell shipped a mouse test (the old screenshot URLs are from 2015); the current `../tcell`
  checkout keeps that code only as `_demos/mouse.go` under `//go:build ignore`, and `../tcell/demos` has no
  mouse demo. Per Q-7 it stays, is never given an invented URL, and was reworded in Phase 3 only to stop
  claiming a shipped demo - and it stays the un-numbered 49th bullet so Appendix B's migration contract
  keeps holding. Its two API names are deliberately **not** in backticks: Q-6 gives a symbol to exactly one
  page, and `EnableMouse`/`MouseFlags` belong to `Function-Reference`'s Mouse table.

# Markdown Conventions

- Internal links omit the extension and any path: `[Gallery](Gallery)`, never `Gallery.md` or
  `./Gallery`. Internal anchors follow the renderer's model, which is the *page body*: a page's duplicate
  `#` H1 contributes no anchor (PLAN 7 says GitHub drops it), a heading inside a blockquote does (so
  `Gallery#demos-in-the-repository` resolves - `curl` of the published page shows GitHub really renders
  that anchor), and `check-links.py` therefore feeds `anchors_in()` the body with the H1 line removed.
  Handing it whole files got both halves wrong in opposite directions: a blockquoted heading was invisible,
  so a link that works was reported BROKEN, while an in-file H1 anchor was invented, so a link that would
  404 for a reader passed clean. (Phase 4's T4.4.)
  Multi-word pages are hyphenated (`Getting-Started.md` -> `[Getting-Started]`), never
  `Some_Page.md` or with spaces. **Never rename `Home.md` or `Gallery.md`**: it breaks `Home.md`'s link
  and the `wikis/Gallery` URL hardcoded in `../tcell/README.md`.
- GitHub renders the page slug as the page heading, so an in-file `#` H1 shows up as a duplicate
  title; a page therefore carries exactly one of them. `Gallery.md` always did, `Home.md` got one with
  the Phase 2 rewrite (upstream's `Home.md` has none, which is why its diff is a rewrite and not an
  edit), and the four stubs follow `Gallery.md`.
- `_emphasis_` is the established idiom; don't introduce `*emphasis_` mixes or HTML tags. Blank
  line before and after every list and heading.
- The library is **`_Tcell_` in prose** (Q-9) - bare `Tcell` only in headings, file names and paths,
  and `tcell` inside code/backticks because that is the package name. `check-style.py` rules `name`
  and `heading-period` enforce both, so `Gallery.md`'s `# Gallery of Tcell Examples` H1 stays legal.
- Don't mass-reformat. `Gallery.md` contains one legacy trailing space (`## UI Frameworks `);
  leave whitespace alone unless the whitespace *is* the fix, since cosmetic churn pollutes the
  published page-diff history.
- All page content here is `.md`; don't introduce another wiki markup format (`.org`, `.rst`,
  `.textile` also render on GitHub wikis but none is used here). **A page may not reference anything
  outside itself:** no repo-hosted `images/`, no `tools/` links, no relative `docs/`
  paths, because upstream receives only the text of one `.md` file - diagrams are Mermaid or ASCII in
  fenced blocks (D-5) — and **T5.1 measured both formats on our own wiki on 2026-10-25**: a `mermaid`
  fence becomes an enrichment container GitHub draws with its own bundle (anonymously, on
  `viewscreen.githubusercontent.com`), leaving the diagram's own source in a `<pre lang="mermaid">` behind
  it, so a browser gets a picture while a no-JS, text-mode or raw-`.md` read — which is what an upstream
  paste hands a maintainer — gets the same words as text. A diagram may explain a fact; it must not be the
  only copy of it. A `text` fence is still exactly a code block. The CHECK that Phase 1 flagged from here
  is fixed (`c46369f`): `tools/review-checklist.py` no longer fails the *word* `mermaid`, it fails a
  *reference* to a repo-hosted file outside a fence — `images/arch.png`, `docs/notes.md` — after blanking
  `scheme://` URLs, which keeps Gallery's 2015 hotlinks clean and lets a `console` transcript name a path
  it does not own. One shape measured and deliberately not used: `check-style.py` accepts a snippet marker
  on a diagram fence (`mermaid mode=skip` lints clean) and nobody has checked that the renderer still
  recognises a fence whose info string is longer than exactly `mermaid`. `_Sidebar.md`/`_Footer.md` apply
  to *every* page of whichever wiki renders them: in the draft `_Sidebar.md` is the droppable Phase 1 prototype, listed in `tools/pages.txt`, and
  it is never in an upstream proposal (D-1). Non-page directories (`tools/`, `samples/`) are fine - the
  manifest keeps them out of the render.
- Code fences on a page carry markers, and `tools/check-style.py` rejects invented ones: a bare `go`
  tag is a complete program, `snippet=name` merges fences with the same name, `mode=lib` type-checks a
  fragment, `mode=skip` is not Go (transcripts, v2 comparisons), and `headless=yes` also *runs* the
  program on the vt emulator, which requires an ESC arm. See `samples/README.md`.
- **A page backticks an API name only if it owns it (Q-6).** The single owner is `Function-Reference`,
  which 6.5 requires to name all 179 structural names in its tables, so the other pages write names like
  EventResize and EnableMouse in plain prose, or show them inside a code fence where they are code and
  not a claim. That is why `symbol-coverage.py` reports "0 page-cited symbol(s) checked" and why Phase 6
  will not open with a `SHARE` failure; it also costs nothing at review time, because
  `review-checklist.py`'s "talks about resizing but never names `EventResize`" CHECK is a substring test
  and plain prose passes it. (Home's Install fence and any future fragment are the same rule: a fence is
  not an ownership claim.)
- **Shell commands go in a `console` fence, never in `go`.** PLAN 7's marker, validated by
  `check-style.py` and skipped by `make-samples.py`, and the reason a page can publish a command it has
  actually run: Home's `go get`, Gallery's clone block, and Getting-Started's module setup and its
  module-path demo run, all measured (the last one from a directory with no source file in it). So the
  `review-checklist.py` ASK "page has no `go` fence yet" is the *expected* state for a page whose code is
  shell and whose examples are the library's (Q-Ex): answer it in the review note, do not paste Go to
  silence it.
- **The library's own programs are the examples.** Pages link `demos/` and `TUTORIAL.md` in
  `gdamore/tcell`; they do not re-author sample code, because a wiki fence rots on the next API change
  while `demos/` ships with a rendering test per program. `tools/check-demos.py` verifies the names,
  URLs, `go run` commands and `_demos/` claims against the checkout, and prints the paste-able
  `## Demos in the Repository` block with `TODO(desc)` where a demo has no doc sentence - never an
  invented description.

# Tooling (verified, run from this directory)

Every tool exits 0 clean / 1 a page needs fixing / 2 environment, prints one summary line, and takes
optional page arguments plus `--verbose`. CI (`.github/workflows/qa.yml`) runs all of them against a
fresh `gdamore/tcell` clone via `TCELL_DIR`; locally they default to the sibling `../tcell`.

```text
tools/review-checklist.py   S8.7  all gates below + review questions + both word counts (start here)
tools/check-style.py        S8.5  house style (PLAN.md 7); --all includes non-page docs
tools/check-links.py        S8.2  internal slugs/anchors, then external URLs via curl; --offline
tools/check-gallery.py      S8.4  Gallery migration is lossless vs baseline/ (49 bullets, append-only)
tools/gallery-moves.txt         recorded URL moves (Q-11): old, new, evidence; stale records fail
tools/gallery-sections.txt      the one approved new `##` on Gallery (PLAN 6.2): heading, evidence
tools/check-demos.py        S8.2b the demos/TUTORIAL links a page makes resolve; --markdown prints the
                              Gallery block, --build also builds each `_demos` file a page names
tools/make-samples.py       S8.1  every go fence compiles; headless=yes also runs it (S8.6)
tools/symbol-coverage.py    S8.3  invented API, coverage table, undocumented TCELL_* audit; a backticked
                              path like `vt/emulate.go` is a path, not an API claim
tools/apiface/          S8.3  the surface dumper (go/parser, no downloads) - run from its own dir
tools/wikilib.py              shared stdlib helpers: manifest, fences, links, ASCII, prose words
tools/gallery-additions.txt     approved entries the baseline lacks (Q-13): name, URL, evidence
tools/publish.sh                THE publish path: mirror the preview, then push, then verify (Q-14)
tools/mirror-wiki.sh            render-wiki mirror only; --dry-run to inspect, --check as a gate
```

Allow-lists carry only legacy exceptions with a written reason: `tools/style-allow.txt` (1 upstream
defect left, the `## UI Frameworks ` trailing space D-9 says to leave; its second entry retired when Phase 2
rewrote `Home.md` and fixed the missing final newline as part of the page),
`tools/link-status-allow.txt` (statuses we investigated and deliberately keep - after Q-11
nothing unreachable is left on a page, and allow-listing a dead URL to quiet CI is now explicitly
against policy), `tools/api-allow.txt` (non-API package prefixes). Never add an entry to silence a finding
you do not understand, and never add a `.md` pattern to `.gitignore` (build noise only).

Still useful one-liners that no tool covers:

```bash
# Appended-to sections: shows the current last entry of each category.
awk '/^## /{s=$0} /^- \[/{last[s]=$0} END{for (k in last) print k" -> "last[k]}' Gallery.md

# The raw page diff you are about to publish.
git diff -- Home.md Gallery.md

# Does a published page really carry a rendered Mermaid diagram? T5.1 measured this way on a probe block
# that is since removed; once T5.4 ships a real diagram this is the re-check. 0 means either the page has
# no diagram or the renderer stopped recognising the fence. Anonymous curl is the point: the enrichment
# container is in the server HTML a logged-out reader gets, not something a session adds.
curl -sS https://github.com/radix29/tcell-wiki-draft/wiki/Architecture | grep -c 'data-type="mermaid"'
```

If the `curl` check inside `check-links.py` fails because of sandbox/network restrictions it says so in
its report instead of guessing, and never invent a URL from a project name.

# Workflow Checklist

1. `git status` shows a clean tree, then `git fetch upstream && git log --oneline master..upstream/master`
   - the wiki is edited by many people through the web UI and this clone goes stale.
2. Make the smallest possible edit; grep for the project name/URL before touching `Gallery.md`.
3. Re-read the raw file, not a rendered guess: confirm the entry sits in the right section, then run
   `tools/review-checklist.py --offline` and confirm `git diff --stat` shows the expected single-line
   change.
4. Commit in the wiki's message style (page commits) or plain imperative (tooling), then publish with
   `tools/publish.sh` once the gates are green - committing and publishing are autonomous work now (Q-15),
   not something to ask about, and an unpublished green phase is a preview that has gone stale on purpose.

# Note About This File

This file **is** committed, per route C - and it must never be added to
`tools/pages.txt`, which is the only list the mirror script and therefore any rendered wiki ever sees.
That manifest, not a `.gitignore`, is the single source of truth for what becomes a page; it is why a
`README.md` / `PLAN.md` / `AGENTS.md` commit here is safe while the same commit in a real wiki repo would
publish three stray pages. Never gitignore a `.md` (`PLAN.md` 8 and the CI scripts need `PLAN.md`,
`baseline/` and the pages on disk), and never mirror this file: it uses em dashes in its own prose, and
page bodies must stay pure ASCII.
