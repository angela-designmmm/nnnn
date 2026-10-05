import React from 'react';
import {Img, interpolate, staticFile} from 'remotion';
import {Check, HandArrow, HandOval, Layer} from './common';
import {C, CX, QUESTION_OVAL, SANS, SERIF, SOURCE_LAUFER, SOURCE_NAKATA} from './theme';
import {easeOut, prog, scene, sp, tl, vis, wt} from './time';

const shot: React.CSSProperties = {
  position: 'absolute',
  borderRadius: 14,
  boxShadow: '0 12px 30px rgba(30,42,68,0.20), 0 2px 6px rgba(30,42,68,0.10)',
  background: C.white,
  overflow: 'hidden',
};

// ── S01 + S02: 1300 → 2000, затем вопрос ролика ─────────────────────────────
export const Hook: React.FC<{t: number}> = ({t}) => {
  const grow = wt('S01', 'вырос');
  const seven = wt('S01', 'семьсот');
  const s2 = scene('S02').start;
  const s3 = scene('S03').start;
  if (t > s3 + 0.6) return null;

  const cnt = prog(t, grow, 0.8, easeOut);
  const value = Math.round((1300 + 700 * cnt) / 10) * 10;
  const nov = prog(t, grow + 0.55, 0.35);
  const card2 = sp(t, grow + 0.1, {damping: 20});
  const plus = prog(t, seven, 0.35, easeOut);

  // S02: всё уезжает вверх и бледнеет
  const up = prog(t, s2, 0.7);
  const shift = -330 * up;
  const fade = interpolate(up, [0, 1], [1, 0.14]) * (1 - prog(t, s3, 0.4));

  return (
    <>
      <Layer opacity={fade} style={{transform: `translateY(${shift}px)`}}>
        <Img src={staticFile('images/card_1300.jpg')} style={{...shot, left: 80, top: 250, width: 320, transform: 'rotate(-3deg)'}} />
        <Img
          src={staticFile('images/card_2000.jpg')}
          style={{...shot, left: 560, top: 1060, width: 350, transform: `rotate(2deg) translateY(${(1 - card2) * 40}px)`, opacity: Math.min(1, card2 * 1.4)}}
        />
        <div style={{position: 'absolute', left: 0, width: 2 * CX, top: 720, textAlign: 'center', fontFamily: SERIF, fontSize: 220, lineHeight: 1, color: C.ink, fontVariantNumeric: 'tabular-nums'}}>{value}</div>
        <div style={{position: 'absolute', left: 0, width: 2 * CX, top: 965, textAlign: 'center', fontFamily: SANS, fontWeight: 500, fontSize: 50, color: C.ink}}>
          <span style={{opacity: 1 - nov, position: 'absolute', left: 0, right: 0}}>слов в октябре</span>
          <span style={{opacity: nov, position: 'absolute', left: 0, right: 0}}>слов в ноябре</span>
        </div>
        <div style={{position: 'absolute', left: 640, top: 600, width: 260, textAlign: 'center', fontFamily: SERIF, fontWeight: 700, fontSize: 104, lineHeight: 1, color: C.ink, opacity: plus, transform: `translateY(${(1 - plus) * 10}px)`}}>+700</div>
        <HandOval cx={770} cy={652} rx={150} ry={82} t={t} start={seven + 0.25} seed={4} />
      </Layer>

      {/* S02 */}
      <Layer opacity={vis(t, s2 + 0.25, s3 + 0.45, 0.5, 0.45)}>
        <div style={{position: 'absolute', left: 60, width: 880, top: 760, textAlign: 'center', fontFamily: SERIF, fontSize: 96, lineHeight: 1.12, color: C.ink}}>
          Как сделать,
          <br />
          чтобы слова
          <br />
          зазвучали в речи?
        </div>
        <Wave t={t} start={wt('S02', 'зазвучали')} />
      </Layer>
    </>
  );
};

const Wave: React.FC<{t: number; start: number}> = ({t, start}) => {
  const N = 27;
  const on = prog(t, start - 0.1, 0.4);
  return (
    <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
      {Array.from({length: N}, (_, i) => {
        const x = CX - ((N - 1) * 22) / 2 + i * 22;
        const env = Math.exp(-Math.pow((i - (N - 1) / 2) / (N / 4.2), 2));
        const pulse = Math.abs(Math.sin(t * 7.5 + i * 0.75)) * 0.65 + Math.abs(Math.sin(t * 4.3 - i * 0.4)) * 0.35;
        const h = 14 + on * env * 110 * pulse;
        return <line key={i} x1={x} x2={x} y1={1180 - h / 2} y2={1180 + h / 2} stroke={C.sky} strokeWidth={8} strokeLinecap="round" />;
      })}
    </svg>
  );
};

