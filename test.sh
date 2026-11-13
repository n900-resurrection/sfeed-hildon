TEST_NAME=sfeed-hildon
need_pkg sfeed-hildon
ok in-path sh -c 'command -v sfeed-hildon'
ok desktop-entry test -r /usr/share/applications/hildon/sfeed-hildon.desktop
ok sfeed-tools sh -c 'test -x /opt/sfeed/bin/sfeed_update && test -x /opt/sfeed/bin/sfeed_xmlenc'
ok hildonlite-new sh -c '/opt/python3/bin/python3 -c "import hildonlite; hildonlite.ListView, hildonlite.PannableArea, hildonlite.TextView, hildonlite.Dialog"'
ok data-side sh -c 'cd /opt/sfeed-hildon && SFEEDHILDON_DIR=/home/user/.sfeed-hildon-test /opt/python3/bin/python3 -c "
import sfeed_hildon as S
S.ensure_rc(); S.add_feed(\"t\", \"https://example.org/x\"); assert S.read_rc() == [(\"t\", \"https://example.org/x\")]
assert S.to_text(\"<p>a</p><ul><li>b</li></ul>\") == \"a\n\n• b\"
"; r=$?; rm -rf /home/user/.sfeed-hildon-test; exit $r'
ok browser-dbus sh -c 'command -v dbus-send'
# The screens of the GUI were checked in the emulator (make hildon-run APP=sfeed-hildon); see README.md.
summary
