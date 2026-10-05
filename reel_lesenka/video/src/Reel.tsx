import React from 'react';
import {AbsoluteFill, Audio, staticFile, useCurrentFrame} from 'remotion';
import {Paper} from './common';
import {Ladder} from './Ladder';
import {Apps, Club, Examples, Hook, Laufer, Question, Sources, Teaser} from './Scenes';
import {Subtitles} from './Subtitles';
import {tl} from './time';

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
      <Subtitles t={t} />
      {tl.voice && <Audio src={staticFile(tl.voice)} />}
    </AbsoluteFill>
  );
};
