import React from 'react';
import {interpolate} from 'remotion';
import {Check, HandOval, rnd} from './common';
import {C, SANS} from './theme';
import {easeOut, prog, scene, sp, wt} from './time';

// Геометрия лесенки (полный размер)
export const L = {x0: 230, w: 130, gap: 8, rise: 140, base: 1330, footX: 140};
const colW = L.w - L.gap;
export const stepX = (i: number) => L.x0 + i * L.w;
export const treadY = (i: number) => L.base - L.rise * (i + 1);
const CHIP_H = 104;
const CHIP_W = 176;
const chipCX = (lvl: number) => (lvl < 0 ? L.footX : stepX(lvl) + colW / 2);
const chipBottom = (lvl: number) => (lvl < 0 ? L.base : treadY(lvl));

const STEP_NAMES = ['узнаю', 'вспоминаю значение', 'нахожу слово', 'вспоминаю с подсказкой', 'говорю свободно'];

// Ключевые моменты
const T = () => {
  const build = scene('S04').start + 0.45; // сразу после скриншота вопроса
  const s12 = scene('S12');
  // прыжки не чаще, чем раз в 0.42 с (иначе дуги наезжают друг на друга)
  const hops: number[] = [];
  [0, 1, 2].forEach((k) => hops.push(Math.max(wt('S12', 'хоп', k), k ? hops[k - 1] + 0.42 : 0)));
  return {
    build,
    chipIn: build + 5 * 0.12 + 0.35,
    scaleIn: wt('S04', 'трудную'),
    // прыжки фишки: [время, уровень]
    jumps: [
      [wt('S05', 'узнаю'), 0],
      [wt('S06', 'вспоминаю'), 1],
      [wt('S07', 'нахожу'), 2],
      [wt('S08', 'вспоминаю'), 3],
      [wt('S09', 'говорю'), 4],
      [s12.start + 0.25, -1],
      [hops[0], 0],
      [hops[1], 1],
      [hops[2], 4],
    ] as [number, number][],
    easy: wt('S10', 'проще'),
    hard: wt('S10', 'сложнее'),
    s10end: scene('S10').end,
    s11: scene('S11').start,
    s12: s12.start,
    s13: scene('S13').start,
    oval9: wt('S09', 'говорю') + 0.45,
  };
};

const JUMP = 0.38;

const chipState = (t: number, k: ReturnType<typeof T>) => {
  let from = -1;
  let to = -1;
  let t0 = -1e9;
  let last = false;
  k.jumps.forEach(([tj, lvl], i) => {
    if (t >= tj) {
      from = to;
      to = lvl;
      t0 = tj;
      last = i === k.jumps.length - 1;
    }
  });
  const p = prog(t, t0, JUMP);
  const x = interpolate(p, [0, 1], [chipCX(from), chipCX(to)]);
  const yb = interpolate(p, [0, 1], [chipBottom(from), chipBottom(to)]);
  const arc = Math.sin(Math.PI * p) * (60 + 30 * Math.abs(to - from));
  // приземление: лёгкое пружинящее сжатие; на финальном «хоп» — отскок
  const land = t - (t0 + JUMP);
  let bounce = 0;
  let squash = 0;
  if (land > 0 && land < 0.6) {
    squash = Math.exp(-land * 9) * Math.sin(land * 30) * 0.06;
    if (last) bounce = Math.abs(Math.sin(land * 10)) * Math.exp(-land * 7) * 38;
  }
  return {x, y: yb - arc - bounce, level: p >= 1 ? to : p > 0.5 ? to : from, landed: t >= t0 + JUMP, squash, t0, to};
};

