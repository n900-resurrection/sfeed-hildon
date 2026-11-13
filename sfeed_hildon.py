"""sfeed-hildon: the data side of a small RSS/Atom reader for the N900 (no GUI here, so it can be tested on a PC).

The feeds are fetched and parsed by the tools of sfeed (sfeed_update runs curl, so TLS 1.3 works): ~/.sfeed/sfeedrc lists them, the items land in
~/.sfeed/feeds/<name> as lines of tab separated fields (sfeed(5)):
    1 timestamp  2 title  3 link  4 content  5 content-type (html|plain)  6 id  7 author  8 enclosure  9 category
(newlines, tabs and backslashes in the fields are written as \\n, \\t and \\\\). Read items are remembered in ~/.sfeed/urls, one link per line,
the file that sfeed_markread uses, so the terminal reader and this application agree.
"""
import html, html.parser, os, re, shlex, subprocess, time
import xml.etree.ElementTree as ET

DIR = os.environ.get("SFEEDHILDON_DIR") or os.path.join(os.environ.get("HOME", "/home/user"), ".sfeed")
RC = os.path.join(DIR, "sfeedrc")
FEEDS = os.path.join(DIR, "feeds")
URLS = os.path.join(DIR, "urls")
BIN = os.environ.get("SFEEDHILDON_BIN", "/opt/sfeed/bin")

MINIMAL_RC = """# sfeedrc made by sfeed-hildon. Feeds are downloaded by sfeed_update (curl: TLS 1.3, the CA bundle of the curl package).
sfeedpath="$HOME/.sfeed/feeds"

# feed <name> <feedurl> [basesiteurl] [encoding]
feeds() {
}
"""


# ---- the list of feeds (sfeedrc) ----------------------------------------------------------------------------------------------------------

def quote(text):
    return shlex.quote(text)


def read_rc():
    """-> [(name, url)] of the `feed` lines of sfeedrc (shell quoting understood); lines that do not parse are skipped."""
    out = []
    try:
        lines = open(RC, encoding="utf-8").read().splitlines()
    except OSError:
        return out
    for ln in lines:
        if not re.match(r"\s*feed\s", ln):
            continue
        try:
            parts = shlex.split(ln, comments=True)
        except ValueError:
            continue
        if len(parts) >= 3 and parts[0] == "feed":
            out.append((parts[1], parts[2]))
    return out


def _write_rc(text):
    os.makedirs(DIR, exist_ok=True)
    tmp = RC + ".new"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, RC)


def ensure_rc():
    """Create a minimal sfeedrc when there is none."""
    if not os.path.exists(RC):
        _write_rc(MINIMAL_RC)


def add_feed(name, url):
    """Append `feed 'name' 'url'` to the function feeds() of sfeedrc (the first line `}` after `feeds()`). A name that exists already is refused."""
    ensure_rc()
    if any(n == name for n, _ in read_rc()):
        raise ValueError("a feed with that name exists already")
    text = open(RC, encoding="utf-8").read()
    m = re.search(r"^feeds\s*\(\)\s*\{.*?^\}", text, re.S | re.M)
    line = "\tfeed %s %s\n" % (quote(name), quote(url))
    if not m:
        text = text.rstrip("\n") + "\n\nfeeds() {\n%s}\n" % line
    else:
        end = m.end() - 1
        text = text[:end] + line + text[end:]
    _write_rc(text)


def remove_feed(name, delete_items=True):
    """Delete the `feed` lines of that name from sfeedrc (and its downloaded items)."""
    kept = []
    for ln in open(RC, encoding="utf-8").read().splitlines(True):
        if re.match(r"\s*feed\s", ln):
            try:
                p = shlex.split(ln, comments=True)
            except ValueError:
                p = []
            if len(p) >= 2 and p[1] == name:
                continue
        kept.append(ln)
    _write_rc("".join(kept))
    if delete_items:
        try:
            os.remove(feed_path(name))
        except OSError:
            pass


def feed_path(name):
    return os.path.join(FEEDS, name.replace("/", "_"))       # sfeed_update does the same


# ---- items ----------------------------------------------------------------------------------------------------------------------------------

_ESC = re.compile(r"\\([nt\\])")


