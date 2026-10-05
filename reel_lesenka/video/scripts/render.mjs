// npm run draft           — часть 1, черновик без голоса: out/draft_no_voice.mp4
// npm run final           — часть 1 с голосом: out/reel.mp4 + out/cover.png
// --no-subs               — без субтитров (файлы с суффиксом _no_subs)
// --part 2                — часть 2: out/part2_*.mp4, данные в ../part2
import {execSync} from 'node:child_process';
import fs from 'node:fs';

const mode = process.argv[2] ?? 'draft';
const noSubs = process.argv.includes('--no-subs');
const part2 = process.argv.includes('--part') && process.argv[process.argv.indexOf('--part') + 1] === '2';
const props = noSubs ? `--props='{"subtitles":false}'` : '';
const suffix = noSubs ? '_no_subs' : '';
const pre = part2 ? 'part2_' : '';
const comp = part2 ? 'Reel2' : 'Reel';

execSync('node scripts/prepare.mjs', {stdio: 'inherit'});
execSync('node scripts/prepare.mjs', {stdio: 'inherit', env: {...process.env, PART: '2'}});
const tl = JSON.parse(fs.readFileSync(`src/generated/timeline${part2 ? '2' : ''}.json`, 'utf8'));
if (mode === 'final') {
  if (tl.mode !== 'sync') throw new Error('Нет голоса/транскрипта — финальный рендер невозможен');
  if (!part2 && !tl.hasQuestion) throw new Error('Нет assets/images/subscriber_question.png — заглушку в финал не выпускаем');
}
const browser = process.env.REMOTION_BROWSER ?? '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell';
const bflag = fs.existsSync(browser) ? `--browser-executable=${browser}` : '';
const out = mode === 'final' ? `../out/${pre}reel${suffix}.mp4` : `../out/${pre}draft_no_voice${suffix}.mp4`;
execSync(`npx remotion render ${comp} ${out} ${bflag} ${props}`, {stdio: 'inherit'});
// Обложка: часть 1 — S01 после обводки «+700»; часть 2 — кадр с «Часть 2»
const w = part2 ? tl.words.find((x) => x.scene === 'S02' && x.n === 'часто') : tl.words.find((x) => x.scene === 'S01' && x.n === 'семьсот');
const coverFrame = Math.round((w.start + (part2 ? 1.0 : 0.95)) * tl.fps);
execSync(`npx remotion still ${comp} ../out/${pre}cover${suffix}.png --frame=${coverFrame} ${bflag} ${props}`, {stdio: 'inherit'});
