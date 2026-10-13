import subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# usage: python3 reels_part3.py <source.mov>
SRC = sys.argv[1] if len(sys.argv) > 1 else "v4.mov"
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
F_FINAL = ImageFont.truetype(INTER.format("SemiBold"), 52)
F_FINAL_EN = ImageFont.truetype(INTER.format("Bold"), 56)
F_SUB = ImageFont.truetype(INTER.format("Bold"), 48)
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

def subtitle(s, y=1330):
    """English dialogue subtitle, white bold with soft shadow."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for i, l in enumerate(wrap(s, F_SUB, SAFE_R - SAFE_L - 40)):
        pos = (SAFE_CX - F_SUB.getlength(l) / 2, y + i * 60)
        ImageDraw.Draw(sh).text(pos, l, font=F_SUB, fill=(0, 0, 0, 210))
        ImageDraw.Draw(img).text(pos, l, font=F_SUB, fill=(255, 255, 255, 255))
    sh = sh.filter(ImageFilter.GaussianBlur(4))
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.alpha_composite(sh, (3, 3)); out.alpha_composite(sh); out.alpha_composite(img)
    return out

# ---------------- timeline (seconds in the source) ----------------
TITLE = "Как я ссу разговаривать с иностранцами со своим C1"
FINAL_EN = "Find your comfort person 🫶"
FINAL_RU = "С правильным человеком\nтвой C1 наконец-то заговорит"

SRC_END = 21.2
FINAL_AT = 18.3
FREEZE_END = 1.6  # hold last frame under the final card

OVERLAYS = [  # (kind, start, end, text)
    ("title", 0, FINAL_AT, TITLE),
    ("plaque", 0.0, 3.8, "Спойлер: ссу не со всеми 👀"),
    ("plaque", 3.8, 7.6, "Иногда находится тот самый комфортик 🥹"),
    ("plaque", 7.6, 11.6, "в лице американского коуча"),
    ("plaque", 11.6, FINAL_AT, "и вот я уже рассказываю ей, как каждый раз произношу «Dynador» 🙈"),
    ("sub", 0.3, 3.8, "Have you watched that video? The funny one?"),
    ("sub", 8.6, 11.8, "That video lives rent-free in my head…"),
    ("sub", 11.8, 15.6, "…and every time I see the word, I pronounce it like “Dynador”"),
    ("final", FINAL_AT, 99, None),
]

TITLE_TOP = 250
PLAQUE_TOP = 1060
FINAL_TOP = 760

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
    if kind == "final":
        if kind not in cache:
            ru = wrap(FINAL_RU, F_FINAL, 800)
            lines = [FINAL_EN] + ru
            fonts = [F_FINAL_EN] + [F_FINAL] * len(ru)
            s = "\n".join(lines)
            cache[kind] = plaque(s, F_FINAL, FINAL_TOP, align="center", pad=(44, 34), lh=1.32,
                                 full_lines=lines, fonts=fonts)
        return cache[kind]

def frames(src, a, b):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(a), "-i", src, "-t", str(b - a),
                          "-vf", f"scale={W}:{H}:flags=lanczos,fps={FPS}", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    while True:
        raw = p.stdout.read(W * H * 3)
        if len(raw) < W * H * 3: break
        yield Image.frombytes("RGB", (W, H), raw)
    p.stdout.close(); p.wait()

enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                        "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "video_only.mp4"],
                       stdin=subprocess.PIPE)

def render(fr, t):
    fr = fr.convert("RGBA")
    if t >= FINAL_AT:  # dim under the final card
        fade = min(1.0, (t - FINAL_AT) / 0.4)
        fr = Image.blend(fr, Image.new("RGBA", (W, H), (0, 0, 0, 255)), 0.45 * fade)
    for (ok, r0, r1, txt) in OVERLAYS:
        if r0 <= t < r1:
            fr.alpha_composite(overlay_img(ok, txt, t - r0))
    enc.stdin.write(fr.convert("RGB").tobytes())

n, last = 0, None
for fr in frames(SRC, 0, SRC_END):
    render(fr, n / FPS); last = fr; n += 1
for _ in range(int(FREEZE_END * FPS)):
    render(last, n / FPS); n += 1
enc.stdin.close(); enc.wait()
total = n / FPS

# ---------------- audio ----------------
fc = (f"[0:a]atrim=0:{SRC_END},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,"
      f"apad,atrim=0:{total:.4f},highpass=f=80,afade=t=out:st={total - 1.6:.2f}:d=1.4,"
      "loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-filter_complex", fc, "-map", "[aout]",
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "audio.m4a"], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "video_only.mp4", "-i", "audio.m4a", "-c:v", "copy",
                "-c:a", "copy", "-shortest", "-movflags", "+faststart", OUT], check=True)
print("total", round(total, 2))
