import subprocess, numpy as np, sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
FONT = "fonts/Inter.ttf"
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

def font(size, weight):
    f = ImageFont.truetype(FONT, size)
    f.set_variation_by_name(weight)
    return f

F_PLAQUE = font(58, "Medium")
F_FINAL = font(62, "SemiBold")
F_SUB = font(50, "Bold")
F_EMO = ImageFont.truetype(EMOJI, 109)

def is_emoji(ch):
    return ord(ch) >= 0x1F000

def text_w(s, f):
    w = 0
    for ch in s:
        if is_emoji(ch):
            w += f.size * 1.15
        else:
            w += f.getlength(ch)
    return w

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

def plaque(s, f, top, align="left", center=True, maxw=860, pad=(30, 22), lh=1.22, full_lines=None):
    """White rounded box with black text (Instagram 'classic' style as in part 1).
    full_lines: wrapping of the full string so a typewriter prefix keeps the final box layout."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lines = full_lines if full_lines is not None else wrap(s, f, maxw)
    # typewriter: cut the laid-out lines to len(s) characters
    shown, left = [], len(s)
    for ln in lines:
        if left <= 0: break
        shown.append(ln[:left]); left -= len(ln) + 1
    if not shown or not "".join(shown).strip():
        return img
    lhp = int(f.size * lh)
    bw = max(text_w(l, f) for l in shown) + 2 * pad[0]
    bh = lhp * len(shown) + 2 * pad[1]
    x0 = (W - bw) / 2 if center else 100
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x0, top, x0 + bw, top + bh], radius=22, fill=(255, 255, 255, 255))
    for i, l in enumerate(shown):
        lw = text_w(l, f)
        lx = x0 + pad[0] + ((bw - 2 * pad[0] - lw) / 2 if align == "center" else 0)
        draw_run(img, (lx, top + pad[1] + i * lhp - f.size * 0.02), l, f, (0, 0, 0, 255))
    return img

def subtitle(s, y=1560):
    """English dialogue subtitle, white bold with shadow, like the burned-in subs of part 1."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lines = wrap(s, F_SUB, 900)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for i, l in enumerate(lines):
        lw = F_SUB.getlength(l)
        pos = ((W - lw) / 2, y + i * 62)
        ImageDraw.Draw(sh).text(pos, l, font=F_SUB, fill=(0, 0, 0, 200))
        ImageDraw.Draw(img).text(pos, l, font=F_SUB, fill=(255, 255, 255, 255))
    sh = sh.filter(ImageFilter.GaussianBlur(4))
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.alpha_composite(sh, (3, 3)); out.alpha_composite(sh); out.alpha_composite(img)
    return out

# ---------------- timeline ----------------
TITLE = "Как я ссу разговаривать с незнакомцами на своём C1. Часть 2"
FINAL = "Что я поняла за годы\nразговоров с иностранцами:\nглавное — начать.\nГлавное — не ссать."

# (kind, source, in, out, overlays)   overlays: (kind, rel_start, rel_end, text)
SEGS = [
    ("vid", "v3.mov", 0.05, 3.10, [("title", 0, 99, TITLE)]),
    ("vid", "v2.mov", 6.35, 8.95, [("plaque", 0, 99, "Первые секунды: хочется провалиться сквозь землю 🫠")]),
    ("img", "meme_nervous.webp", 0, 1.5, []),
    ("vid", "v3.mov", 3.25, 8.90, [("plaque", 0, 99, "Но стоило один раз перебороть страх…"),
                                    ("sub", 0.05, 2.0, "Is there like a story?"),
                                    ("sub", 2.0, 5.65, "A storyline? A plot, and it's developing?")]),
    ("vid", "v3.mov", 10.00, 13.70, [("plaque", 0, 99, "…и мы уже болтаем про эту книгу"),
                                      ("sub", 1.0, 3.7, "And the story is really nice")]),
    ("vid", "v3.mov", 13.70, 16.20, [("plaque", 0, 99, "потом про все остальные, которые она читала")]),
    ("vid", "v3.mov", 16.20, 17.78, [("plaque", 0, 99, "я уже забыла, что мне было страшно"),
                                      ("sub", 0.1, 1.58, "I've heard of it")]),
    ("img", "meme_cool.webp", 0, 1.3, []),
    ("vid", "v2.mov", 0.00, 6.30, [("plaque", 0, 3.6, "И конечно, куда же без этого 😅"),
                                    ("sub", 0.0, 1.25, "From Russia."),
                                    ("sub", 1.25, 3.8, "Oh, you're from Russia?"),
                                    ("sub", 3.8, 6.3, "Yeah, well, my parents are Asian, so yeah")]),
    ("vid", "v2.mov", 8.95, 18.30, [("sub", 0.1, 3.3, "I was expecting you to be from, like, East Asia"),
                                     ("sub", 3.3, 6.1, "…but the accent was just not Asian at all"),
                                     ("sub", 6.1, 9.35, "So yeah… okay, thank you very much!")]),
    ("vid", "v2.mov", 18.30, 21.50, [("final", 0, 99, FINAL)]),
]
FREEZE_END = 1.6  # hold last frame under the final plaque

PLAQUE_TOP = 1170
TITLE_TOP = 70

