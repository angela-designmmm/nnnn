import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import {HandOval, Paper} from './common';
import {C, CX, SANS, SERIF} from './theme';

// Обложка первого видео. Всё важное внутри центральной зоны 3:4 (y 240–1680),
// которую Instagram показывает в сетке профиля.
export const COVER1_TITLE = ['Как выводить слова', 'в активную речь'];

export const Cover1: React.FC = () => {
  const k = 1.0;
  const w = 130 * k;
  const rise = 118 * k;
  const base = 1520;
  const x0 = CX - (5 * w) / 2;
  const topCx = x0 + 4 * w + (w - 8) / 2;
  const topY = base - rise * 5;
  return (
    <AbsoluteFill>
      <Paper />
      {/* жёлтая рамка по зоне 3:4 (то, что видно в сетке профиля) */}
      <div style={{position: 'absolute', left: 44, top: 252, width: 1080 - 88, height: 1440 - 24, boxSizing: 'border-box', border: `16px solid ${C.marker}`, borderRadius: 40}} />
      <div style={{position: 'absolute', left: 60, width: 880, top: 330, textAlign: 'center', fontFamily: SANS, fontWeight: 600, fontSize: 40, color: C.sky}}>часть 1 · пять ступенек</div>
      <div style={{position: 'absolute', left: 50, width: 900, top: 400, textAlign: 'center', fontFamily: SERIF, fontSize: 86, lineHeight: 1.14, color: C.ink}}>
        {COVER1_TITLE.map((l) => (
          <div key={l} style={{whiteSpace: 'nowrap'}}>
            {l}
          </div>
        ))}
      </div>
      {[0, 1, 2, 3, 4].map((i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            left: x0 + i * w,
            top: base - rise * (i + 1),
            width: w - 8,
            height: rise * (i + 1),
            background: i === 4 ? C.ink : C.mist,
            borderRadius: '14px 14px 0 0',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'flex-end',
            paddingBottom: 18,
            boxSizing: 'border-box',
            fontFamily: SERIF,
            fontSize: 44,
            color: i === 4 ? C.paper : C.ink,
          }}
        >
          {i + 1}
        </div>
      ))}
      <div
        style={{
          position: 'absolute',
          left: topCx - 88,
          top: topY - 104,
          width: 176,
          height: 104,
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
        }}
      >
        make a<br />decision
      </div>
      <HandOval cx={topCx} cy={topY - 52} rx={128} ry={86} t={10} start={0} seed={11} />
      <div style={{position: 'absolute', left: x0 - 10, top: base - rise - 70, fontFamily: SANS, fontWeight: 600, fontSize: 34, color: C.sky}}>узнаю</div>
      <div style={{position: 'absolute', left: topCx - 140 - 380, width: 380, top: topY - 78, fontFamily: SANS, fontWeight: 600, fontSize: 34, color: C.ink, textAlign: 'right'}}>говорю свободно →</div>
    </AbsoluteFill>
  );
};

// Обложка ролика про подготовку урока к интервью
export const COVER_LESSON_TITLE = ['Давайте создадим урок', 'для моей ученицы'];

export const CoverLesson: React.FC = () => {
  const W = 840;
  const H = 360;
  const crop = {x: 282, w: 1660}; // общий вид доски (board_whole.png 2046×1096)
  const k = W / crop.w;
  const ch = H / k;
  const cy = 548;
  return (
    <AbsoluteFill>
      <Paper />
      <div style={{position: 'absolute', left: 44, top: 252, width: 1080 - 88, height: 1440 - 24, boxSizing: 'border-box', border: `16px solid ${C.marker}`, borderRadius: 40}} />
      <div style={{position: 'absolute', left: 60, width: 960, top: 400, textAlign: 'center', fontFamily: SERIF, fontSize: 76, lineHeight: 1.14, color: C.ink}}>
        {COVER_LESSON_TITLE.map((l) => (
          <div key={l} style={{whiteSpace: 'nowrap'}}>
            {l}
          </div>
        ))}
      </div>
      <div style={{position: 'absolute', left: 60, width: 960, top: 590, display: 'flex', justifyContent: 'center'}}>
        <div style={{background: C.marker, borderRadius: 999, padding: '12px 36px', fontFamily: SANS, fontWeight: 600, fontSize: 50, color: C.ink}}>подготовка к интервью</div>
      </div>
      <div style={{position: 'absolute', left: 120, top: 760, width: W, height: H, borderRadius: 28, overflow: 'hidden', background: C.white, boxShadow: '0 14px 34px rgba(30,42,68,0.16), 0 2px 6px rgba(30,42,68,0.08)'}}>
        <Img src={staticFile('images/board_whole.png')} style={{position: 'absolute', left: -crop.x * k, top: -(cy - ch / 2) * k, width: 2046 * k, height: 1096 * k, maxWidth: 'none'}} />
      </div>
      <div style={{position: 'absolute', left: 60, width: 960, top: 1170, display: 'flex', justifyContent: 'center', gap: 16}}>
        {['Senior Product Manager', 'IT-компания'].map((s) => (
          <div key={s} style={{background: C.white, borderRadius: 999, padding: '12px 28px', boxShadow: '0 6px 16px rgba(30,42,68,0.10)', fontFamily: SANS, fontWeight: 600, fontSize: 38, color: C.ink}}>
            {s}
          </div>
        ))}
      </div>
      <div style={{position: 'absolute', left: 60, width: 960, top: 1280, textAlign: 'center', fontFamily: SANS, fontWeight: 600, fontSize: 40, color: C.sky}}>«Tell me about yourself» за один урок</div>
    </AbsoluteFill>
  );
};
