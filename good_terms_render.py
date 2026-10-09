"""Reels: new phrase "to be on good terms" — explained and used in English only, no translation.

usage: python3 good_terms_render.py <source.mov>   ->  good_terms_reels.mp4
"""
import subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SRC = sys.argv[1]
W, H, FPS = 1080, 1920, 30
INTER = "/usr/share/fonts/opentype/inter/Inter-%s.otf"
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

def font(size, weight):
    return ImageFont.truetype(INTER % weight, size)

F_PLAQUE = font(52, "Medium")
F_TITLE = font(46, "SemiBold")
F_SUB = font(50, "Bold")
F_TAG = font(34, "SemiBold")
F_CARD_LBL = font(40, "SemiBold")
F_CARD_PHRASE = font(92, "ExtraBold")
F_CARD_WITH = font(52, "Medium")
F_FIN_PHRASE = font(60, "Bold")
F_FIN_DEF = font(48, "Medium")
F_FIN = font(56, "SemiBold")
F_EMO = ImageFont.truetype(EMOJI, 109)

HL = (255, 214, 10, 255)      # highlight for target vocabulary in subtitles
GRAY = (120, 120, 120, 255)

def is_emoji(ch):
    return ord(ch) >= 0x1F000 or ch in "✅✨"

def units(s):
    """Split into drawable units, keeping regional-indicator flag pairs (🇬🇧) together."""
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

def plaque(s, f, top, align="left", maxw=860, pad=(30, 22), lh=1.22, full_lines=None):
    """White rounded box with black text (same look as the part 1/2 Reels).
    full_lines: wrapping of the full string so a typewriter prefix keeps the final box layout."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lines = full_lines if full_lines is not None else wrap(s, f, maxw)
    shown, left = [], len(s)
    for ln in lines:
        if left <= 0: break
        shown.append(ln[:left]); left -= len(ln) + 1
    if not shown or not "".join(shown).strip():
        return img
    lhp = int(f.size * lh)
    bw = max(text_w(l, f) for l in shown) + 2 * pad[0]
    bh = lhp * len(shown) + 2 * pad[1]
    x0 = (W - bw) / 2
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x0, top, x0 + bw, top + bh], radius=22, fill=(255, 255, 255, 255))
    for i, l in enumerate(shown):
        lw = text_w(l, f)
        lx = x0 + pad[0] + ((bw - 2 * pad[0] - lw) / 2 if align == "center" else 0)
        draw_run(img, (lx, top + pad[1] + i * lhp - f.size * 0.02), l, f, (0, 0, 0, 255))
    return img

# ---------- subtitles with *highlighted* vocabulary ----------
def tokens(s):
    """'a *b c* d' -> [('a', False), ('b', True), ('c', True), ('d', False)]"""
    out, hl = [], False
    for w in s.split(" "):
        start = w.startswith("*")
        if start: hl = True; w = w[1:]
        end = w.rstrip(",.?!…").endswith("*")
        if end:
            i = w.rfind("*"); w = w[:i] + w[i + 1:]
        out.append((w, hl))
        if end: hl = False
    return out

def subtitle(s, tag=None, y=1560):
    toks = tokens(s)
    sp = F_SUB.getlength(" ")
    lines, cur, cw = [], [], 0
    for w, hl in toks:
        ww = F_SUB.getlength(w)
        if cur and cw + sp + ww > 900:
            lines.append((cur, cw)); cur, cw = [], 0
        cw += (sp if cur else 0) + ww; cur.append((w, hl))
    lines.append((cur, cw))
    txt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dt, ds = ImageDraw.Draw(txt), ImageDraw.Draw(sh)
    for i, (ws, lw) in enumerate(lines):
        x = (W - lw) / 2
        for w, hl in ws:
            ds.text((x, y + i * 62), w, font=F_SUB, fill=(0, 0, 0, 210))
            dt.text((x, y + i * 62), w, font=F_SUB, fill=HL if hl else (255, 255, 255, 255))
            x += F_SUB.getlength(w) + sp
    sh = sh.filter(ImageFilter.GaussianBlur(4))
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if tag:
        tw = text_w(tag, F_TAG)
        d = ImageDraw.Draw(out)
        x0, y0 = (W - tw) / 2 - 22, y - 70
        d.rounded_rectangle([x0, y0, x0 + tw + 44, y0 + 54], radius=27, fill=(0, 0, 0, 150))
        draw_run(out, (x0 + 22, y0 + 6), tag, F_TAG, HL)
    out.alpha_composite(sh, (3, 3)); out.alpha_composite(sh); out.alpha_composite(txt)
    return out

# ---------- intro phrase card / final card ----------
def card(rows, top, pad=(48, 36), gap=14):
    """rows: list of (text, font, color). Centered white card."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    hs = [int(f.size * 1.2) if t else 20 for t, f, _ in rows]
    bw = max(text_w(t, f) for t, f, _ in rows if t) + 2 * pad[0]
    bh = sum(hs) + gap * (len(rows) - 1) + 2 * pad[1]
    x0 = (W - bw) / 2
    d.rounded_rectangle([x0, top, x0 + bw, top + bh], radius=30, fill=(255, 255, 255, 255))
    y = top + pad[1]
    for (t, f, c), h in zip(rows, hs):
        if t:
            draw_run(img, ((W - text_w(t, f)) / 2, y), t, f, c)
        y += h + gap
    return img

