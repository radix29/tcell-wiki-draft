#!/usr/bin/env bash
# Q-14 as one command: publish the render preview and push the draft, in that order.
#
# Why mirror before push, when the rule is "every push runs the mirror": CI's preview gate
# (.github/workflows/qa.yml -> tools/mirror-wiki.sh --check) clones the live render wiki and compares
# it to the pushed commit, and CI starts the moment a push lands. Mirror first and that gate sees a
# preview that already matches the commit under test. Push first and the two race, CI reports a stale
# preview for no real problem, and a gate people learn to ignore is worse than no gate.
#
# If the mirror succeeds and the push then fails (network, auth, a non-ff from someone else's push),
# the preview is ahead of origin by text that is committed here and nowhere else. Re-run this script:
# the mirror half becomes a no-op and the push retries. Nothing is lost either way, because the render
# tree is a build output - the repo is the source (AGENTS.md).
#
# Usage:
#   tools/publish.sh                 mirror, then push the current branch, then verify
#   tools/publish.sh master          explicit branch (the wiki convention this repo keeps)
#   PUSH_REMOTE=origin tools/publish.sh
#   FORCE=1 tools/publish.sh         only for mirror-wiki.sh's uncommitted-page guard; see that file
set -euo pipefail

ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
BRANCH=${1:-master}
PUSH_REMOTE=${PUSH_REMOTE:-origin}

case $BRANCH in
  -*)
    echo "refusing '$BRANCH': this script adds no git push flags, and published history is never" \
         "force-pushed, rebased or amended (AGENTS.md, 'Publishing Model')" >&2
    exit 2
    ;;
esac
git -C "$ROOT" rev-parse --verify "$BRANCH" >/dev/null || {
  echo "'$BRANCH' is not a ref in $ROOT" >&2
  exit 2
}

"$ROOT/mirror-wiki.sh"

echo "== push $PUSH_REMOTE $BRANCH =="
git -C "$ROOT" push "$PUSH_REMOTE" "$BRANCH"

echo "== verify the preview matches what just landed =="
"$ROOT/mirror-wiki.sh" --check
