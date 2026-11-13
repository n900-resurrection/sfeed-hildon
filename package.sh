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
cat > "$STAGE/DEBIAN/postinst" <<'EOT'
#!/bin/sh
# One crontab line (every 30 minutes: "sfeed-hildon --cron" does nothing unless the background update is switched on in the application, its
# interval has elapsed and the phone is online). When no other job of the system runs crond (ical-sync has one), a job for it is made.
# A failure here must not break the installation.
case "$1" in configure)
    mkdir -p /var/spool/cron/crontabs
    CT=/var/spool/cron/crontabs/user
    [ -f "$CT" ] && grep -v "sfeed-hildon" "$CT" > "$CT.new" || : > "$CT.new"
    echo '*/30 * * * * HOME=/home/user /opt/sfeed-hildon/sfeed-hildon --cron >/dev/null 2>&1   # sfeed-hildon' >> "$CT.new"
    chmod 600 "$CT.new"; mv "$CT.new" "$CT"
    if ! grep -ls "crond" /etc/event.d/* 2>/dev/null | grep -v "/sfeed-hildon-cron$" | grep -q .; then
        cat > /etc/event.d/sfeed-hildon-cron <<'EOJ'
description "sfeed-hildon: cron for the background update of the feeds"
author "elPytel"
start on started xomap
stop on stopped xomap
console none
respawn
exec /bin/busybox crond -f -c /var/spool/cron/crontabs -L /dev/null
EOJ
        initctl start sfeed-hildon-cron >/dev/null 2>&1 || true
    fi ;;
esac
exit 0
EOT
cat > "$STAGE/DEBIAN/prerm" <<'EOT'
#!/bin/sh
case "$1" in remove) [ -f /etc/event.d/sfeed-hildon-cron ] && initctl stop sfeed-hildon-cron >/dev/null 2>&1 || true ;; esac
exit 0
EOT
cat > "$STAGE/DEBIAN/postrm" <<'EOT'
#!/bin/sh
# Remove: the crontab line and our own cron job go, the settings and the downloaded feeds stay (~/.sfeed).
CT=/var/spool/cron/crontabs/user
case "$1" in remove|purge)
    [ -f "$CT" ] && { grep -v "sfeed-hildon" "$CT" > "$CT.new" || true; mv "$CT.new" "$CT"; chmod 600 "$CT"; }
    rm -f /etc/event.d/sfeed-hildon-cron ;;
esac
exit 0
EOT
chmod 755 "$STAGE/DEBIAN/postinst" "$STAGE/DEBIAN/prerm" "$STAGE/DEBIAN/postrm"
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
feeds (the list is ~/.sfeed/sfeedrc, shared with the terminal reader sfeed-reader), imports OPML and remembers what was read in the file that sfeed_markread uses.
A job with cron (every 30 minutes, only when the phone is online already) can update the feeds in the background; the interval is set in the application.
Upstream: this project (MIT)."
debpack_build
