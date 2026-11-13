#!/bin/bash
# Draw the icons of sfeed-hildon with ImageMagick: icons/48.png and 64.png (the orange feed symbol on a dark rounded square).
# The PNGs are committed; run this only to change the design.
set -euo pipefail
cd "$(dirname "$0")"
# ImageMagick writes the creation time into the PNG: without these options every run changes the files although the picture is the same.
convert() { command convert +set date:create +set date:modify -define png:exclude-chunk=date,time "$@"; }
mkdir -p icons
# the two arcs of the symbol around the point at the bottom left: radius 70 and 130 (drawn as arcs of circles centred on the point)
convert -size 256x256 xc:none -fill '#26323f' -draw 'roundrectangle 8,8 247,247 44,44' \
  -fill '#f28c28' -stroke none -draw 'circle 72,184 72,208' \
  -fill none -stroke '#f28c28' -strokewidth 22 -draw 'arc -10,102 154,266 -90,0' -draw 'arc -80,32 224,336 -90,0' \
  icons/256.png
for s in 64 48; do convert icons/256.png -resize ${s}x${s} icons/$s.png; done
rm -f icons/256.png
