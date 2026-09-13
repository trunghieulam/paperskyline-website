#!/usr/bin/env bash
# Re-renders every icon and the social card from brand/export/*.html. Run after changing the mark.
set -eu
cd "$(dirname "$0")/.."
CHROME="${CHROME_PATH:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
shot() {  # shot <wrapper> <WxH> <output>
  "$CHROME" --headless=new --hide-scrollbars --force-device-scale-factor=1 \
    --virtual-time-budget=8000 --default-background-color=00000000 \
    --window-size="$2" --screenshot="$3" "file://$(pwd)/brand/export/$1" 2>/dev/null
  echo "$3"
}
shot app-icon.html        1024,1024 brand/app-icon-1024.png
shot og-image.html        1200,630  brand/og-image-1200x630.png
shot apple-touch-icon.html 180,180  apple-touch-icon.png
shot favicon-32.html        32,32   favicon-32.png
