"""Reels quiz series: 'one word fits all three sentences'.

Usage:
  python3 quiz_render.py preview   # one PNG per video
  python3 quiz_render.py           # render video1_B1.mp4 and video2_B2.mp4 (no audio track)
"""
import math, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
SAFE_X0, SAFE_X1, SAFE_Y0, SAFE_Y1 = 80, 960, 250, 1550

BG_TOP, BG_BOTTOM = (0xEA, 0xF6, 0xFF), (0x8F, 0xB8, 0xE6)
INK = (0x1F, 0x2A, 0x44)
INK_SOFT = (0x4A, 0x56, 0x72)
YELLOW = (0xFF, 0xD9, 0x5A)
GREEN = (0x7B, 0xD8, 0x8F)
WHITE = (255, 255, 255)

FONT_DIR = "/usr/share/fonts/opentype/inter/"
def font(weight, size):
    return ImageFont.truetype(FONT_DIR + f"Inter-{weight}.otf", size)

F_BADGE = font("Bold", 40)
F_TITLE = font("Bold", 56)
F_SENT = font("Medium", 48)
F_GAPWORD = font("Bold", 46)
F_NUM = font("Bold", 38)
F_TR_B = font("SemiBold", 32)
F_TR = font("Regular", 32)
F_CTA = font("SemiBold", 42)

GAP_W, GAP_H = 180, 56
CARD_X, CARD_W = SAFE_X0, SAFE_X1 - SAFE_X0
CARD_PAD_Y, CARD_PAD_R = 30, 34
NUM_D = 64
TEXT_X = 28 + NUM_D + 26            # sentence text start inside the card
TEXT_MAXW = CARD_W - TEXT_X - CARD_PAD_R
LH_SENT = 66
SHADOW = 40                          # margin around card for its soft shadow

# ---------- drawing helpers ----------

def rrect(w, h, r, fill, ss=4):
    """Anti-aliased rounded rectangle (supersampled)."""
    big = Image.new("RGBA", (int(w * ss), int(h * ss)), (0, 0, 0, 0))
    ImageDraw.Draw(big).rounded_rectangle([0, 0, w * ss - 1, h * ss - 1], radius=r * ss, fill=fill)
    return big.resize((int(w), int(h)), Image.LANCZOS)

def ellipse(d, fill, ss=4):
    big = Image.new("RGBA", (d * ss, d * ss), (0, 0, 0, 0))
    ImageDraw.Draw(big).ellipse([0, 0, d * ss - 1, d * ss - 1], fill=fill)
    return big.resize((d, d), Image.LANCZOS)

def gradient():
    col = Image.new("RGB", (1, H))
    for y in range(H):
        t = y / (H - 1)
        col.putpixel((0, y), tuple(round(a + (b - a) * t) for a, b in zip(BG_TOP, BG_BOTTOM)))
    return col.resize((W, H)).convert("RGBA")

def wrap(text, f, maxw):
    """Word wrap; explicit newlines force a break."""
    lines = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split():
            t = (cur + " " + word).strip()
            if f.getlength(t) <= maxw or not cur:
                cur = t
            else:
                lines.append(cur); cur = word
        lines.append(cur)
    return lines

def text_block(text, f, maxw, lh, fill=INK):
    """Centered multi-line text on a transparent layer of width maxw."""
    lines = wrap(text, f, maxw)
    img = Image.new("RGBA", (maxw, lh * len(lines) + 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i, l in enumerate(lines):
        d.text((maxw / 2, i * lh + lh / 2), l, font=f, fill=fill, anchor="mm")
    return img

_pill_cache = {}
def gap_pill(scale, color=YELLOW):
    """Pill of GAP_W x GAP_H scaled around its centre, on a fixed canvas (sub-pixel smooth pulse)."""
    key = (round(scale, 3), color)
    if key not in _pill_cache:
        cw, ch, ss = GAP_W + 24, GAP_H + 12, 4
        big = Image.new("RGBA", (cw * ss, ch * ss), (0, 0, 0, 0))
        w, h = GAP_W * scale * ss, GAP_H * scale * ss
        cx, cy = cw * ss / 2, ch * ss / 2
        ImageDraw.Draw(big).rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2],
                                              radius=h * 0.3, fill=color)
        _pill_cache[key] = big.resize((cw, ch), Image.LANCZOS)
    return _pill_cache[key]

# ---------- components ----------

def badge(text, fill, fg):
    tw = F_BADGE.getlength(text)
    w, h = int(tw + 2 * 38), 72
    img = rrect(w, h, h / 2, fill)
    ImageDraw.Draw(img).text((w / 2, h / 2 + 1), text, font=F_BADGE, fill=fg, anchor="mm")
    return img