def frames_of_video(src, a, b):
    n = int(round((b - a) * FPS))
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(a), "-i", src, "-t", str(b - a),
                          "-vf", f"scale={W}:{H}:flags=lanczos,fps={FPS}", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    got = []
    for _ in range(n):
        raw = p.stdout.read(W * H * 3)
        if len(raw) < W * H * 3: break
        got.append(Image.frombytes("RGB", (W, H), raw))
    p.stdout.close(); p.wait()
    while len(got) < n: got.append(got[-1])
    return got

def meme_frames(src, dur):
    im = Image.open(src).convert("RGB")
    bg = im.resize((W, int(im.height * W / im.width) * 2), Image.LANCZOS)
    bg = im.resize((int(im.width * H / im.height), H), Image.LANCZOS)
    bg = bg.crop(((bg.width - W) // 2, 0, (bg.width - W) // 2 + W, H)).filter(ImageFilter.GaussianBlur(40))
    bg = Image.eval(bg, lambda v: int(v * 0.55))
    n = int(round(dur * FPS)); out = []
    for i in range(n):
        z = 1.0 + 0.10 * i / max(1, n - 1)          # slow push-in
        if i < 3: z *= 1.08 - 0.027 * i             # small punch on the cut
        fw = int(W * z); fh = int(im.height * fw / im.width)
        fg = im.resize((fw, fh), Image.LANCZOS)
        fr = bg.copy()
        fr.paste(fg, ((W - fw) // 2, (H - fh) // 2 - 60))
        out.append(fr)
    return out

cache = {}
def overlay_img(kind, text, rel_t):
    if kind == "title":
        key = (kind, text)
        if key not in cache: cache[key] = plaque(text, F_PLAQUE, TITLE_TOP, align="center", maxw=880)
        return cache[key]
    if kind in ("plaque", "plaque_static"):
        full = wrap(text, F_PLAQUE, 860)
        n = len(text)
        k = n if kind == "plaque_static" else min(n, int(rel_t / 0.35 * n) + 1)  # typewriter in 0.35s
        key = (kind, text, k)
        if key not in cache: cache[key] = plaque(text[:k], F_PLAQUE, PLAQUE_TOP, full_lines=full)
        return cache[key]
    if kind == "sub":
        key = (kind, text)
        if key not in cache: cache[key] = subtitle(text)
        return cache[key]
    if kind == "final":
        key = (kind, text)
        if key not in cache:
            lines = wrap(text, F_FINAL, 880)
            bh = int(F_FINAL.size * 1.3) * len(lines) + 60
            cache[key] = plaque(text, F_FINAL, 1120, align="center", maxw=980,
                                pad=(40, 30), lh=1.3)
        return cache[key]

enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                        "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "video_only.mp4"],
                       stdin=subprocess.PIPE)
audio_parts = []
t_global = 0.0
for si, (kind, src, a, b, ovs) in enumerate(SEGS):
    if kind == "vid":
        frs = frames_of_video(src, a, b)
        audio_parts.append(("vid", src, a, a + len(frs) / FPS))
    else:
        frs = meme_frames(src, b)
        audio_parts.append(("sil", len(frs) / FPS))
    last = si == len(SEGS) - 1
    if last:
        frs += [frs[-1]] * int(FREEZE_END * FPS)
        audio_parts.append(("sil", FREEZE_END))
    for i, fr in enumerate(frs):
        rel = i / FPS
        fr = fr.convert("RGBA")
        if last:  # dim under the final plaque
            fade = min(1.0, rel / 0.4)
            fr = Image.blend(fr, Image.new("RGBA", (W, H), (0, 0, 0, 255)), 0.45 * fade)
        for (ok, r0, r1, txt) in ovs:
            if r0 <= rel < r1:
                fr.alpha_composite(overlay_img(ok, txt, rel - r0))
        enc.stdin.write(fr.convert("RGB").tobytes())
    print(f"seg {si} {kind} {src} {a}-{b}: {len(frs)} frames @ {t_global:.2f}s", flush=True)
    t_global += len(frs) / FPS
enc.stdin.close(); enc.wait()

# ---------------- audio ----------------
inputs, filt, labels = [], [], []
import json; json.dump([audio_parts, t_global], open("audio_parts.json", "w"))
for i, p in enumerate(audio_parts):
    idx = i
    if p[0] == "vid":
        _, src, a, b = p
        d = b - a
        inputs += ["-i", src]
        filt.append(f"[{idx}:a]atrim={a}:{b},asetpts=PTS-STARTPTS,aresample=48000,"
                    f"aformat=channel_layouts=stereo,afade=t=in:d=0.02,afade=t=out:st={d-0.03:.3f}:d=0.03,apad,atrim=0:{d:.4f}[a{i}]")
    else:
        inputs += ["-f", "lavfi", "-t", str(p[1]), "-i", "anullsrc=r=48000:cl=stereo"]
        filt.append(f"[{idx}:a]anull[a{i}]")
    labels.append(f"[a{i}]")
fc = ";".join(filt) + ";" + "".join(labels) + f"concat=n={len(labels)}:v=0:a=1,highpass=f=80," \
     "afade=t=out:st=%.2f:d=1.2,loudnorm=I=-14:TP=-1.5:LRA=11[aout]" % (t_global - 1.3)
subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc, "-map", "[aout]",
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "audio.m4a"], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "video_only.mp4", "-i", "audio.m4a", "-c:v", "copy",
                "-c:a", "copy", "-shortest", "-movflags", "+faststart", "part2_reels.mp4"], check=True)
print("total", round(t_global, 2))
