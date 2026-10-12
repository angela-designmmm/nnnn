"""Reels «6070 → 9157 слов» for @secondnature.eng.

Text-only version (no voiceover yet): hook with the student's own audio, then
on-screen text over lesson footage with background music, results, CTA.

  python3 render.py preview   # stills of every scene with the Reels safe zones -> out/
  python3 render.py           # out/reel_6070-9157.mp4 + out/cover.png

Inputs: assets/progress.mov (lesson clip, 21 s, rotated -90), assets/results.png,
optional assets/music.mp3 (otherwise a soft placeholder track is synthesised).
"""
import os, subprocess, sys
import numpy as np
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


# ---------------- lesson footage ----------------
SRC = os.path.join(HERE, "assets", "progress.mov")
SW, SH = 988, 1370                       # displayed (rotated) size of the source
AR = 48000


def fit_crop(z, center):
    """Source-space crop box (x, y, w, h) for zoom z (1 = cover the 9:16 frame) around `center`."""
    s = H / SH * z
    w, h = W / s, H / s
    x = min(max(center[0] - w / 2, 0), SW - w)
    y = min(max(center[1] - h / 2, 0), SH - h)
    return x, y, w, h


def clip_frames(a, b, z0, z1, center):
    """Frames of [a, b) with a slow zoom z0 -> z1 around `center` (source px)."""
    n = int(round((b - a) * FPS))
    zm = max(z0, z1)
    s = H / SH * zm                           # decode once at the largest zoom
    sw, sh = round(SW * s), round(SH * s)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{a:.3f}", "-i", SRC, "-t", f"{b - a + 0.2:.3f}",
                          "-vf", f"fps={FPS},scale={sw}:{sh}:flags=lanczos", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    out = []
    for i in range(n):
        raw = p.stdout.read(sw * sh * 3)
        if len(raw) < sw * sh * 3:
            break
        fr = Image.frombytes("RGB", (sw, sh), raw)
        z = z0 + (z1 - z0) * i / max(1, n - 1)
        x, y, w, h = fit_crop(z, center)
        box = (x * s, y * s, min((x + w) * s, sw), min((y + h) * s, sh))
        out.append(fr.resize((W, H), Image.BICUBIC, box=box))
    p.stdout.close(); p.wait()
    while len(out) < n:
        out.append(out[-1])
    return out


