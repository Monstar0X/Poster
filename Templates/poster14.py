"""Style 14 - "Nova Pastel Hero": Grand Blue (Nova7) + Golden Boy (Nova8) combined into one.  Album poster on the left,
white page on the right with the top bar (menu, search, avatar), bold title, score + studio row, outlined genre pills +
"Avg Ratings", light caps synopsis, black button + bookmark.  Uses: AniList poster."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))) if "__file__" in globals() else None
from nova_kit import *  # noqa

INK, GREY, LINE = (14, 14, 18), (150, 150, 158), (210, 210, 216)


def render(meta, art, button="WATCH NOW", character=None):
    art = art or default_art((150, 150, 220))
    cv = Cv((255, 255, 255))
    cv.photo(art, (0, 0, 470, 720), focus=(0.5, 0.2))
    tint = accent_of(art, (150, 140, 230))
    cv.tint((0, 0, 470, 720), mix(tint, (255, 255, 255), 0.55), 70)
    cv.gradient((0, 520, 470, 720), (0, 0, 0), (0, 0, 0), False, 0, 230)
    cv.text(30, 692, (meta.get("studio") or "Anime").upper()[:22], font("Poppins-Bold.ttf", 10), (255, 255, 255), "lm", track=1)
    # top bar
    nf = font("Poppins-Bold.ttf", 12)
    cv.text(510, 46, "Home", nf, INK, "lm")
    cv.rrect((510, 58, 548, 60), 1, fill=(226, 60, 70))
    cv.text(580, 46, "Category", font("Poppins-Medium.ttf", 12), GREY, "lm")
    cv.text(662, 46, "Anime", font("Poppins-Medium.ttf", 12), GREY, "lm")
    cv.pill(800, 28, "Search on  " + (meta.get("genres") or ["Anime"])[0], font("Poppins-Medium.ttf", 10), fill=(240, 240, 244), ink=GREY, h=36, padx=26)
    cv.ellipse((1196, 28, 1232, 64), fill=INK)
    cv.ellipse((1207, 34, 1221, 48), fill=(255, 255, 255))
    cv.ellipse((1203, 50, 1225, 68), fill=(255, 255, 255))
    # title block
    f, ls, sz = fit_title(meta["title"], "Poppins-Bold.ttf", 690, 52, 26, 2, upper=True)
    y = cv.lines(530, 150, ls, f, INK, sz * 1.1)
    cv.star(540, y + 20, 8, INK, 1.0)
    cv.text(556, y + 20, score_text(meta), font("Poppins-Bold.ttf", 12), INK, "lm")
    cv.text(630, y + 20, (meta.get("studio") or "ANIME").upper()[:24], font("Poppins-Bold.ttf", 12), GREY, "lm", track=1)
    gf = font("Poppins-Medium.ttf", 11)
    x = 530
    for g in (meta.get("genres") or ["Anime"])[:3]:
        x = cv.pill(x, y + 44, g, gf, outline=(90, 90, 100), ink=(40, 40, 46), h=26, padx=14) + 8
    cv.text(x + 12, y + 57, "Avg Ratings:", font("Poppins-Bold.ttf", 12), INK, "lm")
    cv.stars(x + 108, y + 57, meta.get("score"), r=8, fill=(244, 168, 36), empty=(215, 215, 222), gap=3)
    cv.rrect((530, y + 92, 1240, y + 93.2), 0, fill=LINE)
    y2 = cv.para(530, y + 118, (meta.get("desc") or "").upper(), font("Poppins-Medium.ttf", 10.5), GREY, 700, 6, 22)
    cv.rrect((530, y2 + 12, 1240, y2 + 13.2), 0, fill=LINE)
    by = y2 + 40
    bx = cv.button(530, by, button, font("Poppins-ExtraBold.ttf", 11), INK, h=36, padx=24)
    cv.rrect((bx + 14, by, bx + 50, by + 36), 18, fill=INK)
    cv.poly([(bx + 26, by + 10), (bx + 38, by + 10), (bx + 38, by + 27), (bx + 32, by + 22), (bx + 26, by + 27)], (255, 255, 255))
    cv.text(530, by + 66, f"{meta.get('eps') or '—'} EPISODES  ·  {meta.get('year') or '—'}  ·  {(meta.get('fmt') or 'TV').upper()}", font("Poppins-Medium.ttf", 9.5), GREY, track=1)
    return cv.finish()
