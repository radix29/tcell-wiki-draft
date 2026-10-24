# Setup - author in `radix29/tcell-wiki-draft`, propose upstream (route C)

This file is local/draft tooling. It is **never** a wiki page: it is not in `tools/pages.txt`, so
`tools/mirror-wiki.sh` will not copy it into the render target, and nothing here is pasted upstream.

Goal: write Tcell wiki pages in a repo **you** own, render them exactly like the real wiki, run QA in
CI (impossible in a wiki repo), and keep `gdamore/tcell.wiki` read-only until a maintainer accepts
something.

## 0. Topology you end up with

```
gdamore/tcell.wiki.git   (remote name: upstream)   read-only  <- source of truth for what is live
        |  fetch only
        v
~/go/tcell.wiki          your working clone, branch master, plain .md at repo root
        |  push
        +--> radix29/tcell-wiki-draft.git          (origin) source of truth for the draft; holds
        |                                            PLAN.md, AGENTS.md, setup.md, tools/, samples/,
        |                                            .github/ - plain repo, so all of that is fine
        +--> radix29/tcell-wiki-draft.wiki.git     (remote name: render) pages only, via mirror script;
                                                   renders at github.com/radix29/tcell-wiki-draft/wiki
```

Why two push targets: the **plain repo** gives you issues, PRs, Actions CI, `tools/`, a README landing
page and a normal `.gitignore`; the **draft's own wiki** gives byte-accurate wiki rendering (sidebar
behaviour, slug rules, link-without-`.md`, Mermaid) so decisions D-1, D-3, D-5, D-9 and constraint C9
are settled by looking at a screen instead of guessing.

## 1. Create the draft repo (done 2026-10-24 - kept as the recipe in case the repo is ever deleted)

```bash
cd ~/go/tcell.wiki
gh repo create radix29/tcell-wiki-draft --public \
  --description "Unofficial draft rewrite of the gdamore/tcell wiki - proposals, not a fork."
gh auth setup-git    # lets git use the gh token for pushes to radix29/*
```

Or the web UI: `https://github.com/new` -> owner `radix29`, name `tcell-wiki-draft`, Public, **no**
README/license/.gitignore (we are pushing real history into it).

Then enable the render target: repo **Settings -> Pages/Wiki -> check "Wikis"** (a wiki can coexist
with repo files). Confirm the wiki's default branch after the first push:

```bash
git ls-remote --symref https://github.com/radix29/tcell-wiki-draft.wiki.git HEAD   # prints master or main
```

## 2. Rewire the clone (keep the 10 upstream commits as provenance)

```bash
cd ~/go/tcell.wiki
git fetch upstream 2>/dev/null || true          # no-op until the remote exists
git remote rename origin upstream
git remote set-url --push upstream NO-PUSH-official-wiki-is-read-only   # second guard, belt and braces
git remote add origin https://github.com/radix29/tcell-wiki-draft.git
git remote add render https://github.com/radix29/tcell-wiki-draft.wiki.git
git remote -v
git push -u origin master
```

Expected: `git remote -v` lists 3 fetch URLs, and `git push upstream ...` fails with
`'NO-PUSH-official-wiki-is-read-only' does not appear to be a git repository`. Upstream stays
fetchable; nothing you do can publish to the official wiki by accident. Keep the branch named
`master` - GitHub wikis are historically `master`-based and matching avoids surprises in step 4.

**Executed 2026-10-24:** 3 remotes + `origin/master` pushed, `master` kept.

## 3. Let the plain repo carry the tooling

In the **draft** repo the "untracked forever" rule of `AGENTS.md` no longer applies (it protects the
*official* wiki from `PLAN.md` becoming a page). Commit tooling here instead:

```
Home.md  Gallery.md  <new pages>     <- page bodies; must stay self-contained + paste-able upstream
README.md                            <- landing page, unofficial disclaimer (step 6)
PLAN.md AGENTS.md setup.md           <- tracked, but never mirrored (they are not pages)
tools/pages.txt                      <- the page manifest (single source of truth)
tools/  samples/  .github/workflows/ <- S8.1-S8.7 scripts, the compile harness, CI
.gitignore                           <- only build noise (/samples/*/bin, __pycache__, *.orig)
```

Rule that keeps route C honest: **a page may not reference anything outside itself.** No
`images/foo.png` from our repo, no `tools/` links, no relative `docs/` paths - because the upstream
artefact is the text of one `.md` file pasted into someone else's wiki. Diagrams are Mermaid or ASCII
inside fenced blocks until a maintainer agrees to host files (D-5).

`tools/pages.txt` (one file per line, extend as pages land):

```
Home.md
Gallery.md
```

**Executed 2026-10-24:** the manifest above and `.gitignore` (build noise only: `/samples/*/bin`,
`__pycache__/`, `*.orig`) are committed, and `PLAN.md` / `AGENTS.md` / `setup.md` stay tracked while
deliberately absent from the manifest - which is what makes them safe to commit here. Two
consequences to keep in mind: `master` now differs from `upstream/master` **by design** (see 8), and a
page becomes a page exactly when its file name is added to `tools/pages.txt`.