def clip_audio(a, b):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{a:.3f}", "-i", SRC, "-t", f"{b - a:.3f}",
                          "-map", "0:a", "-ac", "2", "-ar", str(AR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
    n = int(round((b - a) * FPS)) * AR // FPS
    x = np.pad(x, ((0, max(0, n - len(x))), (0, 0)))[:n]
    f = int(0.03 * AR)                       # click-free cuts
    x[:f] *= np.linspace(0, 1, f)[:, None]; x[-f:] *= np.linspace(1, 0, f)[:, None]
    return x


# ---------------- text overlays ----------------
def rich_line(d, x, y, text, fh, fa, fill):
    """Draw a Playfair line where '→' comes from Montserrat. Returns width when d is None."""
    parts = text.split("→")
    gap = fh.size * 0.16
    x0 = x
    for i, p in enumerate(parts):
        p = p.strip()
        if d: d.text((x, y), p, font=fh, fill=fill)
        x += fh.getlength(p)
        if i < len(parts) - 1:
            if d: d.text((x + gap, y + fh.size * 0.2), "→", font=fa, fill=fill)
            x += fa.getlength("→") + 2 * gap
    return x - x0


def headline_layer(text="6070 → 9157 слов", size=120, top=SAFE_TOP + 30):
    fh, fa = F_HEAD(size), font("Montserrat.ttf", int(size * 0.78), "SemiBold")
    tw = rich_line(None, 0, 0, text, fh, fa, None)
    pad = (40, 26)
    bw, bh = tw + 2 * pad[0], int(size * 1.25) + 2 * pad[1]
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x0 = CX - bw / 2
    d.rounded_rectangle([x0, top, x0 + bw, top + bh], radius=30, fill=CHAMP + (255,))
    rich_line(d, x0 + pad[0], top + pad[1] - size * 0.05, text, fh, fa, CHOCO + (255,))
    return img


def bottom_plaque(text, head=None, bottom=1450, f=None, f_head=None):
    """Chocolate plaque whose bottom edge sits at `bottom` (above the nick and the safe zone)."""
    f = f or F_TEXT(44)
    f_head = f_head or F_HEAD(62)
    tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bh = plaque(tmp, text, f, 0, head=head, f_head=f_head if head else None)
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.alpha_composite(tmp, (0, bottom - bh))
    return out


def fade_in(layer, t, dur=0.35, rise=30):
    a = ease(t / dur)
    if a >= 1:
        return layer, 0
    l = layer.copy()
    l.putalpha(Image.eval(l.getchannel("A"), lambda v: int(v * a)))
    return l, int(rise * (1 - a))


def nick_layer(color, pill=None):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if pill:                                   # small backing so it reads over bright footage
        tw, y = F_NICK.getlength("@secondnature.eng"), H - SAFE_BOTTOM - 56
        ImageDraw.Draw(img).rounded_rectangle([CX - tw / 2 - 18, y - 6, CX + tw / 2 + 18, y + 44],
                                              radius=25, fill=pill + (230,))
    nick(img, color)
    return img


# ---------------- timeline ----------------
FACE = (300, 640)                 # Angela's face, source px
HOOK_SUBS = [(0.0, 3.3, "But this one… wow, I didn't expect that."),
             (3.3, 6.25, "I thought it was just a minor one.")]
ITEMS = [  # (clips [(a, b)], zoom from, zoom to, centre, head, text)
    ([(3.3, 8.3)], 1.0, 1.06, FACE, None,
     "У неё высокий уровень. Но принцип один и тот же, даже если ты сейчас на A2"),
    ([(8.3, 14.3)], 1.12, 1.18, (320, 700), "1. Рециркуляция слов.", "Возвращаемся к словам из урока в урок"),
    ([(0.0, 3.3), (18.25, 21.1)], 1.28, 1.34, (280, 600), "2. Разные контексты.",
     "Встречаем слово снова и снова, поэтому запоминаем намного больше"),
    ([(14.3, 20.3)], 1.05, 1.12, (360, 720), "3. Слова сразу в речь.", "На занятиях вы говорите 75–80% времени"),
    ([(5.0, 10.0)], 1.35, 1.42, (300, 620), "4. Домашка с автопроверкой.", "Ошибся, сразу видишь, где и почему"),
]
RESULTS_DUR, CTA_DUR = 5.0, 4.5

HEAD_L = headline_layer()
NICK_VIDEO = nick_layer(CHAMP, pill=CHOCO)
SUB_L = {txt: bottom_plaque(txt, f=F_TEXT(46)) for _, _, txt in HOOK_SUBS}


def hook_frames():
    frs = clip_frames(0.0, 3.3, 1.0, 1.03, FACE) + clip_frames(15.3, 18.25, 1.06, 1.09, FACE)
    for i, fr in enumerate(frs):
        t = i / FPS
        fr = fr.convert("RGBA")
        fr.alpha_composite(HEAD_L)
        for a, b, txt in HOOK_SUBS:
            if a <= t < b:
                fr.alpha_composite(SUB_L[txt])
        yield fr


def item_frames(clips, z0, z1, center, head, text):
    total = sum(b - a for a, b in clips)
    frs, acc = [], 0.0
    for a, b in clips:          # one continuous zoom across the clips of a scene
        d = b - a
        frs += clip_frames(a, b, z0 + (z1 - z0) * acc / total, z0 + (z1 - z0) * (acc + d) / total, center)
        acc += d
    layer = bottom_plaque(text, head)
    for i, fr in enumerate(frs):
        fr = fr.convert("RGBA")
        l, dy = fade_in(layer, i / FPS)
        fr.alpha_composite(l, (0, dy))
        fr.alpha_composite(NICK_VIDEO)
        yield fr


def still_frames(fn, dur):
    for i in range(int(round(dur * FPS))):
        yield fn(i / FPS, dur)


def scenes():
    """(name, duration, frame generator, has original audio clips)"""
    out = [("hook", 6.25, hook_frames, [(0.0, 3.3), (15.3, 18.25)])]
    for k, it in enumerate(ITEMS):
        out.append((f"item{k}", sum(b - a for a, b in it[0]), lambda it=it: item_frames(*it), None))
    out.append(("results", RESULTS_DUR, lambda: still_frames(results_frame, RESULTS_DUR), None))
    out.append(("cta", CTA_DUR, lambda: still_frames(cta_frame, CTA_DUR), None))
    return out


# ---------------- music ----------------
def synth_music(dur, sr=AR, bpm=78):
    """Soft placeholder bed: electric-piano chords + round bass + light shaker (Cmaj7 Am7 Fmaj7 G6)."""
    rng = np.random.default_rng(7)
    n = int(dur * sr)
    out = np.zeros((n, 2), np.float32)
    beat = 60 / bpm
    chords = [[48, 60, 64, 67, 71], [45, 57, 60, 64, 67], [41, 57, 60, 64, 69], [43, 55, 59, 62, 64]]
    hz = lambda m: 440 * 2 ** ((m - 69) / 12)

    def note(t0, length, f, amp, bright=1.0, pan=0.0):
        i0 = int(t0 * sr)
        if i0 >= n: return
        m = min(int(length * sr), n - i0)
        tt = np.arange(m) / sr
        env = np.exp(-tt * 2.2) * (1 - np.exp(-tt * 300))
        env *= np.clip((length - tt) / 0.08, 0, 1)
        trem = 1 + 0.08 * np.sin(2 * np.pi * 4.5 * tt)
        x = (np.sin(2 * np.pi * f * tt) + 0.35 * bright * np.sin(4 * np.pi * f * tt) * np.exp(-tt * 6)
             + 0.12 * bright * np.sin(6 * np.pi * f * tt) * np.exp(-tt * 9)) * env * trem * amp
        out[i0:i0 + m, 0] += x * (1 - pan); out[i0:i0 + m, 1] += x * (1 + pan)

    bar = 4 * beat
    t, k = 0.0, 0
    while t < dur:
        c = chords[k % 4]
        for j, m in enumerate(c[1:]):                       # chord on 1, re-voiced on the "and" of 3
            note(t + j * 0.012, bar, hz(m), 0.07, pan=(j - 1.5) * 0.15)
            note(t + 2.5 * beat + j * 0.012, 1.5 * beat, hz(m + 12 if j == 3 else m), 0.035, 0.6, (1.5 - j) * 0.15)
        note(t, 2 * beat, hz(c[0] - 12), 0.16, 0.3)          # bass
        note(t + 2 * beat, 1.8 * beat, hz(c[0] - 12 + (7 if k % 2 else 0)), 0.12, 0.3)
        for e in range(8):                                    # shaker on eighths
            i0 = int((t + e * beat / 2) * sr)
            m = min(int(0.06 * sr), n - i0)
            if m <= 0: continue
            sh = rng.standard_normal(m) * np.exp(-np.arange(m) / sr * 60) * (0.012 if e % 2 else 0.007)
            out[i0:i0 + m] += np.diff(np.concatenate([[0], sh]))[:, None]
        t += bar; k += 1
    f = int(1.0 * sr)
    out[:f] *= np.linspace(0, 1, f)[:, None]; out[-2 * f:] *= np.linspace(1, 0, 2 * f)[:, None]
    return out


def load_music(dur):
    mp = os.path.join(HERE, "assets", "music.mp3")
    if os.path.exists(mp):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", mp, "-t", f"{dur:.3f}", "-ac", "2", "-ar", str(AR),
                              "-f", "f32le", "-"], capture_output=True, check=True).stdout
        x = np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
        return np.pad(x, ((0, max(0, int(dur * AR) - len(x))), (0, 0)))[:int(dur * AR)]
    return synth_music(dur)


