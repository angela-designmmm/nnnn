import React from 'react';
import {AbsoluteFill, Audio, getInputProps, Img, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {HandOval, Layer, Paper} from './common';
import timeline2 from './generated/timeline2.json';
import {Subtitles} from './Subtitles';
import {C, CX, PROFILE_ASPECT, PROFILE_OVAL, SANS, SERIF, SOURCE_EBBINGHAUS, SOURCE_NAKATA} from './theme';
import {easeOut, makeTime, prog, sp, Timeline, vis} from './time';

const {tl, scene, wt} = makeTime(timeline2 as Timeline);
export const tl2 = tl;
const showSubtitles = getInputProps().subtitles !== false;

const card: React.CSSProperties = {
  position: 'absolute',
  padding: '30px 40px',
  boxSizing: 'border-box',
  background: C.white,
  borderRadius: 28,
  boxShadow: '0 8px 24px rgba(30,42,68,0.10)',
  fontFamily: SANS,
  color: C.ink,
};
const shot: React.CSSProperties = {
  position: 'absolute',
  borderRadius: 28,
  boxShadow: '0 12px 30px rgba(30,42,68,0.20), 0 2px 6px rgba(30,42,68,0.10)',
  background: C.white,
  overflow: 'hidden',
};
const hl = (on: number): React.CSSProperties => ({
  background: on > 0 ? `linear-gradient(transparent 60%, rgba(242,201,76,${on}) 60%, rgba(242,201,76,${on}) 92%, transparent 92%)` : 'none',
});

// ── Фишка и маленькая лесенка (как в первой части) ──────────────────────────
const Chip: React.FC<{cx: number; bottom: number; scale?: number; ghost?: number}> = ({cx, bottom, scale = 1, ghost = 0}) => (
  <div
    style={{
      position: 'absolute',
      left: cx - 88,
      top: bottom - 104,
      width: 176,
      height: 104,
      boxSizing: 'border-box',
      background: ghost > 0 ? `rgba(255,255,255,${1 - ghost})` : C.white,
      border: ghost > 0 ? `${3 * ghost}px dashed ${C.sky}` : 'none',
      borderRadius: 20,
      boxShadow: `0 10px 24px rgba(30,42,68,${0.18 * (1 - ghost)})`,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      textAlign: 'center',
      fontFamily: SANS,
      fontWeight: 600,
      fontSize: 36,
      lineHeight: 1.05,
      color: C.ink,
      transform: `scale(${scale})`,
      transformOrigin: 'bottom center',
    }}
  >
    <span style={{opacity: 1 - ghost * 0.85}}>
      make a<br />decision
    </span>
  </div>
);

const MiniLadder: React.FC<{x: number; base: number; k?: number}> = ({x, base, k = 0.55}) => {
  const w = 130 * k;
  const rise = 140 * k;
  return (
    <>
      {[0, 1, 2, 3, 4].map((i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            left: x + i * w,
            top: base - rise * (i + 1),
            width: w - 8 * k,
            height: rise * (i + 1),
            background: i === 4 ? C.ink : C.mist,
            borderRadius: `${14 * k}px ${14 * k}px 0 0`,
          }}
        />
      ))}
      <Chip cx={x + 4 * w + (w - 8 * k) / 2} bottom={base - rise * 5} scale={k} />
    </>
  );
};