## 4. Mirror script (render preview = push the manifest to the draft wiki)

`tools/mirror-wiki.sh`:

```bash
#!/usr/bin/env bash
# Copy ONLY the files listed in tools/pages.txt into a clone of the draft wiki and push.
set -euo pipefail
ROOT=$(git rev-parse --show-toplevel)
MIRROR=${MIRROR:-/tmp/tcell-wiki-draft.wiki}
REMOTE=https://github.com/radix29/tcell-wiki-draft.wiki.git
[ -d "$MIRROR/.git" ] || git clone "$REMOTE" "$MIRROR"
git -C "$MIRROR" pull --ff-only
cd "$ROOT"
while read -r page; do
  [ -n "$page" ] && [ -f "$page" ] && cp "$page" "$MIRROR/$page"
done < tools/pages.txt
git -C "$MIRROR" add -A
git -C "$MIRROR" commit -m "Preview draft pages" || echo "nothing to mirror"
git -C "$MIRROR" push
```

`chmod +x tools/mirror-wiki.sh`, then preview at
`https://github.com/radix29/tcell-wiki-draft/wiki/Home`. This is also where T5.1's Mermaid probe and
any `_Sidebar.md` experiment happen - **never** on the official wiki (that was `PLAN.md` C1/C9 risk).

Heads-up from `git ls-remote --symref render HEAD` (2026-10-24): the render target is `master` and
already carries GitHub's own `Initial Home page` commit (`2ebcbf8`, a one-line placeholder `Home.md`).
The first mirror push overwrites that placeholder; a non-fast-forward push later means the wiki was
edited through the web UI, so pull the mirror rather than forcing.

## 5. CI in the draft repo (the one thing the official wiki can never have)

Draft the QA scripts of `PLAN.md` S8.1-S8.5/S8.7 under `tools/`, then `.github/workflows/qa.yml` runs
them on every push: markdown link + internal-slug check, style lint, Gallery losslessness diff against
`baseline/`, snippet compile harness against `../tcell`. Do not put a `LICENSE` file in this repo - the
upstream wiki ships none and we do not own its text.

## 6. README.md of the draft (landing page, keeps the project honest)

Must say, in plain words: **unofficial draft; not affiliated with, endorsed by, or maintained by the
Tcell project; official wiki at `https://github.com/gdamore/tcell/wiki`; content derived from it, and
the Gallery's names/links are the property of their projects; nothing here is pushed to the official
wiki - proposals go through an issue in `gdamore/tcell`.**

## 7. Proposing upstream (route C's exit ramp) - **PARKED per Q-2 (2026-10-24): build first, talk later**

Keep the draft repo public from day one so that, when you do decide to talk, the issue only has to
contain a URL. Steps 1-5 below stay valid; do not file the issue just because this section exists.


1. Fetch first (still worth doing every session, even while parked - the live wiki changes): `git fetch upstream && git log --oneline master..upstream/master` - the live wiki is
   edited through the web UI by strangers and this clone goes stale.
2. Open one issue in `gdamore/tcell` (not a wall of 13 pages): short description, link to
   `radix29/tcell-wiki-draft`, and lead with the three concrete defects this audit already found -
   `README.md:32` links the legacy `.../wikis/Gallery/` URL, `TCELL_ALTSCREEN`/`TCELL_COLS`/
   `TCELL_LINES` are implemented but documented nowhere, and the Gallery's `mouse demo` bullet
   describes a demo that is no longer shipped.
3. Offer the smallest first change: a `Home.md` rewrite plus a one-line Gallery addition. One page per
   comment, fenced as raw markdown, so a maintainer can paste it in the wiki editor without a diff tool.
4. **Do not** propose: `_Sidebar.md` (it changes every page), Support/commercial links, repo-hosted
   images, page renames, or `../tcell` README/TUTORIAL edits. Those are maintainers' calls
   (`PLAN.md` 4.1 Q-0b) - ask, don't implement.
5. If upstream declines: stop pasting, and only then decide whether the draft becomes a GitHub Pages
   site (MkDocs / Just the Docs), which unlocks sidebar, search, images and Mermaid for real.

## 8. Verify this setup worked

```bash
git remote -v                     # upstream (fetch), origin, render
git push --dry-run origin master  # auth OK via gh token
git log --oneline -1 upstream/master   # live wiki HEAD recorded
grep -c '^- ' Gallery.md          # 49 = the migration contract, must stay 49 until Phase 3 decides
```

Rollback is cheap and matters because this is someone else's project: delete the `origin`/`render`
remotes and the two GitHub repos and this clone is an ordinary wiki clone again. Since step 3, though,
`master` is `upstream/master` **plus** draft commits (that divergence is the point of route C), so
`git reset --hard upstream/master` - while it still restores the two published *page bodies* in one
command - also throws away every tooling, plan and README commit. Prefer
`git checkout upstream/master -- Home.md Gallery.md` to roll a page back, and keep tooling only in
`origin`.
