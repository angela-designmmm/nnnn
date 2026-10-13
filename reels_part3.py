import subprocess, sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# usage: python3 reels_part3.py <talking_head.mov> <dinosaur_reel_screen_recording.mov>
SRC = sys.argv[1] if len(sys.argv) > 1 else "v4.mov"
CLIP = sys.argv[2] if len(sys.argv) > 2 else "dino.mov"
OUT = "part3_reels.mp4"
W, H, FPS = 1080, 1920, 30
INTER = "/usr/share/fonts/opentype/inter/Inter-{}.otf"
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

# Instagram Reels safe zone: top ~250px (header), bottom ~420px (caption/audio),
# right ~140px (like/comment/share buttons). All text stays inside it.
SAFE_L, SAFE_R = 70, W - 140
SAFE_CX = (SAFE_L + SAFE_R) / 2

F_TITLE = ImageFont.truetype(INTER.format("SemiBold"), 56)
F_PLAQUE = ImageFont.truetype(INTER.format("Medium"), 54)
F_SUB = ImageFont.truetype(INTER.format("Bold"), 46)
F_EMO = ImageFont.truetype(EMOJI, 109)

def is_emoji(ch):
    return ord(ch) >= 0x1F000

def text_w(s, f):
    return sum(f.size * 1.15 if is_emoji(ch) else f.getlength(ch) for ch in s)

def draw_run(img, xy, s, f, fill):
    d = ImageDraw.Draw(img)
    x, y = xy
    buf = ""
    def flush():
        nonlocal x, buf
        if buf:
            d.text((x, y), buf, font=f, fill=fill)
            x += f.getlength(buf)
            buf = ""
    for ch in s:
        if is_emoji(ch):
            flush()
            e = Image.new("RGBA", (136, 128), (0, 0, 0, 0))
            ImageDraw.Draw(e).text((0, 0), ch, font=F_EMO, embedded_color=True)
            e = e.crop(e.getbbox())
            sz = int(f.size * 1.05)
            e = e.resize((sz, int(e.height * sz / e.width)), Image.LANCZOS)
            img.alpha_composite(e, (int(x + f.size * 0.08), int(y + f.size * 0.05)))
            x += f.size * 1.15
        else:
            buf += ch
    flush()

def wrap(s, f, maxw):
    lines = []
    for para in s.split("\n"):
        cur = ""
        for word in para.split(" "):
            t = (cur + " " + word).strip()
            if text_w(t, f) <= maxw or not cur:
                cur = t
            else:
                lines.append(cur); cur = word
        lines.append(cur)
    return lines

