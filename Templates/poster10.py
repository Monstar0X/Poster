"""Style 10 - "Nova Berserk" (layout: Nova5.jpg).  Single-character PNG standing over a red block, white page, red title,
SYNOPSIS line, three genre columns.  No PNG -> the album poster sits in the red slash."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))) if "__file__" in globals() else None
from nova_kit import *  # noqa

RED, INK = (206, 40, 46), (18, 18, 22)


def render(meta, art, button="WATCH NOW", character=None):
    cv = Cv((255, 255, 255))
    if character is not None:
        cv.rrect((800, 470, 1280, 720), 0, fill=RED)
        cv.cutout(character, (690, 24, 1270, 720), ax=0.5, grow=1.0)
    else:
        cv.poly([(840, 150), (1280, 70), (1280, 720), (720, 720)], RED)
        cv.photo(art or default_art(RED), (770, 90, 1250, 690), poly=[(900, 140), (1250, 110), (1250, 690), (800, 690)], focus=(0.5, 0.2))
    cv.rrect((380, 36, 560, 64), 14, fill=RED)
    cv.text(470, 50.5, (meta.get("fmt") or "Anime").title() + " Network", font("Poppins-Medium.ttf", 11), (255, 255, 255), "mm")
    cv.text(600, 50, "Category", font("Poppins-Medium.ttf", 14), (70, 70, 76), "lm", track=1.5)
    cv.text(700, 50, "Anime", font("Poppins-Medium.ttf", 14), RED, "lm")
    for i, c in enumerate((RED, (60, 170, 220), (120, 120, 126))):
        cv.ellipse((772 + i * 14, 46, 780 + i * 14, 54), fill=c)
    f, ls, sz = fit_title(meta["title"], "Poppins-ExtraBold.ttf", 600, 64, 32, 2, upper=True)
    y = cv.lines(330, 150, ls, f, RED, sz * 1.1, "ma")
    cv.text(24, y + 40, "SYNOPSIS", font("Poppins-ExtraBold.ttf", 12), INK, "lm")
    cv.rrect((120, y + 39.5, 600, y + 41), 0, fill=INK)
    cv.ellipse((596, y + 36, 604, y + 44), fill=INK)
    y = cv.para(24, y + 66, meta.get("desc", ""), font("Poppins-Medium.ttf", 14), INK, 590, 6, 25)
    cols = [((meta.get("fmt") or "Anime").title(), (meta.get("genres") or ["Action"])[0]),
            ("x", (meta.get("genres") or ["", "Adventure"])[1] if len(meta.get("genres") or []) > 1 else "Studio"),
            ((meta.get("studio") or "Nova")[:12], (meta.get("genres") or ["", "", "Comedy"])[2] if len(meta.get("genres") or []) > 2 else "Score " + score_text(meta))]
    for i, (a, b) in enumerate(cols):
        cx = 110 + i * 190
        cv.text(cx, 598, a, font("Poppins-Bold.ttf", 11), RED if a != "x" else INK, "mm")
        cv.text(cx, 618, b, font("Poppins-Bold.ttf", 11) if a == "x" else font("Poppins-Regular.ttf", 10.5), INK, "mm")
    cv.button(250, 650, button, font("Poppins-Bold.ttf", 10.5), RED, h=30, padx=20)
    for i in range(3):
        cv.ellipse((560 + i * 14, 700, 568 + i * 14, 708), fill=INK if i == 0 else (190, 190, 196))
    return cv.finish()
