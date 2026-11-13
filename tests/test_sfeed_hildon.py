"""Host tests of the data side of sfeed-hildon (no GUI, no network): python3 -I tests/test_sfeed_hildon.py"""
import os, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
os.environ["SFEEDHILDON_DIR"] = tmp = tempfile.mkdtemp(prefix="sfeed-hildon-test-")
os.environ["SFEEDHILDON_BIN"] = "/nonexistent"
import sfeed_hildon as S

fails = []


def ok(cond, what):
    print(("ok    " if cond else "FAIL  ") + what)
    if not cond:
        fails.append(what)


# --- sfeedrc ---
os.makedirs(S.DIR, exist_ok=True)
open(S.RC, "w").write("""# comment
sfeedpath="$HOME/.sfeed/feeds"
fetch() { curl "$2"; }
feeds() {
    feed "alpha" "https://example.org/a.xml"
    #feed "off" "https://example.org/off.xml"
    feed 'It'\\''s news' 'https://example.org/n.rss' https://example.org
}
""")
ok(S.read_rc() == [("alpha", "https://example.org/a.xml"), ("It's news", "https://example.org/n.rss")], "sfeedrc: feeds read, comments skipped, shell quoting understood")
S.add_feed("Beta/feed", "https://example.org/b.atom")
rc = open(S.RC).read()
ok(rc.index("Beta/feed") < rc.index("\n}\n") and "fetch()" in rc, "a feed is added inside feeds(), the rest of the file is kept")
ok(S.read_rc()[-1] == ("Beta/feed", "https://example.org/b.atom"), "the added feed reads back")
try:
    S.add_feed("alpha", "https://example.org/x")
    ok(False, "a duplicate name is refused")
except ValueError:
    ok(True, "a duplicate name is refused")
S.add_feed("It's a \"test\"", "https://example.org/q?a=1&b=$2")
ok(("It's a \"test\"", "https://example.org/q?a=1&b=$2") in S.read_rc(), "quotes and $ in a name or URL survive")
S.remove_feed("Beta/feed")
ok(all(n != "Beta/feed" for n, _ in S.read_rc()) and len(S.read_rc()) == 3, "a feed is removed")

# --- items ---
os.makedirs(S.FEEDS, exist_ok=True)
now = int(time.time())
open(S.feed_path("alpha"), "w").write(
    "%d\tOld one\thttps://example.org/1\t<p>First&nbsp;item</p>\\n<ul><li>one</li><li>two</li></ul>\thtml\tid1\tJane Doe\t\t\n" % (now - 86400 * 400) +
    "%d\tNewest\thttps://example.org/3\tplain text\\twith tab and \\\\ backslash\tplain\tid3\t\thttps://example.org/a.mp3|audio/mpeg\tnews\n" % now +
    "%d\tMiddle\thttps://example.org/2\t<b>bold</b> <script>x=1</script>text\thtml\tid2\t\t\t\n" % (now - 3600))
items = S.load_items("alpha")
ok([i["title"] for i in items] == ["Newest", "Middle", "Old one"], "items are sorted, newest first")
ok(items[0]["content"] == "plain text\twith tab and \\ backslash", "escapes \\n \\t \\\\ of a field are undone in one pass")
ok(items[0]["enclosure"].startswith("https://example.org/a.mp3"), "the enclosure is kept")
ok(S.load_items("nothing") == [], "a feed that was never downloaded has no items")

# --- read state ---
ok(S.counts(["alpha"]) == {"alpha": (3, 3)}, "all items are unread at first")
ok(S.mark_read(["https://example.org/3", "https://example.org/3"]) == 1, "a link is remembered once")
ok(S.mark_read(["https://example.org/3"]) == 0, "marking again adds nothing")
ok(S.counts(["alpha"]) == {"alpha": (2, 3)}, "the unread count goes down")
ok([i["title"] for i in S.unread_items(["alpha"])] == ["Middle", "Old one"], "unread items of all feeds")
ok(open(S.URLS).read() == "https://example.org/3\n", "the url file has one link per line (sfeed_markread format)")

# --- text ---
t = S.to_text(items[2]["content"], "html")
ok(t.splitlines()[0] == "First item" and "• one" in t and "• two" in t, "html: paragraphs, no-break space and list items")
ok(S.to_text(items[1]["content"], "html") == "bold text", "html: tags and script content removed")
ok(S.to_text("a  b\n\n\n\nc", "plain") == "a b\n\nc", "plain text: blanks squeezed")
ok(S.to_text("<p>unclosed <b>tag", "html") == "unclosed tag", "broken html does not fail")
a = S.article_text(items[0])
ok("alpha" in a and "Audio/file: https://example.org/a.mp3" in a and a.rstrip().endswith("Link: https://example.org/3"), "the article text has the feed, the audio link and the link")

