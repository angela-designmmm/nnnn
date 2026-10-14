"""Plush cat in a sombrero dancing to dancing_cat_music.py (120 BPM, 16 s loop).

Usage:
  python3 dancing_cat_render.py out_dir              full set of videos with music
  python3 dancing_cat_render.py out_dir --no-music   just the character, preview mp4s
  PREVIEW=0.5,4.7 python3 dancing_cat_render.py dir  still frames at those times

Full set:
  cat_cream.mp4        on the light slide colour, with music
  cat_brown.mp4        on the dark slide colour, with music
  cat_transparent.mov  ProRes 4444 with alpha, 720x720, with music (Keynote / PowerPoint for Mac)
  cat_transparent.webm VP9 with alpha, with music (web, Canva)
  cat_music.m4a        the music on its own
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

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

GROUND = (C // 2, int(C * 0.95))

# ---------------------------------------------------------------- math helpers

def T(x, y):
    return np.array([[1, 0, x], [0, 1, y], [0, 0, 1]], float)

def R(deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], float)

def S(sx, sy):
    return np.array([[sx, 0, 0], [0, sy, 0], [0, 0, 1]], float)

def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)

def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)

def lerp(a, b, t):
    return a + (b - a) * t

def box(a, r, axis):
    if r < 1:
        return a
    pad = [(0, 0)] * a.ndim
    pad[axis] = (r + 1, r)
    c = np.cumsum(np.pad(a, pad, mode="edge"), axis=axis, dtype=np.float64)
    n = a.shape[axis]
    hi = np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=axis)
    lo = np.take(c, np.arange(0, n), axis=axis)
    return ((hi - lo) / (2 * r + 1)).astype(np.float32)

def blur(a, sigma):
    """Float gaussian-ish blur: three box passes per axis."""
    r = max(1, int(round(sigma * 0.9)))
    for _ in range(3):
        a = box(a, r, 0)
        a = box(a, r, 1)
    return a

def place(canvas, sprite, M):
    """Composite sprite onto canvas using sprite->canvas affine M."""
    inv = np.linalg.inv(M)
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

# ---------------------------------------------------------------- plush shading

RAMP = [
    (0.00, (138, 84, 54)),
    (0.35, (190, 132, 90)),
    (0.62, (222, 174, 126)),
    (0.85, (238, 199, 154)),
    (1.00, (248, 222, 186)),
]

def ramp(v):
    out = np.zeros(v.shape + (3,), np.float32)
    for (a, ca), (b, cb) in zip(RAMP, RAMP[1:]):
        t = np.clip((v - a) / (b - a), 0, 1)[..., None]
        sel = (v >= a)[..., None]
        out = np.where(sel, np.array(ca) + (np.array(cb) - np.array(ca)) * t, out)
    return out

def mask_from(size, ellipses, fillet=34):
    """Smooth union of ellipses -> float mask with soft anti-aliased edge."""
    w, h = size
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    for cx, cy, rx, ry in ellipses:
        d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=255)
    a = np.asarray(m, np.float32) / 255
    if fillet:
        a = smoothstep(0.42, 0.58, blur(a, fillet))
    return a

def plush(mask, seed, light=None, fuzz=9000, fuzz_len=(6, 22), strength=820, bias=0.0):
    """Shade a float mask like a short-haired plush toy and give it a fuzzy edge."""
    rnd = np.random.default_rng(seed)
    h, w = mask.shape
    hm = 0.08 * blur(mask, 14) + 0.27 * blur(mask, 45) + 0.35 * blur(mask, 95) + 0.3 * blur(mask, 180)
    hm = np.power(np.clip(hm, 0, 1), 0.7)
    gy, gx = np.gradient(hm)
    nx, ny, nz = -gx * strength, -gy * strength, np.ones_like(hm)
    nl = np.sqrt(nx * nx + ny * ny + nz * nz)
    nx, ny, nz = nx / nl, ny / nl, nz / nl
    L = np.array([-0.45, -0.62, 0.64])
    L /= np.linalg.norm(L)
    ndl = nx * L[0] + ny * L[1] + nz * L[2]
    diff = np.clip((ndl + 0.42) / 1.42, 0, 1) + bias
    # under-side occlusion (belly bottom, under the chin)
    diff -= 0.12 * np.clip(ny, 0, 1)
    col = ramp(np.clip(diff, 0, 1))
    if light is not None:
        lm = blur(light, 22)[..., None]
        col = col + (np.array([250, 230, 200]) - col) * lm * 0.38
    # soft back-lit rim: fur catching light at the silhouette
    rim = np.power(np.clip(1 - nz, 0, 1), 1.6)[..., None]
    col = col + rim * np.array([40, 34, 28]) * 0.3

    # velvet texture: fine streaks flowing down + soft clumps
    n = rnd.standard_normal((h, w)).astype(np.float32)
    fine = box(box(n, 7, 0), 1, 1)
    fine /= fine.std() + 1e-6
    clump = blur(rnd.standard_normal((h, w)).astype(np.float32), 4)
    clump /= clump.std() + 1e-6
    col = col * (1 + 0.016 * fine + 0.012 * clump)[..., None]
    col = np.clip(col, 0, 255)

    alpha = smoothstep(0.3, 0.7, blur(mask, 1.5))
    img = Image.fromarray(np.dstack([col, alpha * 255]).astype(np.uint8), "RGBA")

    # fuzz: thin hairs crossing the silhouette
    eb = blur(mask, 10)
    ey, ex = np.gradient(eb)
    band = np.argwhere(((mask > 0.25) & (mask < 0.95)) | ((eb > 0.35) & (eb < 0.75)))
    if len(band) and fuzz:
        layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        dr = ImageDraw.Draw(layer)
        for y, x in band[rnd.integers(0, len(band), fuzz)]:
            ox, oy = -ex[y, x], -ey[y, x]
            ol = math.hypot(ox, oy)
            if ol < 1e-5:
                continue
            ox, oy = ox / ol, oy / ol + 0.3
            a = math.atan2(oy, ox) + rnd.normal(0, 0.28)
            ln = rnd.uniform(*fuzz_len)
            back = rnd.uniform(0, ln * 0.6)
            x0, y0 = x - math.cos(a) * back, y - math.sin(a) * back
            x1, y1 = x0 + math.cos(a) * ln, y0 + math.sin(a) * ln
            c = col[min(h - 1, max(0, int(y0))), min(w - 1, max(0, int(x0)))] * rnd.uniform(0.9, 1.03)
            c = tuple(int(v) for v in np.clip(c, 0, 255)) + (int(rnd.uniform(45, 150)),)
            dr.line([(x0, y0), (x1, y1)], fill=c, width=int(rnd.integers(1, 3)))
        img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(0.9)))
    return img

# ---------------------------------------------------------------- body sprite

# body sprite: local origin = ground centre, y up is negative
BW, BH = 1100, 1560
BOX, BOY = BW // 2, 1500

EYE_Y = -872
EYE_X = 142
NOSE_Y = -792

def lp(x, y):
    """local body coords -> body sprite pixel"""
    return x + BOX, y + BOY

def make_body():
    shapes = [
        (0, -370, 372, 370),     # belly
        (0, -250, 398, 250),     # pear bottom
        (0, -640, 320, 210),     # chest
        (0, -935, 352, 330),     # head
        (-250, -830, 180, 160),  # cheeks
        (250, -830, 180, 160),
    ]
    m = mask_from((BW, BH), [(x + BOX, y + BOY, rx, ry) for x, y, rx, ry in shapes], fillet=64)
    light = mask_from((BW, BH), [
        (BOX - 64, BOY - 772, 96, 72), (BOX + 64, BOY - 772, 96, 72), (BOX, BOY - 745, 112, 80),
        (BOX, BOY - 400, 240, 280),
    ], fillet=0)
    light[BOY - 560:] *= 0.4
    img = plush(m, 11, light=light, fuzz=24000)

    # chin cord from under the brim down to a small wooden pendant
    d = ImageDraw.Draw(img)
    for side in (-1, 1):
        pts = []
        for i in range(41):
            t = i / 40
            x = lerp(side * 318, 0, t) + side * 26 * math.sin(math.pi * t)
            y = lerp(-1010, -610, t) + 50 * math.sin(math.pi * t * 0.9)
            pts.append(lp(x, y))
        d.line(pts, fill=(150, 108, 70, 230), width=4, joint="curve")
    px, py = lp(0, -598)
    d.ellipse((px - 12, py - 4, px + 12, py + 32), fill=(176, 126, 74), outline=(118, 80, 46), width=3)
    d.ellipse((px - 5, py + 4, px + 1, py + 12), fill=(222, 180, 120))
    return img

def make_arm():
    w, h = 240, 460
    m = mask_from((w, h), [(120, 100, 66, 72), (120, 210, 58, 112), (120, 340, 64, 66)], fillet=18)
    img = plush(m, 12, fuzz=3000, fuzz_len=(5, 16), strength=320, bias=0.04)
    return img, (120, 92)

def make_foot():
    w, h = 260, 180
    m = mask_from((w, h), [(130, 96, 98, 58)], fillet=10)
    img = plush(m, 13, fuzz=1400, fuzz_len=(4, 12), strength=260, bias=0.06)
    return img, (130, 140)

# ---------------------------------------------------------------- hat sprite

HW, HH = 1320, 900
HCX, HCY = 660, 600   # brim centre

def make_hat():
    ys, xs = np.mgrid[0:HH, 0:HW].astype(np.float32)
    x = xs - HCX
    y = ys - HCY
    a, b = 530.0, 150.0
    droop = 70 * np.power(np.abs(x) / a, 3)
    yy = y - droop
    r = np.sqrt((x / a) ** 2 + (yy / b) ** 2)
    r_lip = np.sqrt((x / a) ** 2 + ((yy - 30) / b) ** 2)
    phi = np.arctan2(yy / b, x / a)

    straw = np.array([214, 170, 106], np.float32)
    weave = 0.055 * np.sin(phi * 150) * np.sin(r * 85) + 0.025 * np.sin(r * 210)
    shade = 0.95 - 0.09 * (x / a) - 0.12 * np.power(np.abs(x) / a, 3) + 0.05 * (-y / b)
    col = straw * (shade + weave)[..., None]

    # embroidered band on the brim
    u = (phi / (2 * math.pi)) * 34
    fu = u - np.floor(u)
    v = (r - 0.56) / 0.24
    ring = (v > 0) & (v < 1)
    dia = np.abs(fu - 0.5) * 2 + np.abs(v - 0.5) * 2
    pat = np.where((dia < 0.32)[..., None], [226, 176, 76],
          np.where((dia < 0.72)[..., None], [70, 138, 134], [180, 84, 60]))
    pat = np.where(((v < 0.13) | (v > 0.87))[..., None], [62, 68, 104], pat)
    pat = pat * (0.95 + weave * 0.8)[..., None] * shade[..., None]
    col = np.where(ring[..., None], col * 0.4 + pat * 0.6, col)
    # stitched rim
    rim = (r > 0.94) & (r <= 1)
    stitch = np.where((np.sin(phi * 130) > 0)[..., None], [180, 84, 60], [238, 214, 168])
    col = np.where(rim[..., None], stitch * shade[..., None], col)
    # crown shadow on the brim
    q = np.sqrt(((x - 36) / 250) ** 2 + ((y - 26) / 84) ** 2)
    col = col * (1 - 0.32 * np.clip(1.35 - q, 0, 0.35) / 0.35)[..., None]
    # underside lip (front edge thickness)
    lip = (r > 1) & (r_lip <= 1)
    col = np.where(lip[..., None], straw * 0.68 * (1 + weave)[..., None], col)
    alpha = ((r <= 1) | lip).astype(np.float32)

    # crown
    top, base_y = -330.0, -10.0
    base_curve = base_y + 46 * np.sqrt(np.clip(1 - (x / 215) ** 2, 0, 1))
    t = np.clip((y + 190) / (base_y + 190), 0, 1)
    hw = np.where(y < -190, 165 * np.sqrt(np.clip(1 - ((y + 190) / (top + 190)) ** 2, 0, 1)), 165 + 50 * t)
    crown = (np.abs(x) <= hw) & (y >= top) & (y <= base_curve)
    hw = np.maximum(hw, 1)
    nxc = np.clip(x / hw, -1, 1)
    cshade = 0.62 + 0.42 * np.sqrt(1 - nxc ** 2) - 0.14 * nxc
    cweave = 0.05 * np.sin(y * 0.55 + 3 * np.sin(x * 0.02)) * np.sin(np.arcsin(nxc) * 60) + 0.03 * np.sin(y * 0.21)
    ccol = straw * (cshade + cweave)[..., None]
    band = crown & (y > base_curve - 74) & (y < base_curve - 6)
    bu = np.arcsin(nxc) / math.pi * 18
    bfu = bu - np.floor(bu)
    bv = (y - (base_curve - 74)) / 68
    tri = np.abs(bfu - 0.5) * 2 < bv
    bcol = np.where(tri[..., None], [180, 84, 60], [62, 68, 104])
    bcol = np.where(((bv > 0.4) & (np.abs(bfu - 0.5) < 0.08))[..., None], [226, 176, 76], bcol)
    bcol = bcol * (cshade + cweave * 0.6)[..., None]
    ccol = np.where(band[..., None], bcol, ccol)
    col = np.where(crown[..., None], ccol, col)
    alpha = np.maximum(alpha, crown.astype(np.float32))

    alpha = blur(alpha, 1.0)
    col = np.clip(col, 0, 255)
    return Image.fromarray(np.dstack([col, alpha * 255]).astype(np.uint8), "RGBA"), (HCX, HCY)

def make_brim_shadow():
    img = Image.new("RGBA", (1300, 520), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse((120, 150, 1180, 380), fill=(110, 58, 30, 120))
    return img.filter(ImageFilter.GaussianBlur(34)), (650, 200)

def make_ground_shadow():
    img = Image.new("RGBA", (1000, 220), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse((90, 50, 910, 170), fill=(60, 30, 10, 75))
    return img.filter(ImageFilter.GaussianBlur(26)), (500, 110)

# ---------------------------------------------------------------- face

def draw_eye(layer, cx, cy, p):
    d = ImageDraw.Draw(layer)
    ew, eh = 55, 63
    if p["happy"] > 0.5:
        d.arc((cx - 52, cy - 26, cx + 52, cy + 62), 205, 335, fill=(58, 32, 22, 255), width=11)
        return
    lid = max(p["lid"], p["blink"])
    top = cy - eh
    if lid > 0.88:
        d.arc((cx - 54, cy - 40, cx + 54, cy + 30), 20, 160, fill=(58, 32, 22, 255), width=10)
        return
    eye = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    e = ImageDraw.Draw(eye)
    lx = p["look"] * 16
    e.ellipse((cx - ew, cy - eh, cx + ew, cy + eh), fill=(34, 20, 16))
    for k in range(10):
        rr = 46 - k * 2.6
        c = (int(96 - k * 5), int(58 - k * 3), int(34 - k * 2))
        e.ellipse((cx + lx - rr, cy + 6 - rr * 1.08, cx + lx + rr, cy + 6 + rr * 1.08), fill=c)
    e.ellipse((cx + lx - 28, cy + 4 - 30, cx + lx + 28, cy + 4 + 30), fill=(14, 8, 6))
    e.ellipse((cx + lx - 33, cy - 38, cx + lx - 7, cy - 10), fill=(255, 255, 255))
    e.ellipse((cx + lx + 12, cy + 20, cx + lx + 22, cy + 30), fill=(255, 255, 255, 210))
    # keep only the part below the eyelid
    y_lid = top + lid * eh * 2
    clip = Image.new("L", layer.size, 0)
    ImageDraw.Draw(clip).ellipse((cx - ew, cy - eh, cx + ew, cy + eh), fill=255)
    if lid > 0.02:
        ImageDraw.Draw(clip).rectangle((0, 0, layer.width, int(y_lid)), fill=0)
    eye.putalpha(Image.fromarray(np.minimum(np.asarray(eye.getchannel("A")), np.asarray(clip))))
    layer.alpha_composite(eye)
    d = ImageDraw.Draw(layer)
    if lid > 0.02:
        half = ew * math.sqrt(max(0.05, 1 - ((y_lid - cy) / eh) ** 2))
        d.line([(cx - half - 4, y_lid + 2), (cx + half + 4, y_lid + 2)], fill=(52, 30, 20, 255), width=7)
    else:
        d.arc((cx - ew - 3, cy - eh - 3, cx + ew + 3, cy + eh + 3), 200, 340, fill=(44, 24, 16, 255), width=7)

def draw_face(body, p):
    img = body.copy()
    # soft shading around the eyes and blush
    soft = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(soft)
    for side in (-1, 1):
        cx, cy = lp(side * EYE_X, EYE_Y)
        sd.ellipse((cx - 72, cy - 74, cx + 72, cy + 80), fill=(150, 96, 62, 40))
        bx, by = lp(side * 228, -790)
        sd.ellipse((bx - 64, by - 30, bx + 64, by + 30), fill=(238, 140, 118, 70))
    img.alpha_composite(soft.filter(ImageFilter.GaussianBlur(16)))

    feat = Image.new("RGBA", img.size, (0, 0, 0, 0))
    for side in (-1, 1):
        cx, cy = lp(side * EYE_X, EYE_Y)
        draw_eye(feat, cx, cy, p)
    d = ImageDraw.Draw(feat)
    nx, ny = lp(0, NOSE_Y)
    d.rounded_rectangle((nx - 15, ny - 10, nx + 15, ny + 6), radius=7, fill=(206, 128, 112))
    d.ellipse((nx - 9, ny - 9, nx - 1, ny - 4), fill=(236, 178, 160))
    mo = p["mouth"]
    my = ny + 22
    if mo > 0.12:
        mh = 14 + 38 * mo
        mw = 26 + 6 * mo
        rad = int(min(mw, mh) * 0.9)
        d.rounded_rectangle((nx - mw, my, nx + mw, my + mh), radius=rad, fill=(92, 36, 32))
        d.ellipse((nx - mw * 0.65, my + mh * 0.48, nx + mw * 0.65, my + mh + 4), fill=(222, 112, 112))
        d.rounded_rectangle((nx - mw, my, nx + mw, my + mh), radius=rad, outline=(92, 36, 32), width=4)
    else:
        d.arc((nx - 30, my - 18, nx + 2, my + 10), 15, 165, fill=(118, 66, 52), width=5)
        d.arc((nx - 2, my - 18, nx + 30, my + 10), 15, 165, fill=(118, 66, 52), width=5)
    img.alpha_composite(feat.filter(ImageFilter.GaussianBlur(0.9)))
    return img

# ---------------------------------------------------------------- dance

def section(k, b):
    ph = b % 1
    bounce = 0.5 - 0.5 * math.cos(2 * math.pi * ph)     # 0 on the beat, 1 between
    sq = math.cos(2 * math.pi * ph)                     # +1 squashed on the beat
    sway = math.sin(math.pi * b / 2)
    wig = math.sin(math.pi * b)
    q = dict(x=0, y=0, sq=0, bend=0, head=0, armL=15, armR=-15, footL=0, footR=0,
             look=0, lid=0, happy=0, mouth=0.15, blink=0)
    if k in (0, 1):      # easy sway, arms swinging, eyes follow
        q.update(x=40 * sway, y=-26 * bounce, sq=0.045 * sq, bend=70 * sway, head=7 * sway,
                 armL=22 + 20 * sway, armR=-22 + 20 * sway,
                 footL=22 * bounce * max(0, sway), footR=22 * bounce * max(0, -sway),
                 look=0.9 * sway, mouth=0.15)
    elif k in (2, 3):    # paws at the chest, pumping
        q.update(x=18 * sway, y=-40 * bounce, sq=0.06 * sq, bend=-34 * wig, head=-7 * wig,
                 armL=-58 + 14 * wig, armR=58 + 14 * wig,
                 footL=30 * bounce * max(0, wig), footR=30 * bounce * max(0, -wig),
                 look=-0.45 * wig, mouth=0.3 + 0.5 * bounce)
    elif k in (4, 5):    # arms out, flapping, happy eyes
        q.update(x=32 * wig, y=-30 * bounce, sq=0.05 * sq, bend=58 * wig, head=-9 * wig,
                 armL=96 + 26 * wig, armR=-96 + 26 * wig,
                 footL=28 * bounce * max(0, -wig), footR=28 * bounce * max(0, wig),
                 happy=1, mouth=0.7)
    elif k == 6:         # little hops, hands up
        q.update(y=-85 * bounce, sq=0.085 * sq, bend=22 * wig, head=5 * wig,
                 armL=160 + 12 * wig, armR=-160 + 12 * wig,
                 footL=36 * bounce, footR=36 * bounce, mouth=0.35 + 0.6 * bounce)
    else:                # sleepy groove with half-closed eyes, side glance
        q.update(x=14 * sway, y=-16 * bounce, sq=0.04 * sq, bend=42 * sway,
                 head=9 * math.sin(math.pi * b), armL=16 + 10 * wig, armR=-16 + 10 * wig,
                 footL=14 * bounce * max(0, wig), footR=14 * bounce * max(0, -wig),
                 lid=0.55, look=0.7, mouth=0.18)
    return q

def raw_pose(t):
    b = (t % LENGTH) / BEAT
    bar = int(b // 4) % 8
    cur = section(bar, b)
    into = (b % 4) - 3.5
    if into > 0:
        nxt = section((bar + 1) % 8, b)
        k = smooth(into / 0.5)
        cur = {key: lerp(cur[key], nxt[key], k) for key in cur}
    for bt in (2.6, 9.4, 13.2, 25.5):
        dt = abs(b - bt)
        if dt < 0.2:
            cur["blink"] = max(cur["blink"], 1 - dt / 0.2)
    return cur

def pose(t):
    p = raw_pose(t)
    lag = raw_pose(t - 0.09)
    lag2 = raw_pose(t - 0.16)
    # secondary motion: hat and arms trail the body a little
    p["hat_rot"] = 0.55 * (lag["head"] - p["head"]) + 0.12 * (lag["bend"] - p["bend"])
    p["hat_dy"] = 0.35 * (lag2["y"] - p["y"])
    p["arm_lag"] = 0.25 * (lag["x"] - p["x"]) + 0.2 * (lag["bend"] - p["bend"])
    return p

# ---------------------------------------------------------------- body warp

HEAD_PIVOT = -660.0
BODY_H = 1270.0

def head_weight(y):
    return smoothstep(-540.0, -790.0, y)

def fwd(qx, qy, p):
    """body-local point -> canvas point (matches the inverse warp in warp_body)."""
    th = math.radians(p["head"]) * float(head_weight(np.float32(qy)))
    dx, dy = qx, qy - HEAD_PIVOT
    x1 = dx * math.cos(th) - dy * math.sin(th)
    y1 = dx * math.sin(th) + dy * math.cos(th) + HEAD_PIVOT
    x2 = x1 + p["bend"] * max(0.0, min(1.0, -y1 / BODY_H)) ** 1.6
    sx, sy = 1 + 0.75 * p["sq"], 1 - p["sq"]
    return GROUND[0] + p["x"] + x2 * sx, GROUND[1] + p["y"] + y1 * sy

def local_angle(qx, qy, p, eps=20.0):
    ax, ay = fwd(qx, qy - eps, p)
    bx, by = fwd(qx, qy + eps, p)
    return math.degrees(math.atan2(-(bx - ax), by - ay))

def warp_body(src, p, bbox):
    """Inverse-map canvas pixels in bbox back into the body sprite (bilinear)."""
    x0, y0, x1, y1 = bbox
    ys, xs = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    sx, sy = 1 + 0.75 * p["sq"], 1 - p["sq"]
    px = (xs - GROUND[0] - p["x"]) / sx
    py = (ys - GROUND[1] - p["y"]) / sy
    px = px - p["bend"] * np.power(np.clip(-py / BODY_H, 0, 1), 1.6)
    th = np.radians(p["head"]) * head_weight(py)
    dx, dy = px, py - HEAD_PIVOT
    c, s = np.cos(-th), np.sin(-th)
    qx = dx * c - dy * s
    qy = dx * s + dy * c + HEAD_PIVOT
    u = qx + BOX
    v = qy + BOY
    h, w = src.shape[:2]
    u0 = np.floor(u).astype(np.int32)
    v0 = np.floor(v).astype(np.int32)
    fu = (u - u0)[..., None]
    fv = (v - v0)[..., None]
    valid = ((u0 >= 0) & (u0 < w - 1) & (v0 >= 0) & (v0 < h - 1))[..., None]
    u0 = np.clip(u0, 0, w - 2)
    v0 = np.clip(v0, 0, h - 2)
    a = src[v0, u0] * (1 - fu) + src[v0, u0 + 1] * fu
    bb = src[v0 + 1, u0] * (1 - fu) + src[v0 + 1, u0 + 1] * fu
    out = (a * (1 - fv) + bb * fv) * valid
    alpha = out[..., 3:4]
    rgb = np.where(alpha > 1e-3, out[..., :3] / np.maximum(alpha, 1e-3), 0)
    return np.dstack([np.clip(rgb, 0, 255), np.clip(alpha * 255, 0, 255)]).astype(np.uint8)

def premul(img):
    a = np.asarray(img, np.float32)
    al = a[..., 3:4] / 255
    return np.dstack([a[..., :3] * al, al])

# ---------------------------------------------------------------- frame

def build_sprites():
    arm, arm_a = make_arm()
    ash = Image.new("RGBA", arm.size, (112, 62, 34, 0))
    ash.putalpha(arm.getchannel("A").point(lambda v: int(v * 0.42)).filter(ImageFilter.GaussianBlur(14)))
    return dict(
        arm_shadow=ash,
        body=make_body(),
        arm_l=(arm, arm_a),
        arm_r=(arm.transpose(Image.FLIP_LEFT_RIGHT), (arm.width - arm_a[0], arm_a[1])),
        foot=make_foot(),
        hat=make_hat(),
        brim_shadow=make_brim_shadow(),
        shadow=make_ground_shadow(),
    )

def at(anchor):
    return T(-anchor[0], -anchor[1])

def frame(sp, t):
    p = pose(t)
    cv = Image.new("RGBA", (C, C), (0, 0, 0, 0))
    gx, gy = GROUND

    sh, sha = sp["shadow"]
    k = 1 + p["y"] / 420
    place(cv, sh, T(gx + p["x"] * 0.8, gy) @ S(k, k) @ at(sha))

    ft, fta = sp["foot"]
    sx, sy = 1 + 0.75 * p["sq"], 1 - p["sq"]
    for side, key in ((-1, "footL"), (1, "footR")):
        M = T(gx + p["x"] * 0.9 + side * 150 * sx, gy - p[key] + p["y"] * 0.2) @ R(-side * p[key] * 0.3) @ at(fta)
        place(cv, ft, M)

    body = draw_face(sp["body"], p)
    bbox = (max(0, int(gx + p["x"] - 760)), max(0, int(gy + p["y"] - 1560)), min(C, int(gx + p["x"] + 760)), C)
    warped = warp_body(premul(body), p, bbox)
    layer = Image.new("RGBA", (C, C), (0, 0, 0, 0))
    layer.paste(Image.fromarray(warped, "RGBA"), bbox[:2])

    # hat transform (follows the warped head)
    hx, hy = fwd(0, -1150, p)
    hang = local_angle(0, -1050, p) + p["hat_rot"]
    hatM = T(hx, hy + p["hat_dy"]) @ R(hang) @ S(0.95 + 0.4 * p["sq"], 0.95 - 0.5 * p["sq"])

    # brim shadow only on the fur
    bsl = Image.new("RGBA", (C, C), (0, 0, 0, 0))
    bs, bsa = sp["brim_shadow"]
    place(bsl, bs, hatM @ T(0, 100) @ S(0.88, 0.9) @ at(bsa))
    arm_ms = []
    for side, key, name in ((-1, "armL", "arm_l"), (1, "armR", "arm_r")):
        img, a_ = sp[name]
        ax, ay = fwd(side * 300, -600, p)
        ang = local_angle(side * 300, -600, p) + p[key] + side * p["arm_lag"] * 0.15
        M = T(ax, ay) @ R(ang) @ S(sx, sy) @ at(a_)
        arm_ms.append((img, M))
        place(bsl, sp["arm_shadow"], T(10, 16) @ M)
    a = np.asarray(bsl.getchannel("A"), np.float32) * np.asarray(layer.getchannel("A"), np.float32) / 255
    bsl.putalpha(Image.fromarray(a.astype(np.uint8)))
    layer.alpha_composite(bsl)
    cv.alpha_composite(layer)

    for img, M in arm_ms:
        place(cv, img, M)

    ht, hta = sp["hat"]
    place(cv, ht, hatM @ at(hta))
    return cv.resize((OUT, OUT), Image.LANCZOS)

# ---------------------------------------------------------------- main

def encode_master(sp, path, wav=None, frames=FRAMES):
    cmd = ["ffmpeg", "-v", "error", "-y",
           "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{OUT}x{OUT}", "-r", str(FPS), "-i", "-"]
    if wav:
        cmd += ["-i", wav]
    cmd += ["-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", "-qscale:v", "9"]
    if wav:
        cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest"]
    enc = subprocess.Popen(cmd + [path], stdin=subprocess.PIPE)
    for i in range(frames):
        enc.stdin.write(frame(sp, i / FPS).tobytes())
        if i % 60 == 0:
            print(f"frame {i}/{frames}", flush=True)
    enc.stdin.close()
    enc.wait()

def on_colour(master, col, path, audio=True):
    hexc = "0x%02x%02x%02x" % col
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", master,
           "-f", "lavfi", "-i", f"color=c={hexc}:s={OUT}x{OUT}:r={FPS}",
           "-filter_complex", "[1][0:v]overlay=shortest=1,format=yuv420p[v]", "-map", "[v]",
           "-c:v", "libx264", "-crf", "18", "-preset", "slow", "-movflags", "+faststart"]
    cmd += ["-map", "0:a", "-c:a", "copy"] if audio else ["-an"]
    subprocess.run(cmd + [path], check=True)

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out = args[0] if args else "dancing_cat"
    os.makedirs(out, exist_ok=True)
    sp = build_sprites()

    if os.environ.get("PREVIEW"):
        ts = [float(x) for x in os.environ["PREVIEW"].split(",")]
        for i, t in enumerate(ts):
            f = frame(sp, t)
            for name, col in (("cream", CREAM_BG), ("brown", BROWN_BG)):
                bg = Image.new("RGBA", f.size, col + (255,))
                bg.alpha_composite(f)
                bg.convert("RGB").save(os.path.join(out, f"_preview_{name}_{i}.png"))
        return

    if "--no-music" in sys.argv:
        master = os.path.join(out, "_master.mov")
        encode_master(sp, master)
        on_colour(master, CREAM_BG, os.path.join(out, "character_cream.mp4"), audio=False)
        on_colour(master, BROWN_BG, os.path.join(out, "character_brown.mp4"), audio=False)
        os.remove(master)
        return

    wav = os.path.join(out, "_music.wav")
    music.save(wav, music.render())
    master = os.path.join(out, "_master.mov")
    encode_master(sp, master, wav)
    on_colour(master, CREAM_BG, os.path.join(out, "cat_cream.mp4"))
    on_colour(master, BROWN_BG, os.path.join(out, "cat_brown.mp4"))
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
