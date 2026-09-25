"""Nieuws-story slide (1080x1920) in Thijs' eigen story-stijl: zwart vlak, witte Nunito Sans, gecentreerd.

Cloudversie van Marketing Agent/scripts/nieuws_story_slide.py (die gebruikt Avenir Next, alleen op de Mac).

Gebruik:
    from nieuws_story_slide import maak_slide
    maak_slide(kop, samenvatting, todo, bron, "/pad/uit.png")
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
ZWART = (10, 10, 10)
WIT = (245, 245, 245)
FONT = str(Path(__file__).resolve().parent.parent / "fonts" / "NunitoSans.ttf")
REG, MED = 400, 500      # gewichten: Regular, Medium
MARGE = 96


def _font(size, gewicht=REG):
    f = ImageFont.truetype(FONT, size)
    f.set_variation_by_axes([gewicht, 100, 12, 500])   # wght, wdth, opsz, YTLC
    return f


def _wrap(d, tekst, font, breedte):
    regels = []
    for alinea in tekst.split("\n"):
        woorden = alinea.split()
        regel = ""
        for w in woorden:
            proef = (regel + " " + w).strip()
            if d.textlength(proef, font=font) <= breedte:
                regel = proef
            else:
                regels.append(regel); regel = w
        regels.append(regel)
    return regels


def maak_slide(kop, samenvatting, todo, bron, uit):
    img = Image.new("RGB", (W, H), ZWART)
    d = ImageDraw.Draw(img)
    breedte = W - 2 * MARGE
    blokken = [
        (kop, _font(64, MED), 82),
        (samenvatting, _font(54), 70),
        ("Wat kun jij doen?", _font(54, MED), 70),
        (todo, _font(54), 70),
    ]
    gerenderd = []
    totaal = 0
    for tekst, font, lh in blokken:
        regels = _wrap(d, tekst, font, breedte)
        gerenderd.append((regels, font, lh))
        totaal += len(regels) * lh + 60
    y = (H - totaal) // 2
    laatste = y
    for regels, font, lh in gerenderd:
        for r in regels:
            w = d.textlength(r, font=font)
            d.text(((W - w) / 2, y), r, font=font, fill=WIT)
            y += lh
        laatste = y
        y += 60
    f_bron = _font(34)
    t = f"Bron: {bron}"
    d.text(((W - d.textlength(t, font=f_bron)) / 2, H - 150), t, font=f_bron, fill=(150, 150, 150))
    img.save(uit)
    return laatste   # y-positie onder de laatste tekstregel; moet onder 1650 blijven
