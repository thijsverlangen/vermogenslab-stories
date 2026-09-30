"""Update-story van de vermogensplanner (IG en FB): nieuwe live updates vinden en de story renderen.

Bron: de publieke changelog op https://vermogenslab.nl/updates. Die pagina is een React-app; de
changelog zit als array {datum, titel, punten} in een van de JS-bestanden onder /assets. Alleen wat
daar staat is echt live (de dev-branch telt niet).

Stijl zoals Thijs' eigen update-story van 30 sep 2026: zwart vlak, witte tekst, links uitgelijnd,
een lettertype zonder vet, alleen het woord VERMOGENSLAB groter, alles tussen y=280 en y=1560.

Gebruik:
    python3 update_story.py check                 # JSON: live-lijst, laatst geplaatst, nieuwe entries
    python3 update_story.py render tekst.json uit.png
        tekst.json = {"blokken": ["Nieuw in de planner op vermogenslab.nl.", "zin", ...]}
        drukt "OK onderkant <y>" af, of stopt met exit 2 als de tekst niet in de veilige zone past.
"""
import json, re, sys, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state" / "update_story.json"
FONT = str(ROOT / "fonts" / "NunitoSans.ttf")
BRONNEN = ["https://vermogenslab.nl/updates/", "https://app.vermogenslab.nl/"]

W, H = 1080, 1920
ZWART, WIT = (0, 0, 0), (255, 255, 255)
TEKST, GROOT, REGEL, MARGE = 46, 72, 62, 90
BOVEN, ONDER = 280, 1560
CTA = "Stuur me een DM met VERMOGENSLAB en je krijgt de link."


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (vermogenslab-stories)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def _str(s):
    """Maakt een JS-string of template-literal leesbaar (escapes weg)."""
    return re.sub(r"\\(.)", r"\1", s)


LIT = r"(`(?:[^`\\]|\\.)*`|\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*')"
ENTRY = re.compile(r"\{datum:" + LIT + r",titel:" + LIT + r",punten:\[(.*?)\]\}", re.S)


def _parse(js):
    items = []
    for m in ENTRY.finditer(js):
        datum, titel = _str(m.group(1)[1:-1]), _str(m.group(2)[1:-1])
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", datum):
            continue
        punten = [_str(p[1:-1]) for p in re.findall(LIT, m.group(3))]
        items.append({"datum": datum, "titel": titel, "punten": punten})
    return items


def changelog():
    """Live changelog, nieuwste eerst. Probeert eerst vermogenslab.nl/updates, dan de app."""
    fouten = []
    for bron in BRONNEN:
        try:
            html = _get(bron)
            basis = re.match(r"https://[^/]+", bron).group(0)
            te_doen = [basis + p for p in re.findall(r'src="(/assets/[^"]+\.js)"', html)]
            gezien = set()
            while te_doen:
                url = te_doen.pop(0)
                if url in gezien or len(gezien) > 40:
                    continue
                gezien.add(url)
                js = _get(url)
                items = _parse(js)
                if len(items) >= 3:
                    return sorted(items, key=lambda i: i["datum"], reverse=True), url
                te_doen += [basis + "/assets/" + n for n in re.findall(r'assets/([A-Za-z0-9_.-]+\.js)', js)]
                te_doen += [basis + "/assets/" + n for n in re.findall(r'["`]\./([A-Za-z0-9_.-]+\.js)["`]', js)]
            fouten.append(f"{bron}: geen changelog in {len(gezien)} bestanden")
        except Exception as e:
            fouten.append(f"{bron}: {e}")
    raise RuntimeError("; ".join(fouten))


def check():
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    laatste = state.get("laatste_datum", "")
    items, bron = changelog()
    nieuw = [i for i in items if i["datum"] > laatste]
    return {"bron": bron, "live_nieuwste": items[0]["datum"], "laatste_geplaatst": laatste,
            "aantal_live": len(items), "nieuw": nieuw}


def f(size):
    fnt = ImageFont.truetype(FONT, size)
    fnt.set_variation_by_axes([500, 100, 12, 500])   # Medium, zoals Avenir Next Medium lokaal
    return fnt


def _afbreken(d, tekst, breedte):
    regels, huidig = [], ""
    for w in tekst.split():
        test = (huidig + " " + w).strip()
        if d.textlength(test, font=f(TEKST)) <= breedte or not huidig:
            huidig = test
        else:
            regels.append(huidig)
            huidig = w
    return regels + ([huidig] if huidig else [])


def _cta_regels(d, breedte):
    regels, huidig = [], []
    for w in CTA.split():
        test = huidig + [w]
        breed = sum(d.textlength(x + " ", font=f(GROOT if x.strip(".,") == "VERMOGENSLAB" else TEKST)) for x in test)
        if breed > breedte and huidig:
            regels.append(huidig)
            huidig = [w]
        else:
            huidig = test
    return regels + [huidig]


def render(blokken, uit):
    img = Image.new("RGB", (W, H), ZWART)
    d = ImageDraw.Draw(img)
    breedte = W - 2 * MARGE
    regels = []
    for zin in blokken:
        regels += _afbreken(d, zin, breedte)
        regels.append("")
    cta = _cta_regels(d, breedte)
    hoog = sum(REGEL if r else REGEL // 2 for r in regels) + int(GROOT * 1.25) * len(cta)
    if hoog > ONDER - BOVEN:
        return None
    y = BOVEN + ((ONDER - BOVEN) - hoog) // 2
    for r in regels:
        if r:
            d.text((MARGE, y), r, font=f(TEKST), fill=WIT)
        y += REGEL if r else REGEL // 2
    for regel in cta:
        x = MARGE
        for woord in regel:
            groot = woord.strip(".,") == "VERMOGENSLAB"
            fnt = f(GROOT if groot else TEKST)
            off = 0 if groot else int(GROOT * 0.78 - TEKST * 0.78)
            d.text((x, y + off), woord, font=fnt, fill=WIT)
            x += d.textlength(woord + " ", font=fnt)
        y += int(GROOT * 1.25)
    img.save(uit)
    return y


if __name__ == "__main__":
    if sys.argv[1:2] == ["check"]:
        print(json.dumps(check(), ensure_ascii=False, indent=1))
    elif sys.argv[1:2] == ["render"]:
        blokken = json.loads(Path(sys.argv[2]).read_text())["blokken"]
        y = render(blokken, sys.argv[3])
        if y is None:
            print("TE LANG: maak de zinnen korter of laat er een weg")
            sys.exit(2)
        print("OK onderkant", y)
    else:
        print(__doc__)
