// Собирает src/generated/timeline.json: границы сцен, тайминги слов и куски субтитров.
// Без голоса (черновик) — длительности из scenes.json.
// С голосом — из public/transcript.json (пословные таймкоды whisper).
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const video = path.resolve(here, '..');
// PART=2 — вторая часть (папка ../part2), PART=lesson — ролик про подготовку урока (../../lesson_prep).
// У каждого свои голос, транскрипт и таймлайн.
const PART = ['2', 'lesson'].includes(process.env.PART) ? process.env.PART : '';
const reelRoot = path.resolve(video, '..');
const root = {'': reelRoot, 2: path.join(reelRoot, 'part2'), lesson: path.resolve(reelRoot, '..', 'lesson_prep')}[PART];
const AUDIO = `audio${PART}`;

const scenesCfg = JSON.parse(fs.readFileSync(path.join(root, 'scenes.json'), 'utf8'));
const scriptMd = fs.readFileSync(path.join(root, 'script.md'), 'utf8');

// Синхронизируем ассеты (картинки, голос) в public/
for (const [dir, to] of [['images', 'images'], ['audio', AUDIO], ['screencasts', 'lesson']]) {
  const src = path.join(root, 'assets', dir);
  if (!fs.existsSync(src)) continue;
  const dst = path.join(video, 'public', to);
  fs.mkdirSync(dst, {recursive: true});
  for (const f of fs.readdirSync(src)) fs.copyFileSync(path.join(src, f), path.join(dst, f));
}

const exists = (p) => fs.existsSync(path.join(video, 'public', p));
const hasQuestion = exists('images/subscriber_question.png');
// пропорции скриншота вопроса (PNG: ширина/высота в заголовке IHDR)
let questionAspect = 860 / 640;
if (hasQuestion) {
  const b = fs.readFileSync(path.join(video, 'public', 'images', 'subscriber_question.png'));
  questionAspect = b.readUInt32BE(16) / b.readUInt32BE(20);
}
const voiceFile = [`${AUDIO}/voiceover_clean.wav`].find(exists) ?? null;
const transcriptPath = path.join(video, 'public', `transcript${PART}.json`);
const hasTranscript = fs.existsSync(transcriptPath) && voiceFile;
const musicFile = ['m4a', 'mp3', 'wav'].map((e) => `${AUDIO}/music.${e}`).find(exists) ?? null;

// Текст сцен из script.md — источник правды для субтитров
const sceneText = {};
for (const m of scriptMd.matchAll(/\*\*\[(S\d+)\]\*\*\s*(.+)/g)) sceneText[m[1]] = m[2].trim();

export const norm = (w) => w.toLowerCase().replace(/ё/g, 'е').replace(/[^a-zа-я0-9]/g, '');

const scriptWords = [];
for (const s of scenesCfg.scenes) {
  const text = sceneText[s.id];
  if (!text) throw new Error(`В script.md нет текста для ${s.id}`);
  for (const w of text.split(/\s+/)) scriptWords.push({w, n: norm(w), scene: s.id});
}

const TAIL = 1.0; // секунда на финальный кадр
let scenes = [];
let words = [];
const notes = [];

