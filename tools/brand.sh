#!/usr/bin/env bash
# Renders favicon-32.png from favicon.svg. The painted images come from tools/art.py.
set -eu
cd "$(dirname "$0")/.."
CHROME="${CHROME_PATH:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
"$CHROME" --headless=new --hide-scrollbars --force-device-scale-factor=1 \
  --virtual-time-budget=8000 --window-size=32,32 --screenshot=favicon-32.png \
  "file://$(pwd)/brand/export/favicon-32.html" 2>/dev/null
echo favicon-32.png
