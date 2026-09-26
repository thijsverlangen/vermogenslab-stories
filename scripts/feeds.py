"""Nieuwsfeeds ophalen en de items van de afgelopen N uur tonen.

Gebruik:
    python3 scripts/feeds.py 24     # of 48; haalt de feeds direct op (werkt alleen als de nieuwssites bereikbaar zijn)
    python3 scripts/feeds.py tinyfish <bestand> 24   # zelfde lijst uit een TinyFish fetch_content-resultaat (format "html")
    python3 scripts/feeds.py tekst <url>   # alle <p>-tekst van een artikel
Onderwerpen die al in state/geplaatst.json staan worden onderaan getoond, zodat je ze kunt overslaan.
"""
import email.utils, html, json, re, subprocess, sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

FEEDS = [("NOS", "https://feeds.nos.nl/nosnieuwseconomie"), ("NU.nl", "https://www.nu.nl/rss/Economie"),
         ("AD", "https://www.ad.nl/economie/rss.xml"), ("RTL", "https://www.rtl.nl/nieuws/economie/rss.xml"),
         ("De Telegraaf", "https://www.telegraaf.nl/financieel/rss")]


def haal(url, timeout=20):
    r = subprocess.run(["curl", "-sL", "-m", str(timeout), "-A", "Mozilla/5.0", url], capture_output=True)
    if r.returncode:
        raise RuntimeError(f"curl-fout {r.returncode}")
    return r.stdout.decode("utf-8", "ignore")


def _veld(item_xml, tag):
    m = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", item_xml, re.S | re.I)
    if not m:
        return ""
    t = re.sub(r"^<!\[CDATA\[|\]\]>$", "", m.group(1).strip())
    return html.unescape(re.sub(r"<[^>]+>", "", html.unescape(t))).strip()


def _link(item_xml):
    """Sommige bronnen (TinyFish html-fetch) verliezen de <link>-tags omdat <link> in HTML
    een voidelement is; de URL blijft dan als kale tekst tussen de andere tags staan."""
    link = _veld(item_xml, "link")
    if link:
        return link
    kaal = re.sub(r"<title.*?</title>", "", item_xml, flags=re.S | re.I)
    kaal = re.sub(r"<description.*?</description>", "", kaal, flags=re.S | re.I)
    m = re.search(r"https?://[^\s<]+", kaal)
    return m.group(0) if m else ""


def druk_items(naam, xml, uren, nu):
    """Print de items uit een RSS-tekst die binnen `uren` vallen; tolerant voor kapotte XML."""
    n = 0
    for item_xml in re.findall(r"<item[ >].*?</item>", xml, re.S):
        try:
            d = email.utils.parsedate_to_datetime(_veld(item_xml, "pubDate"))
        except Exception:
            continue
        h = (nu - d).total_seconds() / 3600
        if h <= uren:
            n += 1
            print(f"{naam} | {h:.0f}u | {d.astimezone().strftime('%d-%m')} | {_veld(item_xml, 'title')} | {_link(item_xml)}")
    return n


def geplaatst():
    p = Path(__file__).resolve().parent.parent / "state" / "geplaatst.json"
    if p.exists():
        print("AL GEPLAATST:", "; ".join(f"{x['datum']} {x['kop']}" for x in json.loads(p.read_text())[-30:]))


def items(uren):
    nu = datetime.now(timezone.utc)
    for naam, url in FEEDS:
        try:
            druk_items(naam, haal(url), uren, nu)
        except Exception as e:
            print(f"FEED-FOUT {naam}: {e}")
    geplaatst()


def items_tinyfish(pad, uren):
    """Leest een opgeslagen TinyFish fetch_content-resultaat (format html) van de vijf feed-URL's."""
    nu = datetime.now(timezone.utc)
    ruw = Path(pad).read_text()
    try:
        data = json.loads(ruw)
        if isinstance(data, list):   # soms als lijst van content-blokken opgeslagen
            data = json.loads(next(x["text"] for x in data if x.get("type") == "text"))
        resultaten = data.get("results", [])
    except Exception:
        resultaten = []
    per_url = {r.get("url", "").rstrip("/"): r.get("text", "") for r in resultaten}
    for naam, url in FEEDS:
        tekst = per_url.get(url.rstrip("/"))
        if tekst is None:
            print(f"FEED-FOUT {naam}: niet in TinyFish-resultaat")
            continue
        xml = html.unescape(tekst)   # het html-formaat geeft de RSS als ge-escapete tekst
        if druk_items(naam, xml, uren, nu) == 0 and "<item" not in xml:
            print(f"FEED-FOUT {naam}: geen items in TinyFish-resultaat")
    geplaatst()
def tekst(url):
    t = haal(url, 30)
    ps = re.findall(r"<p[^>]*>(.*?)</p>", t, re.S)
    uit = [html.unescape(re.sub(r"<[^>]+>", "", p)).strip() for p in ps]
    print("\n".join(o for o in uit if len(o) > 30)[:6000])


if __name__ == "__main__":
    if sys.argv[1] == "tekst":
        tekst(sys.argv[2])
    elif sys.argv[1] == "tinyfish":
        items_tinyfish(sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 24)
    else:
        items(float(sys.argv[1]))
