"""Fictional demo data for the emulator (make hildon-run APP=sfeed-hildon): python3 make_demo.py DIR"""
import os, sys, time
d = sys.argv[1]
os.makedirs(os.path.join(d, "feeds"), exist_ok=True)
now = int(time.time())
open(os.path.join(d, "sfeedrc"), "w").write("""sfeedpath="$HOME/.sfeed/feeds"
feeds() {
	feed 'Example Tech News' 'https://example.org/tech.xml'
	feed 'The Garden Podcast' 'https://example.org/garden.rss'
	feed 'Old Maps Blog' 'https://example.org/maps.atom'
}
""")
def line(ago, title, link, content, ctype="html", author="", enc=""):
    return "\t".join([str(now - ago), title, link, content, ctype, link, author, enc, ""]) + "\n"
open(os.path.join(d, "feeds", "Example Tech News"), "w").write(
    line(600, "A 2009 phone learns TLS 1.3", "https://example.org/tech/1", "<p>Hobbyists ported a modern TLS library to an old smartphone.</p>\\n<ul><li>cross-compiled with a custom toolchain</li><li>packaged as .deb</li></ul><p>More in the full article.</p>", author="Alex Example") +
    line(86400 * 2, "Small tools beat big apps", "https://example.org/tech/2", "<p>Why small command line tools are still popular.</p>") +
    line(86400 * 40, "An older story", "https://example.org/tech/3", "Plain text of an older story.", ctype="plain"))
open(os.path.join(d, "feeds", "The Garden Podcast"), "w").write(
    line(3600 * 5, "Episode 12: Tomatoes in November", "https://example.org/garden/12", "<p>Can you still grow tomatoes indoors?</p>", author="Sam Sample", enc="https://example.org/garden/12.mp3|audio/mpeg") +
    line(86400 * 9, "Episode 11: Compost", "https://example.org/garden/11", "<p>Everything about compost.</p>", enc="https://example.org/garden/11.mp3|audio/mpeg"))
open(os.path.join(d, "urls"), "w").write("https://example.org/tech/2\n")
