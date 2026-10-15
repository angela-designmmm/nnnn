"""Make the fluffy creature dance to track.m4a.

Beats are detected with librosa; every move is driven by the beat phase so it lands on
the music: a squash/stretch bounce on each beat, a side-to-side lean that alternates
with the beats, floppy ears and arms simulated as damped springs, eyes that pop on the
opening hit and close blissfully in the breakdown. Builds on the warps in
creature_animate.py.
"""
import subprocess, sys
import numpy as np, cv2, librosa
import creature_animate as ca

W, H, FPS = ca.W, ca.H, 60
AUDIO = "track.m4a"
OUT = "creature_dance.mp4"
PREVIEW = [float(a) for a in sys.argv[2:]] if len(sys.argv) > 1 and sys.argv[1] == "--preview" else None

# ---------------------------------------------------------------- music analysis
sr = 22050
y = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", AUDIO, "-ac", "1", "-ar", str(sr),
                                  "-f", "f32le", "-"], capture_output=True, check=True).stdout, np.float32)
DUR = len(y) / sr
_, beats = librosa.beat.beat_track(y=y, sr=sr, units="time")
beats = beats - 0.02                                   # tracker sits ~20 ms behind the hits
PERIOD = float(np.median(np.diff(beats)))
HIT = beats[0]                                         # the bright opening hit

def beat_pos(t):
    """Continuous beat counter: integer values exactly on detected beats."""
    t = np.asarray(t, float)
    b = np.interp(t, beats, np.arange(len(beats), dtype=float))
    b = np.where(t < beats[0], (t - beats[0]) / PERIOD, b)
    return np.where(t > beats[-1], len(beats) - 1 + (t - beats[-1]) / PERIOD, b)

def smooth_steps(t, pts):
    """Piecewise curve through (time, value) points with eased segments."""
    ts, vs = zip(*pts)
    i = np.clip(np.searchsorted(ts, t) - 1, 0, len(ts) - 2)
    u = ca.ease((t - np.array(ts)[i]) / (np.array(ts)[i + 1] - np.array(ts)[i]))
    return np.array(vs)[i] * (1 - u) + np.array(vs)[i + 1] * u

N = int(np.ceil(DUR * FPS))
T = np.arange(N) / FPS
B = beat_pos(T)
PH = B % 1.0

ENERGY = smooth_steps(T, [(0, 0.0), (HIT - 0.05, 0.0), (HIT + 0.15, 1.0), (2.0, 1.0), (2.4, 0.85),
                          (9.3, 0.9), (9.7, 0.65), (14.8, 0.65), (15.4, 0.3), (DUR, 0.15)])
HALF = smooth_steps(T, [(0, 0.0), (9.3, 0.0), (9.9, 1.0), (DUR, 1.0)])   # half-time feel

# ---------------------------------------------------------------- choreography curves
sq_full = -np.cos(2 * np.pi * PH)                       # -1 (squash) on every beat
sq_half = -np.cos(np.pi * B)                            # squash every other beat
lean_full = np.cos(np.pi * B)                           # side to side, extreme on the beat
lean_half = np.cos(np.pi * B / 2)                       # slower, wider sway
sq = sq_full * (1 - HALF) + sq_half * HALF
lean = lean_full * (1 - HALF) + lean_half * HALF

SQ = ENERGY * (0.030 * (1 - HALF) + 0.022 * HALF) * sq
LEAN = ENERGY * (36 * (1 - HALF) + 46 * HALF) * lean     # px at the top of the head

# opening: wind-up crouch, then a jelly pop on the hit
u = T - HIT
crouch = -0.035 * ca.ease((T - 0.05) / (HIT - 0.05)) * (u < 0)
pop = np.where(u >= 0, 0.06 * np.exp(-u / 0.35) * np.cos(2 * np.pi * u * 1.7), 0)
SQ += crouch + pop
EYE_POP = 0.22 * np.exp(-((u - 0.12) / 0.22) ** 2)

