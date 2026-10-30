"""Style 11 - "Nova Dark": black page, left column with title / dark synopsis box / gradient button, tall poster panel
on the right.   Layout: Nova6.jpg.  Uses: AniList poster."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))) if "__file__" in globals() else None
from nova_kit import *  # noqa


def render(meta, art, button="WATCH NOW"):
    art = art or default_art((50, 40, 70))
    cv = Cv((12, 12, 14))
    cv.photo(art, (800, 0, 1280, 720), focus=(0.5, 0.2))
    cv.gradient((800, 0, 960, 720), (12, 12, 14), (12, 12, 14), True, 255, 0)
    cv.rrect((780, -40, 830, 760), 0, fill=(12, 12, 14))
    cv.text(630, 62, (meta.get("genres") or ["Anime"])[0].upper(), font("Poppins-Bold.ttf", 10), (255, 255, 255), "rm", track=1)
    cv.rrect((570, 74, 630, 76), 1, fill=(160, 90, 255))
    f, ls, sz = fit_title(meta["title"], "Poppins-Bold.ttf", 600, 52, 28, 3, upper=True)
    y = cv.lines(60, 176, ls, f, (255, 255, 255), sz * 1.14)
    # synopsis box
    box_y = y + 24
    lines = wrap(meta.get("desc", ""), font("Poppins-Medium.ttf", 11), 548, 6)
    bh = 36 + len(lines) * 19
    cv.rrect((60, box_y, 640, box_y + bh), 14, fill=(34, 34, 40))
    cv.lines(76, box_y + 18, lines, font("Poppins-Medium.ttf", 11), (232, 232, 238), 19)
    by = min(box_y + bh + 28, 600)
    # gradient button
    bf = font("Poppins-Bold.ttf", 12.5)
    w = tw(bf, button) + 56
    cv.grad_pill((60, by, 60 + w, by + 40), (86, 116, 255), (190, 90, 255))
    cv.text(60 + w / 2, by + 20.5, button, bf, (255, 255, 255), "mm")
    cv.ellipse((60, 650, 92, 682), outline=(255, 255, 255), width=1.5)
    cv.text(104, 666, (meta.get("studio") or "Anime")[:20], font("Poppins-Medium.ttf", 10.5), (220, 220, 225), "lm")
    return cv.finish()
