"""Подготовка голоса без модели распознавания.

Модели whisper в этом окружении скачать нельзя (Hugging Face закрыт сетевой политикой),
поэтому тайминги слов берутся так:
1. по огибающей громкости находим паузы в записи;
2. текст из script.md (он совпадает с тем, что сказано) раскладываем по фразам между паузами:
   динамическое программирование подбирает, после каких слов стоят паузы, так чтобы длительность
   речи между паузами соответствовала числу букв, а паузы приходились на знаки препинания;
3. внутри куска речи слова распределяются пропорционально длине.

Затем звук: тишина в начале обрезается до 0.2 с, лёгкий шумодав, громкость −14 LUFS,
в конце 1 с под финальный кадр. Результат: public/audio/voiceover_clean.wav и public/transcript.json.

Запуск: python3 scripts/voice.py  (из папки video/)
"""
import json
import re
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np

VIDEO = Path(__file__).resolve().parent.parent
ROOT = VIDEO.parent
audio_dir = ROOT / 'assets' / 'audio'
src = next((p for p in sorted(audio_dir.glob('voiceover.*'))), None)
if not src:
    sys.exit('Нет assets/audio/voiceover.*')

tmp = Path(tempfile.mkdtemp())
w16 = tmp / 'v16.wav'
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', str(src), '-ar', '16000', '-ac', '1', str(w16)], check=True)

# --- огибающая громкости и паузы
w = wave.open(str(w16))
x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
total = len(x) / 16000
hop, win = 160, 400
n = (len(x) - win) // hop
frames = np.lib.stride_tricks.sliding_window_view(x, win)[::hop][:n]
db = 20 * np.log10(np.sqrt((frames ** 2).mean(axis=1)) + 1e-9)
db = np.convolve(db, np.ones(5) / 5, 'same')
noise, speech = np.percentile(db, 10), np.percentile(db, 80)
low = db < noise + (speech - noise) * 0.25
pauses = []
i = 0
while i < n:
    if low[i]:
        j = i
        while j < n and low[j]:
            j += 1
        if (j - i) * 0.01 >= 0.18:
            pauses.append((i * 0.01, j * 0.01))
        i = j
    else:
        i += 1
speech_start = pauses[0][1] if pauses and pauses[0][0] < 0.05 else 0.0
speech_end = pauses[-1][0] if pauses and pauses[-1][1] > total - 0.05 else total
inner = [p for p in pauses if p[0] > speech_start and p[1] < speech_end]
# границы: начало речи, каждая внутренняя пауза, конец речи
bounds = [(speech_start, speech_start)] + inner + [(speech_end, speech_end)]

# --- слова сценария
script = (ROOT / 'script.md').read_text()
scenes = re.findall(r'\*\*\[(S\d+)\]\*\*\s*(.+)', script)
words = [(sid, wd) for sid, txt in scenes for wd in txt.split()]
letters = [len(re.sub(r'[^A-Za-zА-Яа-яЁё0-9]', '', wd)) + 1.5 for _, wd in words]
punct = [bool(re.search(r'[.,:;?!—]$', wd)) for _, wd in words]
cum = np.concatenate([[0], np.cumsum(letters)])
NW = len(words)
NB = len(bounds)

def speech_between(a, b):
    """Длительность речи между границами a и b (паузы внутри вычитаются)."""
    t = bounds[b][0] - bounds[a][1]
    for k in range(a + 1, b):
        t -= bounds[k][1] - bounds[k][0]
    return t

rate = cum[-1] / speech_between(0, NB - 1)  # букв в секунду

# DP: граница k (пауза) ставится после слова j. Паузы можно пропускать (пауза внутри фразы).
INF = 1e18
best = np.full((NB, NW + 1), INF)
prev = {}
best[0][0] = 0
for a in range(NB - 1):
    for j in range(NW + 1):
        if best[a][j] >= INF:
            continue
        for b in range(a + 1, min(NB, a + 6)):
            dur = speech_between(a, b)
            lo = j + 1
            hi = NW if b == NB - 1 else min(NW - 1, j + 70)
            rng = [NW] if b == NB - 1 else range(lo, hi + 1)
            for k in rng:
                ch = cum[k] - cum[j]
                dev = (dur - ch / rate) / (0.35 + 0.12 * dur)
                c = dev * dev
                if b != NB - 1 and not punct[k - 1]:
                    c += 4.0
                c += 0.6 * (b - a - 1)  # пропущенные паузы
                if best[a][j] + c < best[b][k]:
                    best[b][k] = best[a][j] + c
                    prev[(b, k)] = (a, j)
# восстановление
path = []
b, k = NB - 1, NW
while (b, k) != (0, 0):
    a, j = prev[(b, k)]
    path.append((a, j, b, k))
    b, k = a, j
path.reverse()

timed = []
for a, j, b, k in path:
    t0 = bounds[a][1]
    t1 = bounds[b][0]
    # пропущенные паузы внутри куска: распределяем слова по чистому времени речи
    segs = [(bounds[a][1], bounds[a + 1][0] if a + 1 < b else t1)]
    for q in range(a + 1, b):
        segs.append((bounds[q][1], bounds[q + 1][0]))
    sp_total = sum(e - s for s, e in segs)

    def at(frac):
        r = frac * sp_total
        for s, e in segs:
            if r <= e - s:
                return s + r
            r -= e - s
        return segs[-1][1]

    tot = cum[k] - cum[j]
    for m in range(j, k):
        f0 = (cum[m] - cum[j]) / tot
        f1 = (cum[m + 1] - cum[j]) / tot
        timed.append({'scene': words[m][0], 'word': words[m][1], 'start': at(f0), 'end': at(f1) - 0.03})

# --- звук: обрезка начала до 0.2 с, 1 с в конце, шумодав, −14 LUFS
cut = max(0.0, speech_start - 0.2)
end = min(total, speech_end + 1.0)
out_audio = VIDEO / 'public' / 'audio'
out_audio.mkdir(parents=True, exist_ok=True)
clean = out_audio / 'voiceover_clean.wav'
pre = 'highpass=f=70,afftdn=nr=8:nf=-45'
dur_out = end - cut
pad = max(0.0, 1.0 - (total - speech_end))
cut_args = ['-ss', f'{cut:.3f}', '-t', f'{end - cut:.3f}', '-i', str(src)]
# двухпроходная нормализация до −14 LUFS (однопроходная промахивается на 1–2 LU)
meas = subprocess.run(['ffmpeg', '-hide_banner', '-y', *cut_args, '-af', pre + ',loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'],
                      capture_output=True, text=True).stderr
m = json.loads(meas[meas.rindex('{'):meas.rindex('}') + 1])
ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
      f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', *cut_args, '-af', pre + ',' + ln + (f',apad=pad_dur={pad:.3f}' if pad > 0 else ''),
                '-ar', '48000', '-ac', '1', str(clean)], check=True)
dur_out += pad

for t in timed:
    t['start'] = round(t['start'] - cut, 3)
    t['end'] = round(t['end'] - cut, 3)
(VIDEO / 'public' / 'transcript.json').write_text(json.dumps({'duration': round(dur_out, 3), 'method': 'pauses', 'words': timed}, ensure_ascii=False, indent=1))

print(f'речь {speech_start:.2f}–{speech_end:.2f} с, пауз {len(inner)}, обрезано в начале {cut:.2f} с, итог {dur_out:.2f} с')
for a, j, b, k in path:
    print(f'  {bounds[a][1] - cut:6.2f}–{bounds[b][0] - cut:6.2f}  {" ".join(wd for _, wd in words[j:k])}')