// ── S01–S02: слово забылось → часть 2 ───────────────────────────────────────
const Hook: React.FC<{t: number}> = ({t}) => {
  const s2 = scene('S02');
  const s3 = scene('S03').start;
  if (t > s3 + 0.6) return null;
  const forget = prog(t, wt('S01', 'неделю'), 0.7) * (1 - prog(t, wt('S01', 'нормально') + 0.2, 0.6));
  const toLadder = prog(t, s2.start + 0.1, 0.8);
  const ladderBase = 860;
  const lx = CX - (130 * 0.9 * 5) / 2;
  // фишка: из центра (крупно) на вершину лесенки
  const k = 0.9;
  const topCx = lx + 4 * 130 * k + (130 * k - 8 * k) / 2;
  const topBottom = ladderBase - 140 * k * 5;
  const cx = interpolate(toLadder, [0, 1], [CX, topCx]);
  const bottom = interpolate(toLadder, [0, 1], [900, topBottom]);
  const scale = interpolate(toLadder, [0, 1], [1.9, k]);
  const ladderIn = prog(t, s2.start + 0.3, 0.6);
  const part2 = sp(t, wt('S02', 'часто') - 0.1, {damping: 18});
  const out = 1 - prog(t, s3, 0.45);
  return (
    <Layer opacity={out}>
      <div style={{opacity: ladderIn}}>
        {[0, 1, 2, 3, 4].map((i) => (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: lx + i * 130 * k,
              top: ladderBase - 140 * k * (i + 1),
              width: 130 * k - 8 * k,
              height: 140 * k * (i + 1),
              background: i === 4 ? C.ink : C.mist,
              borderRadius: '13px 13px 0 0',
            }}
          />
        ))}
        <div style={{position: 'absolute', left: 60, width: 880, top: ladderBase + 24, textAlign: 'center', fontFamily: SANS, fontWeight: 500, fontSize: 40, color: C.sky}}>часть 1: пять ступенек</div>
      </div>
      <Chip cx={cx} bottom={bottom} scale={scale} ghost={forget} />
      {forget > 0.05 && (
        <div style={{position: 'absolute', left: 60, width: 880, top: 980, textAlign: 'center', fontFamily: SANS, fontWeight: 500, fontSize: 48, color: C.sky, opacity: forget}}>через неделю…</div>
      )}
      {part2 > 0.001 && (
        <div style={{position: 'absolute', left: 60, width: 880, top: 1000, textAlign: 'center', opacity: Math.min(1, part2 * 1.3), transform: `translateY(${(1 - part2) * 24}px)`}}>
          <div style={{fontFamily: SERIF, fontSize: 104, lineHeight: 1.05, color: C.ink}}>Часть 2</div>
          <div style={{fontFamily: SANS, fontWeight: 600, fontSize: 46, color: C.ink, marginTop: 14}}>повторение новых слов</div>
        </div>
      )}
    </Layer>
  );
};

// ── S03–S04: кривая забывания и повторения ──────────────────────────────────
const GX0 = 150;
const GX1 = 880;
const GY0 = 560;
const GY1 = 1010;
const gx = (k: number) => GX0 + (GX1 - GX0) * k;
const gy = (v: number) => GY1 - (GY1 - GY0) * v; // v: 0..1 «сколько помню»
const curve = (k0: number, k1: number, rate: number, floor: number) => {
  const pts: string[] = [];
  const N = 40;
  for (let i = 0; i <= N; i++) {
    const k = k0 + ((k1 - k0) * i) / N;
    const v = floor + (1 - floor) * Math.exp(-(k - k0) * rate);
    pts.push(`${i ? 'L' : 'M'} ${gx(k).toFixed(1)} ${gy(v).toFixed(1)}`);
  }
  return pts.join(' ');
};
const REPS = [0.1, 0.27, 0.55]; // моменты повторений (доля оси времени), промежутки растут
const RATES = [14, 6.5, 3, 1.2];
const FLOORS = [0.15, 0.35, 0.55, 0.72];

