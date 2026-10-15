"""Slow, smooth, seamlessly looping idle animation of the fluffy creature (creature.jpg).

Everything is done by warping the single still image: breathing (squash/stretch from the
feet), a gentle sway, ear and arm motion, slow blinks, a soft camera drift and faint dust
particles in the background. All motion is periodic in LOOP seconds, so the clip loops.
"""
import subprocess, sys
import numpy as np, cv2

W, H, FPS = 1080, 1920, 60
LOOP = 12.0                      # seconds; every motion repeats exactly over this period
OUT = sys.argv[1] if len(sys.argv) > 1 else "creature_loop.mp4"
PREVIEW = "--preview" in sys.argv

src = cv2.cvtColor(cv2.imread("creature.jpg"), cv2.COLOR_BGR2RGB)
S = W / src.shape[1]             # source (504x900) -> output scale
img = cv2.resize(src, (W, H), interpolation=cv2.INTER_LANCZOS4).astype(np.float32)
img = np.clip(img + 0.35 * (img - cv2.GaussianBlur(img, (0, 0), 2.0)), 0, 255)  # light unsharp

def P(x, y):
    return (x * S, y * S)

def soft_mask(draw, grow, blur):
    m = np.zeros((H, W), np.uint8)
    draw(m)
    if grow:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * grow + 1, 2 * grow + 1))
        m = cv2.dilate(m, k)
    return cv2.GaussianBlur(m.astype(np.float32) / 255, (0, 0), blur)

def poly(pts):
    return np.array([[int(x * S), int(y * S)] for x, y in pts], np.int32)

def ell(m, c, ax):
    cv2.ellipse(m, (int(c[0] * S), int(c[1] * S)), (int(ax[0] * S), int(ax[1] * S)), 0, 0, 360, 255, -1)

EAR_L = [(143, 448), (149, 400), (160, 381), (174, 392), (192, 424), (186, 452)]
EAR_R = [(310, 424), (329, 392), (343, 380), (354, 400), (359, 448), (316, 452)]

def silhouette(m):
    ell(m, (250, 588), (118, 186))
    ell(m, (122, 638), (25, 80)); ell(m, (378, 638), (25, 80))
    ell(m, (200, 770), (16, 8)); ell(m, (296, 770), (16, 8))
    cv2.fillPoly(m, [poly(EAR_L), poly(EAR_R)], 255)

W_BODY = soft_mask(silhouette, 34, 26)
W_BODY = np.clip(W_BODY * 1.15, 0, 1)
W_TIGHT = soft_mask(silhouette, 0, 6)           # occludes background particles
W_EAR_L = soft_mask(lambda m: cv2.fillPoly(m, [poly(EAR_L)], 255), 30, 12)
W_EAR_R = soft_mask(lambda m: cv2.fillPoly(m, [poly(EAR_R)], 255), 30, 12)
W_ARM_L = soft_mask(lambda m: ell(m, (120, 645), (26, 78)), 24, 12)
W_ARM_R = soft_mask(lambda m: ell(m, (380, 645), (26, 78)), 24, 12)

FEET = np.array(P(248, 777), np.float32)
FLOOR_Y = FEET[1]
# the floor below the feet must not breathe with the body
W_BODY *= np.clip((FLOOR_Y + 14 - np.arange(H, dtype=np.float32)[:, None]) / 28, 0, 1)

EAR_L_PIV, EAR_R_PIV = np.array(P(172, 447), np.float32), np.array(P(330, 447), np.float32)
ARM_L_PIV, ARM_R_PIV = np.array(P(140, 572), np.float32), np.array(P(360, 572), np.float32)
EYES = [P(209, 487), P(284, 487)]
EYE_R = 9.5 * S

GX, GY = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))

def ease(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)

def wave(t, cycles, phase=0.0):
    return np.sin(2 * np.pi * (cycles * t / LOOP + phase))

def bump(t, start, dur):
    """0 -> 1 -> 0 with smooth ease in/out (sin^2 window), for one-off gestures."""
    u = ((t - start) % LOOP) / dur
    return np.sin(np.pi * u) ** 2 if 0 <= u <= 1 else 0.0

def blink_amount(t):
    # close 0.22s, hold 0.08s, open 0.34s; a single blink and later a slow double blink
    def one(t0):
        u = (t - t0) % LOOP
        if u < 0.22: return ease(u / 0.22)
        if u < 0.30: return 1.0
        if u < 0.64: return 1 - ease((u - 0.30) / 0.34)
        return 0.0
    return max(one(2.4), one(8.1), one(8.85))

def rotate_inv(x, y, piv, ang, w):
    """Inverse map of a rotation by `ang` (radians) around `piv`, blended by weight w."""
    c, s = np.cos(-ang), np.sin(-ang)
    dx, dy = x - piv[0], y - piv[1]
    rx, ry = piv[0] + c * dx - s * dy, piv[1] + s * dx + c * dy
    return x + w * (rx - x), y + w * (ry - y)

def sample(m, x, y):
    return cv2.remap(m, x.astype(np.float32), y.astype(np.float32), cv2.INTER_LINEAR,
                     borderMode=cv2.BORDER_REPLICATE)