def plaque(s, f, top, align="left", maxw=780, pad=(30, 22), lh=1.22, full_lines=None,
           fonts=None):
    """White rounded box with black text, centred inside the safe zone.
    full_lines: wrapping of the full string so a typewriter prefix keeps the final box layout.
    fonts: optional per-line fonts (for the two-language final card)."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lines = full_lines if full_lines is not None else wrap(s, f, maxw)
    shown, left = [], len(s)
    for ln in lines:
        if left <= 0: break
        shown.append(ln[:left]); left -= len(ln) + 1
    if not shown or not "".join(shown).strip():
        return img
    fl = fonts or [f] * len(shown)
    lhs = [int(ff.size * lh) for ff in fl[:len(shown)]]
    bw = max(text_w(l, ff) for l, ff in zip(shown, fl)) + 2 * pad[0]
    bh = sum(lhs) + 2 * pad[1]
    x0 = SAFE_CX - bw / 2
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x0, top, x0 + bw, top + bh], radius=22, fill=(255, 255, 255, 255))
    y = top + pad[1]
    for l, ff, lhp in zip(shown, fl, lhs):
        lw = text_w(l, ff)
        lx = x0 + pad[0] + ((bw - 2 * pad[0] - lw) / 2 if align == "center" else 0)
        draw_run(img, (lx, y - ff.size * 0.02), l, ff, (0, 0, 0, 255))
        y += lhp
    return img

HL_FILL = (255, 222, 61, 255)  # highlighter yellow

def subtitle(s, y=1315):
    """English dialogue subtitle, white bold with soft shadow.
    Words inside [brackets] get a yellow highlighter with dark text."""
    words, on = [], False
    for w in s.split(" "):
        start = w.startswith("[")
        on = on or start
        clean = w.replace("[", "").replace("]", "")
        words.append((clean, on))
        if w.endswith("]") or w.rstrip("….,!?").endswith("]"): on = False
    maxw, sp = SAFE_R - SAFE_L - 40, F_SUB.getlength(" ")
    lines, cur = [], []
    for wd in words:
        t = " ".join(x for x, _ in cur + [wd])
        if cur and F_SUB.getlength(t) > maxw:
            lines.append(cur); cur = [wd]
        else:
            cur.append(wd)
    lines.append(cur)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for i, ln in enumerate(lines):
        lw = F_SUB.getlength(" ".join(x for x, _ in ln))
        x, ly = SAFE_CX - lw / 2, y + i * 57
        for j, (wd, h) in enumerate(ln):
            ww = F_SUB.getlength(wd)
            if h:  # marker box, joined across the gap to the next highlighted word
                nxt = j + 1 < len(ln) and ln[j + 1][1]
                ImageDraw.Draw(hl).rounded_rectangle(
                    [x - 8, ly + 2, x + ww + (sp if nxt else 0) + 8, ly + F_SUB.size + 8],
                    radius=8, fill=HL_FILL)
                ImageDraw.Draw(img).text((x, ly), wd, font=F_SUB, fill=(20, 20, 20, 255))
            else:
                ImageDraw.Draw(sh).text((x, ly), wd, font=F_SUB, fill=(0, 0, 0, 210))
                ImageDraw.Draw(img).text((x, ly), wd, font=F_SUB, fill=(255, 255, 255, 255))
            x += ww + sp
    sh = sh.filter(ImageFilter.GaussianBlur(4))
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.alpha_composite(sh, (3, 3)); out.alpha_composite(sh); out.alpha_composite(hl)
    out.alpha_composite(img)
    return out

# ---------------- timeline (seconds in the talking-head source) ----------------
TITLE = "Как я ссу разговаривать с иностранцами со своим C1"

SRC_END = 21.2

# Dinosaur reel as a small tilted scrapbook card over the talking head,
# right after "...lives rent-free in my head".
CLIP_AT = 11.4
CLIP_CROP = "crop=860:1530:13:205"  # drop phone status bar, back arrow, "Add comment" bar
CARD_W = 400                         # video width inside the white border
CARD_BORDER = 12
CARD_ANGLE = 7                       # degrees, counter-clockwise
CARD_CENTER = (300, 800)             # left side, may cover the face for a moment
CLIP_GAIN_DB = -16                   # quiet under the voice

OVERLAYS = [  # (kind, start, end, text)
    ("title", 0, 99, TITLE),
    ("plaque", 0.0, 3.8, "Спойлер: не со всеми 👀"),
    ("plaque", 3.8, 7.6, "Иногда находится тот самый комфортик 🥹"),
    ("plaque", 7.6, 11.6, "в лице американского коуча"),
    ("sub", 0.3, 3.8, "Have you watched that video? The funny one?"),
    ("sub", 8.6, 11.8, "That video [lives rent-free in my head]…"),
    ("sub", 11.8, 15.6, "…and every time I see the word “dinosaur”, I pronounce it like “Dynador”"),
]

TITLE_TOP = 250
PLAQUE_TOP = 1060

cache = {}
def overlay_img(kind, text, rel_t):
    if kind == "title":
        if kind not in cache:
            cache[kind] = plaque(text, F_TITLE, TITLE_TOP, align="center", maxw=800)
        return cache[kind]
    if kind == "plaque":
        full = wrap(text, F_PLAQUE, 820)
        k = min(len(text), int(rel_t / 0.35 * len(text)) + 1)  # typewriter in 0.35s
        key = (kind, text, k)
        if key not in cache: cache[key] = plaque(text[:k], F_PLAQUE, PLAQUE_TOP, full_lines=full)
        return cache[key]
    if kind == "sub":
        key = (kind, text)
        if key not in cache: cache[key] = subtitle(text)
        return cache[key]

def frames(src, a, b, vf, w, h):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(a), "-i", src, "-t", str(b - a),
                          "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    while True:
        raw = p.stdout.read(w * h * 3)
        if len(raw) < w * h * 3: break
        yield Image.frombytes("RGB", (w, h), raw)
    p.stdout.close(); p.wait()

# ---- scrapbook card ----
CARD_H = round(CARD_W * 16 / 9)
clip_len = min(SRC_END - CLIP_AT, float(subprocess.check_output(
    ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", CLIP])))
clip_frames = list(frames(CLIP, 0, clip_len, f"{CLIP_CROP},scale={CARD_W}:{CARD_H}:flags=lanczos,fps={FPS}",
                          CARD_W, CARD_H))

def card(fr, scale):
    cw, ch = CARD_W + 2 * CARD_BORDER, CARD_H + 2 * CARD_BORDER
    c = Image.new("RGBA", (cw, ch + 26), (0, 0, 0, 0))
    ImageDraw.Draw(c).rounded_rectangle([0, 26, cw - 1, ch + 25], radius=6, fill=(250, 248, 242, 255))
    c.paste(fr, (CARD_BORDER, CARD_BORDER + 26))
    # strip of washi tape across the top edge
    tape = Image.new("RGBA", (130, 40), (236, 214, 160, 200))
    tape = tape.rotate(-4, expand=True, resample=Image.BICUBIC)
    c.alpha_composite(tape, ((cw - tape.width) // 2, 6))
    if scale != 1:
        c = c.resize((max(1, int(c.width * scale)), max(1, int(c.height * scale))), Image.LANCZOS)
    c = c.rotate(CARD_ANGLE, expand=True, resample=Image.BICUBIC)
    sh = Image.new("RGBA", c.size, (0, 0, 0, 0))
    sh.putalpha(c.getchannel("A").point(lambda v: v * 0.45))
    sh = Image.composite(Image.new("RGBA", c.size, (0, 0, 0, 255)), sh, sh)
    sh = sh.filter(ImageFilter.GaussianBlur(10))
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x, y = int(CARD_CENTER[0] - c.width / 2), int(CARD_CENTER[1] - c.height / 2)
    out.alpha_composite(sh, (x + 8, y + 12)); out.alpha_composite(c, (x, y))
    return out

def pop(t, d):  # scale for pop-in / pop-out
    if t < 0.25:
        u = t / 0.25
        return 0.6 + 0.4 * (1 + 2.2 * (u - 1) ** 3 + 1.2 * (u - 1) ** 2)  # slight overshoot
    if t > d - 0.2:
        return max(0.05, (d - t) / 0.2)
    return 1.0

enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                        "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "video_only.mp4"],
                       stdin=subprocess.PIPE)

def render(fr, t):
    fr = fr.convert("RGBA")
    ci = int(round((t - CLIP_AT) * FPS))
    if 0 <= ci < len(clip_frames):
        fr.alpha_composite(card(clip_frames[ci], pop(t - CLIP_AT, len(clip_frames) / FPS)))
    for (ok, r0, r1, txt) in OVERLAYS:
        if r0 <= t < r1:
            fr.alpha_composite(overlay_img(ok, txt, t - r0))
    enc.stdin.write(fr.convert("RGB").tobytes())

n = 0
for fr in frames(SRC, 0, SRC_END, f"scale={W}:{H}:flags=lanczos,fps={FPS}", W, H):
    render(fr, n / FPS); n += 1
enc.stdin.close(); enc.wait()
total = n / FPS

# ---------------- audio ----------------
cl = len(clip_frames) / FPS
fc = (f"[0:a]atrim=0:{SRC_END},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo[v];"
      f"[1:a]atrim=0:{cl:.3f},asetpts=PTS-STARTPTS,volume={CLIP_GAIN_DB}dB,aresample=48000,"
      f"aformat=channel_layouts=stereo,afade=t=in:d=0.2,afade=t=out:st={cl - 0.3:.3f}:d=0.3,"
      f"adelay={int(CLIP_AT * 1000)}|{int(CLIP_AT * 1000)}[c];"
      f"[v][c]amix=inputs=2:duration=first:normalize=0,apad,atrim=0:{total:.4f},highpass=f=80,"
      f"afade=t=out:st={total - 1.6:.2f}:d=1.4,loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-i", CLIP, "-filter_complex", fc, "-map", "[aout]",
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "audio.m4a"], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "video_only.mp4", "-i", "audio.m4a", "-c:v", "copy",
                "-c:a", "copy", "-shortest", "-movflags", "+faststart", OUT], check=True)
print("total", round(total, 2))
