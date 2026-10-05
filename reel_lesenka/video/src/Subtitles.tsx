import React from 'react';
import {C, CX, SANS} from './theme';
import {Timeline, tl as tl1} from './time';

// Субтитры: нижняя граница y = 1480, подложка paper 90 %, текущее слово — маркер снизу
export const Subtitles: React.FC<{t: number; tl?: Timeline}> = ({t, tl = tl1}) => {
  const cur = tl.subtitles.find((s) => t >= s.start && t < s.end);
  if (!cur) return null;
  return (
    <div style={{position: 'absolute', left: 60, width: 2 * (CX - 60), bottom: 1920 - 1480, display: 'flex', justifyContent: 'center'}}>
      <div
        style={{
          background: 'rgba(238,244,250,0.9)',
          borderRadius: 18,
          padding: '12px 26px 14px',
          fontFamily: SANS,
          fontWeight: 600,
          fontSize: 56,
          lineHeight: 1.2,
          color: C.ink,
          textAlign: 'center',
          boxShadow: '0 4px 18px rgba(30,42,68,0.08)',
          maxWidth: 2 * (CX - 60),
        }}
      >
        {cur.words.map((w, i) => {
          const on = t >= w.start && (i === cur.words.length - 1 ? t < cur.end : t < cur.words[i + 1].start);
          return (
            <React.Fragment key={i}>
              {i > 0 && ' '}
              <span style={{background: on ? `linear-gradient(transparent 62%, ${C.marker} 62%, ${C.marker} 92%, transparent 92%)` : 'none', padding: '0 2px'}}>{w.text}</span>
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
