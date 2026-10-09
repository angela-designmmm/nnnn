"""Reels: 3 series about women (Better Things / Straight to Hell / East of Eden).

Talking head is cut down to the important phrases (breaths, "эээ" and pauses removed);
stills and trailer clips for each series play in a window above the head, Russian subtitles
sit on the chest — the face is never covered and every caption stays in the Reels safe zone.

usage: python3 series_render.py <assets_dir>    ->  series_reels.mp4, series_cover.png, series_hook.png
assets_dir: p1.mp4 p2.mov p3.mov p4.mov sr3.mov eoe.mov  p*_words.json (GigaAM word timings)  img/*.png
"""
import subprocess, sys, json, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

A = sys.argv[1]
W, H, FPS, SR = 1080, 1920, 30, 48000
INTER = "/usr/share/fonts/opentype/inter/Inter-%s.otf"
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

# Reels safe zone (right button column, bottom caption bar, top header)
SAFE = (60, 250, 920, 1480)
CX = (SAFE[0] + SAFE[2]) / 2
SAFE_W = SAFE[2] - SAFE[0]
# face sits at y ~760..1250 in every part -> media window above the head, subtitles on the chest
BOX = (SAFE[0], 268, SAFE[2], 733)
SUB_Y = 1290
ZOOM_C = (540, 1000)            # punch-in centre (between the eyes and the chin)

def font(size, weight):
    return ImageFont.truetype(INTER % weight, size)

F_SUB = font(48, "Bold")
F_CHIP = font(34, "Bold")
F_HOOK = font(46, "ExtraBold")
F_HOOK2 = font(36, "SemiBold")
F_EMO = ImageFont.truetype(EMOJI, 109)
HL = (255, 214, 10, 255)
WHITE = (255, 255, 255, 255)
BLACK = (0, 0, 0, 255)

# ---------------- text helpers ----------------
def is_emoji(ch):
    return ord(ch) >= 0x1F000 or ch in "✅✨"

def units(s):
    out, i = [], 0
    while i < len(s):
        if 0x1F1E6 <= ord(s[i]) <= 0x1F1FF and i + 1 < len(s):
            out.append(s[i:i + 2]); i += 2
        else:
            out.append(s[i]); i += 1
    return out

def text_w(s, f):
    return sum(f.size * 1.15 if is_emoji(ch[0]) else f.getlength(ch) for ch in units(s))

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
    for ch in units(s):
        if is_emoji(ch[0]):
            flush()
            e = Image.new("RGBA", (160, 128), (0, 0, 0, 0))
            ImageDraw.Draw(e).text((0, 0), ch, font=F_EMO, embedded_color=True)
            e = e.crop(e.getbbox())
            sz = int(f.size * 1.05)
            e = e.resize((sz, int(e.height * sz / e.width)), Image.LANCZOS)
            img.alpha_composite(e, (int(x + f.size * 0.08), int(y + f.size * 0.05)))
            x += f.size * 1.15
        else:
            buf += ch
    flush()