export const Ladder: React.FC<{t: number}> = ({t}) => {
  const k = T();
  if (t < k.build) return null;

  // С S13 лесенка уезжает вверх, уменьшается и остаётся там до конца
  const shrinkP = prog(t, k.s13 + 0.1, 0.8);
  const small = t >= k.s13;
  const opacity = 1;
  const sc = interpolate(shrinkP, [0, 1], [1, 0.34]);
  // центр рамки лесенки (x 60..940, y 520..1330) → верх кадра
  const bx = 500;
  const by = 925;
  const tx = interpolate(shrinkP, [0, 1], [0, 500 - bx]);
  const ty = interpolate(shrinkP, [0, 1], [0, 380 - by]);
  const detail = 1 - prog(t, k.s13, 0.35); // подписи, шкала, стикеры

  const chip = chipState(t, k);
  const resetAt = k.s12; // в S12 ступеньки заново, начиная с подножия
  const inS12 = t >= resetAt && t < k.s13;
  const chipIn = sp(t, k.chipIn, {damping: 14});

  // какие ступеньки уже пройдены (для подписей — с первого прохода)
  const reachedAt = (i: number) => {
    const j = k.jumps.find(([tj, lvl]) => lvl >= i && tj < k.s12);
    return j ? j[0] + JUMP * 0.6 : Infinity;
  };

  return (
    <div style={{position: 'absolute', inset: 0, opacity, transform: `translate(${tx}px, ${ty}px) scale(${sc})`, transformOrigin: `${bx}px ${by}px`}}>
      {/* Ступеньки */}
      {[0, 1, 2, 3, 4].map((i) => {
        const g = sp(t, k.build + i * 0.12, {damping: 16, stiffness: 160});
        const h = L.rise * (i + 1);
        const cur = chip.landed || chip.level === chip.to ? chip.level : chip.level;
        const active = !small ? cur === i : i === 4;
        const passed = !small ? cur > i : i < 4;
        // S10: подсветка «легко» / «сложно»
        const hl = i === 0 ? Math.min(prog(t, k.easy, 0.3), 1 - prog(t, k.s10end - 0.3, 0.3)) : i === 4 ? Math.min(prog(t, k.hard, 0.3), 1 - prog(t, k.s10end - 0.3, 0.3)) : 0;
        const fill = hl > 0 ? mix(active ? C.ink : C.mist, C.marker, hl) : active ? C.ink : C.mist;
        const passIn = inS12 ? 1 : 1;
        return (
          <div key={i}>
            <div
              style={{
                position: 'absolute',
                left: stepX(i),
                top: treadY(i),
                width: colW,
                height: h,
                background: fill,
                borderRadius: '14px 14px 0 0',
                transform: `scaleY(${g})`,
                transformOrigin: 'bottom',
                transition: 'none',
              }}
            />
            {passed && chip.landed !== undefined && (
              <div style={{position: 'absolute', left: stepX(i) + colW - 42, top: treadY(i) + 10, opacity: passIn}}>
                <Check size={32} color={C.sky} stroke={4} />
              </div>
            )}
            {hl > 0 && (
              <div style={{position: 'absolute', left: stepX(i), width: colW, top: treadY(i) + 40, textAlign: 'center', fontFamily: SANS, fontWeight: 600, fontSize: 30, color: C.ink, opacity: hl}}>
                {i === 0 ? 'легко' : 'сложно'}
              </div>
            )}
          </div>
        );
      })}

      {/* Названия ступенек — слева от ступеньки, на уровне фишки */}
      {[0, 1, 2, 3, 4].map((i) => {
        const a = prog(t, reachedAt(i), 0.4, easeOut) * detail;
        if (a <= 0) return null;
        const right = stepX(i) - (i === 4 ? 46 : 32);
        const isCur = !small && chip.level === i && t < k.s12;
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: 60,
              width: right - 60,
              top: treadY(i) - L.rise + 8,
              height: L.rise - 16,
              display: 'flex',
              alignItems: 'flex-end',
              justifyContent: 'flex-end',
              textAlign: 'right',
              opacity: a,
              color: C.ink,
            }}
          >
            <div style={{fontFamily: SANS, fontWeight: isCur ? 600 : 500, fontSize: 34, lineHeight: 1.1, paddingBottom: 6, whiteSpace: i === 0 ? 'nowrap' : 'normal'}}>
              <span style={{fontFamily: 'inherit', color: C.sky, fontWeight: 600}}>{i + 1}</span> {STEP_NAMES[i]}
            </div>
          </div>
        );
      })}

      {/* Шкала «легко → трудно» справа */}
      <Scale t={t} k={k} detail={detail} />

      {/* Толпа (S11) */}
      <Crowd t={t} k={k} />

      {/* Фишка */}
      {t >= k.chipIn && (
        <div
          style={{
            position: 'absolute',
            left: chip.x - CHIP_W / 2,
            top: chip.y - CHIP_H,
            width: CHIP_W,
            height: CHIP_H,
            background: C.white,
            borderRadius: 20,
            boxShadow: '0 10px 24px rgba(30,42,68,0.18), 0 2px 4px rgba(30,42,68,0.10)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            textAlign: 'center',
            fontFamily: SANS,
            fontWeight: 600,
            fontSize: 36,
            lineHeight: 1.05,
            color: C.ink,
            transform: `scale(${chipIn * (1 + chip.squash)}, ${chipIn * (1 - chip.squash)})`,
            transformOrigin: 'bottom center',
          }}
        >
          make a<br />decision
        </div>
      )}

      {/* S09: обводка вокруг фишки на вершине */}
      {t < k.s10end && <HandOval cx={chipCX(4)} cy={treadY(4) - CHIP_H / 2} rx={128} ry={88} t={t} start={k.oval9} seed={11} opacity={1 - prog(t, scene('S10').start, 0.4)} />}
    </div>
  );
};

