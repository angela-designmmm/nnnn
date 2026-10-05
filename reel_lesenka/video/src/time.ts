import {Easing, interpolate, spring} from 'remotion';
import timeline from './generated/timeline.json';

export type Timeline = {
  mode: 'draft' | 'sync';
  fps: number;
  width: number;
  height: number;
  duration: number;
  hasQuestion: boolean;
  questionAspect: number;
  voice: string | null;
  scenes: {id: string; start: number; end: number}[];
  words: {w: string; n: string; scene: string; start: number; end: number}[];
  subtitles: {start: number; end: number; words: {text: string; start: number; end: number}[]}[];
};

const norm = (w: string) => w.toLowerCase().replace(/ё/g, 'е').replace(/[^a-zа-я0-9]/g, '');

// Помощники времени для конкретного таймлайна (часть 1 или часть 2)
export const makeTime = (tl: Timeline) => {
  const scene = (id: string) => {
    const s = tl.scenes.find((x) => x.id === id);
    if (!s) throw new Error(`Нет сцены ${id}`);
    return s;
  };
  // Время начала слова внутри сцены (n-е вхождение) — к нему привязаны анимации
  const wt = (sceneId: string, word: string, nth = 0): number => {
    const ws = tl.words.filter((w) => w.scene === sceneId);
    const n = norm(word);
    let m = ws.filter((w) => w.n === n);
    if (!m.length) m = ws.filter((w) => w.n.startsWith(n));
    if (!m.length) throw new Error(`Слово «${word}» не найдено в ${sceneId}`);
    return (m[nth] ?? m[m.length - 1]).start;
  };
  return {tl, scene, wt};
};

const part1 = makeTime(timeline as Timeline);
export const tl = part1.tl;
export const scene = part1.scene;
export const wt = part1.wt;

// 0..1 за dur секунд начиная с start
export const prog = (t: number, start: number, dur: number, ease = Easing.inOut(Easing.cubic)) =>
  interpolate(t, [start, start + dur], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});

export const easeOut = Easing.out(Easing.cubic);

// Мягкая пружина, стартующая в момент start (секунды)
export const sp = (t: number, start: number, cfg: {damping?: number; stiffness?: number; mass?: number} = {}) =>
  spring({
    frame: Math.max(0, (t - start) * tl.fps),
    fps: tl.fps,
    config: {damping: 18, stiffness: 140, mass: 0.8, ...cfg},
  });

// Видимость слоя: плавно появляется в a, исчезает в b
export const vis = (t: number, a: number, b: number, fadeIn = 0.35, fadeOut = 0.35) =>
  Math.min(prog(t, a, fadeIn, easeOut), 1 - prog(t, b - fadeOut, fadeOut));
