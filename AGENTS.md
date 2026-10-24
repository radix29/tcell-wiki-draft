# Repository Overview

This is the **Tcell wiki draft** — `radix29/tcell-wiki-draft`, an unofficial rewrite of
`https://github.com/gdamore/tcell/wiki`. The clone started from the published wiki
(`.../gdamore/tcell.wiki.git`, remote `upstream`) and kept its 10 commits as provenance, so `master` is
the live wiki *plus* the draft's own commits on top. `PLAN.md` is the plan, `setup.md` the runbook.

- Three remotes, three trust levels: `upstream` is the official wiki and is **fetch-only** (its push
  URL is deliberately `NO-PUSH-official-wiki-is-read-only`, so nothing here can publish there by
  accident); `origin` is the draft plain repo, where tooling/issues/CI live; `render` is the draft's own
  wiki, written **only** by `tools/mirror-wiki.sh` (`setup.md` 4 - not written yet), which copies exactly
  the files listed in `tools/pages.txt`.
- That topology is the whole safety model: **a file is safe to commit the moment it is absent from
  `tools/pages.txt`.** `PLAN.md`, `AGENTS.md`, `setup.md`, `README.md`, `tools/`, `samples/` are tracked
  on purpose and never render as pages; the upstream artefact is the text of one page `.md`, pasted one
  page at a time into someone else's wiki.
- Page bodies sit at the repo root as plain `.md` — today `Home.md` and `Gallery.md`. `tools/` (QA
  scripts), `samples/` (snippet compile harness) and `.github/workflows/` land per `PLAN.md` 8; until
  they exist there is nothing here to compile, test or lint.
- This wiki repo shares no history with the library repo — never cherry-pick, merge, or branch
  across the two. All three remotes are HTTPS, so a push may need credentials (`gh auth setup-git`)
  even when `../tcell` pushes fine.
- The Tcell library itself lives in a sibling checkout (`../tcell`). Its `README.md` points
  readers at this wiki's Gallery, so the Gallery is the canonical list of Tcell-based projects.
- Page file names decide the slug (`PLAN.md` C3): ASCII, hyphenated, at most three words, no spaces and
  no underscores - `Home.md`, `Gallery.md`, and per Q-3 `Getting-Started.md`, `Function-Reference.md`,
  `Terminal-Setup.md`.

# Publishing Model (Read Before Pushing)

Pushing `origin/master` changes **only the draft** — that is the point of route C, and it is harmless.
What used to be true of this clone is now true of the mirror and of upstream's web editor: **copying a
page into a wiki repo and pushing it changes a rendered wiki instantly**, with no review gate, and the
commit history becomes the visible page revision history. So page bodies still get the discipline below,
and everything in `PLAN.md` 4 that is "an upstream call" (D-1, D-2, D-6 wording, D-7, D-8, F-1) stays a
proposal, not an edit — `setup.md` 7 is parked: no contact with `gdamore/tcell` until the draft owner
says so.

- Never `git push` (or `git commit`) unless explicitly asked to. Ask instead. When asked: `origin`
  takes ordinary commits, the `render` wiki is only ever written by the mirror script, and `upstream`
  cannot be pushed at all.
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
`## Productivity & Utilities` · `## Miscellaneous`

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
- Prefer the project's real home, including non-GitHub hosts (`code.rocketnine.space`,
  `git.sr.ht`, `termshark.io`). Check the URL actually resolves before adding it (see
  `curl` below) — there is no automated link checker here.
- Duplicate display names are tolerated when the URLs differ (`go-tetris` appears twice for two
  different repos). Search for the project name and URL before adding; prefer extending or
  consolidating an existing entry over adding a near-duplicate.
- Don't add dates, star counts, version/compatibility notes, or "(new)" markers to entries — no
  entry carries one, and they rot immediately since nothing here is regenerated.
- The first `## Demonstrations` bullet has no link (`mouse demo - included mouse test ...`). It is
  legacy, from when Tcell shipped a mouse test (the old screenshot URL is from 2015); the current
  `../tcell` checkout keeps that code only as `_demos/mouse.go` under `//go:build ignore`, and
  `../tcell/demos` has no mouse demo. Leave it as-is rather than inventing a URL for it.