// ── S03: скриншот вопроса подписчицы ────────────────────────────────────────
export const Question: React.FC<{t: number}> = ({t}) => {
  const s = scene('S03');
  const s4 = scene('S04').start;
  if (t < s.start || t > s4 + 0.8) return null;
  const inP = sp(t, s.start + 0.1, {damping: 20, stiffness: 120});
  const outP = prog(t, s4, 0.55);
  const y = interpolate(inP, [0, 1], [1100, 0]) + outP * 260;
  const W = 860;
  const H = 640;
  const top = 470;
  const left = CX - W / 2;
  return (
    <Layer opacity={1 - outP} style={{transform: `translateY(${y}px)`}}>
      {tl.hasQuestion ? (
        <Img src={staticFile('images/subscriber_question.png')} style={{...shot, left, top, width: W, height: H, objectFit: 'contain', borderRadius: 28, background: C.white}} />
      ) : (
        <div
          style={{
            ...shot,
            left,
            top,
            width: W,
            height: H,
            borderRadius: 28,
            border: `4px dashed ${C.sky}`,
            boxSizing: 'border-box',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontFamily: SANS,
            fontWeight: 600,
            fontSize: 52,
            color: C.sky,
            textAlign: 'center',
          }}
        >
          сюда скриншот
          <br />
          вопроса
        </div>
      )}
      <HandOval cx={left + W * QUESTION_OVAL.cx} cy={top + H * QUESTION_OVAL.cy} rx={W * QUESTION_OVAL.rx} ry={H * QUESTION_OVAL.ry} t={t} start={s.start + 0.9} seed={8} />
    </Layer>
  );
};

// ── S05–S09: панели-примеры над лесенкой ────────────────────────────────────
const panelBox: React.CSSProperties = {
  position: 'absolute',
  left: 80,
  width: 840,
  top: 236,
  padding: '30px 40px',
  boxSizing: 'border-box',
  background: C.white,
  borderRadius: 28,
  boxShadow: '0 8px 24px rgba(30,42,68,0.10)',
  fontFamily: SANS,
  color: C.ink,
};

const Panel: React.FC<{t: number; id: string; children: React.ReactNode; style?: React.CSSProperties; last?: boolean}> = ({t, id, children, style, last}) => {
  const s = scene(id);
  const a = prog(t, s.start + 0.05, 0.35, easeOut);
  const b = last ? 1 - prog(t, s.end, 0.35) : 1 - prog(t, s.end - 0.1, 0.25);
  const o = Math.min(a, b);
  if (o <= 0) return null;
  return <div style={{...panelBox, ...style, opacity: o, transform: `translateY(${(1 - a) * 14}px)`}}>{children}</div>;
};

