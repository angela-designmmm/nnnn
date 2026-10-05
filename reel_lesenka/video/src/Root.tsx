import {Composition} from 'remotion';
import {Reel} from './Reel';
import {tl} from './time';

export const RemotionRoot: React.FC = () => (
  <Composition
    id="Reel"
    component={Reel}
    durationInFrames={Math.ceil(tl.duration * tl.fps)}
    fps={tl.fps}
    width={tl.width}
    height={tl.height}
  />
);