def pill(text, f, fg, bg, pad=(22, 10)):
    w = text_w(text, f)
    im = Image.new("RGBA", (int(w + 2 * pad[0]), int(f.size * 1.25 + 2 * pad[1])), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=im.height // 2, fill=bg)
    draw_run(im, (pad[0], pad[1] - f.size * 0.02), text, f, fg)
    return im

def subtitle(words):
    """words: [(text, highlighted)] -> white bold subtitle with soft shadow, max 2 lines."""
    sp = F_SUB.getlength(" ")
    lines, cur, cw = [], [], 0
    for w, hl in words:
        ww = text_w(w, F_SUB)
        if cur and cw + sp + ww > SAFE_W - 30:
            lines.append((cur, cw)); cur, cw = [], 0
        cw += (sp if cur else 0) + ww; cur.append((w, hl))
    lines.append((cur, cw))
    txt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for i, (ws, lw) in enumerate(lines):
        x = CX - lw / 2
        for w, hl in ws:
            pos = (x, SUB_Y + i * 60)
            draw_run(sh, pos, w, F_SUB, (0, 0, 0, 230))
            draw_run(txt, pos, w, F_SUB, HL if hl else WHITE)
            x += text_w(w, F_SUB) + sp
    sh = sh.filter(ImageFilter.GaussianBlur(5))
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.alpha_composite(sh, (2, 3)); out.alpha_composite(sh); out.alpha_composite(txt)
    return out

# ---------------- edit decision list ----------------
# (part, first word start, last word start, corrected text).  Corrected text has one token per
# recognised word: "_" = space inside a token, "∅" = drop the word from subtitles, "*x*" = highlight,
# "|" = subtitle break (not a word).
EDL = [
 ("p1", 2.35, 13.19, "Главных героинь этих трёх сериалов | не поймёт и не примет | ни один мужчина. | Или подборка сериалов | для женщин про женщин, | которые обязательно нужно | посмотреть на английском"),

 ("p2", 1.12, 7.72, "Первый сериал — | это *Better_Things* | про мать-одиночку ∅ | с тремя девчонками. | Она актриса,"),
 ("p2", 10.96, 11.80, "она совмещает работу,"),
 ("p2", 14.60, 15.40, "воспитание девчонок,"),
 ("p2", 18.84, 23.62, "Это лёгкий комедийный ∅ ∅ сериал, | но в то_же время | есть очень серьёзные | и глубокие темы."),
 ("p2", 24.54, 34.14, "Некоторые серии меня просто | оставляли в каком-то ∅ | коматозном состоянии. | Мне очень хотелось | позвонить своей маме, | ∅ что я и_делала, | и бесконечно её благодарить."),

 ("p3", 0.80, 3.32, "Второй сериал — | это *Straight* *to* *Hell.*"),
 ("p3", 4.48, 8.36, "Японский сериал, | но он есть на Netflix | с_классной английской озвучкой."),
 ("p3", 9.00, 15.44, "Телеведущая, | которая предсказывает будущее, | зарабатывает миллионы, | она несметно богатая."),
 ("p3", 18.52, 19.08, "Это сериал про"),
 ("p3", 22.38, 22.38, "предпринимательниц,"),
 ("p3", 23.90, 27.54, "про то, как быть мразью, | как расчехлить своё"),
 ("p3", 28.42, 28.94, "чёрное нутро."),
 ("p3", 39.34, 40.78, "Это мини-сериал, ∅ ∅ | поэтому я его"),   # tiny stutter kept: any cut sounds worse
 ("p3", 41.78, 43.50, "проглотила за вечер, | может быть, за два."),

 ("p4", 1.44, 4.72, "Последний сериал — | это *East_of* *Eden,* | новый сериал на Netflix."),
 ("p4", 6.92, 8.52, "То, что случилось | с героиней в детстве,"),
 ("p4", 13.80, 14.48, "нормального человека"),
 ("p4", 15.88, 16.68, "не оставило бы"),
 ("p4", 17.56, 18.08, "вообще в живых."),
 ("p4", 19.12, 20.94, "Но её психика выбрала"),
 ("p4", 23.94, 26.02, "один инструмент | для выживания,"),
 ("p4", 26.86, 27.50, "и это ей помогло"),
 ("p4", 30.62, 31.90, "стать невероятно богатой."),
 ("p4", 41.30, 41.98, "Это опять-таки ∅"),
 ("p4", 42.62, 44.38, "тот сериал, где женщина —"),
 ("p4", 47.39, 48.99, "точно *not* *a_good* *girl.*"),
 ("p4", 49.71, 50.23, "Это женщина,"),
 ("p4", 51.83, 52.39, "которая вытащила"),
 ("p4", 57.53, 58.69, "какие-то ∅ части себя —"),
 ("p4", 59.61, 61.77, "самые некрасивые, | самые неудобные."),
 ("p4", 76.65, 79.13, "Я увидела в этом | бесконечную красоту"),
 ("p4", 80.41, 80.41, "женщин —"),
 ("p4", 81.77, 82.73, "какие они могут быть"),
 ("p4", 84.42, 85.30, "полярными, разными."),
 ("p4", 87.53, 88.73, "Я всем советую | эти сериалы."),
 ("p4", 90.81, 92.81, "Пишите, если вдруг | что-то ∅ смотрели из этого_👇"),
]
SRC = {"p1": "p1.mp4", "p2": "p2.mov", "p3": "p3.mov", "p4": "p4.mov"}
PART_GAP = 0.25      # breath between series
MAX_GAP = 0.30       # inside a span, a silence longer than this is cut out
PAD_IN, PAD_OUT = 0.07, 0.16

# ---------------- audio-aware cut points ----------------
audio = {}
def load_audio(p):
    if p not in audio:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(A, SRC[p]), "-ac", "1", "-ar", str(SR),
                              "-f", "f32le", "-"], capture_output=True, check=True).stdout
        audio[p] = np.frombuffer(raw, np.float32)
    return audio[p]

