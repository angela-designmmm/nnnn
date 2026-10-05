import React from 'react';
import {AbsoluteFill, Audio, getInputProps, Img, interpolate, OffthreadVideo, Sequence, staticFile, useCurrentFrame} from 'remotion';
import {HandOval, Layer, Paper} from './common';
import timelineL from './generated/timelinelesson.json';
import {Subtitles} from './Subtitles';
import {C, SANS, SERIF} from './theme';
import {easeOut, makeTime, prog, sp, Timeline, vis} from './time';

// Ролик «Как я готовлю урок к интервью»: записи экрана Miro + крупные планы доски.
const {tl, scene, wt} = makeTime(timelineL as Timeline);
export const tlLesson = tl;
const showSubtitles = getInputProps().subtitles !== false;

const SRC_W = 2046;
const SRC_H = 1096;
type Crop = {cx: number; cy: number; w: number};

// «Окно» с фрагментом записи экрана или картинки: плавный наезд/панорама от crop `from` к `to`
const Shot: React.FC<{
  t: number;
  t0: number;
  dur: number;
  src: string;
  video?: boolean;
  rate?: number;
  startAt?: number; // секунда исходника, с которой начать
  srcW?: number;
  srcH?: number;
  from: Crop;
  to?: Crop;
  box: {x: number; y: number; w: number; h: number};
  opacity?: number;
  children?: React.ReactNode;
}> = ({t, t0, dur, src, video, rate = 1, startAt = 0, srcW = SRC_W, srcH = SRC_H, from, to = from, box, opacity = 1, children}) => {
  const p = prog(t, t0, dur, (x) => x);
  const e = p * p * (3 - 2 * p);
  const cx = interpolate(e, [0, 1], [from.cx, to.cx]);
  const cy = interpolate(e, [0, 1], [from.cy, to.cy]);
  const cw = interpolate(e, [0, 1], [from.w, to.w]);
  const ch = (cw * box.h) / box.w;
  const k = box.w / cw;
  const media: React.CSSProperties = {position: 'absolute', left: -(cx - cw / 2) * k, top: -(cy - ch / 2) * k, width: srcW * k, height: srcH * k, maxWidth: 'none'};
  return (
    <div
      style={{
        position: 'absolute',
        left: box.x,
        top: box.y,
        width: box.w,
        height: box.h,
        borderRadius: 28,
        overflow: 'hidden',
        background: C.white,
        boxShadow: '0 14px 34px rgba(30,42,68,0.16), 0 2px 6px rgba(30,42,68,0.08)',
        opacity,
      }}
    >
      {video ? (
        <Sequence from={Math.round(t0 * tl.fps)} durationInFrames={Math.max(1, Math.round(dur * tl.fps))} layout="none">
          <OffthreadVideo src={staticFile(src)} muted playbackRate={rate} startFrom={Math.round(startAt * tl.fps)} style={media} />
        </Sequence>
      ) : (
        <Img src={staticFile(src)} style={media} />
      )}
      {children}
    </div>
  );
};

const Heading: React.FC<{t: number; id: string; step?: string; title: string}> = ({t, id, step, title}) => {
  const s = scene(id);
  const a = prog(t, s.start, 0.4, easeOut);
  return (
    <div style={{position: 'absolute', left: 60, width: 880, top: 236, opacity: a, transform: `translateY(${(1 - a) * 10}px)`}}>
      {step && <div style={{fontFamily: SANS, fontWeight: 600, fontSize: 36, color: C.sky}}>{step}</div>}
      <div style={{fontFamily: SERIF, fontSize: 78, lineHeight: 1.08, color: C.ink, marginTop: 4}}>{title}</div>
    </div>
  );
};

const Chip: React.FC<{a: number; children: React.ReactNode; marker?: boolean; style?: React.CSSProperties}> = ({a, children, marker, style}) =>
  a <= 0.001 ? null : (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 12,
        padding: '12px 24px',
        borderRadius: 999,
        background: marker ? C.marker : C.white,
        boxShadow: '0 6px 16px rgba(30,42,68,0.10)',
        fontFamily: SANS,
        fontWeight: 600,
        fontSize: 38,
        color: C.ink,
        opacity: Math.min(1, a * 1.4),
        transform: `translateY(${(1 - a) * 16}px)`,
        ...style,
      }}
    >
      {children}
    </div>
  );

