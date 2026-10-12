"""Reels «6070 → 9157 слов» for @secondnature.eng.

Stage 1 (now): style helpers + the scenes that don't need the lesson video
(results 34–39 s, CTA 39–43 s). `python3 render.py preview` writes stills with the
Reels safe zones drawn on top to out/preview_*.png.
Stage 2 (once assets/IMG_1280.mov, the student's timecode and the voiceover arrive):
video scenes, audio mix, loudnorm, cover.png.
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
CHAMP = (251, 223, 162)
CHOCO = (68, 34, 22)
HERE = os.path.dirname(os.path.abspath(__file__))
SAFE_TOP, SAFE_BOTTOM, SAFE_RIGHT = 220, 380, 140
SAFE_L = 60                                   # our own left margin
CX = (SAFE_L + W - SAFE_RIGHT) / 2            # centre of the usable column (500)
COL_W = W - SAFE_RIGHT - SAFE_L               # 880


def font(name, size, weight):
    f = ImageFont.truetype(os.path.join(HERE, "fonts", name), size)
    f.set_variation_by_name(weight)
    return f

F_HEAD = lambda s: font("PlayfairDisplay.ttf", s, "Bold")
F_TEXT = lambda s: font("Montserrat.ttf", s, "SemiBold")
F_NICK = font("Montserrat.ttf", 30, "SemiBold")


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def wrap(text, f, maxw):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for w in para.split(" "):
            t = (cur + " " + w).strip()
            if f.getlength(t) <= maxw or not cur:
                cur = t
            else:
                lines.append(cur); cur = w
        lines.append(cur)
    return lines


def text_block(img, text, f, top, fill, lh=1.2, maxw=COL_W, cx=CX):
    """Centred multi-line text; returns the bottom y."""
    d = ImageDraw.Draw(img)
    lhp = int(f.size * lh)
    for i, l in enumerate(wrap(text, f, maxw)):
        d.text((cx - f.getlength(l) / 2, top + i * lhp), l, font=f, fill=fill)
    return top + lhp * len(wrap(text, f, maxw))


def plaque(img, text, f, top, box=CHOCO, ink=CHAMP, pad=(36, 26), lh=1.25, maxw=COL_W - 72,
           head=None, f_head=None, alpha=1.0):
    """Rounded plaque in the usable column. Optional bold `head` line above the body text."""
    lines = wrap(text, f, maxw) if text else []
    hl = wrap(head, f_head, maxw) if head else []
    lhp, hlp = int(f.size * lh), int(f_head.size * 1.2) if head else 0
    bw = max([f.getlength(l) for l in lines] + [f_head.getlength(l) for l in hl]) + 2 * pad[0]
    bh = lhp * len(lines) + hlp * len(hl) + (14 if hl and lines else 0) + 2 * pad[1]
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x0 = CX - bw / 2
    d.rounded_rectangle([x0, top, x0 + bw, top + bh], radius=28, fill=box + (255,))
    y = top + pad[1]
    for l in hl:
        d.text((CX - f_head.getlength(l) / 2, y - f_head.size * 0.08), l, font=f_head, fill=ink + (255,)); y += hlp
    if hl and lines: y += 14
    for l in lines:
        d.text((CX - f.getlength(l) / 2, y - f.size * 0.05), l, font=f, fill=ink + (255,)); y += lhp
    if alpha < 1:
        layer.putalpha(Image.eval(layer.getchannel("A"), lambda v: int(v * alpha)))
    img.alpha_composite(layer)
    return top + bh


def arrow_text(img, text, size, top, fill):
    """Playfair line whose → is taken from Montserrat (Playfair's arrow has fletching)."""
    fh, fa = F_HEAD(size), font("Montserrat.ttf", int(size * 0.8), "SemiBold")
    parts = text.split("→")
    gap = size * 0.18
    widths = [fh.getlength(p.strip()) for p in parts]
    total = sum(widths) + (len(parts) - 1) * (fa.getlength("→") + 2 * gap)
    x = CX - total / 2
    d = ImageDraw.Draw(img)
    for i, p in enumerate(parts):
        d.text((x, top), p.strip(), font=fh, fill=fill); x += widths[i]
        if i < len(parts) - 1:
            d.text((x + gap, top + size * 0.2), "→", font=fa, fill=fill); x += fa.getlength("→") + 2 * gap
    return top + int(size * 1.12)


def nick(img, color, y=H - SAFE_BOTTOM - 56):
    d = ImageDraw.Draw(img)
    s = "@secondnature.eng"
    d.text((CX - F_NICK.getlength(s) / 2, y), s, font=F_NICK, fill=color + (255,))


# ---------------- results scene (34–39 s) ----------------
RES = Image.open(os.path.join(HERE, "assets", "results.png")).convert("RGB")
CARD_FEB = RES.crop((0, 0, 424, 180))
CARD_OCT = RES.crop((0, 370, 424, 570))


def card(crop, width=COL_W - 140):
    """Screenshot crop on a white rounded panel with a soft chocolate shadow."""
    sc = (width - 40) / crop.width
    im = crop.resize((round(crop.width * sc), round(crop.height * sc)), Image.LANCZOS)
    pw, ph = im.width + 40, im.height + 40
    out = Image.new("RGBA", (pw + 60, ph + 60), (0, 0, 0, 0))
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([30, 40, 30 + pw, 40 + ph], radius=34, fill=CHOCO + (70,))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    panel = Image.new("RGBA", (pw, ph), (255, 255, 255, 255))
    m = Image.new("L", (pw, ph), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, pw - 1, ph - 1], radius=34, fill=255)
    panel.paste(im, (20, 20))
    out.paste(panel, (30, 30), m)
    return out

