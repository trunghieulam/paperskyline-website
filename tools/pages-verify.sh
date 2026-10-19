#!/usr/bin/env bash
# Read-only checks of a Cloudflare Pages deployment against the live GitHub Pages site (docs/ssr-spike.md).
# Usage: tools/pages-verify.sh https://web-ssr-spike.paperskyline-site.pages.dev [https://paperskyline.org]
set -uo pipefail
cd "$(dirname "$0")/.."
B="${1%/}"; G="${2:-https://paperskyline.org}"
C=/usr/bin/curl
fail=0
bad() { echo "FAIL $*"; fail=1; }
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT

# 1. Every page answers 200, at its canonical path or after Pages' one .html → extensionless hop.
pages=( *.html cities/index.html cities/*/index.html world/index.html world/*/index.html world/*/*/index.html )
n=0
for p in "${pages[@]}"; do
  u="/${p%index.html}"
  r=$($C -s -o /dev/null -w '%{http_code} %{num_redirects}' -L "$B$u")
  [ "${r% *}" = 200 ] || [ "$p" = 404.html ] || bad "$u → $r"
  [ "${r#* }" = 0 ] || echo "hop  $u (${r#* } redirect)"
  n=$((n + 1))
done
echo "pages: $n checked"

# 2. The HTML is byte-identical to GitHub Pages.
for u in / /cities/paris/ /cities/tokyo/ /cities/sydney/ /world/europe/france/ /sitemap.xml; do
  $C -s "$B$u" > "$tmp/a"; $C -s "$G$u" > "$tmp/b"
  cmp -s "$tmp/a" "$tmp/b" && echo "same $u ($(wc -c < "$tmp/a" | tr -d ' ') bytes)" || bad "$u differs from $G"
done

# 3. _headers and _redirects.
h=$($C -sI "$B/cities/paris/")
echo "$h" | grep -qi '^x-robots-tag: noindex' || bad "no X-Robots-Tag: noindex on a pages.dev host"
echo "$h" | grep -qi '^x-content-type-options: nosniff' || bad "_headers not applied (nosniff)"
$C -sI "$B/img/mark-96.png" | grep -qi '^cache-control: public, max-age=86400' || bad "_headers /img/* cache rule"
loc=$($C -s -o /dev/null -w '%{http_code} %{redirect_url}' "$B/play")
case "$loc" in "302 https://play.google.com/store/apps/details?id=paperskyline.org&referrer=utm_source%3Dsite"*) echo "redirect /play ok";; *) bad "/play → $loc";; esac
[ "$($C -s -o /dev/null -w '%{http_code}' "$B/functions/_page.js")" = 404 ] || bad "Functions source is served as an asset"
[ "$($C -s -o /dev/null -w '%{http_code}' "$B/no-such-page/")" = 404 ] || bad "unknown path is not a 404"

# 4. The no-JS wish flow: a form POST, an HTML answer, no script.
r=$($C -s -w '\n%{http_code}' -d city=Jakarta "$B/api/wish")
[ "${r##*$'\n'}" = 200 ] && echo "$r" | grep -q 'Your wish for <strong>Jakarta</strong>' && ! echo "$r" | grep -qi '<script' \
  && echo "wish ok" || bad "POST /api/wish Jakarta"
[ "$($C -s -o /dev/null -w '%{http_code}' --data-urlencode 'city=<b>x</b>' "$B/api/wish")" = 400 ] || bad "wish accepts markup"
$C -s "$B/cities-live/paris/" | grep -q '<p class="votes">' && echo "votes ok" || bad "/cities-live/paris/ has no vote count"

# 5. Time to first byte, median of 7 fresh connections.
for u in "$B/cities/paris/" "$G/cities/paris/"; do
  for i in 1 2 3 4 5 6 7; do $C -s -o /dev/null -w '%{time_starttransfer}\n' "$u"; done |
    python3 -c 'import sys,statistics as s; print(f"ttfb {sys.argv[1]}: {s.median(map(float, sys.stdin)):.3f} s")' "$u"
done

[ $fail -eq 0 ] && echo "pages-verify: OK"
exit $fail