const Line: React.FC<{a: number; top: number; children: React.ReactNode; size?: number}> = ({a, top, children, size = 44}) => (
  <div style={{position: 'absolute', left: 60, width: 880, top, fontFamily: SANS, fontWeight: 600, fontSize: size, lineHeight: 1.25, color: C.ink, opacity: a, transform: `translateY(${(1 - a) * 12}px)`}}>{children}</div>
);

// Сцена видна от своего начала до начала следующей (с коротким перекрёстным фейдом)
const useScene = (t: number, id: string) => {
  const s = scene(id);
  return {s, o: vis(t, s.start, s.end + 0.15, 0.3, 0.3), on: t >= s.start - 0.1 && t <= s.end + 0.2};
};

// ── S01 ──
const S01: React.FC<{t: number}> = ({t}) => {
  const {s, o, on} = useScene(t, 'S01');
  if (!on) return null;
  const c1 = sp(t, s.start + 0.6, {damping: 18});
  const c2 = sp(t, wt('S01', 'senior') - 0.2, {damping: 18});
  return (
    <Layer opacity={o}>
      <div style={{position: 'absolute', left: 60, width: 880, top: 236, fontFamily: SERIF, fontSize: 84, lineHeight: 1.08, color: C.ink}}>
        Готовлю урок
        <br />к интервью
      </div>
      <Shot t={t} t0={s.start} dur={s.end - s.start} src="images/board_whole.png" from={{cx: 1080, cy: 560, w: 1700}} to={{cx: 1020, cy: 540, w: 1250}} box={{x: 60, y: 470, w: 880, h: 560}} />
      <div style={{position: 'absolute', left: 60, top: 1070, display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 16}}>
        <Chip a={c1}>полгода: от хаоса к структуре</Chip>
        <Chip a={c2} marker>
          Senior Product Manager, IT
        </Chip>
      </div>
    </Layer>
  );
};

// ── S02 ресурс ──
const S02: React.FC<{t: number}> = ({t}) => {
  const {s, o, on} = useScene(t, 'S02');
  if (!on) return null;
  const art = sp(t, wt('S02', 'статью') - 0.2, {damping: 18});
  const hw = sp(t, wt('S02', 'домашнее') - 0.2, {damping: 18});
  return (
    <Layer opacity={o}>
      <Heading t={t} id="S02" step="шаг 1 · до урока" title="Ищу ресурс" />
      <Shot t={t} t0={s.start} dur={s.end - s.start} src="images/techinterview_home.webp" srcW={2000} srcH={899} from={{cx: 1000, cy: 450, w: 1900}} to={{cx: 1000, cy: 420, w: 1500}} box={{x: 60, y: 470, w: 880, h: 400}} />
      {art > 0.001 && (
        <div
          style={{
            position: 'absolute',
            left: 100,
            width: 800,
            top: 910,
            padding: '28px 36px',
            boxSizing: 'border-box',
            background: C.white,
            borderRadius: 24,
            boxShadow: '0 8px 24px rgba(30,42,68,0.12)',
            fontFamily: SANS,
            color: C.ink,
            opacity: Math.min(1, art * 1.3),
            transform: `translateY(${(1 - art) * 20}px)`,
          }}
        >
          <div style={{fontSize: 28, fontWeight: 600, color: C.sky}}>techinterview.org</div>
          <div style={{fontSize: 44, fontWeight: 600, marginTop: 6}}>«Tell me about yourself»: interview opener</div>
        </div>
      )}
      <div style={{position: 'absolute', left: 100, top: 1150}}>
        <Chip a={hw} marker>
          домашка: прочитать статью
        </Chip>
      </div>
    </Layer>
  );
};