if (!hasTranscript) {
  // Черновик: длительности из scenes.json, слова равномерно (с весом по длине слова)
  let t = 0;
  for (const s of scenesCfg.scenes) {
    const start = t;
    const end = t + s.est_seconds;
    scenes.push({id: s.id, start, end});
    const sw = scriptWords.filter((x) => x.scene === s.id);
    const a = start + 0.3;
    const b = end - 0.45;
    const weights = sw.map((x) => x.n.length + 2);
    const total = weights.reduce((p, c) => p + c, 0);
    let acc = a;
    sw.forEach((x, i) => {
      const d = ((b - a) * weights[i]) / total;
      words.push({w: x.w, n: x.n, scene: s.id, start: acc, end: acc + d * 0.9});
      acc += d;
    });
    t = end;
  }
} else {
  // Синхронизация: выравниваем слова сценария со словами транскрипта
  const tr = JSON.parse(fs.readFileSync(transcriptPath, 'utf8'));
  const tw = tr.words.map((x) => ({...x, n: norm(x.word)})).filter((x) => x.n);
  // Глобальное выравнивание (Нидлман–Вунш) по нормализованным словам
  const A = scriptWords, B = tw;
  const sim = (a, b) => {
    if (a === b) return 2;
    const k = Math.min(a.length, b.length, 4);
    return k >= 3 && a.slice(0, k) === b.slice(0, k) ? 1 : -1;
  };
  const n = A.length, m = B.length;
  const S = Array.from({length: n + 1}, () => new Float32Array(m + 1));
  const P = Array.from({length: n + 1}, () => new Uint8Array(m + 1));
  for (let i = 1; i <= n; i++) { S[i][0] = -i; P[i][0] = 1; }
  for (let j = 1; j <= m; j++) { S[0][j] = -0.5 * j; P[0][j] = 2; }
  for (let i = 1; i <= n; i++) for (let j = 1; j <= m; j++) {
    const d = S[i - 1][j - 1] + sim(A[i - 1].n, B[j - 1].n);
    const u = S[i - 1][j] - 1;
    const l = S[i][j - 1] - 0.5;
    if (d >= u && d >= l) { S[i][j] = d; P[i][j] = 0; } else if (u >= l) { S[i][j] = u; P[i][j] = 1; } else { S[i][j] = l; P[i][j] = 2; }
  }
  const match = new Array(n).fill(-1);
  for (let i = n, j = m; i > 0 || j > 0;) {
    const p = P[i][j];
    if (i > 0 && j > 0 && p === 0) { if (sim(A[i - 1].n, B[j - 1].n) > 0) match[i - 1] = j - 1; i--; j--; }
    else if (i > 0 && (j === 0 || p === 1)) i--;
    else j--;
  }
  // Слова без пары — интерполяция между соседями
  const times = A.map((_, i) => (match[i] >= 0 ? [B[match[i]].start, B[match[i]].end] : null));
  for (let i = 0; i < n; i++) {
    if (times[i]) continue;
    let p = i - 1; while (p >= 0 && !times[p]) p--;
    let q = i + 1; while (q < n && !times[q]) q++;
    const t0 = p >= 0 ? times[p][1] : 0;
    const t1 = q < n ? times[q][0] : tr.duration;
    const k = (i - p) / (q - p);
    times[i] = [t0 + (t1 - t0) * k - 0.05, t0 + (t1 - t0) * k + 0.2];
  }
  words = A.map((x, i) => ({w: x.w, n: x.n, scene: x.scene, start: times[i][0], end: times[i][1]}));
  // Границы сцен: проверяем якорь (первые слова сцены), старт за 0.15 с до первого слова
  for (const s of scenesCfg.scenes) {
    const idx = A.findIndex((x) => x.scene === s.id);
    const anchorN = s.anchor.split(/\s+/).map(norm);
    const found = anchorN.every((a, k) => match[idx + k] >= 0 && B[match[idx + k]].n === a);
    if (!found) notes.push(`${s.id}: якорь «${s.anchor}» распознан неточно, граница по интерполяции`);
    scenes.push({id: s.id, start: Math.max(0, words[idx].start - 0.15), end: 0});
  }
  scenes[0].start = 0;
  scenes.forEach((s, i) => (s.end = i + 1 < scenes.length ? scenes[i + 1].start : tr.duration));
}

const lastEnd = Math.max(scenes[scenes.length - 1].end, words[words.length - 1].end + TAIL);
scenes[scenes.length - 1].end = lastEnd;

