"""Reels «Проверь уровень на слух»: talking cat reads a story that climbs A1 -> B2.

Usage: KOKORO_DIR=/path/with/kokoro-v1.0.onnx+voices-v1.0.bin python3 cat_listening_render.py cat.jpg
Voice: Kokoro TTS (am_michael). Palette: Champagne #FBDFA2 / Chocolate #442216.
Output: cat_listening_reels.mp4
"""
import os, re, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
SR = 24000
INTER = "/usr/share/fonts/opentype/inter/Inter-{}.otf"
F_HOOK = ImageFont.truetype(INTER.format("Bold"), 58)
F_Q = ImageFont.truetype(INTER.format("Bold"), 60)
F_LVL = ImageFont.truetype(INTER.format("ExtraBold"), 54)
F_TAG = ImageFont.truetype(INTER.format("SemiBold"), 34)

HOOK = "Проверь свой уровень на слух.\nНа каком куске перестал(а) понимать?"
QUESTION = "Why does Anna think losing her suitcase was a good thing?"
VOICE = "am_michael"
A2_NOTE = "Твой уровень A2?\nЗагляни в описание ↓"
CHAMP = (251, 223, 162)
CHOCO = (68, 34, 22)

# (level, colour, speed, gap between sentences, text) — speech gets faster with the level
LEVELS = [
    ("A1", (76, 195, 120), 0.82, 0.45,
     "This is Anna. She is thirty. She lives in Moscow. She likes coffee and books. "
     "Today she is at the airport, and she is very happy."),
    ("A2", (64, 160, 235), 0.92, 0.38,
     "Anna is going to Bali for two weeks. She bought the tickets three months ago. "
     "But when she arrived, her suitcase wasn't there. She waited for an hour, but it never came."),
    ("B1", (245, 166, 35), 1.0, 0.32,
     "The airline told her the suitcase had been sent to Singapore by mistake, and it would take "
     "at least three days to get it back. Anna had nothing except her phone and her passport, "
     "so she decided to make the most of it."),
    ("B2", (235, 80, 90), 1.08, 0.28,
     "Looking back, she admits that losing her luggage turned out to be the best thing that could "
     "have happened. With no pile of outfits to worry about, she spent far less time getting ready "
     "and far more time actually exploring the island."),
]
HOOK_DUR = 3.2      # hook on screen before the cat starts
LEVEL_LEAD = 0.45   # badge pops this long before the level's first word
LEVEL_GAP = 0.75    # silence after each level
Q_TAIL = 4.5        # hold on the question + A2 note after it is read

# ---------------- speech ----------------
from kokoro_onnx import Kokoro
kdir = os.environ.get("KOKORO_DIR", ".")
tts = Kokoro(os.path.join(kdir, "kokoro-v1.0.onnx"), os.path.join(kdir, "voices-v1.0.bin"))

def say(text, speed):
    a, sr = tts.create(text, voice=VOICE, speed=speed, lang="en-us")
    assert sr == SR
    a = np.asarray(a, dtype=np.float32)
    nz = np.flatnonzero(np.abs(a) > 0.01)          # trim model padding
    return a[max(0, nz[0] - 240): nz[-1] + 480] if len(nz) else a

def sil(sec):
    return np.zeros(int(sec * SR), np.float32)

track = [sil(HOOK_DUR)]
t = HOOK_DUR
level_at = []   # (start_time, index)
for i, (lvl, col, speed, gap, text) in enumerate(LEVELS):
    level_at.append((t, i))
    track.append(sil(LEVEL_LEAD)); t += LEVEL_LEAD
    sents = re.split(r"(?<=[.!?])\s+", text)
    for j, s in enumerate(sents):
        a = say(s, speed); track.append(a); t += len(a) / SR
        if j < len(sents) - 1:
            track.append(sil(gap)); t += gap
    track.append(sil(LEVEL_GAP)); t += LEVEL_GAP
    print(f"{lvl}: ends at {t:.2f}s", flush=True)
q_at = t
qa = say(QUESTION, 0.95)
track += [sil(0.3), qa, sil(Q_TAIL)]
t += 0.3 + len(qa) / SR + Q_TAIL
audio = np.concatenate(track)
TOTAL = len(audio) / SR
NF = int(TOTAL * FPS)
import soundfile as sf
sf.write("cat_voice.wav", audio, SR)
print(f"total {TOTAL:.2f}s, {NF} frames", flush=True)

# mouth openness per frame from the loudness envelope
hop = SR // FPS
env = np.array([np.sqrt(np.mean(audio[k * hop:(k + 1) * hop] ** 2) + 1e-9) for k in range(NF)])
db = 20 * np.log10(env)
op = np.clip((db + 42) / 22, 0, 1)
sm = np.zeros_like(op)
for k in range(NF):  # fast open, slightly slower close
    prev = sm[k - 1] if k else 0
    sm[k] = prev + (op[k] - prev) * (0.75 if op[k] > prev else 0.5)
