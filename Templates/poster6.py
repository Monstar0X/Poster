"""Style 6 - "Nova Glass" (layout: Nova4.jpg).  Single-character PNG: blurred warm background (the cover), one frosted
panel, the character pops out of the panel on the right, huge title.  No PNG -> the album poster sits in the panel."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))) if "__file__" in globals() else None
from nova_kit import *  # noqa

ORANGE = (255, 150, 30)


def render(meta, art, button="WATCH NOW", character=None):
    art = art or default_art((120, 90, 70))
    cv = Cv((60, 50, 44))
    cv.backdrop(art, dark=0.15, blur=26, tint=(255, 190, 120, 0.18), focus=(0.5, 0.3))
    cv.glass((40, 70, 1240, 670), 44, blur=22, tint=(255, 255, 255, 38), outline=(255, 255, 255, 150), width=1.8)
    nf = font("Poppins-Medium.ttf", 10)
    for i, t in enumerate((">> HOME", "ABOUT", "GALLERY", "CONTACT")):
        cv.text(400 + i * 78, 108, t, nf, ORANGE if i == 3 else (255, 255, 255), "lm")
    if character is not None:
        cv.cutout(character, (700, 0, 1250, 700), ax=0.6, grow=1.0)
    else:
        cv.photo(art, (900, 96, 1196, 560), r=22, focus=(0.5, 0.2))
        cv.rrect((900, 96, 1196, 560), 22, outline=(255, 255, 255, 160), width=1.5)
    f, ls, sz = fit_title(meta["title"], "Anton-Regular.ttf", 640, 108, 54, 2, upper=True)
    y = cv.lines(90, 190, ls, f, (255, 255, 255), sz * 1.0)
    sub = (meta.get("native") or meta.get("studio") or "ANIME").upper()[:36]
    cv.text(92, y + 12, sub, font_for(sub, "Poppins-ExtraBold.ttf", 15), ORANGE, track=2)
    y = cv.para(90, y + 52, meta.get("desc", ""), font("Poppins-Bold.ttf", 11.5), (255, 255, 255), 520, 5, 20)
    cv.button(90, 556, button, font("Poppins-Bold.ttf", 11.5), ORANGE, ink=(40, 24, 8), h=36, padx=22)
    cv.rrect((90, 612, 118, 640), 4, outline=ORANGE, width=1.5)
    cv.text(104, 626, (meta.get("studio") or "A")[0].upper(), font("Poppins-ExtraBold.ttf", 11), ORANGE, "mm")
    cv.text(128, 626, "Part of  " + (meta.get("studio") or "Anime"), font("Poppins-ExtraBold.ttf", 11.5), ORANGE, "lm")
    return cv.finish()
