import React from 'react';
import {AbsoluteFill} from 'remotion';
import {C} from './theme';
import {prog} from './time';

// Детерминированный псевдослучайный генератор
export const rnd = (seed: number) => {
  let s = seed * 9301 + 49297;
  return () => {
    s = (s * 9301 + 49297) % 233280;
    return s / 233280;
  };
};

// Гладкая кривая через точки (Catmull-Rom → кубические Безье)
const smooth = (pts: [number, number][]) => {
  let d = `M ${pts[0][0].toFixed(1)} ${pts[0][1].toFixed(1)}`;
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[Math.max(0, i - 1)];
    const p1 = pts[i];
    const p2 = pts[i + 1];
    const p3 = pts[Math.min(pts.length - 1, i + 2)];
    const c1 = [p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6];
    const c2 = [p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6];
    d += ` C ${c1[0].toFixed(1)} ${c1[1].toFixed(1)}, ${c2[0].toFixed(1)} ${c2[1].toFixed(1)}, ${p2[0].toFixed(1)} ${p2[1].toFixed(1)}`;
  }
  return d;
};

// Неровный овал «от руки»: чуть больше одного оборота, конец заходит на начало
export const ovalPath = (cx: number, cy: number, rx: number, ry: number, seed = 1) => {
  const r = rnd(seed);
  const pts: [number, number][] = [];
  const turns = 1.12;
  const N = 28;
  const a0 = -Math.PI * 0.62;
  for (let i = 0; i <= N; i++) {
    const k = i / N;
    const a = a0 + k * turns * Math.PI * 2;
    const wob = 1 + (r() - 0.5) * 0.07 + (k > 0.85 ? 0.06 * (k - 0.85) / 0.15 : 0);
    pts.push([cx + Math.cos(a) * rx * wob, cy + Math.sin(a) * ry * wob * (1 + (r() - 0.5) * 0.04)]);
  }
  return smooth(pts);
};

export const HandOval: React.FC<{cx: number; cy: number; rx: number; ry: number; t: number; start: number; seed?: number; opacity?: number}> = ({cx, cy, rx, ry, t, start, seed = 3, opacity = 1}) => {
  const p = prog(t, start, 0.4);
  if (p <= 0) return null;
  return (
    <svg width={1080} height={1920} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible', opacity}}>
      <path
        d={ovalPath(cx, cy, rx, ry, seed)}
        fill="none"
        stroke={C.marker}
        strokeWidth={8}
        strokeLinecap="round"
        pathLength={1}
        strokeDasharray={1}
        strokeDashoffset={1 - p}
      />
    </svg>
  );
};

// Стрелка «от руки» по точкам, рисуется за dur
export const HandArrow: React.FC<{pts: [number, number][]; t: number; start: number; dur?: number}> = ({pts, t, start, dur = 0.6}) => {
  const p = prog(t, start, dur);
  const ph = prog(t, start + dur * 0.85, 0.2);
  if (p <= 0) return null;
  const [x1, y1] = pts[pts.length - 2];
  const [x2, y2] = pts[pts.length - 1];
  const ang = Math.atan2(y2 - y1, x2 - x1);
  const L = 46;
  const head = (da: number) => `M ${x2} ${y2} L ${x2 - L * Math.cos(ang + da)} ${y2 - L * Math.sin(ang + da)}`;
  return (
    <svg width={1080} height={1920} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible'}}>
      <path d={smooth(pts)} fill="none" stroke={C.marker} strokeWidth={8} strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - p} />
      <g opacity={ph}>
        <path d={head(0.5)} stroke={C.marker} strokeWidth={8} strokeLinecap="round" fill="none" />
        <path d={head(-0.45)} stroke={C.marker} strokeWidth={8} strokeLinecap="round" fill="none" />
      </g>
    </svg>
  );
};

export const Check: React.FC<{size: number; color: string; stroke?: number; p?: number}> = ({size, color, stroke = 6, p = 1}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" style={{display: 'inline-block', verticalAlign: 'middle'}}>
    <path d="M4 12.5 L9.5 18 L20 6.5" fill="none" stroke={color} strokeWidth={(stroke * 24) / size} strokeLinecap="round" strokeLinejoin="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - p} />
  </svg>
);

// Бумажный фон: плоский paper + очень слабый шум (~2.5 %)
export const Paper: React.FC = () => (
  <AbsoluteFill style={{backgroundColor: C.paper}}>
    <svg width={1080} height={1920} style={{position: 'absolute', inset: 0, opacity: 0.025}}>
      <filter id="grain">
        <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves={2} seed={7} stitchTiles="stitch" />
        <feColorMatrix type="saturate" values="0" />
      </filter>
      <rect width="100%" height="100%" filter="url(#grain)" />
    </svg>
  </AbsoluteFill>
);

export const Layer: React.FC<{opacity?: number; style?: React.CSSProperties; children: React.ReactNode}> = ({opacity = 1, style, children}) =>
  opacity <= 0.001 ? null : <AbsoluteFill style={{opacity, ...style}}>{children}</AbsoluteFill>;