// ── S03 разминка ──
const S03: React.FC<{t: number}> = ({t}) => {
  const {s, o, on} = useScene(t, 'S03');
  if (!on) return null;
  const mid = s.start + (s.end - s.start) * 0.42;
  const showRes = prog(t, mid, 0.4);
  const gram = prog(t, wt('S03', 'грамматика') - 0.2, 0.4, easeOut);
  // крупный план: подпись «I've been firing on all cylinders this month» в разминке
  const box = {x: 60, y: 470, w: 880, h: 640};
  const crop = {cx: 410, cy: 250, w: 300};
  const ch = (crop.w * box.h) / box.w;
  const k = box.w / crop.w;
  const fx = box.x + (485 - (crop.cx - crop.w / 2)) * k;
  const fy = box.y + (225 - (crop.cy - ch / 2)) * k;
  return (
    <Layer opacity={o}>
      <Heading t={t} id="S03" step="шаг 2 · урок" title="Разминка" />
      <Shot t={t} t0={s.start} dur={mid - s.start + 0.4} src="lesson/sc1_1327.mov" video rate={5} startAt={14} from={{cx: 900, cy: 560, w: 1400}} to={{cx: 900, cy: 560, w: 1250}} box={box} opacity={1 - showRes} />
      {showRes > 0 && <Shot t={t} t0={mid} dur={s.end - mid} src="images/board_detail.png" from={{cx: 410, cy: 250, w: 330}} to={crop} box={box} opacity={showRes} />}
      {gram > 0 && <HandOval cx={fx} cy={fy} rx={150} ry={110} t={t} start={wt('S03', 'грамматика')} seed={21} />}
      <Line a={gram} top={1150}>
        в разминке уже спрятана
        <br />
        грамматика урока: <span style={{background: `linear-gradient(transparent 60%, ${C.marker} 60%)`}}>I&apos;ve been…</span>
      </Line>
    </Layer>
  );
};

// ── S04 замер «до» ──
const Timer: React.FC<{t: number; t0: number; t1: number}> = ({t, t0, t1}) => {
  const left = Math.max(0, 120 * (1 - prog(t, t0, t1 - t0, (x) => x)));
  const m = Math.floor(left / 60);
  const sec = Math.floor(left % 60);
  return (
    <span style={{fontFamily: SERIF, fontSize: 64, fontVariantNumeric: 'tabular-nums'}}>
      {m}:{String(sec).padStart(2, '0')}
    </span>
  );
};

const S04: React.FC<{t: number}> = ({t}) => {
  const {s, o, on} = useScene(t, 'S04');
  if (!on) return null;
  const a = sp(t, wt('S04', 'две') - 0.2, {damping: 18});
  const b = prog(t, wt('S04', 'отправная') - 0.2, 0.4, easeOut);
  return (
    <Layer opacity={o}>
      <Heading t={t} id="S04" step="шаг 3" title="Замер «до»" />
      <Shot t={t} t0={s.start} dur={s.end - s.start} src="lesson/sc2_1337.mov" video rate={3.5} startAt={6} from={{cx: 860, cy: 520, w: 1000}} to={{cx: 860, cy: 560, w: 900}} box={{x: 60, y: 470, w: 880, h: 640}} />
      <div style={{position: 'absolute', left: 60, top: 1150, display: 'flex', gap: 18, alignItems: 'center'}}>
        <Chip a={a} marker>
          «Tell me about yourself»
        </Chip>
        {a > 0.01 && (
          <div style={{opacity: Math.min(1, a * 1.4), color: C.ink}}>
            <Timer t={t} t0={wt('S04', 'две')} t1={s.end} />
          </div>
        )}
      </div>
      <Line a={b} top={1250} size={40}>
        слушаю и записываю: это отправная точка
      </Line>
    </Layer>
  );
};

// ── S05 Present / Past / Future ──
const S05: React.FC<{t: number}> = ({t}) => {
  const {s, o, on} = useScene(t, 'S05');
  if (!on) return null;
  const parts: [string, string, string][] = [
    ['Present', 'present', 'кто я сейчас'],
    ['Past', 'past', 'как я к этому пришла'],
    ['Future', 'future', 'чего хочу дальше'],
  ];
  return (
    <Layer opacity={o}>
      <Heading t={t} id="S05" step="шаг 4" title="Фреймворк из статьи" />
      <Shot t={t} t0={s.start} dur={s.end - s.start} src="lesson/sc3_1339.mov" video rate={5} startAt={2} from={{cx: 820, cy: 560, w: 1500}} to={{cx: 900, cy: 620, w: 1150}} box={{x: 60, y: 470, w: 880, h: 560}} />
      <div style={{position: 'absolute', left: 60, top: 1070, display: 'flex', flexDirection: 'column', gap: 14}}>
        {parts.map(([en, w, ru]) => {
          const a = sp(t, wt('S05', w) - 0.15, {damping: 18});
          return (
            <Chip key={en} a={a} style={{fontSize: 36}}>
              <span style={{background: C.marker, borderRadius: 999, padding: '2px 16px'}}>{en}</span> {ru}
            </Chip>
          );
        })}
      </div>
    </Layer>
  );
};