const Forgetting: React.FC<{t: number}> = ({t}) => {
  const s3 = scene('S03');
  const s4 = scene('S04');
  if (t < s3.start || t > scene('S05').start + 0.6) return null;
  const out = 1 - prog(t, scene('S05').start, 0.45);
  const nameO = vis(t, s3.start + 0.2, s4.start + 0.2, 0.5, 0.4);
  const axes = prog(t, wt('S03', 'повторения') - 0.2, 0.5);
  const first = prog(t, wt('S03', 'сутки') - 0.3, 0.9);
  const label = prog(t, wt('S03', 'кривая'), 0.4);
  const rep = prog(t, wt('S04', 'повторение') - 0.1, 1.8, (x) => x);
  const dimFirst = prog(t, wt('S04', 'повторение') - 0.1, 0.4);
  const gaps = prog(t, wt('S04', 'промежутки'), 0.6);
  const bounds = [0, ...REPS, 1];
  return (
    <Layer opacity={out}>
      <div style={{opacity: nameO}}>
        <div style={{position: 'absolute', left: 60, width: 880, top: 270, textAlign: 'center', fontFamily: SERIF, fontSize: 80, color: C.ink, lineHeight: 1.1}}>Герман Эббингауз</div>
        <div style={{position: 'absolute', left: 60, width: 880, top: 380, textAlign: 'center', fontFamily: SANS, fontWeight: 500, fontSize: 34, color: C.sky}}>психолог, исследователь памяти</div>
      </div>
      <div style={{position: 'absolute', left: 60, width: 880, top: 300, textAlign: 'center', fontFamily: SERIF, fontSize: 80, color: C.ink, opacity: prog(t, s4.start + 0.1, 0.5)}}>с повторениями</div>
      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0, opacity: axes}}>
        <line x1={GX0} y1={GY0 - 20} x2={GX0} y2={GY1} stroke={C.mist} strokeWidth={4} strokeLinecap="round" />
        <line x1={GX0} y1={GY1} x2={GX1 + 20} y2={GY1} stroke={C.mist} strokeWidth={4} strokeLinecap="round" />
        <line x1={gx(0.1)} y1={GY1 - 10} x2={gx(0.1)} y2={GY1 + 10} stroke={C.sky} strokeWidth={4} />
        {/* без повторений */}
        {first > 0 && (
          <path d={curve(0, 1, RATES[0], FLOORS[0])} fill="none" stroke={C.sky} strokeWidth={8} strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - first} opacity={1 - 0.65 * dimFirst} />
        )}
        {/* с повторениями: «пила», каждая кривая спадает медленнее */}
        {rep > 0 &&
          [0, 1, 2, 3].map((i) => {
            const a = bounds[i];
            const b = bounds[i + 1];
            const p = Math.max(0, Math.min(1, (rep - a) / (b - a)));
            if (p <= 0) return null;
            return <path key={i} d={curve(a, b, RATES[i], FLOORS[i])} fill="none" stroke={C.ink} strokeWidth={8} strokeLinecap="round" strokeLinejoin="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - p} />;
          })}
        {rep > 0 &&
          REPS.map((r, i) => {
            if (rep < r) return null;
            const vPrev = FLOORS[i] + (1 - FLOORS[i]) * Math.exp(-(r - bounds[i]) * RATES[i]);
            return (
              <g key={i}>
                <line x1={gx(r)} y1={gy(vPrev)} x2={gx(r)} y2={gy(1)} stroke={C.ink} strokeWidth={6} strokeLinecap="round" />
                <circle cx={gx(r)} cy={gy(1)} r={13} fill={C.marker} />
              </g>
            );
          })}
        {/* скобки-промежутки */}
        {gaps > 0 &&
          [0, 1, 2].map((i) => {
            const a = i === 0 ? 0 : REPS[i - 1];
            const b = REPS[i];
            const g = prog(t, wt('S04', 'промежутки') + i * 0.25, 0.35);
            const y = GY0 - 40;
            return <path key={i} d={`M ${gx(a) + 6} ${y + 14} L ${gx(a) + 6} ${y} L ${gx(b) - 6} ${y} L ${gx(b) - 6} ${y + 14}`} fill="none" stroke={C.marker} strokeWidth={6} strokeLinecap="round" strokeLinejoin="round" opacity={g} />;
          })}
      </svg>
      <div style={{position: 'absolute', left: GX0 + 10, top: GY0 - 74, fontFamily: SANS, fontWeight: 500, fontSize: 30, color: C.sky, opacity: axes * (1 - gaps)}}>помню</div>
      <div style={{position: 'absolute', left: GX1 - 130, top: GY1 + 18, fontFamily: SANS, fontWeight: 500, fontSize: 30, color: C.sky, opacity: axes}}>время →</div>
      <div style={{position: 'absolute', left: gx(0.1) - 60, width: 120, textAlign: 'center', top: GY1 + 18, fontFamily: SANS, fontWeight: 600, fontSize: 30, color: C.sky, opacity: first}}>1 день</div>
      <div style={{position: 'absolute', left: gx(0.3), top: gy(0.15) - 64, fontFamily: SANS, fontWeight: 600, fontSize: 40, color: C.sky, opacity: label * (1 - dimFirst)}}>кривая забывания</div>
      <div style={{position: 'absolute', left: GX0, width: GX1 - GX0, top: GY1 + 80, textAlign: 'center', fontFamily: SANS, fontWeight: 600, fontSize: 40, color: C.ink, opacity: gaps}}>промежутки растут</div>
    </Layer>
  );
};

