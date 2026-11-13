# sfeed-hildon

A native touch reader for RSS and Atom feeds on the Nokia N900 (Maemo 5), written in Python 3 with [hildonlite](https://github.com/n900-resurrection/hildonlite), on top of [sfeed](https://codemadness.org/sfeed-simple-feed-parser.html).
Why: the stock RSS reader (`osso-rss-feed-reader`) and Feed Circuit download through the OpenSSL 0.9.8 of the phone (TLS 1.0 only) and fail with `tlsv1 alert protocol version` on today's servers. Here the feeds are downloaded by `sfeed_update`, which runs curl 8 (TLS 1.2/1.3).

## Use
- **Feeds** (the main view): buttons **Refresh** and **Add feed** on top, then the list of feeds with the number of new items, and **All unread**. Tap a feed to see its items (a dot marks an unread one; **Mark all read** on top), tap an item to read it.
- **An item:** the buttons on top are **Previous**, **Next**, **Page** (the item as a small page in the browser: pictures, links, kinetic scrolling, the idea comes from Feed Circuit) and **Original** (the address of the item). The text scrolls by finger; the keys Up/Down, Page Up/Down and Space scroll it, Left/Right go to the previous/next item.
- The menu of the title bar: *Import feeds from OPML* (a file `*.opml` or `*.xml` in MyDocs, its Downloads/.documents or the home directory; feeds whose address is known are skipped), *Remove the selected feed*, *Mark everything read*.
- The list of feeds is `~/.sfeed/sfeedrc`, the same file the terminal reader `sfeed-reader` uses; what was read is remembered in `~/.sfeed/urls` (the file of `sfeed_markread`), so both readers agree. A podcast item shows the link of the audio file. Errors and crashes of the program are written to `~/.sfeed/hildon.log`.
- Not done yet: a refresh by cron in the background (a `sfeed_update` line in the crontab, the same pattern as ical-sync), per-feed refresh, folders, images inside the text view (use *Page*). The text of an item is plain text made from the HTML of the feed.

## Files
`sfeed-hildon` (the GUI), `sfeed_hildon.py` (the data side: sfeedrc, the item files, the read state, HTML to text; no GUI, so it is tested on the PC), `tests/` (32 tests, `make -C apps/sfeed-hildon build`; `tests/make_demo.py` makes fictional demo feeds), `test.sh` (tests on the phone), `hildon-run.sh` (emulator: `make hildon-run APP=sfeed-hildon`).
Inside the N900 repository (uses `mk/app.mk`): `make -C apps/sfeed-hildon deb`, install with `make -C apps/sfeed-hildon install`. `make-icon.sh` draws the icons.

Depends on `sfeed` (>= 2.4-1maemo4), `curl`, `python3.11`, `python3-hildonlite` (>= 0.4.0). Licence: MIT.