INTRO = card([("НОВАЯ ФРАЗА", F_CARD_LBL, GRAY),
              ("to be on good terms", F_CARD_PHRASE, (0, 0, 0, 255)),
              ("with someone", F_CARD_WITH, (0, 0, 0, 255))], top=1060)
FINAL = card([("to be on good terms with sb", F_FIN_PHRASE, (0, 0, 0, 255)),
              ("= to get along well with sb", F_FIN_DEF, GRAY),
              ("", F_FIN, None),
              ("Ни слова по-русски —", F_FIN, (0, 0, 0, 255)),
              ("а фраза уже в речи 💬", F_FIN, (0, 0, 0, 255))], top=700)
TITLE = "Учим новые фразы без перевода 🇬🇧"

def pop(img, t, dur=0.22):
    """Scale-in from 92% for the first `dur` seconds."""
    if t >= dur: return img
    k = 0.92 + 0.08 * (t / dur)
    bb = img.getbbox()
    if not bb: return img
    c = img.crop(bb)
    c = c.resize((int(c.width * k), int(c.height * k)), Image.LANCZOS)
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
    out.alpha_composite(c, (int(cx - c.width / 2), int(cy - c.height / 2)))
    return out

# ---------------- timeline (source times, seconds) ----------------
CUTS = [(16.75, 33.25), (35.35, 45.75), (48.45, 59.36)]   # dead air between cuts removed
T, S = None, "🎧 ученица"
SUBS = [
    (16.80, 20.40, T, "We were talking yesterday about your direct manager, right?"),
    (20.95, 26.85, T, "And I've never asked you whether you are *on good terms* with your direct manager."),
    (27.50, 33.25, T, "And do you *see eye to eye* on most of the projects that you're working on together?"),
    (35.45, 41.35, S, "*Good terms* means… good connection with the manager?"),
    (41.90, 45.70, T, "Yeah, you're *getting along well*."),
    (48.55, 53.00, S, "I think I would say I have *supportive* manager,"),
    (53.75, 59.36, S, "really supportive one, who never *blame* you or *shame* you or…"),
]
PLAQUES = [
    (16.75, 21.00, "Повторяем лексику с прошлого урока 📚"),
    (21.00, 27.50, "Новая фраза — прямо внутри вопроса"),
    (27.50, 33.25, "…и ещё одна идиома сверху 👀"),
    (35.35, 41.40, "Ученица сама объясняет значение — по-английски"),
    (41.40, 45.75, "Вместо перевода — синоним"),
    (48.45, 58.60, "…и сразу строит развёрнутый ответ 🔥"),
]
INTRO_END = 2.5     # output seconds the phrase card stays on
FINAL_AT = 58.60    # source time the final card appears
FREEZE_END = 2.4    # hold last frame under the final card

PLAQUE_TOP = 1170
TITLE_TOP = 80

