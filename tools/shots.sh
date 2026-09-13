#!/usr/bin/env bash
# Renders pages at 500/768/1280 CSS px in light and dark. Usage: tools/shots.sh [page.html …]
# 500 px is this Chrome's layout-width floor, not a real target — write mobile breakpoints >= 500 px.
set -u
cd "$(dirname "$0")/.."
CHROME="${CHROME_PATH:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
pages=("$@"); [ ${#pages[@]} -eq 0 ] && pages=(index.html)
site="tools/.tmp/site"; rm -rf "$site"; mkdir -p "$site" tools/.tmp/shots
cp ./*.html styles.css favicon.svg "$site"/ 2>/dev/null
cp -r brand "$site"/ 2>/dev/null
# Headless Chrome has no prefers-color-scheme switch — promote the dark block to unconditional instead.
sed 's/@media (prefers-color-scheme: dark)/@media all/' styles.css > "$site/styles-dark.css"
for page in "${pages[@]}"; do
  name=$(echo "${page%.html}" | tr '/' '_')
  for theme in light dark; do
    src="$site/$page"
    if [ "$theme" = dark ]; then
      sed -E 's#href="styles\.css"#href="styles-dark.css"#' "$src" > "${src%.html}.dark.html"
      src="${src%.html}.dark.html"
    fi
    for w in 500 768 1280; do
      "$CHROME" --headless=new --hide-scrollbars --force-device-scale-factor=1 \
        --virtual-time-budget=6000 --window-size="$w,5200" \
        --screenshot="tools/.tmp/shots/$name-$w-$theme.png" "file://$(pwd)/$src" 2>/dev/null
    done
  done
  ls -1 tools/.tmp/shots/"$name"-*
done