def layout_sentence(sentence):
    """Wrap a sentence containing '___' into lines of ('w', text, x) / ('gap', None, x) items."""
    tokens = []
    for i, part in enumerate(sentence.split("___")):
        if i: tokens.append(("gap", None))
        tokens += [("w", w) for w in part.split()]
    sp = F_SENT.getlength(" ")
    lines, cur, x = [], [], 0
    for kind, txt in tokens:
        tw = GAP_W if kind == "gap" else F_SENT.getlength(txt)
        nx = x + (sp if cur else 0)
        if cur and nx + tw > TEXT_MAXW:
            lines.append(cur); cur, nx = [], 0
        cur.append((kind, txt, nx)); x = nx + tw
    lines.append(cur)
    return lines

def card(num, sentence, answer=None, translation=None):
    """Returns (layer incl. shadow margin, list of gap centres relative to layer).
    answer: word drawn on a green pill instead of a pulsing yellow gap.
    translation: (bold_part, rest) small line under the sentence."""
    lines = layout_sentence(sentence)
    body_h = LH_SENT * len(lines)
    tr_h = 50 if translation else 0
    ch = max(CARD_PAD_Y * 2 + body_h + tr_h, NUM_D + 48)
    lw, lh = CARD_W + 2 * SHADOW, ch + 2 * SHADOW
    layer = Image.new("RGBA", (lw, lh), (0, 0, 0, 0))
    # soft shadow
    sh = Image.new("RGBA", (lw, lh), (0, 0, 0, 0))
    sh.alpha_composite(rrect(CARD_W, ch, 28, INK + (40,)), (SHADOW, SHADOW + 10))
    layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
    layer.alpha_composite(rrect(CARD_W, ch, 28, WHITE + (255,)), (SHADOW, SHADOW))
    # number
    ny = SHADOW + (ch - NUM_D) // 2
    layer.alpha_composite(ellipse(NUM_D, INK + (255,)), (SHADOW + 28, ny))
    d = ImageDraw.Draw(layer)
    d.text((SHADOW + 28 + NUM_D / 2, ny + NUM_D / 2 + 1), str(num), font=F_NUM, fill=WHITE, anchor="mm")
    # sentence
    gaps = []
    top = SHADOW + CARD_PAD_Y
    for i, line in enumerate(lines):
        cy = top + i * LH_SENT + LH_SENT / 2
        for kind, txt, x in line:
            ax = SHADOW + TEXT_X + x
            if kind == "w":
                d.text((ax, cy), txt, font=F_SENT, fill=INK, anchor="lm")
            else:
                c = (ax + GAP_W / 2, cy)
                if answer:
                    p = gap_pill(1.0, GREEN)
                    layer.alpha_composite(p, (round(c[0] - p.width / 2), round(c[1] - p.height / 2)))
                    d.text(c, answer, font=F_GAPWORD, fill=INK, anchor="mm")
                else:
                    gaps.append(c)
    if translation:
        bold, rest = translation
        ty = top + body_h + 4 + 20
        tx = SHADOW + TEXT_X
        d.text((tx, ty), bold, font=F_TR_B, fill=INK, anchor="lm")
        d.text((tx + F_TR_B.getlength(bold), ty), rest, font=F_TR, fill=INK_SOFT, anchor="lm")
    return layer, gaps, ch