def frames_of_video(a, b):
    n = int(round((b - a) * FPS))
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(a), "-i", SRC, "-t", str(b - a),
                          "-vf", f"scale={W}:{H}:flags=lanczos,unsharp=5:5:0.6,fps={FPS}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    got = []
    for _ in range(n):
        raw = p.stdout.read(W * H * 3)
        if len(raw) < W * H * 3: break
        got.append(Image.frombytes("RGB", (W, H), raw))
    p.stdout.close(); p.wait()
    while len(got) < n: got.append(got[-1])
    return got

cache = {}
def cached(key, fn):
    if key not in cache: cache[key] = fn()
    return cache[key]

def plaque_at(text, rel):
    full = wrap(text, F_PLAQUE, 900)
    k = min(len(text), int(rel / 0.35 * len(text)) + 1)   # typewriter in 0.35s
    return cached(("p", text, k), lambda: plaque(text[:k], F_PLAQUE, PLAQUE_TOP, full_lines=full))

BLACK = Image.new("RGBA", (W, H), (0, 0, 0, 255))

enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                        "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "video_only.mp4"],
                       stdin=subprocess.PIPE)
t_out = 0.0
final_t0 = None
for ci, (a, b) in enumerate(CUTS):
    frs = frames_of_video(a, b)
    last = ci == len(CUTS) - 1
    n_vid = len(frs)
    if last:
        frs += [frs[-1]] * int(FREEZE_END * FPS)
    for i, fr in enumerate(frs):
        src_t = a + min(i, n_vid - 1) / FPS if i < n_vid else b
        fr = fr.convert("RGBA")
        final = last and src_t >= FINAL_AT
        intro = t_out < INTRO_END
        if final:
            if final_t0 is None: final_t0 = t_out
            fr = Image.blend(fr, BLACK, 0.55 * min(1.0, (t_out - final_t0) / 0.35))
            fr.alpha_composite(pop(FINAL, t_out - final_t0))
        else:
            if intro:
                fade = 1.0 if t_out < INTRO_END - 0.25 else (INTRO_END - t_out) / 0.25
                fr = Image.blend(fr, BLACK, 0.5 * fade)
                fr.alpha_composite(pop(INTRO, t_out))
            else:
                fr.alpha_composite(cached("title", lambda: plaque(TITLE, F_TITLE, TITLE_TOP,
                                                                   align="center", maxw=960)))
                for p0, p1, txt in PLAQUES:
                    if p0 <= src_t < p1:
                        fr.alpha_composite(plaque_at(txt, src_t - max(p0, a)))
            for s0, s1, tag, txt in SUBS:
                if s0 <= src_t < s1:
                    fr.alpha_composite(cached(("s", txt), lambda: subtitle(txt, tag)))
        enc.stdin.write(fr.convert("RGB").tobytes())
        t_out += 1 / FPS
    print(f"cut {ci} {a}-{b}: {len(frs)} frames, out {t_out:.2f}s", flush=True)
enc.stdin.close(); enc.wait()

# ---------------- audio ----------------
inputs, filt, labels = [], [], []
for i, (a, b) in enumerate(CUTS):
    d = b - a
    inputs += ["-i", SRC]
    filt.append(f"[{i}:a]atrim={a}:{b},asetpts=PTS-STARTPTS,aresample=48000,"
                f"aformat=channel_layouts=stereo,afade=t=in:d=0.03,afade=t=out:st={d-0.04:.3f}:d=0.04[a{i}]")
    labels.append(f"[a{i}]")
n = len(CUTS)
inputs += ["-f", "lavfi", "-t", str(FREEZE_END), "-i", "anullsrc=r=48000:cl=stereo"]
filt.append(f"[{n}:a]anull[a{n}]"); labels.append(f"[a{n}]")
fade_st = t_out - FREEZE_END - 1.0
fc = ";".join(filt) + ";" + "".join(labels) + f"concat=n={len(labels)}:v=0:a=1,highpass=f=80," \
     f"afftdn=nf=-25,afade=t=out:st={fade_st:.2f}:d=1.0,loudnorm=I=-14:TP=-1.5:LRA=11[aout]"
subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc, "-map", "[aout]",
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "audio.m4a"], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "video_only.mp4", "-i", "audio.m4a", "-c:v", "copy",
                "-c:a", "copy", "-shortest", "-movflags", "+faststart", "good_terms_reels.mp4"], check=True)
print("total", round(t_out, 2))
