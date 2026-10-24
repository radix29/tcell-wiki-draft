# Repository Overview

This is the **Tcell wiki** — the published content of `https://github.com/gdamore/tcell/wiki`,
cloned from `https://github.com/gdamore/tcell.wiki.git` (branch `master`).

- Documentation only: two Markdown pages, `Home.md` and `Gallery.md`. No code, `go.mod`,
  build, test, or lint tooling. There is nothing to compile or run.
- This wiki repo shares no history with the library repo — never cherry-pick, merge, or branch
  across the two. Its remote is `.../tcell.wiki.git`, served over HTTPS, so a push may need
  credentials even when `../tcell` pushes fine.
- The Tcell library itself lives in a sibling checkout (`../tcell`). Its `README.md` points
  readers at this wiki's Gallery, so the Gallery is the canonical list of Tcell-based projects.
- Every page name is a single PascalCase word with no spaces (`Home.md`, `Gallery.md`). Keep it
  that way for new pages so cross-page links stay trivial.

# Publishing Model (Read Before Pushing)

There is no review gate. **A push to `origin/master` immediately changes the public wiki** for
every reader, and the commit history is the visible page revision history.

- Never `git push` (or `git commit`) unless explicitly asked to. Ask instead.
- Never force-push, rebase, amend, or revert published commits. There is no way to unpublish a wiki
  revision; rewriting history desyncs this clone from GitHub's wiki HEAD and from other clones,
  and every correction is a new forward commit.
- One commit per logical page edit. History is one-entry-per-commit for exactly this reason —
  wiki diffs stay a single added/changed line, so keep each list item on one unwrapped line even
  when it exceeds 80 columns.
- Match the existing commit message style (it mirrors GitHub's wiki UI). `Updated <Page> (markdown)`
  for edits to an existing page, `Created <Page> (markdown)` for a new page, `Added <project>` /
  `Add <project>` for gallery additions, or a short sentence such as `Minor markup fix.` /
  `New gallery from README.` History mixes `Added`/`Add` with and without a trailing period; pick
  one style. All 10 existing messages are a single line with no body — keep it that way, under
  ~60 chars, no `Co-authored-by:`/AI trailers.

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
  `./Gallery`. Multi-word pages would use underscores (`Some_Page.md`), but avoid multi-word
  page names. Never rename `Home.md` or `Gallery.md`: it breaks `Home.md`'s link and the
  `wikis/Gallery` URL hardcoded in `../tcell/README.md`.
- GitHub renders the page slug as the page heading, so an in-file `#` H1 shows up as a duplicate
  title; `Gallery.md` does this and `Home.md` has no H1. Follow `Gallery.md` for new content pages.
- `_emphasis_` is the established idiom; don't introduce `*emphasis_` mixes or HTML tags. Blank
  line before and after every list and heading.
- Don't mass-reformat. `Gallery.md` contains one legacy trailing space (`## UI Frameworks `);
  leave whitespace alone unless the whitespace *is* the fix, since cosmetic churn pollutes the
  published page-diff history.
- All content here is `.md`; don't introduce another wiki markup format (`.org`, `.rst`,
  `.textile` also render on GitHub wikis but none is used here). Don't add images, scripts,
  subdirectories, `_Sidebar.md` or `_Footer.md` without being asked — a sidebar or footer in this
  repo would apply to *every* page in the Tcell wiki, and it goes live on push.

# Useful Commands (tested, run from this directory)

There is no build, test suite, or linter — these are the whole verification story.

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
4. Commit in the wiki's message style, and only push when asked.

# Note About This File

GitHub wikis turn *any* `.md` file in this repo into a public page, so committing `AGENTS.md` and
pushing it would publish an "AGENTS" page in the Tcell wiki listing. Treat this file as local
maintainer tooling: if it should outlive the session, say so and add `AGENTS.md` to
`.git/info/exclude` (local only) rather than committing it or adding a tracked `.gitignore`.