def eyelids(base, c):
    """Return a copy of the rest image with both eyelids closed by amount c (0..1)."""
    out = base.copy()
    r = EYE_R
    for ex, ey in EYES:
        x0, x1 = int(ex - 2.2 * r), int(ex + 2.2 * r)
        y0, y1 = int(ey - 2.0 * r), int(ey + 2.0 * r)
        xs, ys = np.meshgrid(np.arange(x0, x1, dtype=np.float32), np.arange(y0, y1, dtype=np.float32))
        dx = (xs - ex) / r
        # upper lid edge: an arc sliding from above the eye to just below its centre
        edge = ey - 1.15 * r + c * 2.2 * r - 0.3 * r * (dx ** 2)
        cover = np.clip((edge - ys) / 2.2 + 0.5, 0, 1)
        side = np.clip(1.7 - np.abs(dx), 0, 1)              # fade out sideways into the fur
        cover *= side
        fur = sample(base, xs, ys - 2.3 * r)                 # fur from just above the eye
        patch = out[y0:y1, x0:x1]
        patch[:] = patch * (1 - cover[..., None]) + fur * cover[..., None]
        # soft lash line along the lid edge, stronger when the eye is shut
        lash = np.exp(-((ys - edge) / 1.6) ** 2) * np.clip((1.15 - np.abs(dx)) * 2, 0, 1)
        dark = (0.25 + 0.55 * c) * lash * min(1.0, c * 4)
        patch[:] = patch * (1 - dark[..., None]) + np.array([30, 45, 62], np.float32) * dark[..., None]
    return out

rng = np.random.default_rng(7)
N_DUST = 46
DUST = dict(x=rng.uniform(0, W, N_DUST), y=rng.uniform(150, H - 300, N_DUST),
            r=rng.uniform(2.0, 6.5, N_DUST), a=rng.uniform(0.10, 0.32, N_DUST),
            v=rng.uniform(12, 30, N_DUST), ph=rng.uniform(0, 1, N_DUST),
            sw=rng.uniform(8, 22, N_DUST))

def dust_layer(t):
    layer = np.zeros((H, W), np.float32)
    for i in range(N_DUST):
        age = ((t / LOOP + DUST["ph"][i]) % 1.0)             # one life per loop -> seamless
        a = DUST["a"][i] * np.sin(np.pi * age) ** 2
        x = DUST["x"][i] + DUST["sw"][i] * np.sin(2 * np.pi * (2 * age + DUST["ph"][i]))
        y = DUST["y"][i] - DUST["v"][i] * age * LOOP
        r = DUST["r"][i]
        x0, x1 = int(max(0, x - 3 * r)), int(min(W, x + 3 * r + 1))
        y0, y1 = int(max(0, y - 3 * r)), int(min(H, y + 3 * r + 1))
        if x0 >= x1 or y0 >= y1: continue
        xs, ys = np.meshgrid(np.arange(x0, x1), np.arange(y0, y1))
        layer[y0:y1, x0:x1] += a * np.exp(-((xs - x) ** 2 + (ys - y) ** 2) / (2 * (r * 0.6) ** 2))
    return layer

def frame(t):
    breath = wave(t, 3)                                      # 4 s per breath
    breath_lag = wave(t, 3, -0.08)
    sway = wave(t, 1, 0.1)
    # camera: very slow push-in / pull-out and drift
    zoom = 1.018 + 0.012 * wave(t, 1, 0.25)
    cx, cy = W / 2 + 6 * wave(t, 1), H * 0.52 + 5 * wave(t, 2, 0.3)
    x = (GX - W / 2) / zoom + cx
    y = (GY - H / 2) / zoom + cy

    # body: breathing (stretch up from the feet) + sway (rotation around the feet)
    s = 0.013 * breath
    ang = np.radians(1.1 * sway)
    w = sample(W_BODY, x, y)
    c, sn = np.cos(-ang), np.sin(-ang)
    dx, dy = x - FEET[0], y - FEET[1]
    rx, ry = c * dx - sn * dy, sn * dx + c * dy
    bx = FEET[0] + rx / (1 - 0.45 * s)
    by = FEET[1] + ry / (1 + s)
    x, y = x + w * (bx - x), y + w * (by - y)

    # ears: slow alternating sway, plus one curious twitch of the right ear
    twitch = bump(t, 5.2, 1.1)
    ear_l = np.radians(3.2 * wave(t, 2, 0.05) - 2.0 * breath_lag)
    ear_r = np.radians(-3.2 * wave(t, 2, 0.30) + 2.0 * breath_lag + 7.0 * twitch)
    x, y = rotate_inv(x, y, EAR_L_PIV, ear_l, sample(W_EAR_L, x, y))
    x, y = rotate_inv(x, y, EAR_R_PIV, ear_r, sample(W_EAR_R, x, y))

    # arms: open slightly on the in-breath, follow the sway a little late
    arm = 1.8 * breath_lag
    lag_sway = 1.2 * wave(t, 1, 0.0)
    x, y = rotate_inv(x, y, ARM_L_PIV, np.radians(-arm + lag_sway), sample(W_ARM_L, x, y))
    x, y = rotate_inv(x, y, ARM_R_PIV, np.radians(arm + lag_sway), sample(W_ARM_R, x, y))

    b = blink_amount(t)
    base = eyelids(img, b) if b > 0.001 else img
    x, y = x.astype(np.float32), y.astype(np.float32)
    out = cv2.remap(base, x, y, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)

    # dust drifts in the air behind the creature
    occl = 1 - sample(W_TIGHT, x, y)
    d = (dust_layer(t) * occl)[..., None]
    out = out + (np.array([235, 248, 255], np.float32) - out) * np.clip(d, 0, 1)
    return np.clip(out, 0, 255).astype(np.uint8)

if __name__ == "__main__":
    if PREVIEW:
        for t in [0, 2.5, 2.65, 5.7, 8.2]:
            cv2.imwrite(f"preview_{t}.png", cv2.cvtColor(frame(t), cv2.COLOR_RGB2BGR))
        sys.exit()
    n = int(LOOP * FPS)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                            "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
                            "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
    for i in range(n):
        enc.stdin.write(frame(i / FPS).tobytes())
        if i % 60 == 0: print(f"{i}/{n}", flush=True)
    enc.stdin.close(); enc.wait()