def unescape(field):
    return _ESC.sub(lambda m: {"n": "\n", "t": "\t", "\\": "\\"}[m.group(1)], field)


def load_items(name):
    """Items of one feed, newest first: dicts with ts, title, link, content, ctype, id, author, enclosure, category, feed."""
    items = []
    try:
        f = open(feed_path(name), encoding="utf-8", errors="replace")
    except OSError:
        return items
    with f:
        for ln in f:
            c = ln.rstrip("\n").split("\t")
            c += [""] * (9 - len(c))
            try:
                ts = int(c[0])
            except ValueError:
                ts = 0
            items.append({"ts": ts, "title": unescape(c[1]) or "(no title)", "link": c[2], "content": unescape(c[3]), "ctype": c[4] or "plain",
                          "id": c[5], "author": unescape(c[6]), "enclosure": c[7], "category": c[8], "feed": name})
    items.sort(key=lambda i: -i["ts"])
    return items


def read_links():
    try:
        return {ln.strip() for ln in open(URLS, encoding="utf-8", errors="replace") if ln.strip()}
    except OSError:
        return set()


def mark_read(links):
    """Remember these links as read (appended to ~/.sfeed/urls, once each)."""
    new = [l for l in dict.fromkeys(links) if l and l not in read_links()]
    if new:
        os.makedirs(DIR, exist_ok=True)
        with open(URLS, "a", encoding="utf-8") as f:
            f.write("".join(l + "\n" for l in new))
    return len(new)


def counts(names=None):
    """{name: (unread, total)} for every feed of sfeedrc (or the given names)."""
    seen = read_links()
    out = {}
    for name in names if names is not None else [n for n, _ in read_rc()]:
        items = load_items(name)
        out[name] = (sum(1 for i in items if i["link"] not in seen), len(items))
    return out


def unread_items(names=None):
    seen = read_links()
    items = []
    for name in names if names is not None else [n for n, _ in read_rc()]:
        items += [i for i in load_items(name) if i["link"] not in seen]
    items.sort(key=lambda i: -i["ts"])
    return items


def when(ts, now=None):
    """Short date: the time today, 'day.month.' this year, 'day.month.year' earlier."""
    now = time.time() if now is None else now
    t, n = time.localtime(ts), time.localtime(now)
    if (t.tm_year, t.tm_yday) == (n.tm_year, n.tm_yday):
        return time.strftime("%H:%M", t)
    if t.tm_year == n.tm_year:
        return "%d.%d." % (t.tm_mday, t.tm_mon)
    return "%d.%d.%d" % (t.tm_mday, t.tm_mon, t.tm_year)


# ---- text of an item -----------------------------------------------------------------------------------------------------------------------