// ── S05: Наката ─────────────────────────────────────────────────────────────
const Nakata: React.FC<{t: number}> = ({t}) => {
  const s = scene('S05');
  const o = vis(t, s.start + 0.2, s.end, 0.5, 0.35);
  if (o <= 0) return null;
  const five = wt('S05', 'пяти');
  const lineP = prog(t, five - 0.2, 0.5, easeOut);
  const gaps = [0, 1, 2.3, 4.0, 6.3];
  const X0 = 130;
  const X1 = 870;
  const dx = (g: number) => X0 + ((X1 - X0) * g) / gaps[gaps.length - 1];
  const LY = 960;
  return (
    <Layer opacity={o}>
      <div style={{position: 'absolute', left: 60, width: 880, top: 300, textAlign: 'center', fontFamily: SERIF, fontSize: 80, color: C.ink}}>Тацуя Наката</div>
      <div style={{position: 'absolute', left: 60, width: 880, top: 410, textAlign: 'center', fontFamily: SANS, fontWeight: 500, fontSize: 34, color: C.sky}}>лингвист, исследователь лексики</div>
      <div style={{position: 'absolute', left: 100, width: 800, top: 560, textAlign: 'center', fontFamily: SANS, fontWeight: 600, fontSize: 46, lineHeight: 1.25, color: C.ink, opacity: prog(t, wt('S05', 'несколько') - 0.4, 0.4)}}>
        вспомнить самому,
        <br />
        несколько раз, с перерывами
      </div>
      {lineP > 0 && (
        <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
          <line x1={X0 - 30} y1={LY} x2={X0 - 30 + (X1 - X0 + 60) * lineP} y2={LY} stroke={C.sky} strokeWidth={4} strokeLinecap="round" />
          {gaps.map((g, i) => {
            const on = prog(t, five + 0.35 + i * 0.28, 0.25);
            const x = dx(g);
            return (
              <g key={i}>
                <circle cx={x} cy={LY} r={16} fill={on > 0 ? C.ink : C.paper} stroke={C.sky} strokeWidth={4} opacity={lineP} />
                <g transform={`translate(${x - 22} ${LY - 84})`} opacity={on}>
                  <circle cx={22} cy={22} r={22} fill={C.white} stroke={C.ink} strokeWidth={3} />
                  <path d="M 12 23 L 19 30 L 32 15" fill="none" stroke={C.ink} strokeWidth={4} strokeLinecap="round" strokeLinejoin="round" />
                </g>
                <text x={x} y={LY + 60} textAnchor="middle" fontFamily={SANS} fontWeight={600} fontSize={32} fill={C.ink} opacity={on}>
                  {i + 1}
                </text>
              </g>
            );
          })}
        </svg>
      )}
      <div style={{position: 'absolute', left: 60, width: 880, top: LY + 110, textAlign: 'center', fontFamily: SANS, fontWeight: 600, fontSize: 44, color: C.ink, opacity: prog(t, five + 1.8, 0.4)}}>около пяти вспоминаний</div>
    </Layer>
  );
};

