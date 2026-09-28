#!/usr/bin/env bash
# Structural rules for paperskyline.org. Usage: tools/check.sh [page.html …]  (no args = every page)
set -o nounset
cd "$(dirname "$0")/.."
pages=("$@"); [ ${#pages[@]} -eq 0 ] && pages=( *.html )
fail=0
err() { echo "FAIL $1: $2"; fail=1; }

for p in "${pages[@]}"; do
  [ -f "$p" ] || { err "$p" "missing"; continue; }
  dir=$(dirname "$p")
  grep -q '<html lang="' "$p" || err "$p" "no <html lang>"
  for needle in 'name="viewport"' 'name="description"' 'property="og:title"' 'property="og:description"' \
                'property="og:image"' 'name="twitter:card"' 'rel="canonical"' 'rel="icon"' 'rel="manifest"'; do
    grep -q "$needle" "$p" || err "$p" "missing $needle"
  done

  # Zero-JS, JSON-LD excepted.
  if grep -oiE '<script[^>]*>' "$p" | grep -viE 'type="application/ld\+json"' | grep -q .; then
    err "$p" "executable <script> — the site is zero-JS (JSON-LD excepted)"
  fi

  grep -qiE 'lorem|TODO|TBD' "$p" && err "$p" "placeholder text"
  grep -qE 'https://www\.paperskyline\.org' "$p" && err "$p" "www host — the apex is canonical"

  # The game is unpublished: the store badges are drawn but must not link anywhere yet.
  # Invert this rule on launch day, when the listings exist.
  grep -qE '<a[^>]*class="badge"' "$p" && err "$p" "store badge links before the game is published"

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

for f in sitemap.xml robots.txt; do
  grep -qE 'https://www\.paperskyline\.org' "$f" && err "$f" "www host — the apex is canonical"
done
grep -q 'paperskyline.org' CNAME || err CNAME "wrong domain"

# Weight budget: every image is exported sized for its slot, so none should ever be large.
for f in brand/*.png brand/*.jpg *.png img/*; do
  [ -f "$f" ] || continue
  s=$(wc -c < "$f" | tr -d ' '); [ "$s" -le 300000 ] || err "$f" "over 300 KB ($s bytes)"
done

# Markup validity. First run downloads html-validate (needs network).
npx --yes html-validate@8 "${pages[@]}" || fail=1

[ $fail -eq 0 ] && echo "check.sh: OK (${#pages[@]} pages)"
exit $fail
