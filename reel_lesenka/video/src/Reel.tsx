import React from 'react';
import {AbsoluteFill, Audio, staticFile, useCurrentFrame} from 'remotion';
import {Paper} from './common';
import {Ladder} from './Ladder';
import {Apps, Cta, Examples, Hook, Laufer, Nakata, Question, Sources} from './Scenes';
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
      <Nakata t={t} />
      <Cta t={t} />
      <Ladder t={t} />
      <Examples t={t} />
      <Sources t={t} />
      <Subtitles t={t} />
      {tl.voice && <Audio src={staticFile(tl.voice)} />}
    </AbsoluteFill>
  );
};