# a gentle idle breath everywhere, so it never freezes completely
SQ += 0.006 * np.sin(2 * np.pi * T / 4.0)

ZOOM = 1.02 + 0.006 * ENERGY * (1 + np.cos(2 * np.pi * PH)) / 2 * (1 - HALF) \
       + 0.03 * np.where(u >= 0, np.exp(-u / 0.6), 0) * ca.ease(u / 0.08)
FLASH = 0.07 * np.where(u >= 0, np.exp(-u / 0.25), 0)

# ---------------------------------------------------------------- spring-driven ears & arms
FY = ca.FEET[1]
HC = (777 - 380) * ca.S                                   # creature height in output px

def lean_at(src_y):
    h = np.clip((FY - src_y * ca.S) / HC, 0, 1.5)
    return LEAN * h ** 1.6

def spring(drive, target, omega, zeta, lo, hi):
    th, v, out = 0.0, 0.0, np.zeros(N)
    dt = 1 / FPS / 4
    for i in range(N):
        for _ in range(4):
            a = -omega ** 2 * (th - target[i]) - 2 * zeta * omega * v + drive[i]
            v += a * dt; th += v * dt
        out[i] = th = float(np.clip(th, lo, hi))
    return out

def accel(x):
    return np.gradient(np.gradient(x, 1 / FPS), 1 / FPS)

EAR_LEN = 140.0
ax_head = accel(lean_at(447))
ay_head = accel(-(FY - 447 * ca.S) * SQ)                  # + = accelerating downwards
d = np.radians(1)
ear_l = spring(-ax_head / EAR_LEN * 0.8 + ay_head / EAR_LEN * 0.6, np.zeros(N), 2 * np.pi * 2.2, 0.3, -16 * d, 16 * d)
ear_r = spring(-ax_head / EAR_LEN * 0.8 - ay_head / EAR_LEN * 0.6, np.zeros(N), 2 * np.pi * 2.0, 0.3, -16 * d, 16 * d)

lean_n = lean * (ENERGY > 0.01)
flap = ENERGY * (3.5 * (sq < 0) * -sq * (1 - HALF) + 2 * HALF * (1 - sq) / 2)
tgt_l = np.radians(flap + 3.5 * ENERGY * np.clip(-lean_n, 0, 1))
tgt_r = np.radians(flap + 3.5 * ENERGY * np.clip(lean_n, 0, 1))
ax_arm = accel(lean_at(640))
arm_l = spring(ax_arm / 300, tgt_l, 2 * np.pi * 2.6, 0.45, -1.5 * d, 7.5 * d)       # + = outward
arm_r = spring(-ax_arm / 300, tgt_r, 2 * np.pi * 2.6, 0.45, -1.5 * d, 7.5 * d)

# ---------------------------------------------------------------- eyes
BLINKS = [(3.9, 0.12, 0.05, 0.2), (7.38, 0.12, 0.05, 0.2), (beats[20] - 0.25, 0.4, 1.9, 0.45),
          (13.9, 0.15, 0.05, 0.25), (15.9, 0.35, 0.6, 0.6)]

def blink_amount(t):
    c = 0.0
    for t0, close, hold, open_ in BLINKS:
        v = t - t0
        if 0 <= v < close: c = max(c, ca.ease(v / close))
        elif close <= v < close + hold: c = 1.0
        elif close + hold <= v < close + hold + open_: c = max(c, 1 - ca.ease((v - close - hold) / open_))
    return c

