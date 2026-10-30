"""Shared drawing kit for the "nova" poster styles (1, 2, 3, 6, 10, 11, 14-18).

Every template is laid out on a 1280x720 grid (design units) and rendered at 1920x1080 (scale S = 1.5).
Shapes are anti-aliased (drawn 3x bigger as a mask, then shrunk). Only Pillow is needed.
"""
import math
import os
from functools import lru_cache

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps

S = 1.5
W, H = 1920, 1080
DW, DH = 1280, 720

_HERE = os.path.dirname(os.path.abspath(__file__))
_DIRS = [os.environ.get("POSTER_FONT_DIR", ""), os.path.join(_HERE, "fonts"),
         os.path.join(os.path.dirname(_HERE), "fonts"),
         "/usr/share/fonts/truetype/google-fonts", "/usr/share/fonts/truetype/dejavu"]


@lru_cache(maxsize=256)
def _font_px(name: str, px: int):
    for n in (name, "Poppins-Bold.ttf", "DejaVuSans-Bold.ttf"):
        for d in _DIRS:
            p = os.path.join(d, n) if d else ""
            if p and os.path.exists(p):
                try:
                    return ImageFont.truetype(p, px)
                except OSError:
                    pass
    return ImageFont.load_default(px)


def font(name: str, size: float):
    """size in design units"""
    return _font_px(name, max(8, round(size * S)))


def font_for(text: str, name: str, size: float):
    """like font(), but a Japanese / non-latin string gets Noto Sans JP (downloaded by dataset.ensure_fonts)"""
    if all(ord(c) < 0x250 for c in text):
        return font(name, size)
    px = max(8, round(size * S))
    for d in _DIRS:
        p = os.path.join(d, "NotoSansJP-Variable.ttf") if d else ""
        if p and os.path.exists(p):
            try:
                f = ImageFont.truetype(p, px)
                try:
                    f.set_variation_by_axes([500])
                except Exception:
                    pass
                return f
            except OSError:
                pass
    return font(name, size)


def tw(f, s: str) -> float:
    """text width in design units"""
    return f.getlength(s) / S


def lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def mix(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def accent_of(img: Image.Image, fallback=(220, 60, 80)):
    """a saturated, mid-bright colour taken from the artwork"""
    if img is None:
        return fallback
    sm = img.convert("RGB").resize((48, 48))
    best, score = fallback, -1
    for px in sm.getdata():
        mx, mn = max(px), min(px)
        sat = (mx - mn) / (mx + 1)
        s = sat * (1 - abs(mx - 190) / 255)
        if s > score and mx > 90:
            best, score = px, s
    return best


def wrap(text: str, f, maxw: float, maxlines: int):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if cur and tw(f, t) > maxw:
            lines.append(cur)
            cur = w
        else:
            cur = t
    if cur:
        lines.append(cur)
    if len(lines) > maxlines:
        last = " ".join(lines[maxlines - 1:])
        while tw(f, last + "...") > maxw and " " in last:
            last = last.rsplit(" ", 1)[0]
        lines = lines[:maxlines - 1] + [last.rstrip(",.;:") + "..."]
    return lines


def fit_title(text: str, fname: str, maxw: float, start: float, lo: float, maxlines: int, upper=False):
    """biggest size (start..lo) at which the title wraps into <= maxlines lines that all fit"""
    text = text.upper() if upper else text
    size = start
    while True:
        f = font(fname, size)
        lines, cur = [], ""
        for w in text.split():
            t = (cur + " " + w).strip()
            if cur and tw(f, t) > maxw:
                lines.append(cur)
                cur = w
            else:
                cur = t
        if cur:
            lines.append(cur)
        if (len(lines) <= maxlines and all(tw(f, l) <= maxw for l in lines)) or size <= lo:
            if len(lines) > maxlines or any(tw(f, l) > maxw for l in lines):
                lines = wrap(text, f, maxw, maxlines)
                lines = [l if tw(f, l) <= maxw else _squeeze(l, f, maxw) for l in lines]
            return f, lines, size
        size -= 2


def _squeeze(s, f, maxw):
    while len(s) > 3 and tw(f, s + "...") > maxw:
        s = s[:-1]
    return s.rstrip() + "..."


def cover_fit(img: Image.Image, w: int, h: int, focus=(0.5, 0.3)) -> Image.Image:
    img = img.convert("RGB")
    sc = max(w / img.width, h / img.height)
    nw, nh = max(w, round(img.width * sc)), max(h, round(img.height * sc))
    img = img.resize((nw, nh), Image.LANCZOS)
    x = round((nw - w) * focus[0])
    y = round((nh - h) * focus[1])
    return img.crop((x, y, x + w, y + h))


class Cv:
    def __init__(self, bg=(255, 255, 255)):
        self.im = Image.new("RGB", (W, H), bg)
        self.d = ImageDraw.Draw(self.im, "RGBA")

    # ---- units ----
    @staticmethod
    def p(v):
        return int(round(v * S))

    def box(self, b):
        return tuple(int(round(v * S)) for v in b)

    # ---- AA shape machinery ----
    def _apply(self, mask, off, color):
        col = tuple(color[:3])
        a = color[3] if len(color) == 4 else 255
        if a < 255:
            mask = mask.point(lambda v: v * a // 255)
        self.im.paste(Image.new("RGB", mask.size, col), off, mask)

    def _shape(self, bbox_px, fn, color, ss=3):
        x0, y0, x1, y1 = (int(math.floor(bbox_px[0])) - 2, int(math.floor(bbox_px[1])) - 2,
                          int(math.ceil(bbox_px[2])) + 2, int(math.ceil(bbox_px[3])) + 2)
        x0c, y0c, x1c, y1c = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
        if x1c <= x0c or y1c <= y0c:
            return None
        m = Image.new("L", ((x1c - x0c) * ss, (y1c - y0c) * ss), 0)
        fn(ImageDraw.Draw(m), ss, x0c, y0c)
        m = m.resize((x1c - x0c, y1c - y0c), Image.LANCZOS)
        if color is not None:
            self._apply(m, (x0c, y0c), color)
        return m, (x0c, y0c)

    def rrect(self, b, r, fill=None, outline=None, width=1, alpha=None):
        x0, y0, x1, y1 = self.box(b)
        rr = self.p(r)

        def draw_(w_):
            def fn(dr, ss, ox, oy):
                dr.rounded_rectangle(((x0 - ox) * ss, (y0 - oy) * ss, (x1 - ox) * ss - 1, (y1 - oy) * ss - 1),
                                     radius=rr * ss, fill=255)
            return fn
        if fill is not None:
            col = tuple(fill[:3]) + ((alpha,) if alpha is not None else ((fill[3],) if len(fill) == 4 else ()))
            self._shape((x0, y0, x1, y1), draw_(0), col)
        if outline is not None:
            wpx = max(1, self.p(width))
            ocol = tuple(outline[:3]) + ((outline[3],) if len(outline) == 4 else ())

            def ring(dr, ss, ox, oy):
                dr.rounded_rectangle(((x0 - ox) * ss, (y0 - oy) * ss, (x1 - ox) * ss - 1, (y1 - oy) * ss - 1),
                                     radius=rr * ss, outline=255, width=wpx * ss)
            self._shape((x0, y0, x1, y1), ring, ocol)

    def ellipse(self, b, fill=None, outline=None, width=1):
        x0, y0, x1, y1 = self.box(b)

        def f1(dr, ss, ox, oy):
            dr.ellipse(((x0 - ox) * ss, (y0 - oy) * ss, (x1 - ox) * ss - 1, (y1 - oy) * ss - 1), fill=255)
        if fill is not None:
            self._shape((x0, y0, x1, y1), f1, fill)
        if outline is not None:
            wpx = max(1, self.p(width))

            def f2(dr, ss, ox, oy):
                dr.ellipse(((x0 - ox) * ss, (y0 - oy) * ss, (x1 - ox) * ss - 1, (y1 - oy) * ss - 1),
                           outline=255, width=wpx * ss)
            self._shape((x0, y0, x1, y1), f2, outline)

    def poly(self, pts, fill):
        P = [(x * S, y * S) for x, y in pts]
        xs, ys = [q[0] for q in P], [q[1] for q in P]

        def fn(dr, ss, ox, oy):
            dr.polygon([((x - ox) * ss, (y - oy) * ss) for x, y in P], fill=255)
        self._shape((min(xs), min(ys), max(xs), max(ys)), fn, fill)

    def line(self, p0, p1, fill, width=1):
        (x0, y0), (x1, y1) = [(a * S, b * S) for a, b in (p0, p1)]
        wpx = max(1, self.p(width))

        def fn(dr, ss, ox, oy):
            dr.line([((x0 - ox) * ss, (y0 - oy) * ss), ((x1 - ox) * ss, (y1 - oy) * ss)], fill=255, width=wpx * ss)
        self._shape((min(x0, x1) - wpx, min(y0, y1) - wpx, max(x0, x1) + wpx, max(y0, y1) + wpx), fn, fill)

    # ---- images ----
    def photo(self, img, b, r=0, focus=(0.5, 0.3), dim=None, poly=None):
        """cover-fit img into box b (design units); rounded corners r; optional polygon clip (design units)"""
        x0, y0, x1, y1 = self.box(b)
        w, h = x1 - x0, y1 - y0
        pic = cover_fit(img, w, h, focus)
        if dim:
            pic = Image.blend(pic, Image.new("RGB", pic.size, dim[:3]), dim[3] if len(dim) > 3 else 0.35)
        mask = Image.new("L", (w * 3, h * 3), 0)
        md = ImageDraw.Draw(mask)
        if poly:
            md.polygon([((x * S - x0) * 3, (y * S - y0) * 3) for x, y in poly], fill=255)
        else:
            md.rounded_rectangle((0, 0, w * 3 - 1, h * 3 - 1), radius=self.p(r) * 3, fill=255)
        mask = mask.resize((w, h), Image.LANCZOS)
        self.im.paste(pic, (x0, y0), mask)

    def backdrop(self, img, dark=0.55, blur=0, tint=None, focus=(0.5, 0.3)):
        """full-bleed artwork, optional blur / tint / darkening"""
        pic = cover_fit(img, W, H, focus)
        if blur:
            pic = pic.filter(ImageFilter.GaussianBlur(self.p(blur)))
        if tint:
            pic = Image.blend(pic, Image.new("RGB", pic.size, tint[:3]), tint[3])
        if dark:
            pic = Image.blend(pic, Image.new("RGB", pic.size, (0, 0, 0)), dark)
        self.im.paste(pic, (0, 0))

    def glass(self, b, r, blur=14, tint=(255, 255, 255, 36), outline=(255, 255, 255, 90), width=1.2):
        """frosted panel: the pixels behind it are blurred, then tinted"""
        x0, y0, x1, y1 = self.box(b)
        x0, y0, x1, y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
        crop = self.im.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(self.p(blur)))
        w, h = x1 - x0, y1 - y0
        mask = Image.new("L", (w * 3, h * 3), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, w * 3 - 1, h * 3 - 1), radius=self.p(r) * 3, fill=255)
        mask = mask.resize((w, h), Image.LANCZOS)
        self.im.paste(crop, (x0, y0), mask)
        self.rrect(b, r, fill=tint[:3], alpha=tint[3])
        if outline:
            self.rrect(b, r, outline=outline, width=width)

    def shadow(self, b, r=12, blur=14, opacity=90, dy=6, color=(0, 0, 0)):
        x0, y0, x1, y1 = self.box(b)
        pad = self.p(blur) * 3
        w, h = x1 - x0 + pad * 2, y1 - y0 + pad * 2
        m = Image.new("L", (w, h), 0)
        ImageDraw.Draw(m).rounded_rectangle((pad, pad, pad + x1 - x0, pad + y1 - y0), radius=self.p(r), fill=opacity)
        m = m.filter(ImageFilter.GaussianBlur(self.p(blur)))
        self.im.paste(Image.new("RGB", m.size, color), (x0 - pad, y0 - pad + self.p(dy)), m)

    def gradient(self, b, c0, c1, horizontal=True, a0=255, a1=255):
        """linear colour / alpha ramp over box b (design units); horizontal = left -> right, else top -> bottom"""
        x0, y0, x1, y1 = self.box(b)
        x0, y0, x1, y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
        w, h = x1 - x0, y1 - y0
        if w <= 0 or h <= 0:
            return
        if horizontal:
            ramp = Image.linear_gradient("L").rotate(90, expand=True).resize((w, h))
        else:
            ramp = Image.linear_gradient("L").resize((w, h))
        alpha = ramp.point(lambda v: round(a0 + (a1 - a0) * v / 255))
        col = Image.merge("RGB", [ramp.point(lambda v, i=i: round(c0[i] + (c1[i] - c0[i]) * v / 255)) for i in range(3)])
        self.im.paste(col, (x0, y0), alpha)

    def grad_pill(self, b, c0, c1, r=None):
        """rounded box filled with a left -> right colour ramp"""
        x0, y0, x1, y1 = self.box(b)
        w, h = x1 - x0, y1 - y0
        ramp = Image.linear_gradient("L").rotate(90, expand=True).resize((w, h))
        col = Image.merge("RGB", [ramp.point(lambda v, i=i: round(c0[i] + (c1[i] - c0[i]) * v / 255)) for i in range(3)])
        m = Image.new("L", (w * 3, h * 3), 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, w * 3 - 1, h * 3 - 1), radius=(self.p(r) if r is not None else h // 2) * 3, fill=255)
        self.im.paste(col, (x0, y0), m.resize((w, h), Image.LANCZOS))

    # ---- single-character PNG ----
    def cutout(self, img, box, ax=0.5, shadow=110, grow=1.0, flip=False):
        """Paste a transparent character PNG (fanart.tv) into box (design units): trimmed to its outline, scaled to the
        box height (or width when it is wider than tall), bottom-aligned; ax = 0 left / .5 centre / 1 right inside the box.
        grow > 1 lets it overflow the box a little. A soft drop shadow keeps it readable on any background."""
        ch = img.convert("RGBA")
        bb = ch.getchannel("A").getbbox()
        if bb:
            ch = ch.crop(bb)
        if flip:
            ch = ch.transpose(Image.FLIP_LEFT_RIGHT)
        x0, y0, x1, y1 = self.box(box)
        bw, bh = (x1 - x0) * grow, (y1 - y0) * grow
        sc = min(bw / ch.width, bh / ch.height)
        ch = ch.resize((max(1, round(ch.width * sc)), max(1, round(ch.height * sc))), Image.LANCZOS)
        px = round(x0 + ((x1 - x0) - ch.width) * ax)
        py = y1 - ch.height
        if shadow:
            sh = Image.new("RGBA", ch.size, (0, 0, 0, 0))
            sh.putalpha(ch.getchannel("A").point(lambda v: v * shadow // 255))
            pad = self.p(14)
            big = Image.new("RGBA", (ch.width + pad * 2, ch.height + pad * 2), (0, 0, 0, 0))
            big.paste(sh, (pad, pad))
            big = big.filter(ImageFilter.GaussianBlur(self.p(8)))
            self.im.paste(Image.new("RGB", big.size, (0, 0, 0)), (px - pad + self.p(4), py - pad + self.p(6)), big.getchannel("A"))
        self.im.paste(ch.convert("RGB"), (px, py), ch.getchannel("A"))

    def blob(self, pts, fill):
        """smooth closed shape through the given points (design units), Catmull-Rom"""
        n = len(pts)
        out = []
        for i in range(n):
            p0, p1, p2, p3 = pts[(i - 1) % n], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
            for t in [j / 14 for j in range(14)]:
                out.append(tuple(0.5 * ((2 * p1[c]) + (-p0[c] + p2[c]) * t + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t * t
                                      + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * t ** 3) for c in (0, 1)))
        self.poly(out, fill)

    def tint(self, b, color, alpha):
        self.rrect(b, 0, fill=color, alpha=alpha)

    # ---- text ----
    def text(self, x, y, s, f, fill=(0, 0, 0), anchor="la", track=0):
        px, py = x * S, y * S
        if not track:
            self.d.text((px, py), s, font=f, fill=fill, anchor=anchor)
            return
        total = sum(self.d.textlength(ch, font=f) + track * S for ch in s) - track * S
        if anchor[0] == "m":
            px -= total / 2
        elif anchor[0] == "r":
            px -= total
        a = "l" + anchor[1]
        for ch in s:
            self.d.text((px, py), ch, font=f, fill=fill, anchor=a)
            px += self.d.textlength(ch, font=f) + track * S

    def lines(self, x, y, lines, f, fill, leading, anchor="la"):
        for i, ln in enumerate(lines):
            self.text(x, y + i * leading, ln, f, fill, anchor)
        return y + len(lines) * leading

    def para(self, x, y, s, f, fill, maxw, maxlines, leading):
        ls = wrap(s, f, maxw, maxlines)
        return self.lines(x, y, ls, f, fill, leading)

    def vtext(self, x, y, s, f, fill, track=0):
        """text rotated 90deg (reads bottom -> top); (x, y) = centre"""
        tmp = Image.new("RGBA", (W, 400), (0, 0, 0, 0))
        td = ImageDraw.Draw(tmp)
        total = sum(td.textlength(ch, font=f) + track * S for ch in s)
        px = 10
        for ch in s:
            td.text((px, 200), ch, font=f, fill=fill, anchor="lm")
            px += td.textlength(ch, font=f) + track * S
        tmp = tmp.crop((0, 120, int(total) + 20, 280)).rotate(90, expand=True)
        self.im.paste(tmp, (int(x * S - tmp.width / 2), int(y * S - tmp.height / 2)), tmp)

    def pill(self, x, y, s, f, fill=None, ink=(255, 255, 255), outline=None, padx=12, h=26, width=1.2, alpha=None):
        w = tw(f, s) + padx * 2
        self.rrect((x, y, x + w, y + h), h / 2, fill=fill, outline=outline, width=width, alpha=alpha)
        self.text(x + w / 2, y + h / 2 + 0.5, s, f, ink, "mm")
        return x + w

    def button(self, x, y, s, f, fill, ink=(255, 255, 255), h=40, padx=26, r=None, outline=None):
        w = tw(f, s) + padx * 2
        self.rrect((x, y, x + w, y + h), h / 2 if r is None else r, fill=fill, outline=outline)
        self.text(x + w / 2, y + h / 2 + 0.5, s, f, ink, "mm")
        return x + w

    def star(self, cx, cy, r, fill, frac=1.0, empty=None):
        pts = []
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            rr = r if i % 2 == 0 else r * 0.42
            pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
        if empty is not None or frac < 1:
            self.poly(pts, empty or (200, 200, 200))
        if frac >= 1:
            self.poly(pts, fill)
        elif frac > 0:
            x0, y0 = self.box((cx - r, cy - r, cx + r, cy + r))[:2]
            w = self.p(2 * r)
            layer = Image.new("RGB", self.im.size, fill)
            m = Image.new("L", self.im.size, 0)
            md = ImageDraw.Draw(m)
            md.rectangle((x0, y0, x0 + int(w * frac), y0 + w), fill=255)
            sh = Image.new("L", self.im.size, 0)
            ImageDraw.Draw(sh).polygon([(x * S, y * S) for x, y in pts], fill=255)
            self.im.paste(layer, (0, 0), ImageChops.multiply(m, sh))

    def stars(self, x, y, score100, r=9, fill=(250, 190, 40), empty=(210, 210, 215), gap=4):
        v = (score100 or 0) / 20.0
        for i in range(5):
            frac = max(0.0, min(1.0, v - i))
            self.star(x + r + i * (2 * r + gap), y, r, fill, frac, empty)
        return x + 5 * (2 * r + gap)

    def play(self, cx, cy, r, fill=(255, 255, 255, 235), ink=(30, 30, 30)):
        self.ellipse((cx - r, cy - r, cx + r, cy + r), fill=fill)
        self.poly([(cx - r * .3, cy - r * .45), (cx - r * .3, cy + r * .45), (cx + r * .5, cy)], ink)

    def finish(self) -> Image.Image:
        return self.im.convert("RGB")


def score_text(meta) -> str:
    s = meta.get("score")
    return f"{s / 10:.1f}" if s else "N/A"


def info_year(meta) -> str:
    return str(meta.get("year") or "")


def default_art(color=(70, 70, 90)):
    im = Image.new("RGB", (460, 650), color)
    d = ImageDraw.Draw(im)
    for i in range(0, 650, 26):
        d.line((0, i, 460, i - 140), fill=mix(color, (255, 255, 255), 0.08), width=10)
    return im