// Субтитры: куски по 2–4 слова, не длиннее ~24 символов, без точек в конце куска.
// Разбиение по сценам динамическим программированием: штрафуем одиночные слова,
// висящие предлоги в конце куска и разрыв без знака препинания.
const MAX_CHARS = 25;
const WEAK = new Set(['в', 'во', 'на', 'по', 'с', 'со', 'и', 'а', 'из', 'до', 'об', 'о', 'к', 'у', 'за', 'для', 'не', 'мне', 'что', 'чтобы', 'как', 'эти', 'его', 'моей', 'моих', 'ваши', 'мой', 'когда', 'где', 'так', 'около', 'таких', 'каждый', 'каждую', 'каждой', 'чуть', 'более', 'первых', 'верхней', 'нужное', 'готовыми', 'этот', 'целиком', 'в']);
const chunks = [];
for (const s of scenesCfg.scenes) {
  const sw = words.map((w, i) => ({...w, i})).filter((w) => w.scene === s.id);
  const n = sw.length;
  const cost = (a, b) => {
    // кусок sw[a..b)
    const k = b - a;
    const len = sw.slice(a, b).reduce((p, x) => p + x.w.length, 0) + k - 1;
    if (k > 4 || (len > MAX_CHARS && k > 1)) return Infinity;
    let c = Math.pow(Math.max(0, 16 - len), 2) * 0.15;
    if (k === 1) c += 30;
    const last = sw[b - 1].w;
    const punct = /[.?!:,;]$/.test(last);
    if (b < n && !punct) c += 8;
    if (WEAK.has(sw[b - 1].n) && b < n) c += 40;
    // знак препинания внутри куска (кроме запятой) — разрыв предложения
    for (let j = a; j < b - 1; j++) if (/[.?!:]$/.test(sw[j].w)) c += 25;
    return c;
  };
  const best = new Array(n + 1).fill(Infinity);
  const prev = new Array(n + 1).fill(-1);
  best[0] = 0;
  for (let b = 1; b <= n; b++) for (let a = Math.max(0, b - 4); a < b; a++) {
    const c = best[a] + cost(a, b);
    if (c < best[b]) { best[b] = c; prev[b] = a; }
  }
  const parts = [];
  for (let b = n; b > 0; b = prev[b]) parts.unshift(sw.slice(prev[b], b));
  chunks.push(...parts);
}
const subtitles = chunks.map((c, k) => {
  const nx = chunks[k + 1];
  const start = c[0].start - 0.05;
  const end = nx ? Math.min(nx[0].start - 0.05, c[c.length - 1].end + 0.6) : c[c.length - 1].end + 0.6;
  const ws = c.map((x, j) => ({
    text: j === c.length - 1 ? x.w.replace(/[.,:;]+$/, '') : x.w,
    start: x.start,
    end: x.end,
  }));
  return {start, end, words: ws};
});

const out = {
  mode: hasTranscript ? 'sync' : 'draft',
  fps: scenesCfg.fps,
  width: scenesCfg.width,
  height: scenesCfg.height,
  duration: lastEnd,
  hasQuestion,
  questionAspect,
  voice: hasTranscript ? voiceFile : null,
  music: hasTranscript ? musicFile : null,
  scenes,
  words: words.map(({w, n, scene, start, end}) => ({w, n, scene, start: +start.toFixed(3), end: +end.toFixed(3)})),
  subtitles,
  notes,
};
fs.mkdirSync(path.join(video, 'src', 'generated'), {recursive: true});
fs.writeFileSync(path.join(video, 'src', 'generated', `timeline${PART}.json`), JSON.stringify(out, null, 1));
console.log(`timeline: ${out.mode}, ${out.duration.toFixed(2)} с, ${scenes.length} сцен, ${subtitles.length} кусков субтитров`);
if (!hasQuestion && !PART) console.log('ВНИМАНИЕ: нет assets/images/subscriber_question.png — в кадре S03 заглушка');
for (const n of notes) console.log('ВНИМАНИЕ:', n);
