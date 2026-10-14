"""Original 16-second latin-pop loop (120 BPM, 8 bars) for the dancing cat.

Writes a seamless loop: tails that run past the end are wrapped to the start.
Usage: python3 dancing_cat_music.py out.wav
"""
import sys, wave
import numpy as np

SR = 44100
BPM = 120
BEAT = 60 / BPM
BARS = 8
LENGTH = BARS * 4 * BEAT
N = int(round(LENGTH * SR))
rng = np.random.default_rng(7)

def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)

def add(buf, t0, sig, gain=1.0):
    i = int(round(t0 * SR))
    idx = (np.arange(len(sig)) + i) % N
    np.add.at(buf, idx, sig * gain)

def env(n, attack, decay):
    t = np.arange(n) / SR
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    return a * np.exp(-t / decay)

def kick():
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    f = 48 + 110 * np.exp(-t / 0.04)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t / 0.12) + 0.3 * np.sin(ph) * np.exp(-t / 0.01)

def hp_noise(n, k=1):
    x = rng.standard_normal(n + k)
    return x[k:] - x[:-k]

def snare():
    n = int(0.22 * SR)
    t = np.arange(n) / SR
    body = np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.04)
    return 0.5 * body + 0.45 * hp_noise(n) * np.exp(-t / 0.06)

def clap():
    n = int(0.25 * SR)
    t = np.arange(n) / SR
    e = np.zeros(n)
    for d in (0, 0.011, 0.022):
        e += np.where(t >= d, np.exp(-(t - d) / 0.008), 0)
    e += 0.6 * np.exp(-t / 0.09)
    return hp_noise(n, 2) * e * 0.35

def shaker(acc):
    n = int(0.08 * SR)
    t = np.arange(n) / SR
    a = np.clip(t / 0.012, 0, 1)
    return hp_noise(n) * a * np.exp(-t / 0.025) * (0.16 if acc else 0.09)

def bass(note, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = midi(note)
    s = sum(np.sin(2 * np.pi * f * k * t) / k ** 1.6 for k in range(1, 6))
    return s * env(n, 0.005, 0.18) * np.clip((dur - t) / 0.02, 0, 1)

def marimba(note, dur=0.6):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = midi(note)
    s = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.25)
    s += 0.35 * np.sin(2 * np.pi * f * 3.93 * t) * np.exp(-t / 0.04)
    s += 0.15 * np.sin(2 * np.pi * f * 9.2 * t) * np.exp(-t / 0.012)
    return s * np.clip(t / 0.002, 0, 1)

def pluck(note, dur=0.45, bright=0.5):
    """Karplus-Strong nylon-ish guitar string, vectorised per period."""
    n = int(dur * SR)
    p = max(2, int(round(SR / midi(note))))
    out = np.zeros(n + p)
    out[:p] = rng.uniform(-1, 1, p)
    out[:p] = bright * out[:p] + (1 - bright) * np.convolve(out[:p], [0.5, 0.5], "same")
    out[p] = 0.5 * out[0]
    i = p + 1
    while i < n + p:
        j = min(i + p, n + p)
        out[i:j] = 0.996 * 0.5 * (out[i - p:j - p] + out[i - p - 1:j - p - 1])
        i = j
    return out[p:] * np.clip((dur - np.arange(n) / SR) / 0.03, 0, 1)

# Am - F - C - G, twice
CHORDS = [
    (57, [57, 60, 64]),
    (53, [57, 60, 65]),
    (48, [55, 60, 64]),
    (55, [55, 59, 62]),
]

# melody per bar: list of (16th-step, midi, length in 16ths)
HOOK_A = [
    [(0, 76, 2), (3, 76, 1), (4, 79, 2), (6, 76, 2), (8, 74, 2), (10, 72, 2), (12, 74, 4)],
    [(0, 72, 2), (3, 72, 1), (4, 74, 2), (6, 72, 2), (8, 69, 4), (12, 72, 2), (14, 74, 2)],
    [(0, 76, 2), (3, 76, 1), (4, 79, 2), (6, 81, 2), (8, 79, 2), (10, 76, 2), (12, 72, 4)],
    [(0, 74, 2), (2, 74, 2), (4, 71, 2), (6, 74, 2), (8, 79, 4), (14, 71, 2)],
]
HOOK_B = [
    [(0, 81, 2), (3, 81, 1), (4, 79, 2), (6, 76, 2), (8, 79, 2), (10, 76, 2), (12, 74, 4)],
    [(0, 72, 2), (3, 72, 1), (4, 74, 2), (6, 76, 2), (8, 77, 4), (12, 76, 2), (14, 74, 2)],
    [(0, 76, 2), (3, 79, 1), (4, 84, 2), (6, 81, 2), (8, 79, 2), (10, 76, 2), (12, 79, 4)],
    [(0, 81, 1), (1, 79, 1), (2, 74, 2), (4, 71, 2), (6, 74, 2), (8, 76, 4), (12, 72, 2), (14, 71, 2)],
]

def render():
    drums = np.zeros(N)
    bas = np.zeros(N)
    gtr = np.zeros(N)
    mel = np.zeros(N)
    s16 = BEAT / 4
    K, SN, CL = kick(), snare(), clap()
    for bar in range(BARS):
        t_bar = bar * 4 * BEAT
        root, chord = CHORDS[bar % 4]
        for b in range(4):
            add(drums, t_bar + b * BEAT, K, 0.95)
        # dembow-style snare accents + clap on 2 and 4
        for st in (3, 6, 11, 14):
            add(drums, t_bar + st * s16, SN, 0.42)
        for b in (1, 3):
            add(drums, t_bar + b * BEAT, CL, 0.9)
        for st in range(16):
            add(drums, t_bar + st * s16, shaker(st % 2 == 1))
        # bass: tumbao-ish
        for st, off, ln in ((0, 0, 3), (3, 0, 1), (6, 7, 2), (8, 0, 3), (11, 0, 1), (14, 7, 2)):
            add(bas, t_bar + st * s16, bass(root - 12 + off, ln * s16), 0.55)
        # off-beat guitar strums
        for st in (2, 6, 10, 13):
            for k, note in enumerate(chord):
                add(gtr, t_bar + st * s16 + k * 0.012, pluck(note, 0.4, 0.6), 0.16)
        hook = (HOOK_A if bar < 4 else HOOK_B)[bar % 4]
        for st, note, ln in hook:
            add(mel, t_bar + st * s16, marimba(note, 0.2 + ln * s16), 0.32)
            add(mel, t_bar + st * s16, marimba(note + 12, 0.15 + ln * s16), 0.06)
    mix = drums * 0.85 + bas + gtr + mel
    # gentle soft-clip and normalise
    mix = np.tanh(mix * 1.1)
    mix /= np.max(np.abs(mix)) + 1e-9
    mix *= 0.89
    # tiny stereo width: delay the guitar slightly on the right
    d = int(0.011 * SR)
    left = mix
    right = mix - gtr * 0.3 + np.roll(gtr, d) * 0.3
    right = np.tanh(right * 1.1)
    right /= np.max(np.abs(right)) + 1e-9
    right *= 0.89
    return np.stack([left, right], axis=1)

def save(path, st):
    data = (st * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())

if __name__ == "__main__":
    save(sys.argv[1] if len(sys.argv) > 1 else "music.wav", render())