OPEN = np.round(sm * 10).astype(int)   # 0..10, cached

# ---------------- picture ----------------
src = Image.open(sys.argv[1]).convert("RGB")
SC = W / src.width
FG = src.resize((W, round(src.height * SC)), Image.LANCZOS).filter(
    ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
FGA = np.asarray(FG).astype(np.float32)
FG_Y = 300                                   # photo top on the canvas
MX, MY = 543 * SC, 547 * SC                 # cat's mouth line (under the nose)
HW, FALL, DMAX = 24 * SC, 40 * SC, 14 * SC   # mouth half-width, chin falloff, max jaw drop
FACE = (560 * SC, 520 * SC)                 # push-in anchor

bg = src.resize((round(src.width * H / src.height), H), Image.LANCZOS)
bg = bg.crop(((bg.width - W) // 2, 0, (bg.width - W) // 2 + W, H)).filter(ImageFilter.GaussianBlur(45))
BG = Image.blend(bg, Image.new("RGB", (W, H), CHOCO), 0.85)   # chocolate with a hint of the photo

px0, px1 = int(MX - HW - 4), int(MX + HW + 4)
py0, py1 = int(MY - 6), int(MY + FALL + DMAX + 4)
yy, xx = np.mgrid[py0:py1, px0:px1].astype(np.float32)
u = np.clip(np.abs(xx - MX) / HW, 0, 1)
wx = 0.5 * (1 + np.cos(np.pi * u))                         # 1 at centre -> 0 at corners
y0 = MY + 3 * SC * u ** 2                                  # corners sit a bit lower (cat "ω" mouth)

warp_cache = {}
def face(o):
    """Foreground with the jaw dropped by o/10 of DMAX."""
    if o in warp_cache:
        return warp_cache[o]
    if o == 0:
        warp_cache[o] = FG; return FG
    D = DMAX * o / 10
    rel = np.clip((yy - y0) / FALL, 0, 1)
    d = np.where(yy >= y0, D * wx * (1 - rel) ** 1.4, 0)
    gap = (yy >= y0) & (yy - d < y0)
    sy = np.where(gap, y0, yy - d)
    # bilinear sample of the patch
    y_lo = np.floor(sy).astype(int); fy = (sy - y_lo)[..., None]
    x_i = xx.astype(int)
    patch = FGA[y_lo, x_i] * (1 - fy) + FGA[y_lo + 1, x_i] * fy
    # mouth interior: dark at the top, a hint of pink tongue at the bottom
    depth = np.clip((yy - y0) / np.maximum(d, 1e-3), 0, 1)
    tongue = np.clip((depth - 0.55) / 0.45, 0, 1)[..., None] * min(1, o / 6)
    inside = np.array([22, 11, 12], np.float32) * (1 - tongue) + np.array([128, 62, 70], np.float32) * tongue
    m = Image.fromarray((gap * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))
    m = (np.asarray(m).astype(np.float32) / 255)[..., None]
    patch = patch * (1 - m) + inside * m
    out = FGA.copy()
    out[py0:py1, px0:px1] = patch
    img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
    warp_cache[o] = img
    return img

def ease(x):
    x = min(max(x, 0), 1)
    return 1 - (1 - x) ** 3

def plaque(text, f, top, maxw=920, pad=(38, 28), lh=1.25, alpha=255, box=CHAMP, ink=CHOCO, border=None):
    """Rounded box with centred text: champagne box + chocolate text by default."""
    lines = []
    for para in text.split("\n"):
        cur = ""
        for w in para.split(" "):
            tt = (cur + " " + w).strip()
            if f.getlength(tt) <= maxw or not cur:
                cur = tt
            else:
                lines.append(cur); cur = w
        lines.append(cur)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    lhp = int(f.size * lh)
    bw = max(f.getlength(l) for l in lines) + 2 * pad[0]
    bh = lhp * len(lines) + 2 * pad[1]
    x0 = (W - bw) / 2
    d.rounded_rectangle([x0, top, x0 + bw, top + bh], radius=26, fill=box + (alpha,),
                        outline=border + (alpha,) if border else None, width=4)
    for i, l in enumerate(lines):
        d.text(((W - f.getlength(l)) / 2, top + pad[1] + i * lhp - f.size * 0.04), l, font=f, fill=ink + (alpha,))
    return img

HOOK_IMG = plaque(HOOK, F_HOOK, FG_Y + 70, maxw=980)
Q_IMG = plaque(QUESTION, F_Q, FG_Y + 70, maxw=900)
A2_IMG = plaque(A2_NOTE, F_HOOK, 1420, maxw=900, box=CHOCO, ink=CHAMP, border=CHAMP)

def level_bar(active, pop):
    """A1 · A2 · B1 · B2 pills; the current one is coloured and pops in."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pw, ph, gap = 200, 92, 26
    x = (W - (4 * pw + 3 * gap)) / 2
    y = 150
    for i, (lvl, col, *_ ) in enumerate(LEVELS):
        if i == active:
            s = 1 + 0.18 * (1 - ease(pop)) if pop < 1 else 1
            if pop < 0.25: s = 0.8 + 1.6 * pop
            w2, h2 = pw * s, ph * s
            cx, cy = x + pw / 2, y + ph / 2
            d.rounded_rectangle([cx - w2 / 2, cy - h2 / 2, cx + w2 / 2, cy + h2 / 2], radius=h2 / 2, fill=CHAMP + (255,))
            fc = CHOCO + (255,)
        elif active is not None and i < active:
            d.rounded_rectangle([x, y, x + pw, y + ph], radius=ph / 2, fill=CHAMP + (60,))
            fc = CHAMP + (150,)
        else:
            d.rounded_rectangle([x, y, x + pw, y + ph], radius=ph / 2, outline=CHAMP + (130,), width=3)
            fc = CHAMP + (170,)
        d.text((x + (pw - F_LVL.getlength(lvl)) / 2, y + ph / 2 - F_LVL.size * 0.62), lvl, font=F_LVL, fill=fc)
        x += pw + gap
    return img

# photo edges fade into the chocolate background (mask moves with the push-in)
MASK = Image.new("L", FG.size, 255)
md = ImageDraw.Draw(MASK)
for i in range(170):
    a = int(255 * (i / 170) ** 1.3)
    md.line([(0, i), (W, i)], fill=a)
    md.line([(0, FG.height - 1 - i), (W, FG.height - 1 - i)], fill=a)

enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                        "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "cat_video_only.mp4"],
                       stdin=subprocess.PIPE)
bar_cache = {}
for k in range(NF):
    tt = k / FPS
    # slow push-in towards the face, plus a tiny nod while talking
    z = 1.0 + 0.12 * tt / TOTAL
    if tt < 0.25: z *= 1.05 - 0.2 * tt
    fg = face(int(OPEN[k]))
    fw, fh = round(FG.width * z), round(FG.height * z)
    fz = fg.resize((fw, fh), Image.BILINEAR)
    mz = MASK.resize((fw, fh), Image.BILINEAR)
    ox = FACE[0] - FACE[0] * z
    oy = FACE[1] - FACE[1] * z + FG_Y - 1.2 * OPEN[k] / 10
    fr = BG.copy()
    fr.paste(fz, (round(ox), round(oy)), mz)
    fr = fr.convert("RGBA")

    active = None
    for st, i in level_at:
        if tt >= st: active = i
    if tt >= q_at: active = None
    pop = min(1.0, (tt - level_at[active][0]) / 0.35) if active is not None else 1.0
    key = (active, round(pop, 2), tt >= q_at)
    if key not in bar_cache:
        bar_cache[key] = level_bar(active if tt < q_at else -1, pop)
    fr.alpha_composite(bar_cache[key])

    if tt < HOOK_DUR:
        fr.alpha_composite(HOOK_IMG)
    if tt >= q_at:
        a = ease((tt - q_at) / 0.3)
        dim = Image.new("RGBA", (W, H), CHOCO + (int(110 * a),))
        fr.alpha_composite(dim)
        if a < 1:
            q = Q_IMG.copy(); q.putalpha(Image.eval(q.getchannel("A"), lambda v: int(v * a)))
            fr.alpha_composite(q, (0, int(30 * (1 - a))))
        else:
            fr.alpha_composite(Q_IMG)
        b = ease((tt - q_at - 1.0) / 0.35)
        if b > 0:
            n = A2_IMG.copy(); n.putalpha(Image.eval(n.getchannel("A"), lambda v: int(v * b)))
            fr.alpha_composite(n, (0, int(40 * (1 - b))))
    enc.stdin.write(fr.convert("RGB").tobytes())
    if k % 300 == 0: print(f"frame {k}/{NF}", flush=True)
enc.stdin.close(); enc.wait()

subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "cat_video_only.mp4", "-i", "cat_voice.wav",
                "-filter_complex", "[1:a]aresample=48000,aformat=channel_layouts=stereo,highpass=f=70,"
                "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]",
                "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-shortest", "-movflags", "+faststart", "cat_listening_reels.mp4"], check=True)
for f in ("cat_video_only.mp4", "cat_voice.wav"):
    os.remove(f)
print("done", round(TOTAL, 2))