# --- dates ---
ok(S.when(now, now) == time.strftime("%H:%M", time.localtime(now)), "today: the time")
ok(S.when(now - 86400 * 400, now).count(".") == 2 and str(time.localtime(now - 86400 * 400).tm_year) in S.when(now - 86400 * 400, now), "an older year: with the year")

# --- OPML ---
opml = os.path.join(tmp, "feeds.opml")
open(opml, "w").write("""<?xml version="1.0"?><opml version="1.0"><head><title>x</title></head><body>
<outline text="Folder"><outline text="Tech" title="Tech Blog" type="rss" xmlUrl="https://example.org/tech.xml" htmlUrl="https://example.org"/>
<outline text="alpha" type="rss" xmlUrl="https://example.org/other-alpha.xml"/></outline>
<outline text="Same address" xmlUrl="https://example.org/a.xml"/><outline text="No address"/></body></opml>""")
ok(S.parse_opml(opml) == [("Tech Blog", "https://example.org/tech.xml"), ("alpha", "https://example.org/other-alpha.xml"), ("Same address", "https://example.org/a.xml")], "OPML: nested outlines, title before text, outlines without an address skipped")
before = len(S.read_rc())
added, skipped = S.import_opml(opml)
names = [n for n, _u in S.read_rc()]
ok(added == 2 and skipped == 1, "OPML import: new feeds added, a known address skipped (%d added, %d skipped)" % (added, skipped))
ok("alpha (2)" in names and "Tech Blog" in names, "OPML import: a taken name gets a number")
try:
    bad = os.path.join(tmp, "bad.opml"); open(bad, "w").write("<html>not opml")
    S.import_opml(bad); ok(False, "OPML import: a file that is not OPML is refused")
except ValueError:
    ok(True, "OPML import: a file that is not OPML is refused")

# --- the page for the browser ---
pg = open(S.write_page(items[1])).read()
ok("<h2>Middle</h2>" in pg and "<b>bold</b>" in pg and "https://example.org/2" in pg, "a page for the browser holds the title, the html of the item and the link")
pg = open(S.write_page(items[0])).read()
ok("a.mp3" in pg and "<pre" in pg, "a plain text item is shown preformatted, with the audio link")

# --- background update (cron) ---
S.LAST = os.path.join(tmp, "hildon.last")
ran = []
ok(S.background_minutes() == 0 and S.cron_run(is_online=lambda: True, run=lambda: ran.append(1) or True) == "off" and not ran, "background update is off by default: cron does nothing")
S.set_background_minutes(180)
ok(S.background_minutes() == 180, "the interval is stored")
ok(S.cron_run(is_online=lambda: False, run=lambda: True) == "offline", "no connection: nothing")
ok(S.cron_run(is_online=lambda: True, run=lambda: ran.append(1) or True) == "updated" and ran == [1], "due and online: the feeds are updated")
ok(S.cron_run(is_online=lambda: True, run=lambda: ran.append(1) or True) == "not due" and ran == [1], "the interval has not elapsed: nothing")
ok(S.cron_run(now=time.time() + 181 * 60, is_online=lambda: True, run=lambda: ran.append(1) or True) == "updated" and ran == [1, 1], "after the interval: updated again")
os.utime(S.LAST, (0, 0))
ok(S.cron_run(is_online=lambda: True, run=lambda: False) == "failed" and S.last_update() == 0, "a failed update does not move the time of the last update")
open(S.PIDFILE, "w").write(str(os.getpid()))
ok(not S.running_update(), "a pid file of a process that is not sfeed_update is ignored")
S.set_background_minutes(0)

# --- rc creation and update command ---
os.remove(S.RC)
S.ensure_rc()
ok("feeds() {" in open(S.RC).read() and S.read_rc() == [], "no sfeedrc: a minimal one is made")
S.add_feed("x", "https://example.org/x")
ok(S.read_rc() == [("x", "https://example.org/x")], "a feed can be added to the minimal sfeedrc")
ok(S.update_command() == ["/nonexistent/sfeed_update", S.RC], "sfeed_update is started with our sfeedrc")
sys.exit(1 if fails else 0)
