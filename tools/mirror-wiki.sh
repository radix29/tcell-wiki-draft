#!/usr/bin/env bash
# Mirror ONLY the pages listed in tools/pages.txt into a clone of the draft wiki and push.
#
# This is the sole path by which anything in this repo becomes a wiki page (PLAN.md C2 + Q-0c):
# PLAN.md, AGENTS.md, README.md, tools/ and samples/ are tracked in the plain repo and can
# never reach a rendered wiki, because they are not in the manifest.
#
# Usage:
#   tools/mirror-wiki.sh                  copy manifest pages, commit, push to the render remote
#   tools/mirror-wiki.sh --dry-run        show exactly what would be published; commit/push nothing
#   tools/mirror-wiki.sh --check          CI's drift gate: exit 1 if the live render wiki does NOT
#                                         render these pages exactly (never writes; Q-14)
#   MSG='Updated Home (markdown)' tools/mirror-wiki.sh
#                                         one-page-per-push history that reads like the real wiki
#   MIRROR=/tmp/x.git-replica REMOTE=/tmp/x.git tools/mirror-wiki.sh
#                                         sandbox against another wiki repo (CI smoke test, no secrets)
set -euo pipefail

ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
MIRROR=${MIRROR:-/tmp/tcell-wiki-draft.wiki}
REMOTE=${REMOTE:-https://github.com/radix29/tcell-wiki-draft.wiki.git}
MANIFEST=${MANIFEST:-$ROOT/tools/pages.txt}
MSG=${MSG:-Preview draft pages}
# The render tree is a build output of the repo, so it must be built from committed content: an
# uncommitted page edit published "because the mirror runs after every push" would put text on a
# public wiki that no commit and no review ever saw (Q-14). FORCE=1 overrides for emergencies.
FORCE=${FORCE:-0}
# BRANCH defaults to whatever the render clone is on, which after a clone is the wiki's own default
# branch. `git ls-remote --symref render HEAD` says it is `master` for the draft wiki; override only if that
# ever changes out from under us.
BRANCH=${BRANCH:-}

DRY=0
CHECK=0
case "${1:-}" in
  -n | --dry-run) DRY=1 ;;
  -c | --check) CHECK=1 ;;
  '') ;;
  *)
    echo "usage: ${0##*/} [--dry-run | --check]" >&2
    exit 2
    ;;
esac
[ -f "$MANIFEST" ] || {
  echo "no manifest at $MANIFEST" >&2
  exit 2
}

