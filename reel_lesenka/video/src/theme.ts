import {loadFont} from '@remotion/fonts';
import {staticFile} from 'remotion';

export const C = {
  paper: '#EEF4FA',
  mist: '#C9DCF0',
  sky: '#7FA7D6',
  ink: '#1E2A44',
  marker: '#F2C94C',
  ok: '#3DBE6B',
  white: '#FFFFFF',
};

// Шрифты Google Fonts (Old Standard TT, Golos Text), файлы лежат в public/fonts:
// headless-браузер рендера не доверяет CA прокси, поэтому не тянем их с gstatic на лету.
const CYR = 'U+0301, U+0400-045F, U+0490-0491, U+04B0-04B1, U+2116';
const LAT = 'U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD';
export const SERIF = 'Old Standard TT';
export const SANS = 'Golos Text';
const face = (family: string, file: string, weight: string, unicodeRange: string) =>
  loadFont({family, url: staticFile(`fonts/${file}.woff2`), weight, unicodeRange, format: 'woff2'});
for (const w of ['400', '700']) {
  face(SERIF, `old${w}-cyr`, w, CYR);
  face(SERIF, `old${w}-lat`, w, LAT);
}
face(SANS, 'golos-cyr', '400 700', CYR);
face(SANS, 'golos-lat', '400 700', LAT);

// Подписи-источники. Анджела проверит точные ссылки — менять здесь.
export const SOURCE_LAUFER = 'Laufer & Goldstein, 2004';
export const SOURCE_NAKATA = 'Nakata, 2013, 2017';

// Безопасная зона Reels
export const SAFE = {top: 220, bottom: 1500, left: 60, right: 940};
export const CX = (SAFE.left + SAFE.right) / 2; // центр безопасной зоны по x

// Где на скриншоте подписчицы сам вопрос (доли ширины/высоты картинки) — для обводки маркером.
// Подстроить, когда появится subscriber_question.png.
export const QUESTION_OVAL = {cx: 0.45, cy: 0.48, rx: 0.38, ry: 0.25};

// Скриншот шапки профиля (S13): пропорции и где строка «Анкета записи на Speaking Club» + ссылка
export const PROFILE_ASPECT = 1290 / 824;
export const PROFILE_OVAL = {cx: 0.31, cy: 0.808, rx: 0.33, ry: 0.06};