# Markdown Conventions

- Internal links omit the extension and any path: `[Gallery](Gallery)`, never `Gallery.md` or
  `./Gallery`. Multi-word pages are hyphenated (`Getting-Started.md` -> `[Getting-Started]`), never
  `Some_Page.md` or with spaces. **Never rename `Home.md` or `Gallery.md`**: it breaks `Home.md`'s link
  and the `wikis/Gallery` URL hardcoded in `../tcell/README.md`.
- GitHub renders the page slug as the page heading, so an in-file `#` H1 shows up as a duplicate
  title; `Gallery.md` does this and `Home.md` has no H1. Follow `Gallery.md` for new content pages.
- `_emphasis_` is the established idiom; don't introduce `*emphasis_` mixes or HTML tags. Blank
  line before and after every list and heading.
- Don't mass-reformat. `Gallery.md` contains one legacy trailing space (`## UI Frameworks `);
  leave whitespace alone unless the whitespace *is* the fix, since cosmetic churn pollutes the
  published page-diff history.
- All page content here is `.md`; don't introduce another wiki markup format (`.org`, `.rst`,
  `.textile` also render on GitHub wikis but none is used here). **A page may not reference anything
  outside itself** (`setup.md` 3): no repo-hosted `images/`, no `tools/` links, no relative `docs/`
  paths, because upstream receives only the text of one `.md` file — diagrams are Mermaid or ASCII in
  fenced blocks (D-5). `_Sidebar.md`/`_Footer.md` apply to *every* page of whichever wiki renders them:
  in the draft a sidebar is a droppable Phase 1 prototype mirrored only to `render`, and it is never in
  an upstream proposal (D-1). Non-page directories (`tools/`, `samples/`) are fine — the manifest keeps
  them out of the render.

# Useful Commands (tested, run from this directory)

There is no build, test suite, or linter yet — these are the whole verification story until `tools/`
lands (`PLAN.md` 8, `setup.md` 5).

```bash
# Appended-to sections: shows the current last entry of each category.
awk '/^## /{s=$0} /^- \[/{last[s]=$0} END{for (k in last) print k" -> "last[k]}' Gallery.md

# Malformed markdown links, e.g. `[tiki])url)` — the shape that needed a follow-up wiki fix commit.
# Prints nothing when clean. Scope it to the wiki pages; AGENTS.md prose contains brackets.
grep -nP '\[[^\]]*\](?!\()' Gallery.md Home.md

# Does a candidate project URL resolve? Needs network; prints an HTTP status.
curl -sS -o /dev/null -m 8 -w '%{http_code}\n' -I <url>

# Total gallery entries, and the raw diff you are about to publish.
grep -c '^- \[' Gallery.md && git diff
```

If the `curl` check fails because of sandbox/network restrictions, say so in your reply instead of
adding the URL on assumption, and never invent a URL from a project name.

# Workflow Checklist

1. `git status` shows a clean tree, then `git pull --ff-only` — the wiki is edited by many people
   through the web UI and this clone goes stale.
2. Make the smallest possible edit; grep for the project name/URL before touching `Gallery.md`.
3. Re-read the raw file, not a rendered guess: confirm the entry sits in the right section, run the
   link-syntax `grep` and `curl` checks above, and confirm `git diff --stat` shows the expected
   single-line change.
4. Commit in the wiki's message style (page commits) or plain imperative (tooling), and only push when
   asked.

# Note About This File

This file **is** committed, per route C (`setup.md` 3) — and it must never be added to
`tools/pages.txt`, which is the only list the mirror script and therefore any rendered wiki ever sees.
That manifest, not a `.gitignore`, is the single source of truth for what becomes a page; it is why a
`README.md` / `PLAN.md` / `AGENTS.md` commit here is safe while the same commit in a real wiki repo would
publish three stray pages. Never gitignore a `.md` (`PLAN.md` 8 and the CI scripts need `PLAN.md`,
`baseline/` and the pages on disk), and never mirror this file: it uses em dashes in its own prose, and
page bodies must stay pure ASCII.
