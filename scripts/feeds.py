"""Nieuwsfeeds ophalen en de items van de afgelopen N uur tonen.

Gebruik:
    python3 scripts/feeds.py 24     # of 48
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


def items(uren):
    nu = datetime.now(timezone.utc)
    for naam, url in FEEDS:
        try:
            root = ET.fromstring(haal(url).encode())
        except Exception as e:
            print(f"FEED-FOUT {naam}: {e}")
            continue
        for it in root.iter("item"):
            try:
                d = email.utils.parsedate_to_datetime(it.findtext("pubDate"))
            except Exception:
                continue
            h = (nu - d).total_seconds() / 3600
            if h <= uren:
                print(f"{naam} | {h:.0f}u | {d.astimezone().strftime('%d-%m')} | {it.findtext('title')} | {it.findtext('link')}")
    p = Path(__file__).resolve().parent.parent / "state" / "geplaatst.json"
    if p.exists():
        print("AL GEPLAATST:", "; ".join(f"{x['datum']} {x['kop']}" for x in json.loads(p.read_text())[-30:]))


def tekst(url):
    t = haal(url, 30)
    ps = re.findall(r"<p[^>]*>(.*?)</p>", t, re.S)
    uit = [html.unescape(re.sub(r"<[^>]+>", "", p)).strip() for p in ps]
    print("\n".join(o for o in uit if len(o) > 30)[:6000])


if __name__ == "__main__":
    if sys.argv[1] == "tekst":
        tekst(sys.argv[2])
    else:
        items(float(sys.argv[1]))