def rms_min(p, lo, hi):
    """time of the quietest 10 ms window in [lo, hi]"""
    a = load_audio(p); hop = SR // 100
    i0, i1 = max(0, int(lo * SR)), min(len(a) - hop, int(hi * SR))
    if i1 <= i0: return (lo + hi) / 2
    fr = a[i0:i1 + hop][: (i1 - i0) // hop * hop + hop]
    n = len(fr) // hop
    e = (fr[: n * hop].reshape(n, hop) ** 2).mean(axis=1)
    return lo + int(np.argmin(e)) * hop / SR

level = {}
def env(p):
    """10 ms RMS envelope of a part and its 'silence' threshold"""
    if p not in level:
        a = load_audio(p); hop = SR // 100; n = len(a) // hop
        e = np.sqrt((a[: n * hop].reshape(n, hop) ** 2).mean(axis=1))
        level[p] = (e, max(np.percentile(e, 95) * 0.07, np.percentile(e, 10) * 1.6))   # above room noise
    return level[p]

def edge_out(p, t_from, t_max):
    """first quiet 10 ms window after the last word (so pauses aren't carried along)"""
    e, thr = env(p)
    for k in range(int(t_from * 100), int(t_max * 100)):
        if k < len(e) and e[k] < thr: return k / 100 + 0.03
    return rms_min(p, t_from, t_max)

def edge_in(p, t_to, t_min):
    if t_min >= t_to: return t_min
    e, thr = env(p)
    for k in range(int(t_to * 100), int(t_min * 100), -1):
        if 0 <= k < len(e) and e[k] < thr: return k / 100
    return rms_min(p, t_min, t_to)

words = {p: json.load(open(os.path.join(A, f"{p}_words.json"))) for p in SRC}
pieces = []          # (part, src_in, src_out, [(token_text, highlight, src_time, break_before)])
for part, t0, t1, text in EDL:
    ws = words[part]
    idx = [i for i, (w, a, b) in enumerate(ws) if t0 - 0.005 <= a <= t1 + 0.005]
    toks, brk = [], True                          # every EDL span starts a new subtitle
    for t in text.split(" "):
        if t == "|": brk = True; continue
        if t == "—" and toks:                      # a dash belongs to the previous word
            toks[-1] = (toks[-1][0] + "_—", toks[-1][1]); continue
        toks.append((t, brk)); brk = False
    assert len(toks) == len(idx), (part, t0, [ws[i][0] for i in idx], [t for t, _ in toks])
    # split the span at long internal silences
    groups, cur = [], [idx[0]]
    for i in idx[1:]:
        gap = ws[i][1] - ws[cur[-1]][2]
        if gap > MAX_GAP:
            groups.append(cur); cur = [i]
        else:
            cur.append(i)
    groups.append(cur)
    k = 0
    for g in groups:
        first, last = ws[g[0]], ws[g[-1]]
        prev_end = ws[g[0] - 1][2] if g[0] > 0 else 0
        next_start = ws[g[-1] + 1][1] if g[-1] + 1 < len(ws) else len(load_audio(part)) / SR
        a = edge_in(part, first[1] - 0.07, max(prev_end - 0.04, first[1] - 0.22))   # soft onsets (ч, с, ф)
        b = edge_out(part, last[2] - 0.02, min(next_start - 0.03, last[2] + 0.3))
        if pieces and pieces[-1][0] == part and a < pieces[-1][2]:   # never replay audio
            a = pieces[-1][2]
        sub = []
        for i in g:
            t, br = toks[k]; k += 1
            hl = t.startswith("*") and t.endswith("*")
            t = t.strip("*").replace("_", " ")
            sub.append((t, hl, ws[i][1], br))
        pieces.append((part, a, b, sub))

# ---------------- output timeline ----------------
timeline, t = [], 0.0       # (part, a, b, out_start, zoom)
zoom_flip = 0
prev_part = None
for part, a, b, sub in pieces:
    if prev_part and part != prev_part: t += PART_GAP
    zoom_flip ^= 1
    timeline.append((part, a, b, t, 1.0 if zoom_flip else 1.07, sub))
    t += b - a
    prev_part = part
TOTAL = t + 0.6
print(f"{len(pieces)} pieces, total {TOTAL:.1f}s")

def out_time(part, src_t):
    for p, a, b, o, z, s in timeline:
        if p == part and a - 0.3 <= src_t <= b + 0.05:
            return o + max(0, src_t - a)
    # cue lands in a removed stretch -> next kept piece of that part
    nxt = [o for p, a, b, o, z, s in timeline if p == part and a >= src_t]
    return nxt[0] if nxt else TOTAL
part_start = {p: min(o for q, a, b, o, z, s in timeline if q == p) for p in SRC}
part_end = {p: max(o + b - a for q, a, b, o, z, s in timeline if q == p) for p in SRC}

# subtitle chunks
chunks = []                 # (start, end, [(word, hl)])
allw = [(o + max(0, st - a), w, hl, br, p) for p, a, b, o, z, s in timeline for (w, hl, st, br) in s]
cur = []
MAX_SUB_W = 2 * (SAFE_W - 30) * 0.9               # keep every subtitle to two lines
def sub_w(c): return sum(text_w(w, F_SUB) + F_SUB.getlength(" ") for _, w, _ in c if w)
for i, (ot, w, hl, br, p) in enumerate(allw):
    too_long = w and w != "∅" and sub_w(cur) + text_w(w, F_SUB) > MAX_SUB_W
    if (br or too_long or (cur and allw[i - 1][4] != p)) and cur:
        chunks.append(cur); cur = []
    if w != "∅": cur.append((ot, w, hl))
    elif not cur: cur.append((ot, None, False))
chunks.append(cur)
SUBS = []
for i, c in enumerate(chunks):
    ws_ = [(w, hl) for _, w, hl in c if w]
    if not ws_: continue
    s0 = c[0][0] - 0.05
    s1 = chunks[i + 1][0][0] - 0.05 if i + 1 < len(chunks) else TOTAL
    SUBS.append((s0, min(s1, s0 + 4.0), ws_))

# ---------------- media ----------------
def load_img(n):
    return Image.open(os.path.join(A, "img", f"{n}.png")).convert("RGB")

BW, BH = BOX[2] - BOX[0], BOX[3] - BOX[1]
def fit_box(im, z=1.0):
    """Fill the media window: cover-fit for landscape stills, contain over a blurred fill otherwise."""
    ar = im.width / im.height
    def cover(src, zz):
        s = max(BW / src.width, BH / src.height) * zz
        r = src.resize((int(src.width * s + 1), int(src.height * s + 1)), Image.LANCZOS)
        x, y = (r.width - BW) // 2, (r.height - BH) // 2
        return r.crop((x, y, x + BW, y + BH))
    if 1.45 <= ar <= 2.3:
        return cover(im, z)
    bg = cover(im.resize((im.width // 4 + 1, im.height // 4 + 1)), 1.0).filter(ImageFilter.GaussianBlur(14))
    bg = Image.eval(bg, lambda v: int(v * 0.6))
    s = min(BW / im.width, BH / im.height) * z
    fg = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    bg.paste(fg, ((BW - fg.width) // 2, (BH - fg.height) // 2))
    return bg

clip_cache = {}
def clip_frames(name, a, b, crop):
    key = (name, a, b)
    if key not in clip_cache:
        n = int(round((b - a) * FPS))
        cw, ch, cx, cy = crop
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(a), "-i", os.path.join(A, name), "-t", str(b - a),
                              "-vf", f"crop={cw}:{ch}:{cx}:{cy},scale={BW}:{BH}:force_original_aspect_ratio=increase,"
                                     f"crop={BW}:{BH},fps={FPS}", "-an", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                             stdout=subprocess.PIPE)
        fr = []
        for _ in range(n):
            raw = p.stdout.read(BW * BH * 3)
            if len(raw) < BW * BH * 3: break
            fr.append(Image.frombytes("RGB", (BW, BH), raw))
        p.stdout.close(); p.wait()
        clip_cache[key] = fr
    return clip_cache[key]

SR3_CROP = (700, 430, 0, 0)       # drop the player's mute icon, NETFLIX corner, timer and progress bar
# the screen recording shows the mouse cursor at 5..8.3 s — cues below skip that stretch
EOE_CROP = (1280, 652, 0, 0)

# cues: (part, source time it appears, media) ; media = ("img", n) | ("clip", file, clip_start, crop)
CUES = [
 ("p2", 1.12, ("img", 4)), ("p2", 3.96, ("img", 5)), ("p2", 7.44, ("img", 2)), ("p2", 10.96, ("img", 3)),
 ("p2", 18.84, ("img", 4)), ("p2", 24.54, ("img", 3)), ("p2", 30.26, ("img", 1)),
 ("p3", 0.80, ("img", 6)), ("p3", 4.48, ("img", 8)), ("p3", 6.08, ("clip", "sr3.mov", 3.4, SR3_CROP)),
 ("p3", 7.67, ("clip", "sr3.mov", 8.5, SR3_CROP)), ("p3", 9.00, ("clip", "sr3.mov", 15.7, SR3_CROP)),
 ("p3", 14.40, ("img", 7)), ("p3", 18.52, ("clip", "sr3.mov", 20.3, SR3_CROP)), ("p3", 39.34, ("img", 6)),
 ("p4", 1.44, ("clip", "eoe.mov", 2.6, EOE_CROP)), ("p4", 6.92, ("img", 12)),
 ("p4", 13.80, ("clip", "eoe.mov", 12.2, EOE_CROP)), ("p4", 19.12, ("img", 9)), ("p4", 26.86, ("img", 10)),
 ("p4", 30.62, ("clip", "eoe.mov", 15.6, EOE_CROP)), ("p4", 41.30, ("img", 11)), ("p4", 49.71, ("img", 9)),
 ("p4", 76.65, ("clip", "eoe.mov", 5.6, EOE_CROP)), ("p4", 87.53, ("collage",)),
]
CHIPS = {"p2": "1/3 · Better Things", "p3": "2/3 · Straight to Hell", "p4": "3/3 · East of Eden"}
cue_t = [(out_time(p, s), p, m) for p, s, m in CUES]
cue_t.sort(key=lambda c: c[0])

def media_at(t):
    """(media, local time, cue index) shown at output time t, or None"""
    cur = None
    for i, (ct, p, m) in enumerate(cue_t):
        if ct <= t < part_end[p] + 0.001 + (PART_GAP if p != "p4" else 99):
            cur = (m, t - ct, i, p)
    return cur

COLLAGE = [4, 6, 10]
def collage_img(t, top, h, bg=True):
    """three posters side by side; pop in one after another"""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gap = 18; tw = (BW - 2 * gap) // 3
    for i, n in enumerate(COLLAGE):
        k = min(1.0, max(0.0, (t - i * 0.18) / 0.22))
        if k <= 0: continue
        im = load_img(n); s = max(tw / im.width, h / im.height)
        r = im.resize((int(im.width * s + 1), int(im.height * s + 1)), Image.LANCZOS)
        r = r.crop(((r.width - tw) // 2, (r.height - h) // 2, (r.width - tw) // 2 + tw, (r.height - h) // 2 + h))
        m = Image.new("L", (tw, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, tw - 1, h - 1], radius=22, fill=255)
        tile = Image.new("RGBA", (tw, h)); tile.paste(r, (0, 0)); tile.putalpha(m)
        if k < 1:
            sz = 0.85 + 0.15 * k
            tile = tile.resize((max(1, int(tw * sz)), max(1, int(h * sz))), Image.LANCZOS)
            a = tile.getchannel("A").point(lambda v: int(v * k)); tile.putalpha(a)
        x = BOX[0] + i * (tw + gap) + (tw - tile.width) // 2
        img.alpha_composite(tile, (x, top + (h - tile.height) // 2))
    return img

box_mask = Image.new("L", (BW, BH), 0)
ImageDraw.Draw(box_mask).rounded_rectangle([0, 0, BW - 1, BH - 1], radius=28, fill=255)
box_shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(box_shadow).rounded_rectangle([BOX[0], BOX[1] + 8, BOX[2], BOX[3] + 8], radius=28, fill=(0, 0, 0, 110))
box_shadow = box_shadow.filter(ImageFilter.GaussianBlur(14))

chip_cache = {}
def media_layer(t):
    cur = media_at(t)
    if not cur: return None
    m, lt, ci, part = cur
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if m[0] == "collage":
        layer.alpha_composite(collage_img(lt, BOX[1] + 70, BH - 70))
        chip = chip_cache.setdefault("cta", pill("Смотрели что-то? Пишите 👇", F_CHIP, BLACK, HL))
        layer.alpha_composite(chip, (int(CX - chip.width / 2), BOX[1]))
        return layer
    dur = (cue_t[ci + 1][0] if ci + 1 < len(cue_t) else TOTAL) - cue_t[ci][0]
    if m[0] == "img":
        im = fit_box(load_img(m[1]), 1.0 + 0.06 * min(1.0, lt / max(dur, 0.5)))   # slow push-in
    else:
        _, name, c0, crop = m
        fr = clip_frames(name, c0, c0 + dur + 0.2, crop)
        im = fr[min(len(fr) - 1, int(lt * FPS))]
    tile = Image.new("RGBA", (BW, BH)); tile.paste(im, (0, 0)); tile.putalpha(box_mask)
    # first media of a series pops in, the following ones swap with a quick flash-free crossfade
    first_of_part = ci == 0 or cue_t[ci - 1][1] != part
    if first_of_part and lt < 0.22:
        k = lt / 0.22; sz = 0.9 + 0.1 * k
        tile = tile.resize((int(BW * sz), int(BH * sz)), Image.LANCZOS)
        tile.putalpha(tile.getchannel("A").point(lambda v: int(v * k)))
    elif lt < 0.12:
        prev = media_layer(t - lt - 1 / FPS)           # crossfade over the previous still/clip
        if prev is not None: layer = prev
        tile.putalpha(tile.getchannel("A").point(lambda v: int(v * lt / 0.12)))
    else:
        layer.alpha_composite(box_shadow)
    layer.alpha_composite(tile, (int(CX - tile.width / 2), int((BOX[1] + BOX[3]) / 2 - tile.height / 2)))
    chip = chip_cache.setdefault(part, pill(CHIPS[part], F_CHIP, BLACK, HL))
    layer.alpha_composite(chip, (BOX[0] + 18, BOX[1] + 18))
    return layer

# hook (part 1): headline + three posters
HOOK = Image.new("RGBA", (W, H), (0, 0, 0, 0))
hl1, hl2 = "3 сериала, героинь которых", "не поймёт ни один мужчина"
hw = max(text_w(hl1, F_HOOK), text_w(hl2, F_HOOK)) + 56
ImageDraw.Draw(HOOK).rounded_rectangle([CX - hw / 2, SAFE[1] + 4, CX + hw / 2, SAFE[1] + 4 + 136], radius=24, fill=WHITE)
for i, s in enumerate([hl1, hl2]):
    draw_run(HOOK, (CX - text_w(s, F_HOOK) / 2, SAFE[1] + 20 + i * 56), s, F_HOOK, BLACK)
HOOK_COLLAGE_TOP, HOOK_COLLAGE_H = SAFE[1] + 158, BOX[3] - SAFE[1] - 158

# ---------------- render video ----------------
def frames_of(part, a, b):
    n = int(round((b - a) * FPS))
    vf = f"scale={W}:{H}:flags=lanczos" + (",unsharp=5:5:0.5" if part != "p1" else "") + f",fps={FPS}"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{a:.3f}", "-i", os.path.join(A, SRC[part]), "-t", f"{b - a + 0.1:.3f}",
                          "-vf", vf, "-an", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    got = []
    for _ in range(n):
        raw = p.stdout.read(W * H * 3)
        if len(raw) < W * H * 3: break
        got.append(Image.frombytes("RGB", (W, H), raw))
    p.stdout.close(); p.wait()
    while len(got) < n: got.append(got[-1])
    return got

def zoomed(fr, z):
    if z == 1.0: return fr
    cw, ch = W / z, H / z
    x0, y0 = ZOOM_C[0] - cw * ZOOM_C[0] / W, ZOOM_C[1] - ch * ZOOM_C[1] / H
    return fr.resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch))

sub_cache = {}
def sub_layer(t):
    for s0, s1, ws_ in SUBS:
        if s0 <= t < s1:
            key = tuple(ws_)
            if key not in sub_cache: sub_cache[key] = subtitle(ws_)
            return sub_cache[key]

def compose(fr, t):
    fr = fr.convert("RGBA")
    if t < part_start["p2"] - 0.01:                     # hook
        fr.alpha_composite(HOOK)
        fr.alpha_composite(collage_img(max(0, t - 0.9), HOOK_COLLAGE_TOP, HOOK_COLLAGE_H))
    else:
        ml = media_layer(t)
        if ml is not None: fr.alpha_composite(ml)
    sl = sub_layer(t)
    if sl is not None: fr.alpha_composite(sl)
    return fr.convert("RGB")

if __name__ == "__main__" and "--stills" not in sys.argv:
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                            "-pix_fmt", "yuv420p", "video_only.mp4"], stdin=subprocess.PIPE)
    nf = 0
    last = None
    for part, a, b, o, z, s in timeline:
        while nf / FPS < o - 1e-6:                       # breath between series: hold last frame
            enc.stdin.write(compose(last, nf / FPS).tobytes()); nf += 1
        n_target = int(round((o + b - a) * FPS)) - nf
        for fr in frames_of(part, a, a + n_target / FPS)[:n_target]:
            last = zoomed(fr, z)
            enc.stdin.write(compose(last, nf / FPS).tobytes()); nf += 1
    while nf / FPS < TOTAL:
        enc.stdin.write(compose(last, nf / FPS).tobytes()); nf += 1
    enc.stdin.close(); enc.wait()
    print("video frames", nf)

    # ---------------- audio: same pieces, 15 ms fades at every cut ----------------
    out = np.zeros(int(TOTAL * SR) + SR, np.float32)
    fade = int(0.015 * SR)
    for part, a, b, o, z, s in timeline:
        seg = load_audio(part)[int(a * SR):int(b * SR)].copy()
        ramp = np.linspace(0, 1, fade, dtype=np.float32)
        seg[:fade] *= ramp; seg[-fade:] *= ramp[::-1]
        i = int(o * SR); out[i:i + len(seg)] += seg
    out = out[:int(TOTAL * SR)]
    out.tofile("voice.f32")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "voice.f32",
                    "-af", "highpass=f=80,afftdn=nf=-25,loudnorm=I=-14:TP=-1.5:LRA=11,aformat=channel_layouts=stereo",
                    "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "audio.m4a"], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "video_only.mp4", "-i", "audio.m4a", "-c:v", "copy",
                    "-c:a", "copy", "-shortest", "-movflags", "+faststart", "series_reels.mp4"], check=True)
    json.dump({"pieces": [(p, round(a, 3), round(b, 3), round(o, 3)) for p, a, b, o, z, s in timeline],
               "subs": [(round(s0, 2), round(s1, 2), " ".join(w for w, _ in ws_)) for s0, s1, ws_ in SUBS]},
              open("series_edl.json", "w"), ensure_ascii=False, indent=1)
    print("total", round(TOTAL, 2))

# ---------------- stills: hook PNG (transparent) and cover ----------------
HOOK_FULL = HOOK.copy(); HOOK_FULL.alpha_composite(collage_img(9, HOOK_COLLAGE_TOP, HOOK_COLLAGE_H))
HOOK_FULL.save("series_hook.png")
cover = frames_of("p1", 3.0, 3.1)[0].convert("RGBA")
cover.alpha_composite(HOOK_FULL)
tag = pill("на английском 🇬🇧", F_HOOK2, BLACK, HL)
cover.alpha_composite(tag, (int(CX - tag.width / 2), SUB_Y))
cover.convert("RGB").save("series_cover.png")