const Radio: React.FC<{on: number; ok?: boolean; text: string}> = ({on, ok, text}) => (
  <div style={{display: 'flex', alignItems: 'center', gap: 22, fontSize: 44, fontWeight: 500, height: 62}}>
    <div style={{width: 34, height: 34, borderRadius: 17, border: `4px solid ${on > 0 ? C.ink : C.sky}`, boxSizing: 'border-box', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
      <div style={{width: 16 * on, height: 16 * on, borderRadius: 8, background: C.ink}} />
    </div>
    <span style={{fontWeight: on > 0 ? 600 : 500}}>{text}</span>
    {ok && on > 0 && <Check size={44} color={C.ok} stroke={6} p={on} />}
  </div>
);

export const Examples: React.FC<{t: number}> = ({t}) => {
  const s5 = scene('S05').start;
  const pick = prog(t, wt('S05', 'выбираю'), 0.35);
  const s6 = scene('S06').start;
  const mean = prog(t, s6 + 0.6, 0.45, easeOut);
  const s7 = scene('S07').start;
  const choose = prog(t, wt('S07', 'выбираю'), 0.35);
  const fill = wt('S08', 'достаю');
  const s9 = scene('S09').start;
  if (t < s5 - 0.1 || t > scene('S10').start + 0.5) return null;

  const blank = (letter: string, rest: string, delay: number) => (
    <span>
      {letter}
      {rest.split('').map((ch, i) => {
        const p = prog(t, fill + delay + i * 0.045, 0.12);
        return (
          <span key={i} style={{display: 'inline-block', position: 'relative', minWidth: '0.5em', textAlign: 'center'}}>
            <span style={{opacity: 1 - p, color: C.sky, position: p > 0.5 ? 'absolute' : 'static', left: 0, right: 0}}>_</span>
            <span style={{opacity: p, position: p > 0.5 ? 'static' : 'absolute', left: 0, right: 0, background: `linear-gradient(transparent 64%, ${C.marker} 64%)`}}>{ch}</span>
          </span>
        );
      })}
    </span>
  );

  return (
    <>
      <Panel t={t} id="S05">
        <div style={{fontSize: 52, fontWeight: 600, marginBottom: 14}}>make a decision</div>
        <Radio on={0} text="сделать ошибку" />
        <Radio on={pick} ok text="принять решение" />
        <Radio on={0} text="поменять план" />
      </Panel>

      <Panel t={t} id="S06" style={{paddingTop: 44, paddingBottom: 44}}>
        <div style={{fontSize: 56, fontWeight: 600}}>
          make a decision <span style={{color: C.sky}}>= ?</span>
        </div>
        <div style={{fontSize: 52, fontWeight: 500, marginTop: 22, opacity: mean, transform: `translateY(${(1 - mean) * 10}px)`}}>принять решение</div>
      </Panel>

      <Panel t={t} id="S07" style={{paddingTop: 40, paddingBottom: 44}}>
        <div style={{fontSize: 48, fontWeight: 500}}>«принять решение» →</div>
        <div style={{display: 'flex', alignItems: 'center', gap: 16, marginTop: 30, fontSize: 46, fontWeight: 600}}>
          {['do', 'make', 'get'].map((w) => {
            const ok = w === 'make';
            const c = ok ? choose : 0;
            return (
              <div
                key={w}
                style={{
                  padding: '8px 26px',
                  borderRadius: 16,
                  border: `3px solid ${c > 0 ? C.ok : C.mist}`,
                  background: c > 0 ? `rgba(61,190,107,${0.16 * c})` : C.paper,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                {w}
                {ok && c > 0 && <Check size={38} color={C.ok} stroke={6} p={c} />}
              </div>
            );
          })}
          <span style={{fontWeight: 500, marginLeft: 6}}>a decision</span>
        </div>
      </Panel>

      <Panel t={t} id="S08" style={{paddingTop: 44, paddingBottom: 40}}>
        <div style={{fontSize: 52, fontWeight: 600, whiteSpace: 'nowrap'}}>
          I had to {blank('m', 'ake', 0)} a {blank('d', 'ecision', 0.15)} fast.
        </div>
        <div style={{fontSize: 34, fontWeight: 500, color: C.sky, marginTop: 20}}>пришлось быстро принять решение</div>
      </Panel>

      <Panel t={t} id="S09" last style={{top: 250, width: 640, padding: '32px 40px', borderRadius: 34, opacity: 1}}>
        <div style={{fontSize: 46, fontWeight: 600, lineHeight: 1.25}}>So I made a decision and changed my job.</div>
        {/* хвостик облачка к фишке */}
        <svg width={80} height={60} style={{position: 'absolute', right: 40, bottom: -44}}>
          <path d="M 0 0 L 80 0 L 66 52 Z" fill={C.white} />
        </svg>
      </Panel>
      {t >= s9 && null}
    </>
  );
};

// ── S10: Лауфер ─────────────────────────────────────────────────────────────
export const Laufer: React.FC<{t: number}> = ({t}) => {
  const s = scene('S10');
  const o = vis(t, s.start + 0.2, s.end, 0.5, 0.35);
  if (o <= 0) return null;
  return (
    <Layer opacity={o}>
      <div style={{position: 'absolute', left: 60, width: 880, top: 270, textAlign: 'center', fontFamily: SERIF, fontSize: 80, color: C.ink, lineHeight: 1.1}}>Батья Лауфер</div>
      <div style={{position: 'absolute', left: 60, width: 880, top: 380, textAlign: 'center', fontFamily: SANS, fontWeight: 500, fontSize: 32, color: C.sky}}>исследователь лексики, Хайфский университет</div>
    </Layer>
  );
};

// ── S11: учебники и приложения ──────────────────────────────────────────────
export const Apps: React.FC<{t: number}> = ({t}) => {
  const s = scene('S11');
  const a = wt('S11', 'учебники');
  const o = vis(t, a, s.end, 0.4, 0.3);
  if (o <= 0) return null;
  const st = {fill: 'none', stroke: C.ink, strokeWidth: 5, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const};
  return (
    <Layer opacity={o}>
      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
        {/* раскрытая книга */}
        <g transform="translate(150 330)">
          <path d="M 0 20 Q 60 0 110 20 L 110 130 Q 60 110 0 130 Z" {...st} />
          <path d="M 110 20 Q 160 0 220 20 L 220 130 Q 160 110 110 130 Z" {...st} />
          <path d="M 25 48 L 85 40 M 25 72 L 85 64 M 135 40 L 195 48 M 135 64 L 195 72" {...st} strokeWidth={4} stroke={C.sky} />
        </g>
        {/* телефон с карточкой */}
        <g transform="translate(430 290)">
          <rect x={0} y={0} width={120} height={210} rx={22} {...st} />
          <rect x={18} y={48} width={84} height={70} rx={10} {...st} strokeWidth={4} stroke={C.sky} />
          <path d="M 24 140 L 96 140 M 24 162 L 80 162" {...st} strokeWidth={4} stroke={C.sky} />
          <path d="M 48 20 L 72 20" {...st} strokeWidth={4} />
        </g>
      </svg>
      <div style={{position: 'absolute', left: 600, top: 360, width: 320, fontFamily: SANS, fontWeight: 500, fontSize: 38, color: C.ink, lineHeight: 1.2}}>тренируют
        <br />узнавание</div>
    </Layer>
  );
};

// ── S13: Наката и повторения ────────────────────────────────────────────────
export const Nakata: React.FC<{t: number}> = ({t}) => {
  const s = scene('S13');
  const o = vis(t, s.start + 0.4, s.end, 0.5, 0.35);
  if (o <= 0) return null;
  const five = wt('S13', 'пяти');
  const therefore = wt('S13', 'поэтому');
  const next = wt('S13', 'следующем');
  const week = wt('S13', 'неделю');
  const fourth = wt('S13', 'четвёртый');

  const nameUp = prog(t, five - 0.2, 0.6); // когда лесенка исчезает, имя поднимается
  const lineP = prog(t, five, 0.5, easeOut);
  const lineOut = 1 - prog(t, therefore, 0.4);
  const gaps = [0, 1, 2.3, 4.0, 6.3];
  const X0 = 110;
  const X1 = 880;
  const dx = (g: number) => X0 + ((X1 - X0) * g) / gaps[gaps.length - 1];
  const LY = 900;

  const rowIn = (i: number) => sp(t, therefore + 0.15 + i * 0.06, {damping: 16});
  const cxs = Array.from({length: 8}, (_, i) => 120 + i * 105);
  const RY = 1010;
  const arc = (to: number, start: number, hgt: number) => {
    const p = prog(t, start, 0.5);
    if (p <= 0) return null;
    const x1 = cxs[0];
    const x2 = cxs[to];
    return (
      <path
        d={`M ${x1} ${RY - 50} C ${x1 + 20} ${RY - 50 - hgt}, ${x2 - 20} ${RY - 50 - hgt}, ${x2} ${RY - 50}`}
        fill="none"
        stroke={C.ink}
        strokeWidth={4}
        strokeLinecap="round"
        pathLength={1}
        strokeDasharray={1}
        strokeDashoffset={1 - p}
      />
    );
  };

  return (
    <Layer opacity={o}>
      <div style={{position: 'absolute', left: 60, width: 880, top: interpolate(nameUp, [0, 1], [560, 300]), textAlign: 'center', fontFamily: SERIF, fontSize: 80, color: C.ink}}>Тацуя Наката</div>
      <div style={{position: 'absolute', left: 60, width: 880, top: interpolate(nameUp, [0, 1], [665, 405]), textAlign: 'center', fontFamily: SANS, fontWeight: 500, fontSize: 36, color: C.sky, opacity: prog(t, wt('S13', 'вспоминаете'), 0.4)}}>
        вспомнить самому, несколько раз, с перерывами
      </div>

      {/* линия времени с 5 вспоминаниями */}
      {lineP > 0 && lineOut > 0 && (
        <svg width={1080} height={1920} style={{position: 'absolute', inset: 0, opacity: lineOut}}>
          <line x1={X0 - 30} y1={LY} x2={X0 - 30 + (X1 - X0 + 60) * lineP} y2={LY} stroke={C.sky} strokeWidth={4} strokeLinecap="round" />
          {gaps.map((g, i) => {
            const on = prog(t, five + 0.35 + i * 0.28, 0.25);
            const x = dx(g);
            return (
              <g key={i}>
                <circle cx={x} cy={LY} r={16} fill={on > 0 ? C.ink : C.paper} stroke={C.sky} strokeWidth={4} opacity={lineP} />
                <g transform={`translate(${x - 22} ${LY - 82})`} opacity={on}>
                  <circle cx={22} cy={22} r={22} fill={C.white} stroke={C.ink} strokeWidth={3} />
                  <path d="M 12 23 L 19 30 L 32 15" fill="none" stroke={C.ink} strokeWidth={4} strokeLinecap="round" strokeLinejoin="round" />
                </g>
              </g>
            );
          })}
          <text x={X0 - 30} y={LY + 56} fontFamily={SANS} fontWeight={500} fontSize={30} fill={C.sky} opacity={lineP}>
            время →
          </text>
        </svg>
      )}

      {/* месяц занятий: 8 уроков */}
      {t > therefore && (
        <>
          <div style={{position: 'absolute', left: 60, width: 880, top: 820, textAlign: 'center', fontFamily: SANS, fontWeight: 500, fontSize: 34, color: C.sky, opacity: prog(t, therefore + 0.2, 0.4)}}>месяц занятий</div>
          <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
            {arc(1, next, 70)}
            {arc(2, week, 120)}
          </svg>
          {cxs.map((x, i) => {
            const a = rowIn(i);
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
                {rep > 0 && (
                  <div style={{position: 'absolute', left: x - 100, width: 200, top: RY + 56, textAlign: 'center', fontFamily: SANS, fontWeight: 600, fontSize: 30, color: C.ink, opacity: rep}}>
                    повторение
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </>
      )}
    </Layer>
  );
};

// ── S14: призыв ─────────────────────────────────────────────────────────────
export const Cta: React.FC<{t: number}> = ({t}) => {
  const s = scene('S14');
  if (t < s.start) return null;
  const c1 = sp(t, wt('S14', 'пишите') - 0.1, {damping: 18});
  const c2 = sp(t, wt('S14', 'клубе') - 0.35, {damping: 18});
  const head = wt('S14', 'шапке');
  const card = (a: number, top: number, l1: string, l2: string) =>
    a > 0.001 && (
      <div
        style={{
          ...panelBox,
          left: 100,
          width: 760,
          top,
          padding: '30px 40px',
          opacity: Math.min(1, a * 1.3),
          transform: `translateY(${(1 - a) * 30}px)`,
        }}
      >
        <div style={{fontSize: 46, fontWeight: 600, lineHeight: 1.15, whiteSpace: 'nowrap'}}>{l1}</div>
        <div style={{fontSize: 42, fontWeight: 500, color: C.sky, marginTop: 8}}>{l2}</div>
      </div>
    );
  const lab = prog(t, head + 0.1, 0.35);
  return (
    <>
      {card(c1, 600, 'Индивидуально и в группах', 'пишите в личку')}
      {card(c2, 830, 'Разговорный клуб', 'каждые выходные')}
      <div style={{position: 'absolute', left: 100, width: 660, top: 1150, textAlign: 'center', fontFamily: SANS, fontWeight: 600, fontSize: 44, color: C.ink, opacity: lab}}>анкета в шапке профиля</div>
      <HandArrow
        pts={[
          [770, 1180],
          [860, 1130],
          [895, 960],
          [892, 700],
          [880, 470],
          [870, 260],
        ]}
        t={t}
        start={head}
        dur={0.6}
      />
    </>
  );
};

// ── Подписи-источники ───────────────────────────────────────────────────────
export const Sources: React.FC<{t: number}> = ({t}) => {
  const items: [string, string][] = [
    ['S10', SOURCE_LAUFER],
    ['S13', SOURCE_NAKATA],
  ];
  return (
    <>
      {items.map(([id, text]) => {
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
};