class Screen:
    """One quiz screen: badge, title, three cards, optional CTA, with its own animation clock."""
    G_BADGE, G_TITLE, G_CARD, G_CTA = 34, 52, 24, 56

    def __init__(self, badge_text, badge_style, title, sentences, cta=None, answer=None, translations=None):
        self.badge = badge(badge_text, *badge_style)
        self.title = text_block(title, F_TITLE, CARD_W, 70)
        self.cards = [card(i + 1, s, answer, translations[i] if translations else None)
                      for i, s in enumerate(sentences)]
        self.cta = text_block(cta, F_CTA, CARD_W, 54) if cta else None
        total = (self.badge.height + self.G_BADGE + self.title.height + self.G_TITLE
                 + sum(c[2] for c in self.cards) + self.G_CARD * 2
                 + ((self.G_CTA + self.cta.height) if self.cta else 0))
        y = SAFE_Y0 + (SAFE_Y1 - SAFE_Y0 - total) // 2
        assert y >= SAFE_Y0, f"content too tall: {total}px"
        self.y_badge = y; y += self.badge.height + self.G_BADGE
        self.y_title = y; y += self.title.height + self.G_TITLE
        self.y_cards = []
        for c in self.cards:
            self.y_cards.append(y); y += c[2] + self.G_CARD
        y += self.G_CTA - self.G_CARD
        self.y_cta = y
        if self.cta: assert y + self.cta.height <= SAFE_Y1 + 16

    def static_layer(self):
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        img.alpha_composite(self.badge, ((W - self.badge.width) // 2, self.y_badge))
        img.alpha_composite(self.title, (CARD_X, self.y_title))
        return img

    def draw(self, base, t):
        """Draw onto base (RGBA, background already there) at local time t."""
        if not hasattr(self, "_static"): self._static = self.static_layer()
        base.alpha_composite(self._static)
        pulse = 1 + 0.025 * (1 - math.cos(2 * math.pi * t / 1.5))       # 100% .. 105%
        for i, (layer, gaps, ch) in enumerate(self.cards):
            p = min(1.0, max(0.0, (t - i * 0.15) / 0.30))                # staggered, done by 0.6 s
            off = round(60 * (1 - p) ** 3)                               # ease-out slide from below
            ox, oy = CARD_X - SHADOW, self.y_cards[i] - SHADOW + off
            base.alpha_composite(layer, (ox, oy))
            for (gx, gy) in gaps:
                pill = gap_pill(pulse)
                base.alpha_composite(pill, (round(ox + gx - pill.width / 2), round(oy + gy - pill.height / 2)))
        if self.cta and t >= 1.0:
            p = min(1.0, (t - 1.0) / 0.35)
            e = 1 - (1 - p) ** 3
            layer = self.cta
            if p < 1:
                layer = layer.copy()
                layer.putalpha(layer.getchannel("A").point(lambda a: int(a * e)))
            base.alpha_composite(layer, (CARD_X, self.y_cta + round(20 * (1 - e))))

# ---------- content ----------

BADGE_LEVEL = (INK + (255,), WHITE)
BADGE_ANSWER = (GREEN + (255,), INK)
TITLE = "Одно слово подходит\nво все три предложения.\nЗнаешь его? Значит, у тебя {}"
CTA = "Пиши слово в комментариях.\nОтвет в следующем видео"

S_B1 = ["It's hard to ___ a decision when you're tired.",
        "Blow out the candles and ___ a wish!",
        "Tonight it's my turn to ___ dinner."]
S_B2 = ["Bright colours always ___ your eye.",
        "Hurry up, or we won't ___ the last train.",
        "Put on a jacket, or you'll ___ a cold."]

def video1():
    s = Screen("B1", BADGE_LEVEL, TITLE.format("B1"), S_B1, CTA)
    return 12.0, lambda base, t: s.draw(base, t)

def video2():
    a = Screen("Ответ", BADGE_ANSWER, "Ответ на прошлое видео:\nMAKE", S_B1, answer="make",
               translations=[("make a decision", " = принять решение"),
                             ("make a wish", " = загадать желание"),
                             ("make dinner", " = приготовить ужин")])
    b = Screen("B2", BADGE_LEVEL, TITLE.format("B2"), S_B2, CTA)
    T_SWITCH, T_FADE = 5.0, 0.5
    def draw(base, t):
        if t < T_SWITCH - T_FADE:
            a.draw(base, t)
        elif t < T_SWITCH:
            # dip through the background: answer fades out, then the new task fades in
            k = (t - (T_SWITCH - T_FADE)) / T_FADE
            screen, st, k = (a, t, 1 - 2 * k) if k < 0.5 else (b, 0.0, 2 * k - 1)
            k = k * k * (3 - 2 * k)                                      # smoothstep
            fg = base.copy()
            screen.draw(fg, st)
            base.paste(Image.blend(base, fg, k))
        else:
            b.draw(base, t - T_SWITCH)
    return 16.0, draw

VIDEOS = {"video1_B1": video1, "video2_B2": video2}
PREVIEW_T = {"video1_B1": [2.0], "video2_B2": [2.0, 7.0]}

BG = gradient()

def frame(draw, t):
    base = BG.copy()
    draw(base, t)
    return base.convert("RGB")

def render(name, dur, draw):
    out = f"{name}.mp4"
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-an",
                            "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high",
                            "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for i in range(int(round(dur * FPS))):
        enc.stdin.write(frame(draw, i / FPS).tobytes())
    enc.stdin.close(); enc.wait()
    print("wrote", out)

if __name__ == "__main__":
    for name, make in VIDEOS.items():
        dur, draw = make()
        if sys.argv[1:] == ["preview"]:
            for t in PREVIEW_T[name]:
                p = f"preview_{name}_{t:.0f}s.png"
                frame(draw, t).save(p); print("wrote", p)
        else:
            render(name, dur, draw)