class _Text(html.parser.HTMLParser):
    BLOCK = {"p", "div", "br", "tr", "section", "article", "header", "footer", "blockquote", "pre", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "table"}
    SKIP = {"script", "style", "head", "svg"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.skip, self.links, self.href = [], 0, [], None

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        elif tag in self.BLOCK:
            self.out.append("\n")
        elif tag == "li":
            self.out.append("\n• ")
        elif tag == "a":
            self.href = dict(attrs).get("href")
        elif tag == "img":
            alt = dict(attrs).get("alt")
            if alt:
                self.out.append("[%s]" % alt)

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self.skip = max(0, self.skip - 1)
        elif tag in self.BLOCK:
            self.out.append("\n")
        elif tag == "a":
            self.href = None

    def handle_data(self, data):
        if not self.skip:
            self.out.append(data)


def to_text(content, ctype="html"):
    """Plain text of the content of an item: tags removed, lists and paragraphs kept as lines, blank lines squeezed."""
    if ctype == "html":
        p = _Text()
        try:
            p.feed(content)
            p.close()
        except Exception:
            return re.sub(r"<[^>]*>", "", content)
        text = "".join(p.out)
    else:
        text = content
    text = text.replace(" ", " ")
    text = "\n".join(re.sub(r"[ \t]+", " ", ln).strip() for ln in text.splitlines())
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def article_text(item):
    parts = []
    head = [when(item["ts"])] if item["ts"] else []
    if item["author"]:
        head.append(item["author"])
    head.append(item["feed"])
    parts.append("  ·  ".join(head))
    body = to_text(item["content"], item["ctype"]) if item["content"] else "(no text in the feed)"
    parts.append(body)
    if item["enclosure"]:
        parts.append("Audio/file: " + item["enclosure"].split("|")[0])
    parts.append("Link: " + item["link"])
    return "\n\n".join(parts)


# ---- settings and the update in the background -----------------------------------------------------------------------------------------------

CONF = os.path.join(DIR, "hildon.conf")
LAST = os.path.join(DIR, "hildon.last")            # its modification time: when the feeds were updated the last time
PIDFILE = os.path.join(DIR, "update.pid")          # the sfeed_update that runs now (started by the GUI or by cron)
INTERVALS = [("Off", 0), ("Every hour", 60), ("Every 3 hours", 180), ("Every 6 hours", 360), ("Every 12 hours", 720), ("Every 24 hours", 1440)]


def load_conf():
    conf = {"background_minutes": "0"}
    try:
        for ln in open(CONF, encoding="utf-8"):
            k, sep, v = ln.partition("=")
            if sep and k.strip() in conf:
                conf[k.strip()] = v.strip()
    except OSError:
        pass
    return conf


def background_minutes():
    try:
        return max(0, int(load_conf()["background_minutes"]))
    except ValueError:
        return 0


def set_background_minutes(minutes):
    os.makedirs(DIR, exist_ok=True)
    with open(CONF, "w", encoding="utf-8") as f:
        f.write("# sfeed-hildon: how often cron (every 30 minutes, when the phone is online already) updates the feeds; 0 = never\nbackground_minutes=%d\n" % int(minutes))


def last_update():
    try:
        return os.stat(LAST).st_mtime
    except OSError:
        return 0


def touch_last():
    os.makedirs(DIR, exist_ok=True)
    with open(LAST, "a"):
        pass
    os.utime(LAST, None)


def running_update():
    """True while a sfeed_update started by this program runs (the pid file names it; a stale file is ignored)."""
    try:
        pid = int(open(PIDFILE).read().strip())
        return "sfeed_update" in open("/proc/%d/cmdline" % pid, "rb").read().decode("utf-8", "replace")
    except (OSError, ValueError):
        return False


def online():
    """True when a default route exists (a connection is up); does not touch the connection manager."""
    try:
        with open("/proc/net/route") as f:
            return any(ln.split()[1:2] == ["00000000"] for ln in f.read().splitlines()[1:])
    except OSError:
        return False


def cron_run(now=None, is_online=online, run=None):
    """What cron starts (every 30 minutes): update the feeds when the background update is on, its interval has elapsed, a connection is up and
    no update runs. Returns the reason in a word (for tests and the log)."""
    minutes = background_minutes()
    if not minutes:
        return "off"
    now = time.time() if now is None else now
    if now - last_update() < minutes * 60:
        return "not due"
    if running_update():
        return "running"
    if not is_online():
        return "offline"
    if run is None:
        p = start_update()
        try:
            p.wait(timeout=900)
        except subprocess.TimeoutExpired:
            p.kill()
            return "timeout"
        ok = p.returncode == 0
    else:
        ok = run()
    if ok:
        touch_last()
    return "updated" if ok else "failed"


# ---- fetching and the browser ---------------------------------------------------------------------------------------------------------------

def update_command():
    return [os.path.join(BIN, "sfeed_update"), RC]


def start_update():
    """Start sfeed_update in the background; returns the Popen (poll() is None while it runs). PATH gets the directory of the sfeed tools."""
    ensure_rc()
    os.makedirs(FEEDS, exist_ok=True)
    env = dict(os.environ, PATH=BIN + ":" + os.environ.get("PATH", ""), HOME=os.environ.get("HOME", "/home/user"))
    p = subprocess.Popen(update_command(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
    with open(PIDFILE, "w") as f:
        f.write(str(p.pid))
    return p


def _session_bus():
    """The environment for D-Bus: the session bus address of the user (a program started from a shell by ssh does not have it)."""
    env = dict(os.environ)
    if not env.get("DBUS_SESSION_BUS_ADDRESS"):
        try:
            m = re.search(r"DBUS_SESSION_BUS_ADDRESS='([^']+)'", open("/tmp/session_bus_address.user").read())
            if m:
                env["DBUS_SESSION_BUS_ADDRESS"] = m.group(1)
        except OSError:
            pass
    return env


_children = []


def open_in_browser(url):
    """Ask the browser of the N900 (MicroB) to open an address (a web page or a file:// path) through D-Bus. The call is not waited for
    (a cold start of the browser takes many seconds and the window of this program must not freeze meanwhile); False when it cannot be sent."""
    for c in [c for c in _children if c.poll() is not None]:         # reap the ones that ended
        _children.remove(c)
    env = _session_bus()
    if not env.get("DBUS_SESSION_BUS_ADDRESS"):
        return False
    try:
        _children.append(subprocess.Popen(["dbus-send", "--type=method_call", "--dest=com.nokia.osso_browser", "/com/nokia/osso_browser/request",
                                           "com.nokia.osso_browser.load_url", "string:" + url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env))
        return True
    except OSError:
        return False


PAGES = os.path.join(DIR, "pages")


def write_page(item):
    """A small HTML page of an item in ~/.sfeed/pages (for the browser: pictures, links, kinetic scrolling); returns its path."""
    os.makedirs(PAGES, exist_ok=True)
    for old in sorted(os.listdir(PAGES))[:-40]:                        # keep the last 40 pages only
        try:
            os.remove(os.path.join(PAGES, old))
        except OSError:
            pass
    name = "%d-%d.html" % (int(time.time()), abs(hash(item["link"])) % 100000)
    body = item["content"] if item["ctype"] == "html" else "<pre style='white-space:pre-wrap'>%s</pre>" % html.escape(item["content"])
    meta = html.escape("  \u00b7  ".join(x for x in (when(item["ts"]) if item["ts"] else "", item["author"], item["feed"]) if x))
    enc = ("<p><a href='%s'>Audio/file</a></p>" % html.escape(item["enclosure"].split("|")[0], quote=True)) if item["enclosure"] else ""
    page = ("<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>%s</title></head><body>"
            "<h2>%s</h2><p><small>%s</small></p>%s%s<p><a href='%s'>Open the original page</a></p></body></html>"
            % (html.escape(item["title"]), html.escape(item["title"]), meta, body, enc, html.escape(item["link"], quote=True)))
    path = os.path.join(PAGES, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(page)
    return path


# ---- OPML --------------------------------------------------------------------------------------------------------------------------------

def parse_opml(path):
    """[(name, url)] of the feeds (outline elements with xmlUrl, folders are walked through) in an OPML file; raises ValueError for a file that is not OPML."""
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as e:
        raise ValueError("not an OPML file: %s" % e)
    out = []
    for o in root.iter("outline"):
        url = (o.get("xmlUrl") or o.get("xmlurl") or "").strip()
        if url:
            name = (o.get("title") or o.get("text") or url).strip().replace("\n", " ")
            out.append((name, url))
    return out


def import_opml(path):
    """Add the feeds of an OPML file that are not in sfeedrc yet (by address); a name that is taken gets a number. -> (added, skipped)."""
    ensure_rc()
    have = read_rc()
    urls = {u for _n, u in have}
    names = {n for n, _u in have}
    added = skipped = 0
    for name, url in parse_opml(path):
        if url in urls:
            skipped += 1
            continue
        base, k = name, 2
        while name in names:
            name = "%s (%d)" % (base, k)
            k += 1
        add_feed(name, url)
        urls.add(url)
        names.add(name)
        added += 1
    return added, skipped


def find_opml_files():
    """OPML/XML files in the places where a file lands on the phone (MyDocs, its Documents/Downloads, the home directory)."""
    home = os.environ.get("HOME", "/home/user")
    found = []
    for d in (os.path.join(home, "MyDocs"), os.path.join(home, "MyDocs", ".documents"), os.path.join(home, "MyDocs", "Downloads"), home):
        try:
            for e in sorted(os.scandir(d), key=lambda e: e.name.lower()):
                if e.is_file() and not e.name.startswith(".") and e.name.lower().endswith((".opml", ".xml")) and e.path not in found:
                    found.append(e.path)
        except OSError:
            continue
    return found
