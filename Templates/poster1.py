"""Style 1 - "Nova Blue" (layout: Nova1.jpg).  Single-character PNG: the character stands on a navy blob, name chips,
star row, score bar.  No PNG -> the album poster is cropped into the blob.   render(meta, art, button, character)"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))) if "__file__" in globals() else None
from nova_kit import *  # noqa

NAVY, BLUE, INK, GREY = (28, 44, 128), (60, 92, 230), (22, 26, 52), (110, 116, 140)


def render(meta, art, button="WATCH NOW", character=None):
    cv = Cv((248, 249, 253))
    cv.blob([(560, -40), (1320, -40), (1320, 760), (790, 760), (690, 640), (740, 500), (660, 350), (610, 190)], BLUE)
    cv.blob([(590, -40), (1320, -40), (1320, 760), (810, 760), (720, 640), (770, 500), (690, 350), (640, 190)], NAVY)
    if character is not None:
        cv.cutout(character, (560, 40, 1270, 720), ax=0.55, grow=1.08)
    else:
        cv.photo(art or default_art(NAVY), (700, 60, 1230, 700), r=34, focus=(0.5, 0.2))
    nf = font("Poppins-Bold.ttf", 10)
    for i, t in enumerate(("About", "Characters", "News", "Picture")):
        cv.text(330 + i * 62, 36, t, nf, INK)
    cv.pill(880, 24, meta["title"].lower()[:24], font("Poppins-Medium.ttf", 9.5), fill=(255, 255, 255), ink=GREY, h=28, padx=16)
    pf = font("Poppins-Medium.ttf", 10.5)
    x = cv.pill(44, 96, "about", pf, outline=INK, ink=INK, h=24)
    cv.pill(x + 8, 96, "streaming", pf, fill=NAVY, h=24)
    f, ls, sz = fit_title(meta["title"], "Poppins-Bold.ttf", 430, 46, 26, 3)
    y = cv.lines(44, 140, ls, f, INK, sz * 1.1)
    cv.text(44, y + 8, " ".join(" ".join(g.lower()) for g in (meta.get("genres") or ["anime"])[:1]), font("Poppins-Medium.ttf", 8), GREY, track=0)
    y = cv.para(44, y + 36, meta.get("desc", ""), font("Poppins-Regular.ttf", 10), GREY, 400, 5, 16)
    cv.pill(44, y + 12, "rating", pf, outline=INK, ink=INK, h=22)
    sx = cv.stars(44, y + 52, meta.get("score"), r=12, fill=(247, 170, 40), empty=(205, 208, 220))
    cv.text(46, y + 78, f"{score_text(meta)} ({(meta.get('score') or 0) * 53:,} users)", font("Poppins-Regular.ttf", 9), GREY, "lm")
    # score bar widget
    cv.rrect((44, 590, 340, 640), 12, fill=(255, 255, 255), outline=(205, 208, 225))
    cv.rrect((54, 600, 90, 630), 8, fill=NAVY)
    for i, hh in enumerate((8, 14, 11, 18)):
        cv.rrect((60 + i * 6, 622 - hh, 63 + i * 6, 622), 1, fill=(255, 255, 255))
    cv.rrect((104, 614, 326, 617), 2, fill=(205, 208, 225))
    cv.rrect((104, 614, 104 + 222 * min(1, (meta.get("score") or 0) / 100), 617), 2, fill=NAVY)
    cv.text(44, 664, f"{meta.get('studio') or ''}  ·  {meta.get('year') or ''}  ·  {meta.get('eps') or '—'} eps", font("Poppins-Regular.ttf", 8.5), GREY)
    # name chips on the art
    cf = font("Poppins-Bold.ttf", 11)
    names = (meta.get("chars") or [])[:2] or [(meta.get("genres") or ["Anime"])[0]]
    for i, nm in enumerate(names):
        t = nm.upper()[:16]
        w = tw(cf, t) + 52
        cx = 700 if i == 0 else 1130 - w + 100
        cy = 230 if i == 0 else 480
        cv.rrect((cx, cy, cx + w, cy + 30), 15, fill=NAVY)
        cv.ellipse((cx + w - 26, cy + 5, cx + w - 8, cy + 23), fill=(255, 255, 255))
        cv.text(cx + 16, cy + 15.5, t, cf, (255, 255, 255), "lm")
    cv.button(360, 596, button, font("Poppins-Bold.ttf", 11), BLUE, h=38, padx=22)
    return cv.finish()
