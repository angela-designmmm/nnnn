import {Composition, Still} from 'remotion';
import {Cover1} from './Cover';
import {Reel2, tl2} from './Part2';
import {Reel} from './Reel';
import {tl} from './time';

export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="Reel" component={Reel} durationInFrames={Math.ceil(tl.duration * tl.fps)} fps={tl.fps} width={tl.width} height={tl.height} />
    <Composition id="Reel2" component={Reel2} durationInFrames={Math.ceil(tl2.duration * tl2.fps)} fps={tl2.fps} width={tl2.width} height={tl2.height} />
    <Still id="Cover1" component={Cover1} width={1080} height={1920} />
  </>
);
