"""Style 16 - "Nova Indigo" (layout: Swordsmith01.jpg).  Single-character PNG: big character on a white / indigo diagonal
split, blocky title, tabs, stars, Favorite pill, score ring, episode thumbnails.  No PNG -> album poster on the left."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))) if "__file__" in globals() else None
from nova_kit import *  # noqa

C0, C1 = (62, 84, 232), (118, 84, 228)


def render(meta, art, button="WATCH NOW", character=None):
    art = art or default_art((70, 80, 200))
    cv = Cv((250, 250, 255))
    cv.grad_pill((0, 0, 1280, 720), C0, C1, r=0)
    cv.poly([(0, 0), (420, 0), (250, 720), (0, 720)], (250, 250, 255))
    cv.poly([(420, 0), (470, 0), (300, 720), (250, 720)], (200, 205, 250, 150))
    if character is not None:
        cv.cutout(character, (-40, 30, 640, 720), ax=0.3, grow=1.12)
    else:
        cv.photo(art, (0, 0, 560, 720), poly=[(0, 0), (560, 0), (420, 720), (0, 720)], focus=(0.5, 0.15))
    x0 = 660
    pf = font("Poppins-Medium.ttf", 8.5)
    x = x0
    for t in ((meta.get("genres") or ["Anime"])[:3]):
        x = cv.pill(x, 40, t, pf, outline=(255, 255, 255, 170), ink=(255, 255, 255), h=18, padx=10) + 6
    f, ls, sz = fit_title(meta["title"], "Poppins-ExtraBold.ttf", 560, 50, 28, 2, upper=True)
    y = cv.lines(x0, 78, ls, f, (255, 255, 255), sz * 1.08)
    tf = font("Poppins-Bold.ttf", 8.5)
    x = x0
    for i, t in enumerate(("SYNOPSIS", "CHARACTER", "GALLERY", "REVIEW")):
        cv.text(x, y + 20, t, tf, (255, 255, 255) if i == 0 else (222, 226, 255), "lm", track=0.6)
        if i == 0:
            cv.rrect((x, y + 30, x + tw(tf, t), y + 31.5), 0, fill=(255, 255, 255))
        x += tw(tf, t) + 22
    y = cv.para(x0, y + 50, meta.get("desc", ""), font("Poppins-Regular.ttf", 9.5), (240, 242, 255), 570, 9, 17)
    cv.stars(x0, y + 22, meta.get("score"), r=9, fill=(255, 255, 255), empty=(150, 160, 245), gap=3)
    cv.rrect((x0, y + 54, x0 + 118, y + 84), 15, fill=(255, 255, 255, 235))
    cv.text(x0 + 59, y + 69, button.title(), font("Poppins-Bold.ttf", 9.5), (70, 80, 220), "mm")
    cv.ellipse((x0 + 270, y + 40, x0 + 340, y + 110), outline=(255, 255, 255), width=2)
    cv.text(x0 + 305, y + 75, score_text(meta), font("Poppins-Bold.ttf", 15), (255, 255, 255), "mm")
    cv.rrect((x0 + 362, y + 52, x0 + 363.5, y + 100), 0, fill=(255, 255, 255, 140))
    cv.text(x0 + 382, y + 66, (meta.get("studio") or "ANIME")[:18], font("Poppins-Bold.ttf", 10.5), (255, 255, 255), "lm")
    cv.text(x0 + 382, y + 86, " · ".join((meta.get("genres") or [])[:2]), font("Poppins-Regular.ttf", 9.5), (230, 232, 255), "lm")
    ey = 590
    cv.text(x0 + 300, ey - 14, "Episode:", font("Poppins-Bold.ttf", 9.5), (255, 255, 255), "lm")
    for i in range(2):
        bx = x0 + 300 + i * 150
        cv.photo(art, (bx, ey, bx + 140, ey + 100), r=12, focus=(0.3 + 0.4 * i, 0.35))
        cv.rrect((bx, ey, bx + 140, ey + 100), 12, fill=(30, 30, 90, 70))
        cv.text(bx + 12, ey + 84, f"EP{i + 1}", font("Poppins-Bold.ttf", 11), (255, 255, 255), "lm")
    return cv.finish()
