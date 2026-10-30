"""Style 3 - "Nova Quotes" (layout: Nova3.jpg).  ONE big banner image, full-bleed, no panel on top of it - only a dark
fade on the text side, a thin red slash, red / white title, quote line, thumbnails, red badge.  Uses: AniList banner."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))) if "__file__" in globals() else None
from nova_kit import *  # noqa

RED = (226, 36, 46)


def render(meta, art, button="WATCH NOW", character=None):
    art = art or default_art((60, 60, 70))
    cv = Cv((20, 20, 24))
    cv.backdrop(art, dark=0.12, focus=(0.6, 0.3))
    cv.gradient((0, 0, 820, 720), (8, 8, 12), (8, 8, 12), True, 235, 0)
    cv.gradient((0, 560, 1280, 720), (8, 8, 12), (8, 8, 12), False, 0, 170)
    cv.poly([(838, 0), (862, 0), (610, 720), (586, 720)], (*RED, 230))
    # nav
    nf = font("Poppins-Medium.ttf", 10)
    for i, t in enumerate(("HOME", "STORY", "WALLPAPERS")):
        cv.text(390 + i * 62 + (14 if i == 2 else 0), 54, t, nf, (240, 240, 244), "lm")
    cv.pill(590, 40, "QUOTES", font("Poppins-Bold.ttf", 9.5), fill=(255, 255, 255), ink=RED, h=24, padx=14)
    for dy in (44, 52, 60):
        cv.rrect((1210, dy, 1240, dy + 3), 1.5, fill=(255, 255, 255, 235))
    cv.rrect((60, 90, 1240, 91), 0, fill=(255, 255, 255, 70))
    # title
    f, ls, sz = fit_title(meta["title"], "Poppins-ExtraBold.ttf", 640, 66, 30, 2, upper=True)
    y = 150
    for i, ln in enumerate(ls):
        if len(ls) == 1 and " " in ln:
            a, b = ln.split(" ", 1)
            cv.text(70, y, a, f, RED)
            cv.text(70 + tw(f, a + " "), y, b, f, (255, 255, 255))
        else:
            cv.text(70, y, ln, f, RED if i == 0 else (255, 255, 255))
        y += sz * 1.1
    desc = meta.get("desc", "")
    q = (desc.split(". ")[0].rstrip(".") + ".") if desc else ""
    y = cv.para(70, y + 20, "“" + q + "”", font("Poppins-MediumItalic.ttf", 15), (235, 235, 240), 560, 4, 26)
    cv.text(70, y + 8, "- " + (meta.get("studio") or "Anime"), font("Poppins-Medium.ttf", 12), (200, 200, 208))
    # left arrow, next button, thumbnails
    cv.ellipse((16, 340, 48, 372), fill=(255, 255, 255), outline=RED, width=1.5)
    cv.text(32, 355, "‹", font("Poppins-Bold.ttf", 18), RED, "mm")
    by = 520
    bx = cv.button(70, by, button + "  ›", font("Poppins-Bold.ttf", 12), (255, 255, 255), ink=RED, h=44, padx=24, r=10)
    for i, fx in enumerate((0.15, 0.8)):
        x0 = bx + 26 + i * 122
        cv.photo(art, (x0, by - 8, x0 + 108, by + 54), r=2, focus=(fx, 0.4))
        cv.rrect((x0, by - 8, x0 + 108, by + 54), 2, outline=(255, 255, 255, 200), width=1.2)
    cv.rrect((1020, 596, 1220, 654), 12, fill=(255, 255, 255, 235))
    cv.text(1120, 625, (meta.get("studio") or "ANIME").upper()[:16], font("Poppins-ExtraBold.ttf", 13), RED, "mm")
    cv.text(70, 650, " · ".join(meta.get("genres", [])[:3]).upper(), font("Poppins-Medium.ttf", 10), (200, 200, 208), track=1)
    return cv.finish()
