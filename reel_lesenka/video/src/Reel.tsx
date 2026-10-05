import React from 'react';
import {AbsoluteFill, Audio, getInputProps, staticFile, useCurrentFrame} from 'remotion';
import {Paper} from './common';
import {Ladder} from './Ladder';
import {Apps, Club, Examples, Hook, Laufer, Question, Sources, Teaser} from './Scenes';
import {Subtitles} from './Subtitles';
import {tl} from './time';

// --props='{"subtitles":false}' — рендер без субтитров
const showSubtitles = getInputProps().subtitles !== false;

export const Reel: React.FC = () => {
  const t = useCurrentFrame() / tl.fps;
  return (
    <AbsoluteFill>
      <Paper />
      <Hook t={t} />
      <Question t={t} />
      <Laufer t={t} />
      <Apps t={t} />
      <Club t={t} />
      <Teaser t={t} />
      <Ladder t={t} />
      <Examples t={t} />
      <Sources t={t} />
      {showSubtitles && <Subtitles t={t} />}
      {tl.voice && <Audio src={staticFile(tl.voice)} />}
    </AbsoluteFill>
  );
};
