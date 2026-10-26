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

The diff against upstream is the deliverable, and the build is finished: all six content pages plus `Home`
exist, are published, and are recorded phase by phase in `PLAN.md`. `Gallery.md` differs from upstream's one
line per recorded decision - Q-11's two URL moves, Q-13's one addition, Q-7's reword of the unlinked
mouse-demo claim so it stops promising a demo the library no longer ships, and one navigation sentence added
at Phase 7 so the Gallery is not the one page with no way out of it - plus the generated
`## Demos in the Repository` section (PLAN 6.2, the only new `##` anyone may add, written by
`tools/check-demos.py --markdown`). `Home.md` is the Phase 2 rewrite: upstream's Home is three sentences and
a link, so this page replaces an apology with the hub the wiki never had, and it is the one page whose diff is
a rewrite rather than an edit (T2.1). `Getting-Started.md` is the plan's routing rule made visible: install
from an empty directory, the demo to run first, the five pieces every program contains, and the order to read
`TUTORIAL.md` in - with no code of its own to paste, because its examples are the library's and its
walk-through is the library's tutorial (Q-4, Q-Ex). `Architecture.md` tells the request/answer/tick-triplet
story in three Mermaid diagrams and no Go. `Function-Reference.md` owns every API name in twelve tables.
`Terminal-Setup.md` owns every environment variable, with precedence stated per knob because one rule for
all of them would be wrong for two. `baseline/` keeps upstream's two files byte for byte, so any page here can
still be compared with what it replaced. `_Sidebar.md` is D-1's droppable navigation prototype, in the
manifest and linked from nothing. Pages are gated by `tools/pages.txt`: a file becomes a wiki page exactly
when its name is on that list. `PLAN.md`, `AGENTS.md`, this README, `MAINTAINING.md`,
`UPSTREAM-FOLLOWUPS.md`, `tools/` and `samples/` are tracked but never mirrored, which is what makes it safe
to keep tooling in a repo whose push target renders pages.

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
$ tools/symbol-coverage.py                # invented API, coverage gate, and the env audit
$ tools/check-gallery.py                  # Gallery migration is lossless vs baseline/
$ tools/check-demos.py --build            # the demos the pages link really ship
```

Then look at the page the way a reader does, against the **published** wiki rather than the file:

```console
$ curl -sS .../wiki/Function-Reference | grep -c '<table'      # 12, the same count the file has
$ node tools/viewport-probe.cjs .../wiki/<Page> --width=375 --control   # the wide-table case, on a phone
$ lynx -dump -nolist -width=80 .../wiki/<Page>                  # the page in a browser with no JavaScript
```

The probe starts its own headless Chrome and needs no install; it is the only tool here that is not a gate and
not in CI, because CI has no browser. Its `--control` injects a table carrying an 80-character word, so a
clean report means "checked and clean" instead of "the probe was blind". Full commands and today's numbers are
in `AGENTS.md`; `MAINTAINING.md` says which of these a given change actually needs.

Publishing a preview (never the official wiki):

```console
$ tools/mirror-wiki.sh --dry-run          # what a publish would ship, publishing nothing
$ tools/publish.sh                        # mirror, then push, then re-read the live wiki (Q-14)
```

`tools/publish.sh` is the whole publish path and needs no approval: Q-15 pre-delegated it, so a green gate
set is the only input, and the preview is never left behind a commit on purpose. The official wiki is still
reached by an issue with page markdown attached (Q-2), never by a push - this repo cannot push there even
if it wanted to. The library-side asks this draft accumulated along the way (a legacy URL in `README.md`,
two pointers from the repo to the wiki, doc comments that do not match the code, `TUTORIAL.md` thin spots) are
listed in `UPSTREAM-FOLLOWUPS.md`, which is prepared and parked: nothing in it has been filed, and filing it
is a human decision.

## Ground rules worth knowing before you send a PR

- A page may not reference anything outside itself: no repo-hosted `images/`, no `tools/` links, no
  relative paths. Upstream receives the text of one `.md` file, pasted into someone else's wiki.
- Diagrams are Mermaid or ASCII in fenced blocks until a maintainer agrees to host files.
- The library's own programs are the examples: pages link `demos/` and `TUTORIAL.md` in
  `gdamore/tcell` rather than re-authoring sample code that would rot on the next API change.
- `Gallery.md` gains entries at the end of a category, one line each, and `baseline/` proves nothing
  was lost when it was migrated.
- A new page picks a slug forever, because the file name is the URL. ASCII, hyphenated, at most three
  words, no `Home`/`Gallery` rename (the library's own README links `wikis/Gallery`), one in-file `#` H1 and
  nothing on the page that is not on the page. `MAINTAINING.md` has the checklist.
- Wide tables are safe here and worth knowing why before adding a column: GitHub's wiki stylesheet gives a
  markdown table `display: block; overflow-x: auto`, so a table too wide for a phone becomes a swipe inside
  its own box instead of a broken page. The number to re-check is the drag width, with the viewport probe.
- `Home` is the wiki's landing page, so `/wiki/Home` is a redirect to `/wiki`: it needs no inbound link to
  be reachable and no page owes it one.
- No `LICENSE` file here: the upstream wiki ships none, so this draft implies none.
