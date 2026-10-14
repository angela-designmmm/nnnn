"""Fluffy cat in a sombrero dancing to dancing_cat_music.py (120 BPM, 16 s loop).

Usage: python3 dancing_cat_render.py out_dir
Writes RGBA frames straight into ffmpeg and produces:
  cat_cream.mp4        on the light slide colour, with music
  cat_brown.mp4        on the dark slide colour, with music
  cat_transparent.mov  ProRes 4444 with alpha, 720x720, with music (Keynote / PowerPoint for Mac)
  cat_transparent.webm VP9 with alpha, with music (web, Canva)
  cat_music.m4a        the music on its own
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

import dancing_cat_music as music

OUT = 1080            # final square size
SS = 2                # supersampling
C = OUT * SS
FPS = 30
BEAT = music.BEAT
LENGTH = music.LENGTH
FRAMES = int(round(LENGTH * FPS))

CREAM_BG = (250, 222, 161)
BROWN_BG = (67, 33, 21)

FUR_LIGHT = np.array([252, 232, 202], float)
FUR_BASE = np.array([236, 196, 146], float)
FUR_DARK = np.array([170, 118, 74], float)

GROUND = (C // 2, int(C * 0.945))

# ---------------------------------------------------------------- helpers

def T(x, y):
    return np.array([[1, 0, x], [0, 1, y], [0, 0, 1]], float)

def R(deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], float)

def S(sx, sy):
    return np.array([[sx, 0, 0], [0, sy, 0], [0, 0, 1]], float)

def place(canvas, sprite, M):
    """Composite sprite onto canvas using sprite->canvas affine M."""
    inv = np.linalg.inv(M)
    # bounding box of the sprite on the canvas, to keep transforms small
    w, h = sprite.size
    pts = M @ np.array([[0, w, w, 0], [0, 0, h, h], [1, 1, 1, 1]], float)
    x0 = max(0, int(math.floor(pts[0].min())) - 2)
    y0 = max(0, int(math.floor(pts[1].min())) - 2)
    x1 = min(canvas.width, int(math.ceil(pts[0].max())) + 2)
    y1 = min(canvas.height, int(math.ceil(pts[1].max())) + 2)
    if x1 <= x0 or y1 <= y0:
        return
    local = inv @ T(x0, y0)
    data = (local[0, 0], local[0, 1], local[0, 2], local[1, 0], local[1, 1], local[1, 2])
    piece = sprite.transform((x1 - x0, y1 - y0), Image.AFFINE, data, resample=Image.BICUBIC)
    canvas.alpha_composite(piece, (x0, y0))

def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)

def lerp(a, b, t):
    return a + (b - a) * t

# ---------------------------------------------------------------- fur

def fur(mask, seed, strokes=7000, length=26, light_mask=None, shade_bias=0.0,
        light_dir=(-0.45, -0.9)):
    """Turn an L-mode silhouette into a soft, shaded, fluffy RGBA sprite."""
    rnd = np.random.default_rng(seed)
    m = np.asarray(mask, float) / 255
    h, w = m.shape
    big = np.asarray(mask.filter(ImageFilter.GaussianBlur(70)), float) / 255
    gy, gx = np.gradient(big)
    lx, ly = light_dir
    shade = 0.2 + 0.85 * big - 45 * (gx * lx + gy * ly) + shade_bias
    ys = np.linspace(0, 1, h)[:, None]
    shade = shade - 0.22 * ys
    shade = np.clip(shade, 0, 1.25)
    col = np.where(
        (shade < 0.75)[..., None],
        FUR_DARK + (FUR_BASE - FUR_DARK) * (shade / 0.75)[..., None],
        FUR_BASE + (FUR_LIGHT - FUR_BASE) * np.clip((shade - 0.75) / 0.5, 0, 1)[..., None],
    )
    if light_mask is not None:
        lm = np.asarray(light_mask.filter(ImageFilter.GaussianBlur(25)), float)[..., None] / 255
        col = col + (FUR_LIGHT - col) * lm * 0.6
    col = np.clip(col, 0, 255)

    pad = length * 2
    W, H = w + 2 * pad, h + 2 * pad
    base_a = np.asarray(mask.filter(ImageFilter.GaussianBlur(3)), float)
    base = np.zeros((H, W, 4), np.uint8)
    base[pad:pad + h, pad:pad + w, :3] = col.astype(np.uint8)
    base[pad:pad + h, pad:pad + w, 3] = base_a.astype(np.uint8)
    img = Image.fromarray(base, "RGBA")

    edge = np.asarray(mask.filter(ImageFilter.GaussianBlur(14)), float) / 255
    ey, ex = np.gradient(edge)
    inside = np.argwhere(m > 0.5)
    if len(inside) == 0:
        return img, pad
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    pick = inside[rnd.integers(0, len(inside), strokes)]
    order = np.argsort(edge[pick[:, 0], pick[:, 1]])[::-1]  # interior first, edge last
    for y, x in pick[order]:
        nx, ny = -ex[y, x], -ey[y, x]
        nl = math.hypot(nx, ny)
        e = edge[y, x]
        if nl < 1e-4:
            ang = math.pi / 2 + rnd.normal(0, 0.6)
            nx, ny = math.cos(ang), math.sin(ang)
        else:
            nx, ny = nx / nl, ny / nl
            ang = math.atan2(ny, nx) + rnd.normal(0, 0.35)
            # interior strands droop downward a little
            down = math.atan2(1, 0)
            ang = lerp(down, ang, min(1, 0.35 + 1.3 * (1 - e)))
            nx, ny = math.cos(ang), math.sin(ang)
        ln = length * (0.5 + 1.2 * (1 - e)) * rnd.uniform(0.6, 1.3)
        c = col[y, x] * (rnd.uniform(0.86, 1.1) if e < 0.6 else rnd.uniform(0.95, 1.05))
        al = rnd.uniform(50, 120) if e > 0.85 else rnd.uniform(150, 230)
        c = tuple(int(v) for v in np.clip(c, 0, 255)) + (int(al),)
        x0, y0 = x + pad, y + pad
        # slightly curved, tapering tuft
        mx, my = x0 + nx * ln * 0.5 - ny * ln * 0.12, y0 + ny * ln * 0.5 + nx * ln * 0.12
        wd = int(rnd.integers(4, 8))
        d.line([(x0, y0), (mx, my)], fill=c, width=wd)
        d.line([(mx, my), (x0 + nx * ln, y0 + ny * ln)], fill=c, width=max(2, wd - 3))
    layer = layer.filter(ImageFilter.GaussianBlur(1.8))
    img.alpha_composite(layer)
    return img, pad

def ellipse_mask(size, boxes):
    m = Image.new("L", size, 0)
    d = ImageDraw.Draw(m)
    for b in boxes:
        d.ellipse(b, fill=255)
    return m

# ---------------------------------------------------------------- sprites

def make_body():
    w, h = 700, 760
    m = ellipse_mask((w, h), [(40, 40, 660, 740), (70, 260, 630, 750)])
    belly = ellipse_mask((w, h), [(190, 260, 510, 700)])
    img, pad = fur(m, 1, strokes=6500, light_mask=belly)
    # anchor: bottom-centre of the body ellipse
    return img, (pad + 350, pad + 740)

def make_arm():
    w, h = 220, 380
    m = ellipse_mask((w, h), [(40, 10, 180, 300), (25, 220, 195, 370)])
    img, pad = fur(m, 2, strokes=1800, length=20, shade_bias=0.1)
    # little toe lines on the paw
    d = ImageDraw.Draw(img)
    for dx in (-30, 0, 30):
        x = pad + 110 + dx
        d.line([(x, pad + 330), (x, pad + 360)], fill=(176, 130, 88, 170), width=5)
    return img, (pad + 110, pad + 50)

def make_foot():
    w, h = 240, 150
    m = ellipse_mask((w, h), [(15, 15, 225, 140)])
    img, pad = fur(m, 3, strokes=900, length=16, shade_bias=0.05)
    return img, (pad + 120, pad + 120)

HEAD_W, HEAD_H = 1000, 900

def make_head():
    w, h = HEAD_W, HEAD_H
    m = ellipse_mask((w, h), [
        (70, 60, 930, 840),        # skull
        (30, 360, 400, 800),       # left cheek fluff
        (600, 360, 970, 800),      # right cheek fluff
        (250, 520, 750, 880),      # chin
    ])
    muzzle = ellipse_mask((w, h), [(330, 520, 520, 720), (480, 520, 670, 720), (380, 640, 620, 820)])
    img, pad = fur(m, 4, strokes=11000, length=30, light_mask=muzzle)
    return img, pad

def make_hat():
    w, h = 1400, 760
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = w // 2
    straw = (222, 176, 102)
    straw_dk = (176, 128, 64)
    straw_lt = (240, 205, 140)
    red, teal, navy, yel, cream = (196, 62, 48), (34, 136, 132), (44, 52, 96), (238, 186, 52), (250, 236, 206)

    # brim underside (front lip)
    d.ellipse((40, 400, w - 40, 730), fill=straw_dk)
    # brim top
    d.ellipse((40, 380, w - 40, 700), fill=straw)
    # patterned rim: concentric ring with zigzag
    ring = Image.new("L", (w, h), 0)
    rd = ImageDraw.Draw(ring)
    rd.ellipse((40, 380, w - 40, 700), fill=255)
    rd.ellipse((110, 410, w - 110, 670), fill=0)
    pat = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pat)
    pd.rectangle((0, 0, w, h), fill=red)
    for i in range(0, w, 46):
        pd.polygon([(i, 0), (i + 23, 0), (i + 46, h)], fill=teal)
    for i in range(0, w, 46):
        pd.polygon([(i + 23, h), (i + 46, h), (i + 23, 0)], fill=yel)
    pat.putalpha(ring)
    img.alpha_composite(pat)
    d = ImageDraw.Draw(img)
    d.ellipse((40, 380, w - 40, 700), outline=navy, width=8)
    d.ellipse((110, 410, w - 110, 670), outline=cream, width=6)
    # straw weave on brim
    for k in range(1, 6):
        inset = 110 + k * 50
        d.ellipse((inset, 410 + k * 18, w - inset, 670 - k * 14), outline=straw_dk + (110,), width=3)
    # crown: tall rounded cone, shaded left to right
    crown = Image.new("L", (w, h), 0)
    cd = ImageDraw.Draw(crown)
    cd.polygon([(cx - 290, 570), (cx - 165, 170), (cx + 165, 170), (cx + 290, 570)], fill=255)
    cd.ellipse((cx - 175, 50, cx + 175, 300), fill=255)
    cd.ellipse((cx - 292, 500, cx + 292, 620), fill=255)
    xs = np.linspace(-1, 1, w)[None, :]
    grad = np.clip(1.0 - 0.28 * (xs + 0.35) ** 2 * 2.2, 0, 1)
    grad = np.repeat(grad, h, axis=0)
    cimg = np.zeros((h, w, 4), np.uint8)
    for k in range(3):
        cimg[..., k] = np.clip(straw[k] * (0.72 + 0.38 * grad), 0, 255)
    cimg[..., 3] = np.asarray(crown)
    img.alpha_composite(Image.fromarray(cimg, "RGBA"))
    d = ImageDraw.Draw(img)
    for k in range(7):
        y = 120 + k * 58
        half = 175 + (290 - 175) * (y - 130) / 440
        d.arc((cx - half, y - 40, cx + half, y + 40), 15, 165, fill=straw_dk + (120,), width=3)
    # crown band with zigzag pattern
    band = Image.new("L", (w, h), 0)
    bd = ImageDraw.Draw(band)
    bd.rectangle((cx - 292, 470, cx + 292, 560), fill=255)
    bd.ellipse((cx - 292, 520, cx + 292, 610), fill=255)
    bd.ellipse((cx - 292, 410, cx + 292, 500), fill=0)
    bpat = Image.new("RGBA", (w, h), navy)
    bp = ImageDraw.Draw(bpat)
    for i in range(cx - 300, cx + 300, 40):
        bp.polygon([(i, 600), (i + 20, 470), (i + 40, 600)], fill=red)
        bp.polygon([(i + 10, 600), (i + 20, 520), (i + 30, 600)], fill=yel)
    for i in range(cx - 300, cx + 300, 40):
        bp.ellipse((i + 14, 478, i + 26, 490), fill=teal)
    bpat.putalpha(band)
    img.alpha_composite(bpat)
    d = ImageDraw.Draw(img)
    d.arc((cx - 292, 410, cx + 292, 500), 0, 180, fill=cream, width=6)
    # soft shading on brim edges
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse((900, 400, 1380, 720), fill=(90, 50, 20, 60))
    sh = sh.filter(ImageFilter.GaussianBlur(40))
    sh.putalpha(ImageChops.multiply(sh.getchannel("A"), img.getchannel("A")))
    img.alpha_composite(sh)
    # anchor: centre of the brim
    return img, (cx, 560)

def make_shadow():
    img = Image.new("RGBA", (900, 200), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse((60, 40, 840, 160), fill=(60, 30, 10, 70))
    return img.filter(ImageFilter.GaussianBlur(22)), (450, 100)

# ---------------------------------------------------------------- face

def draw_face(head, pad, p):
    img = head.copy()
    d = ImageDraw.Draw(img)
    ox, oy = pad, pad
    px = p["look"] * 26
    for side in (-1, 1):
        cx = ox + HEAD_W // 2 + side * 170
        cy = oy + 480
        ew, eh = 108, 124
        if p["eyes"] > 0.5:   # happy ^ ^
            d.arc((cx - 80, cy - 40, cx + 80, cy + 100), 200, 340, fill=(60, 34, 22), width=16)
            continue
        open_ = 1 - p["blink"]
        if open_ < 0.15:
            d.arc((cx - 85, cy - 70, cx + 85, cy + 40), 20, 160, fill=(60, 34, 22), width=14)
            continue
        top = cy - eh * open_
        d.ellipse((cx - ew - 4, top - 4, cx + ew + 4, cy + eh + 4), fill=(52, 30, 18))
        d.ellipse((cx - ew, top, cx + ew, cy + eh), fill=(140, 88, 44))
        d.ellipse((cx - ew + 22, top + 14, cx + ew - 22, cy + eh - 6), fill=(92, 52, 26))
        pr = 76
        d.ellipse((cx + px - pr, cy + 10 - pr * open_, cx + px + pr, cy + 10 + pr), fill=(22, 12, 10))
        # catchlights
        d.ellipse((cx + px - 62, cy - 62 * open_, cx + px - 8, cy - 8 * open_ + 4), fill=(255, 255, 255))
        d.ellipse((cx + px + 26, cy + 50, cx + px + 50, cy + 74), fill=(255, 255, 255, 220))
        # upper lid line + lashes
        d.arc((cx - ew - 6, top - 6, cx + ew + 6, cy + eh + 6), 200, 340, fill=(48, 26, 16), width=10)
    # blush
    bl = Image.new("RGBA", img.size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(bl)
    for side in (-1, 1):
        cx = ox + HEAD_W // 2 + side * 290
        bd.ellipse((cx - 70, oy + 600, cx + 70, oy + 670), fill=(240, 140, 120, 90))
    img.alpha_composite(bl.filter(ImageFilter.GaussianBlur(14)))
    d = ImageDraw.Draw(img)
    # nose
    nx, ny = ox + HEAD_W // 2, oy + 615
    d.polygon([(nx - 30, ny - 16), (nx + 30, ny - 16), (nx, ny + 16)], fill=(214, 120, 112))
    d.ellipse((nx - 12, ny - 14, nx + 2, ny - 6), fill=(245, 185, 175))
    # mouth
    mo = p["mouth"]
    if mo > 0.1:
        mh = 18 + 50 * mo
        d.ellipse((nx - 34, ny + 26, nx + 34, ny + 26 + mh), fill=(120, 44, 40))
        d.ellipse((nx - 22, ny + 26 + mh * 0.5, nx + 22, ny + 26 + mh - 4), fill=(232, 120, 120))
    else:
        d.arc((nx - 46, ny + 4, nx + 2, ny + 44), 20, 160, fill=(110, 60, 42), width=7)
        d.arc((nx - 2, ny + 4, nx + 46, ny + 44), 20, 160, fill=(110, 60, 42), width=7)
    # whiskers
    for side in (-1, 1):
        for k, (dy, ang) in enumerate(((0, -8), (22, 2), (44, 12))):
            x0 = nx + side * 120
            y0 = ny + 20 + dy
            x1 = x0 + side * 190
            y1 = y0 + ang * 2.2
            d.line([(x0, y0), (x1, y1)], fill=(255, 250, 240, 200), width=4)
    # hat chin strap with a wooden bead
    cord = (120, 82, 50)
    d.line([(ox + 95, oy + 330), (ox + 230, oy + 720), (nx, oy + 820)], fill=cord, width=7, joint="curve")
    d.line([(ox + HEAD_W - 95, oy + 330), (ox + HEAD_W - 230, oy + 720), (nx, oy + 820)], fill=cord, width=7, joint="curve")
    d.ellipse((nx - 20, oy + 790, nx + 20, oy + 840), fill=(150, 96, 52), outline=(96, 60, 32), width=4)
    return img

# ---------------------------------------------------------------- dance

def pose(t):
    """Dance parameters at time t (seconds), synced to the beat."""
    b = t / BEAT                      # beat position
    bar = int(b // 4) % 8
    ph = b % 1                        # phase inside beat
    hop = math.sin(math.pi * ph) ** 2   # 0 on the beat, up between beats... invert below
    bounce = 1 - abs(math.cos(math.pi * ph))  # peak mid-beat
    land = math.exp(-ph * 8)                  # squash right on the beat
    sway = math.sin(math.pi * b / 2)          # one side per 2 beats
    wig = math.sin(math.pi * b)               # one side per beat

    p = dict(x=0, y=0, squash=0, body=0, head=0, hat=0, armL=18, armR=-18,
             footL=0, footR=0, eyes=0, blink=0, look=0, mouth=0)

    def section(k):
        q = dict(p)
        if k in (0, 1):      # sway + gentle arm swing
            q.update(x=70 * sway, y=-38 * bounce, squash=0.07 * land, body=-6 * sway,
                     head=9 * sway, armL=25 + 20 * sway, armR=-25 + 20 * sway,
                     footL=max(0, sway) * 30 * bounce, footR=max(0, -sway) * 30 * bounce,
                     look=sway * 0.8, mouth=0.0)
        elif k in (2, 3):    # paws up in front, pumping
            q.update(x=30 * sway, y=-55 * bounce, squash=0.1 * land, body=-3 * wig,
                     head=-7 * wig, armL=150 + 25 * wig, armR=-150 + 25 * wig,
                     footL=max(0, wig) * 40 * bounce, footR=max(0, -wig) * 40 * bounce,
                     look=-wig * 0.6, mouth=0.6 * bounce)
        elif k in (4, 5):    # hip wiggle, arms out, happy eyes
            q.update(x=45 * wig, y=-30 * bounce, squash=0.08 * land, body=10 * wig,
                     head=-12 * wig, armL=75 - 25 * wig, armR=-75 - 25 * wig,
                     footL=max(0, -wig) * 35 * bounce, footR=max(0, wig) * 35 * bounce,
                     eyes=1, mouth=0.8)
        elif k == 6:         # hands up, jumping
            q.update(x=0, y=-110 * bounce, squash=0.14 * land, body=0,
                     head=6 * wig, armL=165 + 12 * wig, armR=-165 + 12 * wig,
                     footL=50 * bounce, footR=50 * bounce, mouth=1.0 * bounce + 0.3,
                     look=0)
        else:                # head bob + side glance (like the original)
            q.update(x=25 * sway, y=-22 * bounce, squash=0.06 * land, body=-4 * sway,
                     head=14 * math.sin(2 * math.pi * b), armL=35 + 12 * wig, armR=-35 + 12 * wig,
                     footL=max(0, wig) * 20 * bounce, footR=max(0, -wig) * 20 * bounce,
                     look=1.0 if (b % 4) < 2 else -1.0, mouth=0.2)
        return q

    cur = section(bar)
    # blend into the next section over the last half beat of a bar
    into = (b % 4) - 3.5
    if into > 0:
        nxt = section((bar + 1) % 8)
        k = smooth(into / 0.5)
        cur = {key: lerp(cur[key], nxt[key], k) for key in cur}
    # hat lags behind the head
    cur["hat"] = -0.6 * cur["head"] * 0.4 + 4 * math.sin(math.pi * b + 0.8)
    # blinks at fixed times (skip happy-eye section)
    for bt in (2.6, 9.4, 13.2, 25.5, 30.3):
        dt = abs(b - bt)
        if dt < 0.18:
            cur["blink"] = max(cur["blink"], 1 - dt / 0.18)
    return cur

# ---------------------------------------------------------------- frame

def build_sprites():
    body, body_a = make_body()
    arm, arm_a = make_arm()
    arm_l = arm
    arm_r = arm.transpose(Image.FLIP_LEFT_RIGHT)
    arm_r_a = (arm.width - arm_a[0], arm_a[1])
    foot, foot_a = make_foot()
    head, head_pad = make_head()
    hat, hat_a = make_hat()
    shadow, shadow_a = make_shadow()
    return dict(body=(body, body_a), arm_l=(arm_l, arm_a), arm_r=(arm_r, arm_r_a),
                foot=(foot, foot_a), head=(head, head_pad), hat=(hat, hat_a),
                shadow=(shadow, shadow_a))

def at(anchor):
    return T(-anchor[0], -anchor[1])

def frame(sp, t):
    p = pose(t)
    cv = Image.new("RGBA", (C, C), (0, 0, 0, 0))
    gx, gy = GROUND
    sq = p["squash"]
    root = T(gx + p["x"], gy) @ S(1 + sq, 1 - sq)
    lift = T(0, p["y"])

    # shadow shrinks as the cat rises
    sh, sha = sp["shadow"]
    k = 1 + p["y"] / 400
    place(cv, sh, T(gx + p["x"] * 0.8, gy) @ S(k, k) @ at(sha))

    # feet (stay near the ground, lift alternately)
    ft, fta = sp["foot"]
    for side, key in ((-1, "footL"), (1, "footR")):
        M = root @ T(side * 165, -p[key] + p["y"] * 0.25) @ R(-side * p[key] * 0.25) @ at(fta)
        place(cv, ft, M)

    torso = root @ lift @ R(p["body"])
    bd, bda = sp["body"]
    place(cv, bd, torso @ T(0, -40) @ at(bda))

    neck = torso @ T(0, -650)
    headM = neck @ R(p["head"]) @ T(0, -330)       # head centre
    hd, hpad = sp["head"]
    face = draw_face(hd, hpad, p)
    place(cv, face, headM @ T(-(hpad + HEAD_W / 2), -(hpad + HEAD_H / 2)))

    hatM = headM @ T(0, -215) @ R(p["hat"]) @ S(0.92, 0.92)
    ht, hta = sp["hat"]
    place(cv, ht, hatM @ at(hta))

    # arms in front, pivot at the shoulders
    for side, key, name in ((-1, "armL", "arm_l"), (1, "armR", "arm_r")):
        img, a = sp[name]
        M = torso @ T(side * 255, -560) @ R(p[key]) @ at(a)
        place(cv, img, M)

    return cv.resize((OUT, OUT), Image.LANCZOS)

# ---------------------------------------------------------------- main

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "dancing_cat"
    os.makedirs(out, exist_ok=True)
    wav = os.path.join(out, "_music.wav")
    music.save(wav, music.render())

    sp = build_sprites()
    if os.environ.get("PREVIEW"):
        ts = [float(x) for x in os.environ["PREVIEW"].split(",")]
        for i, t in enumerate(ts):
            f = frame(sp, t)
            bg = Image.new("RGBA", f.size, CREAM_BG + (255,))
            bg.alpha_composite(f)
            bg.convert("RGB").save(os.path.join(out, f"_preview_{i}.png"))
        return

    master = os.path.join(out, "_master.mov")
    enc = subprocess.Popen([
        "ffmpeg", "-v", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{OUT}x{OUT}", "-r", str(FPS), "-i", "-",
        "-i", wav,
        "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", "-qscale:v", "9",
        "-c:a", "aac", "-b:a", "192k", "-shortest", master,
    ], stdin=subprocess.PIPE)
    for i in range(FRAMES):
        enc.stdin.write(frame(sp, i / FPS).tobytes())
        if i % 60 == 0:
            print(f"frame {i}/{FRAMES}", flush=True)
    enc.stdin.close()
    enc.wait()

    for name, col in (("cat_cream.mp4", CREAM_BG), ("cat_brown.mp4", BROWN_BG)):
        hexc = "0x%02x%02x%02x" % col
        subprocess.run([
            "ffmpeg", "-v", "error", "-y", "-i", master,
            "-f", "lavfi", "-i", f"color=c={hexc}:s={OUT}x{OUT}:r={FPS}",
            "-filter_complex", "[1][0:v]overlay=shortest=1,format=yuv420p[v]", "-map", "[v]",
            "-c:v", "libx264", "-crf", "18", "-preset", "slow", "-movflags", "+faststart",
            "-map", "0:a", "-c:a", "copy", os.path.join(out, name),
        ], check=True)
    subprocess.run([
        "ffmpeg", "-v", "error", "-y", "-i", master,
        "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", "30", "-row-mt", "1",
        "-c:a", "libopus", "-b:a", "128k", os.path.join(out, "cat_transparent.webm"),
    ], check=True)
    subprocess.run([
        "ffmpeg", "-v", "error", "-y", "-i", wav, "-c:a", "aac", "-b:a", "192k",
        os.path.join(out, "cat_music.m4a"),
    ], check=True)
    # ProRes is heavy: keep the shipped alpha .mov at 720px so it stays a sane size
    subprocess.run([
        "ffmpeg", "-v", "error", "-y", "-i", master, "-vf", "scale=720:720",
        "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", "-qscale:v", "13",
        "-c:a", "copy", os.path.join(out, "cat_transparent.mov"),
    ], check=True)
    os.remove(master)
    os.remove(wav)

if __name__ == "__main__":
    main()