CARD1, CARD2 = card(CARD_FEB), card(CARD_OCT)


def results_frame(t, dur=5.0):
    """t: seconds into the scene. 6070 first, 9157 slides in at 1.2 s, headline at 2.2 s."""
    img = Image.new("RGBA", (W, H), CHAMP + (255,))
    z = 1.0 + 0.04 * t / dur                       # gentle push-in on the whole layout
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    a = ease((t - 2.2) / 0.5)
    if a > 0:
        f = F_HEAD(84)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        text_block(layer, "+3087 слов\nза 8 месяцев", f, SAFE_TOP + 40 + 30 * (1 - a), CHOCO + (255,))
        layer.putalpha(Image.eval(layer.getchannel("A"), lambda v: int(v * a)))
        lay.alpha_composite(layer)
    y1 = 500
    a1 = ease(t / 0.4)
    c1 = CARD1.copy(); c1.putalpha(Image.eval(c1.getchannel("A"), lambda v: int(v * a1)))
    lay.alpha_composite(c1, (round(CX - CARD1.width / 2), y1))
    arrow_y = y1 + CARD1.height - 10
    a2 = ease((t - 1.2) / 0.45)
    if a2 > 0:
        f = font("Montserrat.ttf", 72, "Bold")
        d = ImageDraw.Draw(lay)
        d.text((CX - f.getlength("↓") / 2, arrow_y), "↓", font=f, fill=CHOCO + (int(255 * a2),))
        c2 = CARD2.copy(); c2.putalpha(Image.eval(c2.getchannel("A"), lambda v: int(v * a2)))
        lay.alpha_composite(c2, (round(CX - CARD2.width / 2), round(arrow_y + 80 + 60 * (1 - a2))))
    if z != 1:
        zw, zh = round(W * z), round(H * z)
        lay = lay.resize((zw, zh), Image.BICUBIC).crop(((zw - W) // 2, (zh - H) // 2, (zw - W) // 2 + W, (zh - H) // 2 + H))
    img.alpha_composite(lay)
    nick(img, CHOCO)
    return img


# ---------------- CTA scene (39–43 s) ----------------
def cta_frame(t, dur=4.0):
    img = Image.new("RGBA", (W, H), CHOCO + (255,))
    a, b = ease(t / 0.45), ease((t - 0.5) / 0.45)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    yb = text_block(layer, "Группы", F_HEAD(130), 600 + 30 * (1 - a), CHAMP + (255,), lh=1.12)
    yb = arrow_text(layer, "A2 → B1", 130, yb, CHAMP + (255,))
    layer.putalpha(Image.eval(layer.getchannel("A"), lambda v: int(v * a)))
    img.alpha_composite(layer)
    if b > 0:
        plaque(img, "Анкета в шапке профиля", F_TEXT(50), yb + 70, box=CHAMP, ink=CHOCO, alpha=b)
    nick(img, CHAMP)
    return img


def safe_overlay(img):
    o = img.copy()
    zones = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(zones)
    red = (220, 40, 40, 90)
    d.rectangle([0, 0, W, SAFE_TOP], fill=red)
    d.rectangle([0, H - SAFE_BOTTOM, W, H], fill=red)
    d.rectangle([W - SAFE_RIGHT, 0, W, H], fill=red)
    o.alpha_composite(zones)
    return o


if __name__ == "__main__" and sys.argv[1:2] == ["preview"]:
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    shots = [("results_0.6s", results_frame(0.6)), ("results_end", results_frame(4.9)),
             ("cta_end", cta_frame(3.9))]
    for name, im in shots:
        safe_overlay(im).convert("RGB").save(os.path.join(HERE, "out", f"preview_{name}.png"))
    print("ok")