# --- read the manifest: blank lines ignored, '#' comments allowed, every other line must exist ----
pages=()
lineno=0
while IFS= read -r line || [ -n "$line" ]; do
  lineno=$((lineno + 1))
  line=${line%$'\r'}
  [ -n "$line" ] || continue
  case $line in
    \#*) continue ;;
  esac
  # A wiki page is a flat file name at the wiki root: no directories, no dots beyond the extension.
  # Checked before existence so a typo like `doc/Foo.md` reports the real problem.
  case $line in
    */* | .* | *[[:space:]]* | *'..'*)
      echo "$MANIFEST:$lineno: '$line' is not a flat page name (no path, no spaces, no dot prefix)" >&2
      exit 2
      ;;
  esac
  [ -f "$ROOT/$line" ] || {
    echo "$MANIFEST:$lineno lists missing file '$line'" >&2
    exit 2
  }
  pages+=("$line")
done <"$MANIFEST"

[ ${#pages[@]} -gt 0 ] || {
  echo "manifest lists no pages; refusing to mirror an empty wiki" >&2
  exit 2
}

# --- refuse to publish text that is not committed (see FORCE above) ------------------------------
dirty_pages=$(git -C "$ROOT" status --porcelain -- "${pages[@]}" || true)
if [ -n "$dirty_pages" ] && [ "$FORCE" != 1 ]; then
  { echo "refusing to publish: these manifest pages have uncommitted changes"
    printf '%s\n' "$dirty_pages" | sed 's|^|  |'
    echo "  the render wiki is a build output of committed content; commit first (Q-14), or"
    echo "  FORCE=1 if you really mean to publish text that no commit contains."
  } >&2
  exit 2
fi

# --- clone / update the render clone -------------------------------------------------------------
[ -d "$MIRROR/.git" ] || git clone "$REMOTE" "$MIRROR"
if git -C "$MIRROR" rev-parse -q --verify HEAD >/dev/null 2>&1; then
  # A rejected pull means someone edited the wiki through the web UI: fix the clone, never force-push.
  before=$(git -C "$MIRROR" rev-parse HEAD)
  git -C "$MIRROR" pull --ff-only
  after=$(git -C "$MIRROR" rev-parse HEAD)
  if [ "$before" != "$after" ]; then
    # The render tree is a build output, so anything that landed there without going through this
    # script (a wiki web-UI edit) is about to be overwritten by the copy below. Say so loudly - the
    # text of that edit is otherwise unrecoverable, since the draft wiki is the only copy of it.
    foreign=$(git -C "$MIRROR" log --pretty=%s "$before..$after" | grep -vx "$MSG" || true)
    if [ -n "$foreign" ]; then
      touched=$(git -C "$MIRROR" diff --name-only "$before" "$after" -- "${pages[@]}" || true)
      if [ -n "$touched" ]; then
        { echo "warning: the render wiki moved since the last mirror, not via this script:"
          printf '%s\n' "$foreign" | sed 's/^/  commit: /'
          printf '%s\n' "$touched" | sed 's|^|  it edited:  |'
          echo "  copying the manifest over it next; if that edit was meant to last, commit the text"
          echo "  into $ROOT/<page> first (the wiki is the build output, the repo is the source)."
        } >&2
      fi
    fi
  fi
else
  echo "note: remote wiki has no commits yet; this push creates the first one"
fi
# Worktree dirt in the render clone can only come from an interrupted run of this script (a --check
# killed by a pager or `head` after the copy+add but before its restore step). A wiki web-UI edit is
# different: it arrives by the pull above and is reported there. The clone is a build output, nobody
# edits it by hand and everything in it is reproducible from this repo, so reset it and say so instead
# of asking a human to clean a directory that is never the source of truth.
dirt=$(git -C "$MIRROR" status --porcelain)
if [ -n "$dirt" ]; then
  { echo "note: the render clone had leftover state; resetting it (nothing there is unrecoverable -"       "the wiki is the output, this repo is the source):"
    printf '%s\n' "$dirt" | sed 's|^|  |'
  } >&2
  git -C "$MIRROR" reset -q --hard HEAD
  git -C "$MIRROR" clean -qfd -- "${pages[@]}" 2>/dev/null || true
fi

# --- copy the manifest and nothing else ----------------------------------------------------------
for page in "${pages[@]}"; do
  cp "$ROOT/$page" "$MIRROR/$page"
done
git -C "$MIRROR" add -A -- "${pages[@]}"

# Anything else in the wiki is a file we never claimed: a placeholder GitHub created when the wiki
# was enabled, or a page that fell off the manifest. Publishing or deleting either one silently would
# be a surprise, so report both and let a human decide (prune with: git -C $MIRROR rm <file>).
patterns=()
for page in "${pages[@]}"; do patterns+=(-e "$page"); done
extra=$(git -C "$MIRROR" ls-files | grep -vxF "${patterns[@]}" || true)
untracked=$(git -C "$MIRROR" ls-files --others --exclude-standard | grep -vxF "${patterns[@]}" || true)
if [ -n "$extra$untracked" ]; then
  echo "note: files in the render tree that this manifest does not publish:" >&2
  if [ -n "$extra" ]; then
    printf '%s\n' "$extra" | sed 's|^|  tracked:   |' >&2
  fi
  if [ -n "$untracked" ]; then
    printf '%s\n' "$untracked" | sed 's|^|  untracked: |' >&2
  fi
  echo "  (left alone; a page that fell off the manifest keeps rendering until someone removes it)" >&2
fi

if [ -z "$BRANCH" ]; then
  BRANCH=$(git -C "$MIRROR" symbolic-ref --short HEAD 2>/dev/null || echo master)
fi
echo "== $REMOTE ($BRANCH) =="
git -C "$MIRROR" status --porcelain
restore_mirror() {
  # A check/dry-run that leaves files copied or staged would make the next real run abort with
  # "mirror clone is dirty", which reads like a repository problem instead of a tool problem.
  for page in "${pages[@]}"; do
    git -C "$MIRROR" reset -q -- "$page" 2>/dev/null || true
    if git -C "$MIRROR" ls-files --error-unmatch "$page" >/dev/null 2>&1; then
      git -C "$MIRROR" checkout -- "$page"
    else
      rm -f "$MIRROR/$page"
    fi
  done
}

if [ -z "$(git -C "$MIRROR" status --porcelain)" ]; then
  if [ $CHECK -eq 1 ]; then
    echo "preview is current: $REMOTE renders exactly the ${#pages[@]} page(s) in $MANIFEST"
    echo "  render HEAD $(git -C "$MIRROR" rev-parse --short HEAD)"
    exit 0
  fi
  echo "nothing to mirror: the render tree already matches the manifest"
  exit 0
fi
git -C "$MIRROR" diff
git -C "$MIRROR" diff --cached --stat

if [ $CHECK -eq 1 ]; then
  restore_mirror
  { echo "preview is BEHIND the draft: the live wiki does not render the pages at $(git -C "$ROOT" rev-parse --short HEAD)"
    echo "  render HEAD is $(git -C "$MIRROR" rev-parse --short HEAD); the diff above is what publishing would change"
    echo "  the standing rule (Q-14) is that every push to the draft is published with it; run tools/publish.sh,"
    echo "  or tools/mirror-wiki.sh on its own, then re-run this check."
    echo "  If the diff above is a page someone edited in the wiki web UI, decide first whether that edit"
    echo "  belongs in the repo - the wiki is the output, the repo is the source."
  } >&2
  exit 1
fi

if [ $DRY -eq 1 ]; then
  echo "--dry-run: stopped before commit/push (message would have been: $MSG)"
  restore_mirror
  echo "--dry-run: $MIRROR restored to $(git -C "$MIRROR" rev-parse --short HEAD)"
  exit 0
fi

git -C "$MIRROR" commit -m "$MSG"
git -C "$MIRROR" push origin "$BRANCH"
echo "published $(git -C "$MIRROR" rev-parse --short HEAD) -> $REMOTE"
