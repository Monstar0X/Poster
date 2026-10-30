"""Style 2 - "Nova Red": white page, red corner + bottom bar, vertical genre text, red title, framed poster.
Layout: Nova2.jpg (Thumbnail- repo).  Uses: AniList poster."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))) if "__file__" in globals() else None
from nova_kit import *  # noqa

RED, INK, GREY = (238, 38, 44), (20, 20, 24), (96, 98, 108)


def render(meta, art, button="WATCH NOW"):
    art = art or default_art(RED)
    cv = Cv((255, 255, 255))
    cv.poly([(560, 0), (1280, 0), (1280, 60), (700, 60)], RED)
    cv.poly([(650, 60), (710, 60), (680, 14)], (205, 206, 212))
    cv.d.rectangle((0, H - cv.p(14), W, H), fill=RED)
    # dotted chevrons
    for k in range(2):
        for r in range(7):
            for c in range(4):
                if c + r * 0.0 <= 3 - abs(r - 3) and c >= 0:
                    x, y = 270 + k * 66 + c * 9, 40 + r * 9
                    cv.ellipse((x, y, x + 5, y + 5), fill=RED)
    # vertical genres
    vf = font("Poppins-Bold.ttf", 12)
    gs = (meta.get("genres") or ["Anime"])[:3]
    for i, g in enumerate(gs):
        cv.vtext(34, 200 + i * 130, g.upper(), vf, INK, track=3)
    # poster in a framed rounded rect
    cv.rrect((780, 70, 1236, 672), 26, fill=RED)
    cv.photo(art, (790, 80, 1226, 662), r=20, focus=(0.5, 0.25))
    # caption
    capf = font("Poppins-Medium.ttf", 12)
    cap = " ".join(x for x in ((meta.get("season") or "").upper(), str(meta.get("year") or "")) if x) or "ANIME"
    cv.text(110, 198, f"{cap} / {meta.get('eps') or 'N/A'} EPISODE", capf, INK, track=1)
    f, ls, sz = fit_title(meta["title"], "Poppins-ExtraBold.ttf", 620, 62, 30, 2, upper=True)
    y = cv.lines(110, 224, ls, f, RED, sz * 1.1)
    cv.text(110, y + 14, (meta.get("studio") or "ANIME").upper(), font("Poppins-Bold.ttf", 12), INK, track=1)
    y = cv.para(110, y + 50, meta.get("desc", ""), font("Poppins-Regular.ttf", 11.5), GREY, 560, 4, 19)
    bx = cv.button(110, max(y + 22, 520), button, font("Poppins-Bold.ttf", 12), RED, h=40)
    cv.rrect((bx + 18, max(y + 22, 520), bx + 21, max(y + 22, 520) + 40), 1, fill=RED)
    cv.text(bx + 34, max(y + 22, 520) + 20, (meta.get("status") or "ONGOING").upper(), font("Poppins-ExtraBold.ttf", 15), INK, "lm")
    return cv.finish()
