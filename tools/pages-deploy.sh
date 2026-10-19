#!/usr/bin/env bash
# Deploys the committed tree (HEAD) and its Functions to the Cloudflare Pages project paperskyline-site.
# Outward-facing: needs the user's OK. Credentials go from the Keychain into wrangler's environment only.
# Usage: tools/pages-deploy.sh [branch]   (default: the current git branch; main is the production branch)
set -euo pipefail
cd "$(dirname "$0")/.."
PROJECT="${PAGES_PROJECT:-paperskyline-site}"
branch="${1:-$(git rev-parse --abbrev-ref HEAD)}"
sha="$(git rev-parse HEAD)"
msg="$(git log -1 --format=%s)"

keychain() { security find-generic-password -s "$1" -w; }
wrangler() {
  CLOUDFLARE_API_TOKEN="$(keychain paperskyline-cloudflare)" CLOUDFLARE_ACCOUNT_ID="$(keychain paperskyline-cloudflare-account)" \
    CI=1 npm exec --yes --package=wrangler@4 -- wrangler "$@"
}

[ -z "$(git status --porcelain)" ] || echo "note: uncommitted changes are not deployed, only $sha"
# A clean export, like GitHub Pages' branch root: no tools/.tmp shots or wrangler state ride along.
out="$(mktemp -d)"; trap 'rm -rf "$out"' EXIT
git archive HEAD | tar -x -C "$out"

if ! wrangler pages project list 2>/dev/null | grep -q " $PROJECT "; then
  wrangler pages project create "$PROJECT" --production-branch main
fi
cd "$out"
wrangler pages deploy . --project-name "$PROJECT" --branch "$branch" --commit-hash "$sha" --commit-message "$msg"
