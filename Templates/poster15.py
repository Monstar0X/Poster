"""Style 15 - "Nova Season" (layout: Swordsmith5.jpg).  One big banner image, glass top bar (menu + search), season
caption, big uppercase title, studio line, white genre chips.  Uses: AniList banner."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))) if "__file__" in globals() else None
from nova_kit import *  # noqa


def render(meta, art, button="WATCH NOW", character=None):
    art = art or default_art((90, 110, 170))
    cv = Cv((10, 10, 14))
    cv.backdrop(art, dark=0.1, focus=(0.55, 0.3))
    cv.gradient((0, 0, 900, 720), (6, 6, 10), (6, 6, 10), True, 215, 0)
    cv.gradient((0, 560, 1280, 720), (6, 6, 10), (6, 6, 10), False, 0, 190)
    cv.glass((0, 0, 1280, 74), 0, blur=10, tint=(40, 40, 46, 110), outline=None)
    cv.text(390, 38, "Home", font("Poppins-Bold.ttf", 15), (255, 255, 255), "lm")
    cv.rrect((390, 52, 430, 54), 1, fill=(255, 255, 255))
    cv.text(470, 38, "Anime", font("Poppins-Medium.ttf", 14), (232, 232, 238), "lm")
    cv.text(548, 38, "Movie", font("Poppins-Medium.ttf", 14), (232, 232, 238), "lm")
    cv.pill(960, 20, "Search on  " + (meta.get("genres") or ["Anime"])[0], font("Poppins-Medium.ttf", 10), fill=(255, 255, 255), ink=(60, 60, 66), h=34, padx=24, alpha=190)
    season = (meta.get("season") or "").upper()
    cap = f"{season} ANIME {meta.get('year') or ''}".strip() if season else f"ANIME {meta.get('year') or ''}".strip()
    cv.text(60, 150, cap, font("Poppins-Medium.ttf", 14), (255, 255, 255), track=3)
    f, ls, sz = fit_title(meta["title"], "Poppins-Bold.ttf", 620, 48, 26, 3, upper=True)
    y = cv.lines(60, 180, ls, f, (255, 255, 255), sz * 1.18)
    cv.text(60, y + 14, "STUDIO - " + (meta.get("studio") or "ANIME").upper(), font("Poppins-Bold.ttf", 12), (240, 240, 245), track=1)
    x = 60
    cf = font("Poppins-Bold.ttf", 11.5)
    for g in (meta.get("genres") or ["Anime"])[:3]:
        x = cv.pill(x, y + 44, g, cf, fill=(255, 255, 255, 235), ink=(30, 30, 34), h=34, padx=22) + 12
    y = cv.para(60, y + 108, meta.get("desc", ""), font("Poppins-Medium.ttf", 12.5), (240, 240, 245), 560, 6, 23)
    cv.button(60, y + 22, button, font("Poppins-Bold.ttf", 12), (255, 255, 255), ink=(20, 20, 24), h=38, padx=26)
    return cv.finish()