const Scale: React.FC<{t: number; k: ReturnType<typeof T>; detail: number}> = ({t, k, detail}) => {
  const p = prog(t, k.scaleIn, 0.6, easeOut);
  if (p <= 0 || detail <= 0) return null;
  const x = 915;
  const y1 = L.base - 10;
  const y2 = treadY(4) + 20;
  const yy = y1 - (y1 - y2) * p;
  const hl = Math.min(prog(t, k.easy, 0.5), 1 - prog(t, k.s10end - 0.3, 0.3));
  return (
    <div style={{position: 'absolute', inset: 0, opacity: detail}}>
      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
        {hl > 0 && <line x1={x} y1={y1} x2={x} y2={y1 - (y1 - y2) * hl} stroke={C.marker} strokeWidth={22} strokeLinecap="round" />}
        <line x1={x} y1={y1} x2={x} y2={yy} stroke={C.sky} strokeWidth={4} strokeLinecap="round" />
        {p > 0.9 && <path d={`M ${x - 13} ${y2 + 18} L ${x} ${y2} L ${x + 13} ${y2 + 18}`} fill="none" stroke={C.sky} strokeWidth={4} strokeLinecap="round" strokeLinejoin="round" />}
      </svg>
      {[
        ['легко', y1 - 70],
        ['трудно', y2 + 75],
      ].map(([s, y]) => (
        <div
          key={s as string}
          style={{
            position: 'absolute',
            left: x - 30 - 100,
            top: (y as number) - 18,
            width: 200,
            height: 36,
            textAlign: 'center',
            transform: 'rotate(-90deg)',
            fontFamily: SANS,
            fontWeight: 600,
            fontSize: 24,
            color: C.sky,
            opacity: p,
          }}
        >
          {s}
        </div>
      ))}
    </div>
  );
};

const Crowd: React.FC<{t: number; k: ReturnType<typeof T>}> = ({t, k}) => {
  if (t < k.s11 || t > k.s12 + 0.5) return null;
  const out = 1 - prog(t, k.s12, 0.35);
  const r = rnd(5);
  const dots: {x: number; y: number; d: number}[] = [];
  [0, 1].forEach((s) => {
    const n = s === 0 ? 10 : 8;
    for (let j = 0; j < n; j++) {
      const row = j < Math.ceil(n / 2) ? 0 : 1;
      const col = row === 0 ? j : j - Math.ceil(n / 2);
      const x = stepX(s) + 16 + col * 22 + (row ? 11 : 0) + (r() - 0.5) * 6;
      const y = treadY(s) - 15 - row * 26 - r() * 4;
      dots.push({x, y, d: (s * 10 + j) * 0.025});
    }
  });
  return (
    <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
      {dots.map((d, i) => {
        const a = sp(t, k.s11 + 0.2 + d.d, {damping: 14});
        return <circle key={i} cx={d.x} cy={d.y} r={13 * a} fill={C.sky} opacity={out} />;
      })}
    </svg>
  );
};

function mix(a: string, b: string, k: number) {
  const pa = [1, 3, 5].map((i) => parseInt(a.slice(i, i + 2), 16));
  const pb = [1, 3, 5].map((i) => parseInt(b.slice(i, i + 2), 16));
  return `rgb(${pa.map((v, i) => Math.round(v + (pb[i] - v) * k)).join(',')})`;
}
