"""Style 18 - "Nova Neon" (layout: Swordsmith3.jpg).  Vivid neon background built from the cover, TWO dark cards:
header (cover + [Title] + three wide buttons) and info (list + trailer + synopsis).  Uses: AniList poster."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))) if "__file__" in globals() else None
from nova_kit import *  # noqa

BLUE = (22, 76, 200)


def _cut(s, f, maxw):
    while len(s) > 3 and tw(f, s) > maxw:
        s = s[:-2].rstrip()
    return s


def render(meta, art, button="WATCH NOW", character=None):
    art = art or default_art((80, 40, 160))
    from PIL import ImageEnhance
    cv = Cv((12, 8, 40))
    bg = ImageEnhance.Color(art.convert("RGB")).enhance(2.2)
    cv.backdrop(bg, dark=0.22, blur=3, tint=(40, 10, 140, 0.35), focus=(0.5, 0.3))
    for i, c in enumerate(((255, 40, 190, 90), (40, 210, 255, 90), (150, 70, 255, 110), (255, 40, 190, 70))):
        cv.poly([(80 + i * 330, 720), (130 + i * 330, 720), (330 + i * 330, 0), (290 + i * 330, 0)], c)
    CARD = (14, 12, 36)
    cv.rrect((26, 26, 1254, 212), 30, fill=CARD, alpha=225, outline=(255, 255, 255, 60), width=1)
    cv.photo(art, (52, 44, 152, 194), r=6, focus=(0.5, 0.2))
    st = (meta.get("studio") or "ANIME").upper()
    cv.text(176, 62, f"{st} NETWORK  +  {(meta.get('status') or 'ONGOING').upper()}", font("Poppins-Bold.ttf", 11), (60, 130, 255), "lm", track=1)
    f, ls, sz = fit_title(meta["title"], "Poppins-Bold.ttf", 820, 40, 22, 1)
    cv.text(176, 100, "[ " + ls[0] + " ]", f, (255, 255, 255), "lm")
    nat = (meta.get("native") or meta["title"])[:50]
    cv.text(176, 134, "| " + nat, font_for(nat, "Poppins-Regular.ttf", 10), (205, 210, 240), "lm")
    bw = 380
    bf = font("Poppins-Bold.ttf", 11)
    for i, (t, fill, ink) in enumerate(((button.title(), BLUE, (255, 255, 255)), ("My List", (255, 255, 255), (20, 20, 40)),
                                         (((meta.get("season") or "").title() + " " + str(meta.get("year") or "")).strip() or "Anime", BLUE, (255, 255, 255)))):
        x = 176 + i * (bw + 14) if False else 176 + i * 350
        cv.rrect((x, 160, x + 332, 194), 6, fill=fill)
        cv.text(x + 166, 177.5, t, bf, ink, "mm")
    cv.rrect((26, 232, 1254, 696), 30, fill=CARD, alpha=225, outline=(255, 255, 255, 60), width=1)
    cv.text(60, 264, meta["title"][:40], font("Poppins-Bold.ttf", 15), (255, 255, 255), "lm")
    cv.text(60, 284, "| " + nat, font_for(nat, "Poppins-Regular.ttf", 9), (190, 195, 225), "lm")
    rows = (("Genre", ", ".join(meta.get("genres", [])[:3]) or "—"), ("Type", meta.get("fmt") or "TV"),
            ("Status", meta.get("status") or "—"), ("Runtime", f"{meta.get('runtime') or '—'} minutes"),
            ("Season", (meta.get("season") or "—").title()), ("Episodes", str(meta.get("eps") or "—")),
            ("Studio", meta.get("studio") or "—"))
    rf, rb = font("Poppins-Regular.ttf", 10.5), font("Poppins-Bold.ttf", 10.5)
    for i, (k, v) in enumerate(rows):
        yy = 318 + i * 24
        cv.ellipse((62, yy - 6, 74, yy + 6), outline=(255, 255, 255, 210), width=1.2)
        cv.text(86, yy, k + " - ", rb, (255, 255, 255), "lm")
        cv.text(86 + tw(rb, k + " - "), yy, _cut(v, rf, 420 - tw(rb, k + " - ")), rf, (225, 228, 250), "lm")
    cv.rrect((640, 262, 641.5, 490), 0, fill=(255, 255, 255, 110))
    cv.ellipse((676, 258, 692, 274), outline=(255, 255, 255), width=1.5)
    cv.text(700, 266, "TRAILER :", font("Poppins-Bold.ttf", 10), (255, 255, 255), "lm")
    cv.photo(art, (676, 286, 1210, 458), r=12, focus=(0.5, 0.35))
    cv.rrect((676, 286, 1210, 458), 12, fill=(0, 0, 0), alpha=60)
    cv.play(943, 372, 24)
    for i, t in enumerate(("LIKE", "SHARE", "FOLLOW")):
        cv.text(740 + i * 200, 480, t, font("Poppins-Bold.ttf", 10), (255, 255, 255), "mm", track=1)
    cv.text(60, 520, "Synopsis", font("Poppins-Bold.ttf", 14), (255, 255, 255), "lm")
    cv.rrect((60, 534, 1220, 535), 0, fill=(255, 255, 255, 110))
    cv.para(60, 548, meta.get("desc", ""), font("Poppins-Regular.ttf", 10), (222, 226, 248), 1160, 6, 17)
    return cv.finish()