// ── S06: рециркуляция ───────────────────────────────────────────────────────
const Recirc: React.FC<{t: number}> = ({t}) => {
  const s = scene('S06');
  const o = vis(t, s.start + 0.1, s.end, 0.35, 0.35);
  if (o <= 0) return null;
  const items: [string, string, React.ReactNode, number][] = [
    ['текст', 'тексте', <>She finally <span style={hl(1)}>made a decision</span> to move.</>, 290],
    ['задание', 'задании', <>___ a decision: <span style={hl(1)}>make</span> / do / take</>, 560],
    ['разговор', 'разговоре', <>I need to <span style={hl(1)}>make a decision</span> by Friday.</>, 830],
  ];
  const big = prog(t, wt('S06', 'рециркуляция') - 0.2, 0.5, easeOut);
  return (
    <Layer opacity={o}>
      {items.map(([label, word, body, top], i) => {
        const a = sp(t, wt('S06', word) - 0.35, {damping: 18});
        if (a <= 0.001) return null;
        return (
          <div key={label} style={{...card, left: 80, width: 820, top, opacity: Math.min(1, a * 1.3), transform: `translateY(${(1 - a) * 26}px)`, borderRadius: i === 2 ? 40 : 28}}>
            <div style={{fontSize: 30, fontWeight: 600, color: C.sky, marginBottom: 10}}>{label}</div>
            <div style={{fontSize: 44, fontWeight: 600, lineHeight: 1.2}}>{body}</div>
          </div>
        );
      })}
      {big > 0 && (
        <>
          <svg width={1080} height={1920} style={{position: 'absolute', inset: 0, opacity: big}}>
            {/* петля: стрелка по кругу */}
            <path d="M 236 1186 A 46 46 0 1 1 236 1260" fill="none" stroke={C.sky} strokeWidth={6} strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - big} />
            <path d="M 236 1260 L 256 1248 M 236 1260 L 252 1276" fill="none" stroke={C.sky} strokeWidth={6} strokeLinecap="round" opacity={big > 0.9 ? 1 : 0} />
          </svg>
          <div style={{position: 'absolute', left: 300, top: 1168, fontFamily: SERIF, fontSize: 86, color: C.ink, opacity: big}}>рециркуляция</div>
        </>
      )}
    </Layer>
  );
};

// ── S07: месяц занятий ──────────────────────────────────────────────────────
const Month: React.FC<{t: number}> = ({t}) => {
  const s = scene('S07');
  const o = vis(t, s.start + 0.1, s.end, 0.4, 0.35);
  if (o <= 0) return null;
  const next = wt('S07', 'следующем');
  const week = wt('S07', 'неделю');
  const fourth = wt('S07', 'четвёртый');
  const cxs = Array.from({length: 8}, (_, i) => 120 + i * 105);
  const RY = 900;
  const arc = (to: number, start: number, hgt: number, label: string) => {
    const p = prog(t, start - 0.1, 0.5);
    if (p <= 0) return null;
    const x1 = cxs[0];
    const x2 = cxs[to];
    return (
      <g>
        <path d={`M ${x1} ${RY - 50} C ${x1 + 20} ${RY - 50 - hgt}, ${x2 - 20} ${RY - 50 - hgt}, ${x2} ${RY - 50}`} fill="none" stroke={C.ink} strokeWidth={4} strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - p} />
        <text x={x2 + 18} y={RY - 50 - hgt * 0.55} fontFamily={SANS} fontWeight={600} fontSize={30} fill={C.ink} opacity={p} stroke={C.paper} strokeWidth={8} paintOrder="stroke">
          {label}
        </text>
      </g>
    );
  };
  return (
    <Layer opacity={o}>
      <div style={{position: 'absolute', left: 60, width: 880, top: 420, textAlign: 'center', fontFamily: SERIF, fontSize: 80, color: C.ink}}>на моих уроках</div>
      <div style={{position: 'absolute', left: 60, width: 880, top: 530, textAlign: 'center', fontFamily: SANS, fontWeight: 500, fontSize: 36, color: C.sky}}>месяц занятий</div>
      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
        {arc(1, next, 70, 'следующий урок')}
        {arc(2, week, 190, 'через неделю')}
      </svg>
      {cxs.map((x, i) => {
        const a = sp(t, s.start + 0.2 + i * 0.06, {damping: 16});
        const rep = i === 3 || i === 7 ? prog(t, fourth + (i === 7 ? 0.25 : 0), 0.35) : 0;
        return (
          <React.Fragment key={i}>
            <div
              style={{
                position: 'absolute',
                left: x - 40,
                top: RY - 40,
                width: 80,
                height: 80,
                borderRadius: 40,
                boxSizing: 'border-box',
                border: `4px solid ${rep > 0 ? C.marker : C.ink}`,
                background: rep > 0 ? `rgba(242,201,76,${rep})` : C.white,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontFamily: SERIF,
                fontSize: 42,
                color: C.ink,
                transform: `scale(${a})`,
              }}
            >
              {i + 1}
            </div>
            {rep > 0 && <div style={{position: 'absolute', left: x - 100, width: 200, top: RY + 56, textAlign: 'center', fontFamily: SANS, fontWeight: 600, fontSize: 30, color: C.ink, opacity: rep}}>повторение</div>}
          </React.Fragment>
        );
      })}
    </Layer>
  );
};

