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
F_FINAL = ImageFont.truetype(INTER.format("SemiBold"), 52)
F_FINAL_EN = ImageFont.truetype(INTER.format("Bold"), 56)
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

def subtitle(s, y=1315):
    """English dialogue subtitle, white bold with soft shadow."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for i, l in enumerate(wrap(s, F_SUB, SAFE_R - SAFE_L - 40)):
        pos = (SAFE_CX - F_SUB.getlength(l) / 2, y + i * 57)
        ImageDraw.Draw(sh).text(pos, l, font=F_SUB, fill=(0, 0, 0, 210))
        ImageDraw.Draw(img).text(pos, l, font=F_SUB, fill=(255, 255, 255, 255))
    sh = sh.filter(ImageFilter.GaussianBlur(4))
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.alpha_composite(sh, (3, 3)); out.alpha_composite(sh); out.alpha_composite(img)
    return out

# ---------------- timeline ----------------
TITLE = "Как я ссу разговаривать с иностранцами со своим C1"
FINAL_EN = "Find your comfort person 🫶"
FINAL_RU = "С правильным человеком\nтвой C1 наконец-то заговорит"

# Screen recording of the dinosaur reel: crop away the phone status bar, the back arrow
# and the "Add comment" bar, keep 9:16.
CLIP_CROP = "crop=860:1530:13:205"
CLIP_GAIN_DB = -4  # the recording is ~5 dB louder than the talking head

# (source, in, out, overlays)   overlays: (kind, rel_start, rel_end, text)
SEGS = [
    (SRC, 0.0, 3.8, [("title", 0, 99, TITLE),
                     ("plaque", 0, 99, "Спойлер: не со всеми 👀"),
                     ("sub", 0.3, 99, "Have you watched that video? The funny one?")]),
    (CLIP, 0.0, 7.7, [("top", 0, 99, "Вот то самое видео 🦖")]),
    (SRC, 3.8, 18.3, [("title", 0, 99, TITLE),
                      ("plaque", 0.0, 3.8, "Иногда находится тот самый комфортик 🥹"),
                      ("plaque", 3.8, 7.8, "в лице американского коуча"),
                      ("plaque", 7.8, 99, "и вот я уже рассказываю ей, как каждый раз произношу «Dynador» 🙈"),
                      ("sub", 4.8, 8.0, "That video lives rent-free in my head…"),
                      ("sub", 8.0, 11.8, "…and every time I see the word “dinosaur”, I pronounce it like “Dynador”")]),
    (SRC, 18.3, 21.2, [("final", 0, 99, None)]),
]
FREEZE_END = 1.6  # hold last frame under the final card

TITLE_TOP = 250
PLAQUE_TOP = 1060
FINAL_TOP = 760

cache = {}
def typed(kind, text, rel_t, top):
    full = wrap(text, F_PLAQUE, 820)
    k = min(len(text), int(rel_t / 0.35 * len(text)) + 1)  # typewriter in 0.35s
    key = (kind, text, k)
    if key not in cache: cache[key] = plaque(text[:k], F_PLAQUE, top, full_lines=full)
    return cache[key]

def overlay_img(kind, text, rel_t):
    if kind == "title":
        if kind not in cache:
            cache[kind] = plaque(text, F_TITLE, TITLE_TOP, align="center", maxw=800)
        return cache[kind]
    if kind == "plaque":
        return typed(kind, text, rel_t, PLAQUE_TOP)
    if kind == "top":  # plaque in the title slot, used over the inserted clip
        return typed(kind, text, rel_t, TITLE_TOP)
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
    vf = (CLIP_CROP + "," if src == CLIP else "") + f"scale={W}:{H}:flags=lanczos,fps={FPS}"
    n = int(round((b - a) * FPS))
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(a), "-i", src, "-t", str(b - a),
                          "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    got = []
    for _ in range(n):
        raw = p.stdout.read(W * H * 3)
        if len(raw) < W * H * 3: break
        got.append(Image.frombytes("RGB", (W, H), raw))
    p.stdout.close(); p.wait()
    while len(got) < n: got.append(got[-1])
    return got

enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                        "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "video_only.mp4"],
                       stdin=subprocess.PIPE)

audio_parts = []
total = 0.0
for si, (src, a, b, ovs) in enumerate(SEGS):
    frs = frames(src, a, b)
    audio_parts.append((src, a, len(frs) / FPS))
    last = si == len(SEGS) - 1
    if last:
        frs += [frs[-1]] * int(FREEZE_END * FPS)
    for i, fr in enumerate(frs):
        rel = i / FPS
        fr = fr.convert("RGBA")
        if last:  # dim under the final card
            fr = Image.blend(fr, Image.new("RGBA", (W, H), (0, 0, 0, 255)), 0.45 * min(1.0, rel / 0.4))
        for (ok, r0, r1, txt) in ovs:
            if r0 <= rel < r1:
                fr.alpha_composite(overlay_img(ok, txt, rel - r0))
        enc.stdin.write(fr.convert("RGB").tobytes())
    print(f"seg {si} {os.path.basename(src)} {a}-{b}: {len(frs)} frames @ {total:.2f}s", flush=True)
    total += len(frs) / FPS
enc.stdin.close(); enc.wait()

# ---------------- audio ----------------
inputs, filt, labels = [], [], []
for i, (src, a, d) in enumerate(audio_parts):
    inputs += ["-i", src]
    gain = f"volume={CLIP_GAIN_DB}dB," if src == CLIP else ""
    filt.append(f"[{i}:a]atrim={a}:{a + d:.4f},asetpts=PTS-STARTPTS,{gain}aresample=48000,"
                f"aformat=channel_layouts=stereo,afade=t=in:d=0.03,afade=t=out:st={d - 0.04:.3f}:d=0.04,"
                f"apad,atrim=0:{d:.4f}[a{i}]")
    labels.append(f"[a{i}]")
fc = (";".join(filt) + ";" + "".join(labels) + f"concat=n={len(labels)}:v=0:a=1,apad,atrim=0:{total:.4f},"
      f"highpass=f=80,afade=t=out:st={total - 1.6:.2f}:d=1.4,loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc, "-map", "[aout]",
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "audio.m4a"], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "video_only.mp4", "-i", "audio.m4a", "-c:v", "copy",
                "-c:a", "copy", "-shortest", "-movflags", "+faststart", OUT], check=True)
print("total", round(total, 2))