def rms_db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)


def mix(sc):
    total = sum(d for _, d, _, _ in sc)
    n = int(round(total * FPS)) * AR // FPS
    voice = np.zeros((n, 2), np.float32)
    duck = np.ones(n, np.float32)
    t = 0.0
    for _, d, _, clips in sc:
        if clips:
            v = np.concatenate([clip_audio(a, b) for a, b in clips])
            i0 = int(round(t * FPS)) * AR // FPS
            voice[i0:i0 + len(v)] += v[:n - i0]
            duck[i0:i0 + len(v)] = 0
        t += d
    # 0 under the voice, 1 elsewhere, with 0.4 s ramps
    k = int(0.4 * AR)
    duck = np.convolve(duck, np.ones(k) / k, mode="same").astype(np.float32)
    v_on = voice[np.abs(voice).max(1) > 1e-4]
    voice *= 10 ** ((-18 - rms_db(v_on)) / 20)               # student's voice ≈ -18 dBFS RMS
    music = load_music(total)
    music *= 10 ** ((-20 - rms_db(music[int(8 * AR):int(30 * AR)])) / 20)
    music *= (10 ** (-22 / 20) + (1 - 10 ** (-22 / 20)) * duck)[:, None]   # -22 dB under the voice
    return voice + music, total


def render():
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    sc = scenes()
    audio, total = mix(sc)
    wav = os.path.join(HERE, "out", "_mix.f32")
    audio.astype(np.float32).tofile(wav)
    tmpv = os.path.join(HERE, "out", "_video.mp4")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                            "-pix_fmt", "yuv420p", tmpv], stdin=subprocess.PIPE)
    t = 0.0
    for name, d, gen, _ in sc:
        n = int(round(d * FPS)); k = 0
        for fr in gen():
            if k >= n: break
            enc.stdin.write(fr.convert("RGB").tobytes()); k += 1
        print(f"{name:8s} {t:6.2f}s +{d:.2f}s ({k} frames)", flush=True)
        t += d
    enc.stdin.close(); enc.wait()
    out = os.path.join(HERE, "out", "reel_6070-9157.mp4")
    raw_in = ["-f", "f32le", "-ar", str(AR), "-ac", "2", "-i", wav]
    target = "I=-14:TP=-1.5:LRA=11"
    # two-pass loudnorm: measure, then normalise linearly to -14 LUFS (a limiter catches the peaks)
    log = subprocess.run(["ffmpeg", "-hide_banner", *raw_in, "-af", f"loudnorm={target}:print_format=json",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    import json
    m = json.loads(log[log.rindex("{"):log.rindex("}") + 1])
    gain = -14 - float(m["input_i"])
    af = (f"volume={gain:.2f}dB,alimiter=limit={10 ** (-1.5 / 20):.4f}:attack=5:release=60:level=disabled,"
          "aresample=48000")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmpv, *raw_in,
                    "-af", af, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest",
                    "-movflags", "+faststart", out], check=True)
    os.remove(wav); os.remove(tmpv)
    print("total", round(total, 2))


def cover():
    fr = clip_frames(15.6, 15.7, 1.06, 1.06, FACE)[0].convert("RGBA")
    fr.alpha_composite(headline_layer(size=130, top=330))
    fr.convert("RGB").save(os.path.join(HERE, "out", "cover.png"))


def preview():
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    shots = []
    for name, d, gen, _ in scenes():
        for k, fr in enumerate(gen()):
            if k == int(min(d - 0.3, 1.5) * FPS):
                shots.append((name, fr)); break
    for name, im in shots:
        safe_overlay(im.convert("RGBA")).convert("RGB").save(os.path.join(HERE, "out", f"preview_{name}.png"))
    print("ok", [n for n, _ in shots])


if __name__ == "__main__":
    if sys.argv[1:2] == ["preview"]:
        preview()
    else:
        render(); cover()