// ── S06 scaffolding ──
const S06: React.FC<{t: number}> = ({t}) => {
  const {s, o, on} = useScene(t, 'S06');
  if (!on) return null;
  const a = prog(t, wt('S06', 'scaffolding') - 0.2, 0.5, easeOut);
  const b = prog(t, wt('S06', 'несколько') - 0.2, 0.4, easeOut);
  return (
    <Layer opacity={o}>
      <Heading t={t} id="S06" step="шаг 5" title="Готовые начала фраз" />
      <Shot t={t} t0={s.start} dur={s.end - s.start} src="lesson/sc4_1341.mov" video rate={3.8} startAt={0} from={{cx: 1260, cy: 560, w: 1250}} to={{cx: 1240, cy: 520, w: 1000}} box={{x: 60, y: 470, w: 880, h: 600}} />
      <div style={{position: 'absolute', left: 60, top: 1110, fontFamily: SERIF, fontSize: 80, color: C.ink, opacity: a, transform: `translateY(${(1 - a) * 12}px)`}}>
        <span style={{background: `linear-gradient(transparent 62%, ${C.marker} 62%)`}}>scaffolding</span>
      </div>
      <Line a={b} top={1230} size={40}>
        одна мысль — несколько способов её сказать
      </Line>
    </Layer>
  );
};

// ── S07 грамматика ──
const S07: React.FC<{t: number}> = ({t}) => {
  const {s, o, on} = useScene(t, 'S07');
  if (!on) return null;
  const tenses: [string, string, number][] = [
    ['Past Simple', 'past', 0],
    ['Present Perfect', 'perfect', 0],
    ['Present Perfect Continuous', 'perfect', 1],
  ];
  const ex = wt('S07', 'составить');
  return (
    <Layer opacity={o}>
      <Heading t={t} id="S07" step="шаг 6" title="Грамматика опыта" />
      <Shot
        t={t}
        t0={s.start}
        dur={ex - s.start + 0.6}
        src="images/board_detail.png"
        from={{cx: 1053, cy: 551, w: 700}}
        to={{cx: 1053, cy: 551, w: 660}}
        box={{x: 60, y: 470, w: 880, h: 420}}
        opacity={1 - prog(t, ex - 0.1, 0.5)}
      />
      {t > ex - 0.2 && <Shot t={t} t0={ex - 0.1} dur={s.end - ex} src="images/board_detail.png" from={{cx: 1020, cy: 870, w: 660}} to={{cx: 1000, cy: 870, w: 640}} box={{x: 60, y: 470, w: 880, h: 420}} opacity={prog(t, ex - 0.1, 0.5)} />}
      <div style={{position: 'absolute', left: 60, top: 940, display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 14}}>
        {tenses.map(([name, w, nth], i) => (
          <Chip key={name} a={sp(t, wt('S07', w, nth) - 0.15, {damping: 18})} marker={i > 0} style={{fontSize: 36}}>
            {i === 0 ? 'не только ' : i === 1 ? 'но и ' : 'и '}
            {name}
          </Chip>
        ))}
      </div>
      <Line a={prog(t, ex - 0.1, 0.4, easeOut)} top={1215} size={40}>
        предложения о себе — с этими временами
      </Line>
    </Layer>
  );
};

// ── S08 опоры ──
const S08: React.FC<{t: number}> = ({t}) => {
  const {s, o, on} = useScene(t, 'S08');
  if (!on) return null;
  const em = wt('S08', 'emergent');
  const a = sp(t, wt('S08', 'corporate') - 0.2, {damping: 18});
  const b = sp(t, em - 0.2, {damping: 18});
  return (
    <Layer opacity={o}>
      <Heading t={t} id="S08" step="на доске" title="Опоры" />
      <Shot t={t} t0={s.start} dur={em - s.start + 0.5} src="images/board_detail.png" from={{cx: 1770, cy: 270, w: 560}} to={{cx: 1760, cy: 260, w: 520}} box={{x: 60, y: 470, w: 880, h: 560}} opacity={1 - prog(t, em - 0.1, 0.5)} />
      {t > em - 0.2 && <Shot t={t} t0={em - 0.1} dur={s.end - em} src="images/board_detail.png" from={{cx: 1780, cy: 640, w: 540}} to={{cx: 1770, cy: 630, w: 520}} box={{x: 60, y: 470, w: 880, h: 560}} opacity={prog(t, em - 0.1, 0.5)} />}
      <div style={{position: 'absolute', left: 60, top: 1070, display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 14}}>
        <Chip a={a} style={{fontSize: 36}}>
          <span style={{background: C.marker, borderRadius: 999, padding: '2px 16px'}}>corporate speak</span> owned · drove · scaled
        </Chip>
        <Chip a={b} style={{fontSize: 36}}>
          <span style={{background: C.marker, borderRadius: 999, padding: '2px 16px'}}>Emergent Vocabulary</span> новые слова урока
        </Chip>
      </div>
      <Line a={prog(t, wt('S08', 'переделываем') - 0.2, 0.4, easeOut)} top={1250} size={40}>
        все примеры — под неё
      </Line>
    </Layer>
  );
};

