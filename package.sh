#!/bin/bash
# Package sfeed-hildon as a .deb for Maemo 5: make -C apps/sfeed-hildon deb
# Output: /project/build/deb/sfeed-hildon_<VERSION>-<REV>_armel.deb
set -euo pipefail
PROJ=/project
. "$PROJ/scripts/debpack.sh"

PKG=sfeed-hildon
VERSION="${VERSION:-0.1}"
STAGE="$PROJ/build/deb/stage-$PKG"
HERE="$PROJ/apps/sfeed-hildon"

rm -rf "$STAGE"
mkdir -p "$STAGE/opt/$PKG" "$STAGE/usr/bin" "$STAGE/usr/share/applications/hildon" "$STAGE/DEBIAN"
install -m 755 "$HERE/sfeed-hildon" "$STAGE/opt/$PKG/"
install -m 644 "$HERE/sfeed_hildon.py" "$STAGE/opt/$PKG/"
for sz in 48 64; do
    mkdir -p "$STAGE/usr/share/icons/hicolor/${sz}x${sz}/apps"
    install -m 644 "$HERE/icons/$sz.png" "$STAGE/usr/share/icons/hicolor/${sz}x${sz}/apps/$PKG.png"
done
ln -s ../../opt/$PKG/sfeed-hildon "$STAGE/usr/bin/sfeed-hildon"
cat > "$STAGE/usr/share/applications/hildon/$PKG.desktop" <<'EOT'
[Desktop Entry]
Encoding=UTF-8
Version=1.0
Type=Application
Name=Feed reader
Icon=sfeed-hildon
Exec=/usr/bin/sfeed-hildon
X-Osso-Type=application/x-executable
EOT

SECTION=user/network
DEPENDS="python3.11, python3-hildonlite (>= 0.4.0), sfeed (>= 2.4-1maemo4), curl"
DISPLAY_NAME="Feed reader"
SHORT_DESC="Native RSS/Atom and podcast feed reader on top of sfeed"
LONG_DESC="A touch reader for RSS and Atom feeds (and the text of podcast episodes). The feeds are downloaded by sfeed_update with curl, so
modern HTTPS servers (TLS 1.2 and 1.3) work, where the stock RSS reader and Feed Circuit fail with a TLS error. The application lists the feeds
with the number of new items, the items of a feed or all unread ones, shows the text of an item, opens its link in the browser, adds and removes
feeds (the list is ~/.sfeed/sfeedrc, shared with the terminal reader sfeed-reader) and remembers what was read in the file that sfeed_markread uses.
Upstream: this project (MIT)."
debpack_build
