#!/bin/bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PUBLIC_REMOTE="${PUBLIC_REMOTE:-public}"
PUBLIC_BRANCH="${PUBLIC_BRANCH:-main}"
TEMP_BRANCH="push-to-public-$(date +%Y%m%d-%H%M%S)"

usage() {
  echo "Usage: $0 <commit-ish>..."
  echo "  Cherry-picks infrastructure commits from the private fork"
  echo "  to the public template repo, with personal data audit gate."
  echo
  echo "  <commit-ish>  One or more commits to cherry-pick (SHA, branch, tag)"
  echo
  echo "Example:"
  echo "  $0 HEAD~2..HEAD      # cherry-pick last 2 commits"
  echo "  $0 abc1234 def5678    # cherry-pick specific commits"
  exit 1
}

[ $# -ge 1 ] || usage

if ! git remote get-url "$PUBLIC_REMOTE" &>/dev/null; then
  echo "ERROR: Remote '$PUBLIC_REMOTE' not found. Add it first:"
  echo "  git remote add $PUBLIC_REMOTE git@github.com:dallman2/ai-job-search.git"
  exit 1
fi

echo "Fetching $PUBLIC_REMOTE/$PUBLIC_BRANCH..."
git fetch "$PUBLIC_REMOTE" "$PUBLIC_BRANCH"

ORIGINAL_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Stashing working tree (including untracked files)..."
git stash push --include-untracked -m "push-to-public temp stash" 2>/dev/null || true
echo "Creating temp branch: $TEMP_BRANCH"
git checkout -b "$TEMP_BRANCH" "$PUBLIC_REMOTE/$PUBLIC_BRANCH"

echo "Cherry-picking: $@"
if ! git cherry-pick "$@"; then
  echo "ERROR: Cherry-pick conflict. Abort with:"
  echo "  git cherry-pick --abort"
  echo "  git checkout $ORIGINAL_BRANCH && git branch -D $TEMP_BRANCH"
  echo "  git stash pop"
  exit 1
fi

# Strip original commit author — replace with noreply for public repo
GIT_AUTHOR_NAME="dallman2" GIT_AUTHOR_EMAIL="dallman2@users.noreply.github.com" \
GIT_COMMITTER_NAME="dallman2" GIT_COMMITTER_EMAIL="dallman2@users.noreply.github.com" \
git -c user.name="dallman2" -c user.email="dallman2@users.noreply.github.com" \
  filter-branch -f --env-filter '
    export GIT_AUTHOR_NAME="dallman2"
    export GIT_AUTHOR_EMAIL="dallman2@users.noreply.github.com"
    export GIT_COMMITTER_NAME="dallman2"
    export GIT_COMMITTER_EMAIL="dallman2@users.noreply.github.com"
  ' "$PUBLIC_REMOTE/$PUBLIC_BRANCH..HEAD" 2>/dev/null

echo
echo "Running personal data audit..."
if ! bash scripts/audit-personal-data.sh; then
  echo
  echo "=== AUDIT FAILED ==="
  echo "Personal data detected in cherry-picked changes."
  echo "Aborting push. Cleaning up."
  git checkout "$ORIGINAL_BRANCH"
  git branch -D "$TEMP_BRANCH"
  git stash pop 2>/dev/null || true
  exit 1
fi

echo
echo "Audit passed. Pushing to $PUBLIC_REMOTE/$PUBLIC_BRANCH..."
git push "$PUBLIC_REMOTE" "$TEMP_BRANCH:$PUBLIC_BRANCH"

git checkout "$ORIGINAL_BRANCH"
git branch -D "$TEMP_BRANCH"
git stash pop 2>/dev/null || true

echo
echo "Done. Pushed to $PUBLIC_REMOTE/$PUBLIC_BRANCH."
