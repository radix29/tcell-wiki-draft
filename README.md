# Tcell wiki draft (unofficial)

**This is an unofficial draft rewrite of the [Tcell wiki](https://github.com/gdamore/tcell/wiki).
It is not affiliated with, endorsed by, or maintained by the Tcell project.** The official wiki lives
at [`gdamore/tcell.wiki`](https://github.com/gdamore/tcell/wiki) and is the authoritative version.
Content here is derived from it, and the Gallery's project names and links remain the property of
their projects. **Nothing in this repo is pushed to the official wiki**; proposals go through an issue
in [`gdamore/tcell`](https://github.com/gdamore/tcell), and none has been filed (see `PLAN.md` Q-2:
build first, talk later).

## What this repo is

A place to write Tcell wiki pages properly: in a repo the author owns, with history, review, and CI -
which a GitHub wiki cannot have. Three remotes carry the whole arrangement:

```text
gdamore/tcell.wiki.git        (upstream)  read-only; the push URL is a dead string on purpose
radix29/tcell-wiki-draft.git  (origin)    this repo; source of truth for the draft
...-draft.wiki.git            (render)    pages only, written by tools/mirror-wiki.sh
```

The diff against upstream is the deliverable. `Gallery.md` differs by three lines, each one a recorded
decision (Q-11's two URL moves, Q-13's one addition), so a Gallery edit stays one logical change.
`Home.md` is the Phase 2 rewrite: upstream's Home is three sentences and a link, so this page replaces an
apology with the hub the wiki never had - lede, Why, Versions, Install, Gallery, How to Use, Platforms,
License - keeping that one link, and it is the one page whose diff is a rewrite rather than an edit (T2.1).
`baseline/` keeps upstream's two files byte for byte, so any page here can still be compared with what it
replaced. Three of the Q-3 pages (`Architecture`, `Function-Reference`, `Terminal-Setup`) are still
honest stubs. `Getting-Started.md` is the Phase 4 page and the plan's routing rule made visible: install
from an empty directory, the demo to run first, the five pieces every program contains, and the order to
read `TUTORIAL.md` in - with no code of its own to paste, because its examples are the library's and its
walk-through is the library's tutorial (Q-4, Q-Ex). `_Sidebar.md` is D-1's droppable navigation prototype;
all of it reaches the preview at the next publish. Pages are gated by `tools/pages.txt`: a file becomes a wiki
page exactly when its name is on that list. `PLAN.md`, `AGENTS.md`, this README, `tools/` and `samples/`
are tracked but never mirrored, which is what makes it safe to keep tooling in a repo whose
push target renders pages.

The draft wiki at [`radix29/tcell-wiki-draft/wiki`](https://github.com/radix29/tcell-wiki-draft/wiki)
exists for one reason: to see how GitHub's wiki renderer actually treats a page (slug rules, links
without `.md`, Mermaid, sidebar behaviour) before anyone proposes it upstream.

## Running the checks locally

Requires Python 3 (stdlib only), Go 1.26, `curl`, and a checkout of the library beside this repo (or
`TCELL_DIR` pointing at one):

```console
$ tools/review-checklist.py --offline     # all six gates plus per-page review questions
$ tools/check-style.py --all              # house style (PLAN.md 7) on pages and docs
$ tools/check-links.py                    # internal slugs, then external URLs via curl
$ tools/make-samples.py                   # every go fence on a page must compile
$ tools/symbol-coverage.py                # invented API and undocumented TCELL_* vars
$ tools/check-gallery.py                  # Gallery migration is lossless vs baseline/
$ tools/check-demos.py --build            # the demos the pages link really ship
```

Publishing a preview (never the official wiki):

```console
$ tools/mirror-wiki.sh --dry-run          # what a publish would ship, publishing nothing
$ tools/publish.sh                        # mirror, then push, then re-read the live wiki (Q-14)
```

`tools/publish.sh` is the whole publish path and needs no approval: Q-15 pre-delegated it, so a green gate
set is the only input, and the preview is never left behind a commit on purpose. The official wiki is still
reached by an issue with page markdown attached (Q-2), never by a push - this repo cannot push there even
if it wanted to.

## Ground rules worth knowing before you send a PR

- A page may not reference anything outside itself: no repo-hosted `images/`, no `tools/` links, no
  relative paths. Upstream receives the text of one `.md` file, pasted into someone else's wiki.
- Diagrams are Mermaid or ASCII in fenced blocks until a maintainer agrees to host files.
- The library's own programs are the examples: pages link `demos/` and `TUTORIAL.md` in
  `gdamore/tcell` rather than re-authoring sample code that would rot on the next API change.
- `Gallery.md` gains entries at the end of a category, one line each, and `baseline/` proves nothing
  was lost when it was migrated.
- No `LICENSE` file here: the upstream wiki ships none, so this draft implies none.
