"""Reels "vocab card" style: clip on top, lined notebook paper with a paperclip below,
English phrase (bold, bullet) + Russian translation (italic) on the lines.

Usage:  python3 vocab_render.py clips.json out.mp4
clips.json: [{"src": "v1.mov", "in": 12.3, "out": 16.9, "en": "as corny as it sounds",
              "ru": "как бы банально это ни звучало", "zoom": 1.0, "cx": 0.5, "cy": 0.4}, ...]
zoom/cx/cy are optional: extra zoom into the top video and the focus point (0..1) of the crop.
"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
VID_H = 860                       # top video area
LINE0, LINE_STEP = 1040, 92       # notebook ruling
# Reels safe zone for text: clear of the top bar, the right action buttons and the bottom caption
SAFE_X1, SAFE_Y1 = 900, 1500
HERE = os.path.dirname(os.path.abspath(__file__))
F_EN = os.path.join(HERE, "fonts/OpenSans[wdth,wght].ttf")
F_RU = os.path.join(HERE, "fonts/OpenSans-Italic[wdth,wght].ttf")


def font(path, size, weight):
    f = ImageFont.truetype(path, size)
    f.set_variation_by_axes([weight, 100])
    return f


def paper():
    """Off-white grainy paper, ruled lines, torn binder holes and a paperclip (static)."""
    rng = np.random.default_rng(7)
    ph = H - VID_H
    base = np.array([236, 238, 232], np.float32)
    blot = Image.fromarray((rng.random((ph // 40, W // 40)) * 255).astype(np.uint8)).resize(
        (W, ph), Image.BICUBIC).filter(ImageFilter.GaussianBlur(30))
    blot = (np.asarray(blot, np.float32) / 255 - 0.5) * 10
    grain = rng.normal(0, 3.2, (ph, W)).astype(np.float32)
    arr = np.clip(base[None, None, :] + (blot + grain)[..., None], 0, 255).astype(np.uint8)
    img = Image.new("RGB", (W, H), (0, 0, 0))
    img.paste(Image.fromarray(arr), (0, VID_H))
    d = ImageDraw.Draw(img)
    d.rectangle([0, VID_H, W, VID_H + 6], fill=(246, 247, 244))          # light top edge

    for y in range(LINE0, H, LINE_STEP):                                   # ruling, slightly uneven
        for x in range(0, W, 3):
            jy = y + (0.6 if (x // 90) % 2 else 0)
            d.point((x, jy), fill=(70, 76, 90)); d.point((x, jy + 1), fill=(120, 126, 138))
            if rng.random() < 0.5: d.point((x + 1, jy), fill=(95, 100, 112))
            if rng.random() < 0.7: d.point((x + 2, jy), fill=(150, 155, 162))

    holes = Image.new("RGBA", (W, H), (0, 0, 0, 0))                        # torn binder holes
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd, sd = ImageDraw.Draw(holes), ImageDraw.Draw(sh)
    for i, y in enumerate(range(VID_H + 60, H + 60, 120)):
        x0 = 22 + rng.integers(-6, 6)
        pts = []
        for t in np.linspace(0, 1, 9)[:-1]: pts.append((x0 + 78 * t, y + rng.normal(0, 2.5)))
        for t in np.linspace(0, 1, 9)[:-1]: pts.append((x0 + 78 + rng.normal(0, 2.5), y + 72 * t))
        for t in np.linspace(1, 0, 9)[:-1]: pts.append((x0 + 78 * t, y + 72 + rng.normal(0, 2.5)))
        for t in np.linspace(1, 0, 9)[:-1]: pts.append((x0 - 14 * (t < 0.5) + rng.normal(0, 2.5), y + 72 * t))
        sd.polygon([(px + 3, py + 4) for px, py in pts], fill=(0, 0, 0, 90))
        hd.polygon(pts, fill=(251, 251, 249, 255), outline=(150, 152, 150, 255))
    sh = sh.filter(ImageFilter.GaussianBlur(4))
    img = img.convert("RGBA"); img.alpha_composite(sh); img.alpha_composite(holes)

    clip = Image.new("RGBA", (W, H), (0, 0, 0, 0))                         # paperclip
    cd = ImageDraw.Draw(clip)
    def u(x0, x1, ytop0, ytop1, ybot, w, col):
        r = (x1 - x0) / 2
        cd.line([(x0, ytop0), (x0, ybot)], fill=col, width=w)
        cd.line([(x1, ytop1), (x1, ybot)], fill=col, width=w)
        cd.arc([x0 - w / 2, ybot - r - w / 2, x1 + w / 2, ybot + r + w / 2], 0, 180, fill=col, width=w)
    u(146, 228, VID_H + 15, VID_H + 95, LINE0 + 110, 9, (40, 40, 44, 255))      # outer loop
    u(146, 228, VID_H + 15, VID_H + 95, LINE0 + 110, 3, (150, 150, 156, 255))   # highlight
    cd.arc([142, VID_H + 2, 168, VID_H + 34], 180, 360, fill=(40, 40, 44, 255), width=8)
    shadow = clip.split()[3].filter(ImageFilter.GaussianBlur(5))
    s = Image.new("RGBA", (W, H), (0, 0, 0, 0)); s.putalpha(shadow.point(lambda v: v * 0.35))
    img.alpha_composite(s, (6, 7)); img.alpha_composite(clip)
    return img


def wrap(s, f, maxw):
    """Greedy wrap; short words (в, с, под, ...) stick to the next word, as in Russian typography."""
    words, glue = [], ""
    for w in s.split():
        if len(w) <= 3 and w.isalpha(): glue += w + "\u00a0"
        else: words.append(glue + w); glue = ""
    if glue: words.append(glue.rstrip("\u00a0"))
    lines, cur = [], ""
    for word in words:
        t = (cur + " " + word).strip()
        if f.getlength(t) <= maxw or not cur: cur = t
        else: lines.append(cur); cur = word
    return lines + [cur]


def card(base, en, ru):
    img = base.copy()
    d = ImageDraw.Draw(img)
    # English: bold, bullet, sits on the 1st ruled line; shrink if it does not fit the safe zone
    size = 58
    while size > 40 and font(F_EN, size, 700).getlength(en) > SAFE_X1 - 322: size -= 2
    fe = font(F_EN, size, 700)
    base_y = LINE0 + LINE_STEP - 16
    d.ellipse([268, base_y - size * 0.4 - 11, 290, base_y - size * 0.4 + 11], fill=(0, 0, 0))
    d.text((322, base_y), en, font=fe, fill=(0, 0, 0), anchor="ls")
    # Russian: italic, one empty row below, up to 3 lines, kept inside the safe zone
    size = 52
    while True:
        fr = font(F_RU, size, 400)
        lines = wrap(ru, fr, SAFE_X1 - 300)
        if len(lines) <= 3 or size <= 40: break
        size -= 2
    for i, ln in enumerate(lines[:3]):
        y = LINE0 + (3 + i) * LINE_STEP - 26
        assert y + 14 <= SAFE_Y1, "translation runs out of the safe zone"
        d.text((300, y), ln, font=fr, fill=(0, 0, 0), anchor="ls")
    return img


def render(clips, out, tmp):
    base = paper()
    os.makedirs(tmp, exist_ok=True)
    inputs, filt, cat = [], [], ""
    for i, c in enumerate(clips):
        png = os.path.join(tmp, f"card{i}.png")
        card(base, c["en"], c["ru"]).convert("RGB").save(png)
        d = c["out"] - c["in"]
        z, cx, cy = c.get("zoom", 1.0), c.get("cx", 0.5), c.get("cy", 0.5)
        inputs += ["-ss", str(c["in"]), "-t", f"{d:.3f}", "-i", c["src"],
                   "-loop", "1", "-t", f"{d:.3f}", "-r", str(FPS), "-i", png]
        vw, vh = int(W * z), int(VID_H * z)
        filt.append(
            f"[{2*i}:v]fps={FPS},scale={vw}:{vh}:force_original_aspect_ratio=increase:flags=lanczos,"
            f"crop={W}:{VID_H}:(iw-{W})*{cx}:(ih-{VID_H})*{cy},setsar=1[t{i}];"
            f"[{2*i+1}:v][t{i}]overlay=0:0:shortest=1,format=yuv420p,setsar=1[v{i}];"
            f"[{2*i}:a]aresample=48000,aformat=channel_layouts=stereo,"
            f"afade=t=in:d=0.02,afade=t=out:st={d-0.03:.3f}:d=0.03,apad,atrim=0:{d:.3f}[a{i}]")
        cat += f"[v{i}][a{i}]"
    fc = ";".join(filt) + f";{cat}concat=n={len(clips)}:v=1:a=1[v][a0];" \
         "[a0]highpass=f=80,loudnorm=I=-14:TP=-1.5:LRA=11[a]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc,
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", out],
                   check=True)


if __name__ == "__main__":
    clips = json.load(open(sys.argv[1]))
    out = sys.argv[2] if len(sys.argv) > 2 else "vocab_reels.mp4"
    render(clips, out, os.path.splitext(out)[0] + "_tmp")
    print("done", out)
