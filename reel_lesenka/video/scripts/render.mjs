// npm run draft  — черновик без голоса: out/draft_no_voice.mp4 + out/cover.png
// npm run final  — финал с голосом: out/reel.mp4 + out/cover.png
import {execSync} from 'node:child_process';
import fs from 'node:fs';

const mode = process.argv[2] ?? 'draft';
execSync('node scripts/prepare.mjs', {stdio: 'inherit'});
const tl = JSON.parse(fs.readFileSync('src/generated/timeline.json', 'utf8'));
if (mode === 'final') {
  if (tl.mode !== 'sync') throw new Error('Нет голоса/транскрипта — финальный рендер невозможен');
  if (!tl.hasQuestion) throw new Error('Нет assets/images/subscriber_question.png — заглушку в финал не выпускаем');
}
const browser = process.env.REMOTION_BROWSER ?? '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell';
const bflag = fs.existsSync(browser) ? `--browser-executable=${browser}` : '';
const out = mode === 'final' ? '../out/reel.mp4' : '../out/draft_no_voice.mp4';
execSync(`npx remotion render Reel ${out} ${bflag}`, {stdio: 'inherit'});
// Обложка: S01 после обводки «+700»
const w = tl.words.find((x) => x.scene === 'S01' && x.n === 'семьсот');
const coverFrame = Math.round((w.start + 0.25 + 0.4 + 0.3) * tl.fps);
execSync(`npx remotion still Reel ../out/cover.png --frame=${coverFrame} ${bflag}`, {stdio: 'inherit'});