// ── S09 замер «после» ──
const S09: React.FC<{t: number}> = ({t}) => {
  const {s, o, on} = useScene(t, 'S09');
  if (!on) return null;
  const a = sp(t, wt('S09', 'две') - 0.2, {damping: 18});
  const b = sp(t, wt('S09', 'сравниваем') - 0.2, {damping: 18});
  return (
    <Layer opacity={o}>
      <Heading t={t} id="S09" step="шаг 7" title="Замер «после»" />
      <Shot t={t} t0={s.start} dur={s.end - s.start} src="images/board_detail.png" from={{cx: 1675, cy: 868, w: 480}} to={{cx: 1670, cy: 868, w: 470}} box={{x: 60, y: 470, w: 880, h: 380}} />
      <div style={{position: 'absolute', left: 60, top: 900, display: 'flex', gap: 18, alignItems: 'center'}}>
        <Chip a={a} marker>
          снова 2 минуты
        </Chip>
      </div>
      <div style={{position: 'absolute', left: 60, top: 1000, display: 'flex', gap: 16, alignItems: 'center', opacity: Math.min(1, b * 1.4)}}>
        <Chip a={b}>до</Chip>
        <span style={{fontFamily: SANS, fontWeight: 600, fontSize: 44, color: C.ink}}>→</span>
        <Chip a={b} marker>
          после
        </Chip>
        <span style={{fontFamily: SANS, fontWeight: 600, fontSize: 36, color: C.ink}}>что изменилось</span>
      </div>
    </Layer>
  );
};

// ── S10 призыв ──
const S10: React.FC<{t: number}> = ({t}) => {
  const s = scene('S10');
  if (t < s.start - 0.1) return null;
  const a = sp(t, s.start + 0.2, {damping: 18});
  const b = sp(t, wt('S10', 'личку') - 0.3, {damping: 18});
  return (
    <Layer opacity={prog(t, s.start, 0.3)}>
      <div style={{position: 'absolute', left: 60, width: 880, top: 236, fontFamily: SERIF, fontSize: 78, lineHeight: 1.08, color: C.ink}}>
        Урок под
        <br />
        конкретную цель
      </div>
      <Shot t={t} t0={s.start} dur={s.end - s.start} src="images/board_whole.png" from={{cx: 1060, cy: 550, w: 1500}} to={{cx: 1080, cy: 560, w: 1700}} box={{x: 60, y: 470, w: 880, h: 500}} />
      {a > 0.001 && (
        <div style={{position: 'absolute', left: 80, width: 840, top: 1010, padding: '30px 40px', boxSizing: 'border-box', background: C.white, borderRadius: 28, boxShadow: '0 8px 24px rgba(30,42,68,0.12)', fontFamily: SANS, color: C.ink, opacity: Math.min(1, a * 1.3), transform: `translateY(${(1 - a) * 24}px)`}}>
          <div style={{fontSize: 48, fontWeight: 600}}>Индивидуальные уроки</div>
          <div style={{fontSize: 40, fontWeight: 500, color: C.sky, marginTop: 6}}>готовимся к интервью на английском</div>
        </div>
      )}
      <div style={{position: 'absolute', left: 80, top: 1220}}>
        <Chip a={b} marker>
          пишите в личку
        </Chip>
      </div>
    </Layer>
  );
};

export const LessonReel: React.FC = () => {
  const t = useCurrentFrame() / tl.fps;
  return (
    <AbsoluteFill>
      <Paper />
      <S01 t={t} />
      <S02 t={t} />
      <S03 t={t} />
      <S04 t={t} />
      <S05 t={t} />
      <S06 t={t} />
      <S07 t={t} />
      <S08 t={t} />
      <S09 t={t} />
      <S10 t={t} />
      {showSubtitles && <Subtitles t={t} tl={tl} />}
      {tl.voice && <Audio src={staticFile(tl.voice)} />}
    </AbsoluteFill>
  );
};