// ── S08: уроки, разговорный клуб, шапка профиля ─────────────────────────────
const Club: React.FC<{t: number}> = ({t}) => {
  const s = scene('S08');
  if (t < s.start) return null;
  const c1 = sp(t, wt('S08', 'группах') - 0.2, {damping: 18});
  const c2 = sp(t, wt('S08', 'клубе') - 0.2, {damping: 18});
  const head = wt('S08', 'шапке');
  const cardsOut = prog(t, head - 0.35, 0.35);
  const shotIn = sp(t, head - 0.15, {damping: 20, stiffness: 120});
  const lab = prog(t, head + 0.5, 0.35);
  const box = (a: number, top: number, l1: string, l2: string) =>
    a > 0.001 &&
    cardsOut < 1 && (
      <div style={{...card, left: 80, width: 820, top, opacity: Math.min(1, a * 1.3) * (1 - cardsOut), transform: `translateY(${(1 - a) * 30 - cardsOut * 40}px)`}}>
        <div style={{fontSize: 50, fontWeight: 600, lineHeight: 1.15, whiteSpace: 'nowrap'}}>{l1}</div>
        <div style={{whiteSpace: 'pre-line', fontSize: 40, fontWeight: 500, color: C.sky, marginTop: 8}}>{l2}</div>
      </div>
    );
  const W = 860;
  const H = W / PROFILE_ASPECT;
  const left = CX - W / 2;
  const top = 580;
  return (
    <>
      <div style={{position: 'absolute', inset: 0, opacity: prog(t, s.start, 0.5)}}>
        <MiniLadder x={CX - (130 * 0.5 * 5) / 2} base={500} k={0.5} />
      </div>
      {box(c1, 610, 'Индивидуально и в группах', 'повторения по графику')}
      {box(c2, 830, 'Разговорный клуб', 'знакомство с подходом,\nкаждые выходные')}
      {shotIn > 0.001 && (
        <div style={{position: 'absolute', inset: 0, opacity: Math.min(1, shotIn * 1.5), transform: `translateY(${(1 - shotIn) * 500}px)`}}>
          <Img src={staticFile('images/profile_header.png')} style={{...shot, left, top, width: W, height: H}} />
          <HandOval cx={left + W * PROFILE_OVAL.cx} cy={top + H * PROFILE_OVAL.cy} rx={W * PROFILE_OVAL.rx} ry={H * PROFILE_OVAL.ry} t={t} start={head + 0.45} seed={13} />
        </div>
      )}
      <div style={{position: 'absolute', left: 60, width: 880, top: top + H + 40, textAlign: 'center', fontFamily: SANS, fontWeight: 600, fontSize: 48, color: C.ink, opacity: lab}}>анкета в шапке профиля</div>
    </>
  );
};

const Sources: React.FC<{t: number}> = ({t}) => (
  <>
    {(
      [
        ['S03', SOURCE_EBBINGHAUS],
        ['S05', SOURCE_NAKATA],
      ] as [string, string][]
    ).map(([id, text]) => {
      const s = scene(id);
      const o = vis(t, s.start + 0.5, s.end, 0.5, 0.3);
      if (o <= 0) return null;
      return (
        <div key={id} style={{position: 'absolute', left: 60, width: 880, top: 1338, textAlign: 'center', fontFamily: SANS, fontWeight: 500, fontSize: 32, color: C.sky, opacity: o}}>
          {text}
        </div>
      );
    })}
  </>
);

export const Reel2: React.FC = () => {
  const t = useCurrentFrame() / tl.fps;
  return (
    <AbsoluteFill>
      <Paper />
      <Hook t={t} />
      <Forgetting t={t} />
      <Nakata t={t} />
      <Recirc t={t} />
      <Month t={t} />
      <Club t={t} />
      <Sources t={t} />
      {showSubtitles && <Subtitles t={t} tl={tl} />}
      {tl.voice && <Audio src={staticFile(tl.voice)} />}
    </AbsoluteFill>
  );
};
