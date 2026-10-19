#!/usr/bin/env bash
# Structural rules for paperskyline.org. Usage: tools/check.sh [page.html …]  (no args = every page)
set -o nounset
cd "$(dirname "$0")/.."
pages=("$@"); [ ${#pages[@]} -eq 0 ] && pages=( *.html cities/index.html cities/*/index.html world/index.html world/*/index.html world/*/*/index.html
  devlog/*/index.html {zh-Hans,id}/index.html {zh-Hans,id}/cities/index.html {zh-Hans,id}/cities/*/index.html {zh-Hans,id}/world/index.html {zh-Hans,id}/world/*/index.html {zh-Hans,id}/world/*/*/index.html )
fail=0
discord=$(python3 -c "import sys; sys.path.insert(0, 'tools'); from i18n import DISCORD; print(DISCORD)")
err() { echo "FAIL $1: $2"; fail=1; }

for p in "${pages[@]}"; do
  [ -f "$p" ] || { err "$p" "missing"; continue; }
  dir=$(dirname "$p")
  grep -q '<html lang="' "$p" || err "$p" "no <html lang>"
  for needle in 'name="viewport"' 'name="description"' 'property="og:title"' 'property="og:description"' \
                'property="og:image"' 'name="twitter:card"' 'rel="canonical"' 'rel="icon"' 'rel="manifest"'; do
    grep -q "$needle" "$p" || err "$p" "missing $needle"
  done

  # Zero-JS, JSON-LD excepted, plus exactly one inline script (tools/gift.js) on the two gift pages.
  nscripts=$(grep -oiE '<script[^>]*>' "$p" | grep -viEc 'type="application/ld\+json"')
  case "$p" in
    index.html|dragon.html)
      expect="<script>$(python3 -c "print(open('tools/gift.js',encoding='utf-8').read().strip(),end='')")</script>"
      [ "$nscripts" -eq 1 ] && grep -qF -- "$expect" "$p" || err "$p" "the one allowed script must be tools/gift.js, byte for byte"
      grep -qF "script-src '$(cat tools/gift.sha256)'" "$p" || err "$p" "CSP script-src hash missing or stale (tools/gift.sha256)"
      grep -qF 'connect-src https://paperskyline-stats.paperskyline-stats.workers.dev"' "$p" || err "$p" "CSP connect-src missing"
      ;;
    *) [ "$nscripts" -eq 0 ] || err "$p" "executable <script>: the site is zero-JS (JSON-LD and the gift script excepted)" ;;
  esac

  python3 -c 'import json,re,sys; [json.loads(b) for b in re.findall(r"<script type=\"application/ld\+json\">(.*?)</script>", open(sys.argv[1], encoding="utf-8").read(), re.S)]' "$p" 2>/dev/null \
    || err "$p" "JSON-LD that does not parse"
  grep -qiE 'lorem|TODO|TBD' "$p" && err "$p" "placeholder text"
  grep -q '—' "$p" && err "$p" "em dash in copy: use a period, comma, colon or | instead"
  grep -qE 'https://www\.paperskyline\.org' "$p" && err "$p" "www host — the apex is canonical"
  sed -n '/<footer class="site-footer">/,/<\/footer>/p' "$p" | grep -qF "href=\"$discord\"" \
    || err "$p" "footer without the Discord link (tools/i18n.py DISCORD; re-run tools/cities.py after a swap)"

  # Google Play is live; the App Store badge stays an unlinked placeholder until iOS ships.
  grep -qE '<a[^>]*class="badge"' "$p" && err "$p" "App Store badge links before the iPhone version is published"
  grep -oE '<a[^>]*class="store-link"[^>]*>' "$p" | grep -vqF 'href="https://play.google.com/store/apps/details?id=paperskyline.org&amp;referrer=' \
    && err "$p" "store link that is not the Play listing"
  # Play Console counts the site's installs per page and slot only through this referrer.
  grep -oE '<a[^>]*href="https://play\.google\.com[^"]*"' "$p" | grep -vqE 'href="https://play\.google\.com/store/apps/details\?id=paperskyline\.org&amp;referrer=utm_source%3Dsite%26utm_medium%3D[a-z_]+%26utm_campaign%3D[a-z0-9_]+"$' \
    && err "$p" "Play link without the UTM referrer (utm_source=site, utm_medium=<page>, utm_campaign=<slot>)"

  # Claims the copy may not make until they are real (design spec §5).
  grep -qiE 'free to play|no purchases ever|launches (in|on) ' "$p" && err "$p" "price or release-date claim"

  while read -r tag; do
    for a in alt width height; do echo "$tag" | grep -q " $a=" || err "$p" "img without $a: $tag"; done
  done < <(grep -oE '<img[^>]*>' "$p")

  # Inline SVG is the site's art: every one needs an accessible name or an explicit hide.
  while read -r tag; do
    echo "$tag" | grep -qE 'aria-hidden="true"|role="img"' || err "$p" "svg without role=img or aria-hidden: $tag"
  done < <(grep -oE '<svg[^>]*>' "$p")

  while read -r ref; do
    ref="${ref%%\?*}"
    case "$ref" in
      /) target="index.html" ;;
      /*) target=".$ref" ;;
      *) target="$dir/$ref" ;;
    esac
    [ -e "$target" ] || err "$p" "broken link: $ref"
  done < <( { grep -oE '(href|src)="[^"#]+"' "$p" | sed -E 's/^(href|src)="//; s/"$//'
               grep -oE 'srcset="[^"]+"' "$p" | sed -E 's/^srcset="//; s/"$//' | tr ',' '\n' | awk '{print $1}'; } \
           | grep -vE '^(https?:|mailto:|tel:|//)' | sort -u)
done

# hreflang: every alternate is a built page whose own set matches, and the set includes the page's canonical.
python3 - "${pages[@]}" <<'PY' || fail=1
import re, sys
def alts(f):
    s = open(f, encoding='utf-8').read()
    return dict(re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)">', s)), re.search(r'rel="canonical" href="([^"]+)"', s)
bad = 0
for p in sys.argv[1:]:
    a, canon = alts(p)
    if not a:
        continue
    if canon and canon.group(1) not in a.values():
        print(f'FAIL {p}: hreflang set misses its own canonical'); bad = 1
    for lang, u in a.items():
        f = '.' + u.removeprefix('https://paperskyline.org') + ('index.html' if u.endswith('/') else '')
        try:
            back, _ = alts(f)
        except FileNotFoundError:
            print(f'FAIL {p}: hreflang {lang} points at a missing page {u}'); bad = 1; continue
        if back != a:
            print(f'FAIL {p}: hreflang {lang} page {u} does not list the same alternates back'); bad = 1
sys.exit(bad)
PY

# sitemap.xml is an index of one sitemap per page type; every row must be a live, indexable page.
for sm in $(grep -oE 'https://paperskyline\.org/sitemap-[a-z-]+\.xml' sitemap.xml | sed 's#https://paperskyline.org/##'); do
  [ -f "$sm" ] || { err sitemap.xml "missing $sm"; continue; }
  while read -r u; do
    f=".${u#https://paperskyline.org}"; [ "${f%/}" = "$f" ] || f="${f}index.html"
    [ "$f" = "./index.html" ] || [ -f "$f" ] || { err "$sm" "no page for $u"; continue; }
    grep -q 'name="robots" content="noindex' "$f" && err "$sm" "noindex page listed: $u"
  done < <(grep -oE '<loc>[^<]+' "$sm" | sed 's/<loc>//')
done
for f in sitemap.xml sitemap-*.xml robots.txt; do
  grep -qE 'https://www\.paperskyline\.org' "$f" && err "$f" "www host — the apex is canonical"
done
grep -q 'paperskyline.org' CNAME || err CNAME "wrong domain"

# feed.xml: Atom with the required elements, every entry a built devlog page.
python3 - <<'PY' || fail=1
import os, sys, xml.etree.ElementTree as ET
A = '{http://www.w3.org/2005/Atom}'
root, bad = ET.parse('feed.xml').getroot(), []
for el in [root] + root.findall(A + 'entry'):
    bad += [f'{el.findtext(A + "id")}: no {k}' for k in ('id', 'title', 'updated') if not el.findtext(A + k)]
if root.find(A + 'author') is None:
    bad.append('feed: no author')
for e in root.findall(A + 'entry'):
    u = e.findtext(A + 'id').removeprefix('https://paperskyline.org/')
    if not os.path.isfile(u + 'index.html'):
        bad.append(f'{u}: no page')
[print(f'FAIL feed.xml: {b}') for b in bad]
sys.exit(1 if bad else 0)
PY

# Weight budget: every image is exported sized for its slot, so none should ever be large.
for f in brand/*.png brand/*.jpg *.png img/*; do
  [ -f "$f" ] || continue
  s=$(wc -c < "$f" | tr -d ' '); [ "$s" -le 300000 ] || err "$f" "over 300 KB ($s bytes)"
done

# Markup validity. First run downloads html-validate (needs network).
npx --yes html-validate@8 "${pages[@]}" || fail=1

[ $fail -eq 0 ] && echo "check.sh: OK (${#pages[@]} pages)"
exit $fail
