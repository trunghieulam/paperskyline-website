#!/usr/bin/env bash
# Cuts video/reel-206.{mp4,webm} and its poster from the 2.0.6 store clips: silent, 1280x576 (20:9), ~22 s.
# --promo instead writes a full-quality 1920x1080 MP4 (blurred fill above and below) to the media's video/.
# Usage: tools/reel.sh [--promo] [2.0.6 media dir] [game-paper-flights dir]
set -eu
cd "$(dirname "$0")/.."
PROMO=0; [ "${1:-}" = --promo ] && { PROMO=1; shift; }
MEDIA="${1:-../paper-skyline-local-media/docs/store/2.0.6}"
GAME="${2:-../game-paper-flights}"
W=1280 H=576 FPS=30 X=0.4  # X: crossfade seconds
[ $PROMO = 1 ] && W=1920 H=864
TITLE=4

# clip, start, seconds
SHOTS=(
  "v01-paris-throw  0.0  4.0"
  "v04-tokyo-sakura 0.5  4.0"
  "v03-tokyo-kabuki 2.2  5.0"
  "v02-ny-taxi      10.5 3.0"
  "v01-paris-throw  10.5 3.6"
)

tmp=tools/.tmp/reel; mkdir -p "$tmp"
args=() fg="" n=0 len=0 prev=""
for s in "${SHOTS[@]}"; do
  read -r clip ss t <<<"$s"
  args+=(-ss "$ss" -t "$t" -i "$MEDIA/clips/$clip.mp4")
  # delogo paints out the Dynamic Island pill; the crop trims 2868x1320 to 20:9
  fg+="[$n:v]delogo=x=36:y=466:w=122:h=388,crop=2868:1290:0:15,scale=$W:$H:flags=lanczos,fps=$FPS,setsar=1,format=yuv420p,settb=AVTB[v$n];"
  if [ -z "$prev" ]; then prev="v$n" len=$t
  else
    off=$(echo "$len - $X" | bc); fg+="[$prev][v$n]xfade=transition=fade:duration=$X:offset=$off[x$n];"
    prev="x$n" len=$(echo "$len + $t - $X" | bc)
  fi
  n=$((n + 1))
done
# end card: the game's Paris painting under the 2.0 wordmark
args+=(-loop 1 -t "$TITLE" -i "$GAME/Assets/Art/Cities/Paris/paris-background.png"
       -loop 1 -t "$TITLE" -i "$GAME/design/art-source/branding-2-0/export/title/wordmark.png")
fg+="[$n:v]scale=$W:$H:force_original_aspect_ratio=increase,crop=$W:$H,fps=$FPS[bg];[$((n + 1)):v]scale=$((560 * W / 1280)):-1[wm];"
fg+="[bg][wm]overlay=(W-w)/2:(H-h)/2-$((36 * W / 1280)),setsar=1,format=yuv420p,settb=AVTB[title];"
off=$(echo "$len - $X" | bc); fg+="[$prev][title]xfade=transition=fade:duration=$X:offset=$off[out]"

ffmpeg -v error -y "${args[@]}" -filter_complex "$fg" -map "[out]" -an -c:v libx264 -preset slow -crf 12 "$tmp/master-$W.mp4"
if [ $PROMO = 1 ]; then
  out="$MEDIA/video/reel-206-promo-1920x1080.mp4"
  ffmpeg -v error -y -i "$tmp/master-$W.mp4" -filter_complex \
    "[0]split[a][b];[a]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,boxblur=40:2[bg];[bg][b]overlay=0:(H-h)/2,format=yuv420p" \
    -an -c:v libx264 -preset slow -crf 16 -profile:v high -movflags +faststart "$out"
  ls -l "$out"; exit
fi
ffmpeg -v error -y -i "$tmp/master-$W.mp4" -an -c:v libx264 -preset slow -crf 24 -maxrate 2500k -bufsize 5000k \
  -profile:v high -pix_fmt yuv420p -movflags +faststart video/reel-206.mp4
ffmpeg -v error -y -i "$tmp/master-$W.mp4" -an -c:v libvpx-vp9 -crf 36 -b:v 0 -row-mt 1 -deadline good -cpu-used 2 video/reel-206.webm
# poster: the Kabuki Actor's BONK!
ffmpeg -v error -y -ss 9.0 -i "$tmp/master-$W.mp4" -frames:v 1 -q:v 4 video/reel-206-poster.jpg
ls -l video/reel-206*
