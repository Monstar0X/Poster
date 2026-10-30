"""Style 17 - "Nova Mono" (layout: Swordsmith2.jpg).  Single-character PNG between two diagonal bands, cover card,
"Why to watch" card, gallery thumbnail, slanted button.  No PNG -> album poster cut by the band."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))) if "__file__" in globals() else None
from nova_kit import *  # noqa

INK, GREY, DARK = (22, 22, 26), (92, 92, 100), (56, 56, 62)


def render(meta, art, button="WATCH NOW", character=None):
    art = art or default_art((120, 120, 130))
    cv = Cv((250, 250, 251))
    cv.poly([(0, 0), (500, 0), (190, 720), (0, 720)], (238, 238, 240))
    cv.poly([(560, 0), (760, 0), (440, 720), (250, 720)], (66, 66, 72))
    cv.poly([(760, 0), (820, 0), (500, 720), (440, 720)], (255, 255, 255))
    cv.poly([(820, 0), (960, 0), (640, 720), (500, 720)], (226, 226, 230))
    if character is not None:
        cv.cutout(character, (520, 30, 1000, 720), ax=0.5, grow=1.05)
    else:
        cv.photo(art, (470, 0, 1010, 720), poly=[(640, 0), (1010, 0), (870, 720), (500, 720)], focus=(0.5, 0.18))
        cv.gradient((470, 560, 1010, 720), (250, 250, 251), (250, 250, 251), False, 0, 235)
    nf = font("Poppins-Bold.ttf", 8)
    for i, t in enumerate(("HOME", "EPISODE", "REVIEWS")):
        cv.text(1040 + i * 66, 30, t, nf, INK, "lm")
    cv.text(44, 124, (meta.get("studio") or "Anime"), font("Poppins-Medium.ttf", 11), INK)
    f, ls, sz = fit_title(meta["title"], "Poppins-Bold.ttf", 380, 30, 20, 3)
    y = cv.lines(44, 146, ls, f, INK, sz * 1.2)
    cv.text(44, y + 14, "Synopsis:", font("Poppins-Bold.ttf", 11.5), INK, "lm")
    cv.para(44, y + 34, meta.get("desc", ""), font("Poppins-Regular.ttf", 10), GREY, 300, 8, 17)
    cv.rrect((44, 596, 168, 668), 6, fill=(30, 30, 34))
    cv.photo(art, (48, 600, 164, 664), r=4, focus=(0.4, 0.3))
    cv.play(106, 632, 14, fill=(255, 255, 255, 225))
    cv.poly([(168, 596), (260, 596), (292, 668), (168, 668)], DARK)
    cv.text(190, 624, "GALLERY", font("Poppins-Bold.ttf", 8), (255, 255, 255), "lm", track=1)
    cv.rrect((190, 646, 214, 647.5), 0, fill=(255, 255, 255))
    cv.shadow((1066, 150, 1224, 356), 4, blur=12, opacity=120)
    cv.rrect((1060, 144, 1230, 362), 3, fill=(20, 20, 24))
    cv.photo(art, (1066, 150, 1224, 356), r=2, focus=(0.5, 0.2))
    cv.poly([(1010, 420), (1280, 420), (1280, 520), (1010, 520), (1030, 470)], DARK)
    cv.text(1090, 440, "Why to watch", font("Poppins-Bold.ttf", 11), (255, 255, 255), "lm")
    cv.text(1090, 476, " · ".join((meta.get("genres") or ["Anime"])[:3]), font("Poppins-Regular.ttf", 9), (225, 225, 230), "lm")
    cv.text(1090, 496, "Score " + score_text(meta), font("Poppins-Regular.ttf", 9), (225, 225, 230), "lm")
    cv.poly([(1030, 600), (1280, 600), (1280, 650), (1010, 650)], DARK)
    cv.text(1140, 625, button, font("Poppins-Bold.ttf", 11), (255, 255, 255), "mm")
    return cv.finish()