# ---------------------------------------------------------------- masks for the bigger moves
def silhouette(m): ca.silhouette(m)
W_DANCE = np.clip(ca.soft_mask(silhouette, 90, 40) * 1.2, 0, 1)
W_DANCE *= np.clip((FY + 14 - np.arange(H, dtype=np.float32)[:, None]) / 28, 0, 1)
W_EAR_L = ca.soft_mask(lambda m: cv2.fillPoly(m, [ca.poly(ca.EAR_L)], 255), 46, 14)
W_EAR_R = ca.soft_mask(lambda m: cv2.fillPoly(m, [ca.poly(ca.EAR_R)], 255), 46, 14)
XS = np.arange(W, dtype=np.float32)[None, :]
# arms only swing outward, so their masks stop just inside the body edge
# with a wide ramp, so the body side flexes smoothly instead of folding
W_ARM_L = ca.soft_mask(lambda m: ca.ell(m, (118, 645), (27, 80)), 44, 28) * np.clip((185 * ca.S - XS) / (80 * ca.S), 0, 1)
W_ARM_R = ca.soft_mask(lambda m: ca.ell(m, (382, 645), (27, 80)), 44, 28) * np.clip((XS - 315 * ca.S) / (80 * ca.S), 0, 1)
CX0 = 250 * ca.S

def frame(i):
    t = T[i]
    s, L, z = SQ[i], LEAN[i], ZOOM[i]
    cx, cy = W / 2 + 0.12 * L, H * 0.52 + 4 * np.sin(2 * np.pi * t / 8)
    x = ((ca.GX - W / 2) / z + cx).astype(np.float32)
    y = ((ca.GY - H / 2) / z + cy).astype(np.float32)

    # body: undo the lean (a bend that grows with height), then the squash/stretch
    w = ca.sample(W_DANCE, x, y)
    h = np.clip((FY - y) / HC, 0, 1.5)
    bx = x - L * h ** 1.6
    by = y - abs(L) * 0.10 * h
    by = FY + (by - FY) / (1 + s)
    bx = CX0 + (bx - CX0) / (1 - 0.5 * s)
    x, y = x + w * (bx - x), y + w * (by - y)

    x, y = ca.rotate_inv(x, y, ca.EAR_L_PIV, ear_l[i], ca.sample(W_EAR_L, x, y))
    x, y = ca.rotate_inv(x, y, ca.EAR_R_PIV, ear_r[i], ca.sample(W_EAR_R, x, y))
    x, y = ca.rotate_inv(x, y, ca.ARM_L_PIV, arm_l[i], ca.sample(W_ARM_L, x, y))
    x, y = ca.rotate_inv(x, y, ca.ARM_R_PIV, -arm_r[i], ca.sample(W_ARM_R, x, y))

    m = EYE_POP[i]
    if m > 0.002:
        for ex, ey in ca.EYES:
            r2 = ((x - ex) ** 2 + (y - ey) ** 2) / (2.2 * ca.EYE_R) ** 2
            f = 1 + m * np.exp(-r2)
            x, y = ex + (x - ex) / f, ey + (y - ey) / f

    b = blink_amount(t)
    base = ca.eyelids(ca.img, b) if b > 0.001 else ca.img
    out = cv2.remap(base, x.astype(np.float32), y.astype(np.float32), cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_REFLECT)

    occl = 1 - ca.sample(ca.W_TIGHT, x, y)
    pulse = 0.6 + 0.8 * ENERGY[i] * (1 + np.cos(2 * np.pi * PH[i])) / 2
    dust = (ca.dust_layer(t) * pulse * occl)[..., None]
    out = out + (np.array([235, 248, 255], np.float32) - out) * np.clip(dust, 0, 1)
    out = out * (1 + FLASH[i])
    return np.clip(out, 0, 255).astype(np.uint8)

if __name__ == "__main__":
    print(f"{DUR:.2f}s, {len(beats)} beats, {60 / PERIOD:.1f} BPM, {N} frames")
    if PREVIEW is not None:
        for t in PREVIEW:
            cv2.imwrite(f"dance_{t}.png", cv2.cvtColor(frame(int(round(t * FPS))), cv2.COLOR_RGB2BGR))
        sys.exit()
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", AUDIO,
                            "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow",
                            "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                            "-shortest", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
    for i in range(N):
        enc.stdin.write(frame(i).tobytes())
        if i % 60 == 0: print(f"{i}/{N}", flush=True)
    enc.stdin.close(); enc.wait()
