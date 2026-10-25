#!/usr/bin/env node
/**
 * browser_check.mjs — what only a real engine can prove.
 *
 *   CHROME_PATH=/tmp/chromium LD_LIBRARY_PATH=/tmp/al2023/lib \
 *     node tools/sitegen/browser_check.mjs [http://localhost:8000]
 *
 * The gate's other steps read the stylesheet and the built HTML. This one
 * loads the pages and measures what actually composited: that a card's shadow
 * is the hard offset it claims, that hover lifts it three pixels, that nothing
 * overflows a 320px screen, that ink on the hero clears AA, that the service
 * worker serves ten offline reloads, and that print drops the shadows.
 *
 * It is skipped unless CHROME_PATH names a binary, so a machine with no
 * browser stays green. That is a deliberate trade: it means the checks below
 * must be run by hand before any PR that touches layout, because nothing else
 * will remind you. It is not part of `npm test` for the same reason.
 *
 * A browser is not installed by this repo — Chromium is 209 MB and cannot be
 * required. Where to get one is recorded in AGENTS.md.
 *
 * Traps, each of which cost a wrong answer before it was found:
 * - `LD_LIBRARY_PATH=/tmp/al2023/lib` is the whole trick. Without it Chromium
 *   dies on a missing `libnspr4.so`. Set it in the shell AND in `launch({env})`.
 * - `element.offsetParent` is always null for `position: fixed`, so it reports
 *   every fixed element as invisible. Measure the bounding box instead.
 * - The service worker precaches 36 routes, so a reused browser context makes
 *   later routes load in 0.0 s: you measure the cache, not the connection.
 *   Use a fresh `browser.createBrowserContext()` per route.
 * - FCP's `startTime` is already measured from navigation start; adding the
 *   emulated RTT on top double-counts the connection (4.9 s read as 6.9 s).
 * - Probing a page for elements it lacks makes false failures — the home page
 *   has no `.tick`, `/1/start-here/` has no buttons. Probe where the element
 *   exists, and count chrome elements only when present.
 * - A tap-target sweep that includes inline prose links flags false positives.
 *   WCAG 2.2 exempts them; filter with `!e.closest('p, li, td, blockquote')`.
 */
import puppeteer from 'puppeteer-core';
import fs from 'fs';
import path from 'path';

const BASE = process.argv[2] || 'http://localhost:8000';
const executablePath = process.env.CHROME_PATH;
// The built site, walked to find every route. Resolved from this file so the
// sweep works wherever the gate is run from.
const SITE_DIR = path.resolve(new URL('../../_site', import.meta.url).pathname);

if (!executablePath) {
  console.log('\nSKIP  no CHROME_PATH — set it to a Chromium binary to run the browser checks\n');
  process.exit(0);
}

const LIBS = process.env.LD_LIBRARY_PATH || '';
const fails = [];
let passes = 0;

function check(label, ok, detail) {
  if (ok) { passes++; console.log(`  ok   ${label.padEnd(52)} ${detail ?? ''}`); }
  else { fails.push(`${label}: ${detail}`); console.log(`  FAIL ${label.padEnd(52)} ${detail ?? ''}`); }
}

const browser = await puppeteer.launch({
  executablePath,
  headless: true,
  args: ['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu'],
  env: { ...process.env, LD_LIBRARY_PATH: LIBS },
});

const page = await browser.newPage();
await page.setViewport({ width: 1440, height: 900, deviceScaleFactor: 1 });
await page.goto(`${BASE}/1/start-here/`, { waitUntil: 'networkidle0' });
await new Promise((r) => setTimeout(r, 400));

// --------------------------------------------------------- the design system
console.log('\nthe system, as rendered');
const s = await page.evaluate(() => {
  const g = (sel) => { const e = document.querySelector(sel); return e ? getComputedStyle(e) : null; };
  const hero = g('.hero'), card = g('.card'), btn = g('.btn');
  return {
    heroBg: hero?.backgroundColor, heroBorderW: hero?.borderTopWidth,
    heroBorderC: hero?.borderTopColor, heroShadow: hero?.boxShadow,
    cardRadius: card?.borderTopLeftRadius, cardShadow: card?.boxShadow,
    cardBorder: card?.borderTopWidth,
    btnMinH: btn?.minHeight, btnRadius: btn?.borderTopLeftRadius,
    h1Family: g('h1')?.fontFamily, thFamily: g('th')?.fontFamily,
    bodyBg: g('body')?.backgroundColor,
    eyebrowBg: g('.hero-eyebrow')?.backgroundColor,
    eyebrowFg: g('.hero-eyebrow')?.color,
  };
});
check('hero ground is the system blue', s.heroBg === 'rgb(55, 104, 255)', s.heroBg);
check('hero border is 4px cyan', s.heroBorderW === '4px' && s.heroBorderC === 'rgb(101, 232, 255)',
  `${s.heroBorderW} ${s.heroBorderC}`);
check('hero carries a hard 10px pink shadow',
  /rgb\(255, 78, 145\)/.test(s.heroShadow || '') && /10px 10px/.test(s.heroShadow || ''), s.heroShadow);
check('cards are square', s.cardRadius === '0px', s.cardRadius);
check('cards carry a hard 6px shadow',
  /rgb\(30, 37, 83\)/.test(s.cardShadow || '') && /6px 6px/.test(s.cardShadow || ''), s.cardShadow);
check('card borders are 3px', s.cardBorder === '3px', s.cardBorder);
check('headings use the mono chrome face', /mono/i.test(s.h1Family || ''), (s.h1Family || '').split(',')[0]);
check('table heads use the mono chrome face', /mono/i.test(s.thFamily || ''), (s.thFamily || '').split(',')[0]);
check('body ground is the warm paper', s.bodyBg === 'rgb(255, 248, 231)', s.bodyBg);
check('eyebrow is a yellow chip carrying ink',
  s.eyebrowBg === 'rgb(255, 225, 104)' && s.eyebrowFg === 'rgb(17, 20, 43)', `${s.eyebrowBg} / ${s.eyebrowFg}`);

// ------------------------------------------------------------ hover gesture
await page.hover('.card');
await new Promise((r) => setTimeout(r, 350));
const hov = await page.evaluate(() => {
  const c = getComputedStyle(document.querySelector('.card'));
  return { shadow: c.boxShadow, transform: c.transform };
});
check('hover turns the shadow pink at 10px',
  /rgb\(255, 78, 145\)/.test(hov.shadow) && /10px 10px/.test(hov.shadow), hov.shadow);
check('hover lifts the card by 3px',
  /matrix\(1, 0, 0, 1, -3, -3\)/.test(hov.transform), hov.transform);

// ------------------------------------------------------ tap targets (phones)
console.log('\ncontrols, at phone width');
const home = await browser.newPage();
await home.setViewport({ width: 390, height: 844, deviceScaleFactor: 1 });
await home.goto(`${BASE}/`, { waitUntil: 'networkidle0' });
const ctl = await home.evaluate(() => {
  const b = document.querySelector('.btn');
  // Standalone targets only. Inline links inside prose are exempt from WCAG
  // 2.2's target-size rule, so measuring them would be false precision.
  const standalone = [...document.querySelectorAll('a.btn, button, .tick, .site-nav a, select, input')]
    .filter((e) => !e.closest('p, li, td, blockquote'))
    .map((e) => ({ sel: e.tagName.toLowerCase() + '.' + ((e.className || '').toString().split(' ')[0] || '-'),
                   h: Math.round(e.getBoundingClientRect().height) }));
  return { btnMinH: b ? getComputedStyle(b).minHeight : null,
           btnRadius: b ? getComputedStyle(b).borderTopLeftRadius : null,
           small: standalone.filter((c) => c.h < 44), total: standalone.length };
});
check('buttons are at least 48px tall', parseFloat(ctl.btnMinH) >= 48, ctl.btnMinH);
check('buttons are square', ctl.btnRadius === '0px', ctl.btnRadius);
check('no standalone control is under 44px', ctl.small.length === 0,
  ctl.small.length ? JSON.stringify(ctl.small.slice(0, 3)) : `${ctl.total} measured`);
await home.close();

const wk = await browser.newPage();
await wk.setViewport({ width: 390, height: 844, deviceScaleFactor: 1 });
await wk.goto(`${BASE}/2/plan/week/1/`, { waitUntil: 'networkidle0' });
const t = await wk.evaluate(() => {
  const e = document.querySelector('.tick');
  return e ? { h: Math.round(e.getBoundingClientRect().height),
               radius: getComputedStyle(e).borderTopLeftRadius } : null;
});
await wk.close();
check('ticks are at least 48px on a phone', t && t.h >= 48, t ? `${t.h}px` : 'none found');
check('ticks keep the 2px softening', t && t.radius === '2px', t ? t.radius : '-');

// ------------------------------------------------------------ overflow sweep
console.log('\nhorizontal overflow, seven widths');
for (const w of [320, 390, 430, 768, 1024, 1440, 1920]) {
  const p2 = await browser.newPage();
  await p2.setViewport({ width: w, height: 900, deviceScaleFactor: 1 });
  await p2.goto(`${BASE}/2/plan/`, { waitUntil: 'networkidle0' });
  const over = await p2.evaluate(() => {
    const d = document.documentElement;
    return d.scrollWidth - d.clientWidth;
  });
  if (over > 0) fails.push(`${w}px overflows by ${over}px`);
  console.log(`  ${over > 0 ? 'FAIL' : 'ok  '} ${String(w).padStart(5)}px  overflow ${over}px`);
  if (over === 0) passes++;
  await p2.close();
}

// ------------------------------------------------- contrast, as composited
console.log('\ncontrast, as the engine composited it');
const rendered = await page.evaluate(() => {
  const lum = (c) => {
    const [r, g, b] = c.match(/\d+/g).slice(0, 3).map((v) => {
      v = v / 255; return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  };
  const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((m, n) => n - m); return (x + 0.05) / (y + 0.05); };
  const bgOf = (el) => {
    let e = el;
    while (e) { const bg = getComputedStyle(e).backgroundColor;
      if (bg && bg !== 'rgba(0, 0, 0, 0)' && !/rgba\(.*,\s*0\)$/.test(bg)) return bg;
      e = e.parentElement; }
    return 'rgb(255, 255, 255)';
  };
  return ['.hero h1', '.hero-lead', '.hero-eyebrow', '.hero .stamp', '.card p', 'th', 'td', '.note']
    .map((sel) => { const el = document.querySelector(sel); if (!el) return null;
      const bg = bgOf(el);
      return { sel, r: +ratio(getComputedStyle(el).color, bg).toFixed(2),
               fg: getComputedStyle(el).color, bg }; }).filter(Boolean);
});
for (const r of rendered) {
  console.log(`  ${r.r >= 4.5 ? 'ok  ' : 'FAIL'} ${r.sel.padEnd(16)} ${String(r.r).padStart(6)}:1`);
  if (r.r >= 4.5) passes++; else fails.push(`${r.sel} measures ${r.r}:1 in the browser`);
}

// ------------------------------------------------------- service worker run
console.log('\nservice worker: install, go offline, reload ten times');
const sw = await browser.newPage();
await sw.setViewport({ width: 390, height: 844, deviceScaleFactor: 1 });
await sw.goto(`${BASE}/`, { waitUntil: 'networkidle0' });
await new Promise((r) => setTimeout(r, 3000));
const swState = await sw.evaluate(async () => {
  const reg = await navigator.serviceWorker.getRegistration();
  let entries = 0;
  for (const k of await caches.keys()) entries += (await (await caches.open(k)).keys()).length;
  return { active: reg?.active?.state ?? 'none', entries };
});
check('worker is activated', swState.active === 'activated', swState.active);
check('the shell is precached', swState.entries >= 30, `${swState.entries} entries`);
const cdp = await sw.createCDPSession();
await cdp.send('Network.enable');
await cdp.send('Network.emulateNetworkConditions',
  { offline: true, latency: 0, downloadThroughput: 0, uploadThroughput: 0 });
let served = 0;
for (let i = 0; i < 10; i++) {
  try {
    await sw.reload({ waitUntil: 'domcontentloaded', timeout: 15000 });
    const ok = await sw.evaluate(() => (document.querySelector('h1')?.textContent?.trim() ?? '').length > 0
      && document.body.innerText.length > 400);
    if (ok) served++;
  } catch { /* counted below */ }
}
check('ten offline reloads all served', served === 10, `${served}/10`);
const nudge = await sw.evaluate(() => {
  const n = document.querySelector('.sw-note');
  if (!n) return null;
  const r = n.getBoundingClientRect(); const cs = getComputedStyle(n);
  // Not offsetParent: that is always null for position:fixed, so it reports
  // every fixed element as hidden no matter whether it is on screen.
  return { shown: cs.display !== 'none' && cs.visibility !== 'hidden' && r.height > 0
                  && r.top >= 0 && r.bottom <= window.innerHeight,
           box: `${Math.round(r.width)}x${Math.round(r.height)}` };
});
check('the offline nudge is on screen', nudge?.shown === true, nudge ? nudge.box : 'not present');
await sw.close();

// ------------------------------------------- contrast on every filled card
// The static contrast audit reads the stylesheet and the rendered check above
// samples a fixed list of selectors. Neither sees a paragraph of body copy
// sitting on a card tint, which is the one place colour-under-text can fail
// here. This walks every route and measures it. It found a real failure on
// 2026-10-25: the muted ink used for notes and week numbers fell to 3.86:1 on
// the coral tint, because coral was the darkest of the eight.
console.log('\ncontrast on every filled card, all routes');
{
  const routes = [];
  (function walk(dir, prefix) {
    for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
      if (e.isDirectory()) walk(path.join(dir, e.name), `${prefix}${e.name}/`);
      else if (e.name === 'index.html') routes.push('/' + prefix);
    }
  })(SITE_DIR, '');

  const probe = () => {
    const lum = (c) => {
      const [r, g, b] = c.match(/\d+/g).slice(0, 3).map((v) => {
        v = v / 255; return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
      });
      return 0.2126 * r + 0.7152 * g + 0.0722 * b;
    };
    const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((m, n) => n - m);
      return (x + 0.05) / (y + 0.05); };
    const groundOf = (el) => { let e = el;
      while (e) { const c = getComputedStyle(e).backgroundColor;
        if (c && c !== 'rgba(0, 0, 0, 0)' && !/rgba\(.*,\s*0\)$/.test(c)) return c;
        e = e.parentElement; }
      return 'rgb(255, 255, 255)'; };
    let worst = 99, on = '';
    for (const b of document.querySelectorAll('.block')) {
      for (const el of b.querySelectorAll('p, li, h3, span, code, a')) {
        if (!el.textContent.trim() || el.querySelector('svg')) continue;
        const r = ratio(getComputedStyle(el).color, groundOf(el));
        if (r < worst) { worst = r; on = (el.className || el.tagName).toString().slice(0, 30); }
      }
    }
    return { worst: +worst.toFixed(2), on, blocks: document.querySelectorAll('.block').length };
  };

  const p3 = await browser.newPage();
  await p3.setViewport({ width: 390, height: 900, deviceScaleFactor: 1 });
  let worst = 99, worstRoute = '', worstOn = '', cards = 0;
  for (const r of routes) {
    await p3.goto(`${BASE}${r}`, { waitUntil: 'domcontentloaded' });
    const m = await p3.evaluate(probe);
    cards += m.blocks;
    if (m.blocks && m.worst < worst) { worst = m.worst; worstRoute = r; worstOn = m.on; }
  }
  await p3.close();
  check('every filled card carries its text at AA', worst >= 4.5,
    `worst ${worst}:1 on ${worstRoute} .${worstOn}, ${cards} cards in ${routes.length} routes`);
}

// ------------------------------------------------------------------- print
console.log('\nprint');
const pr = await browser.newPage();
await pr.setViewport({ width: 794, height: 1123, deviceScaleFactor: 1 });
await pr.goto(`${BASE}/2/plan/`, { waitUntil: 'networkidle0' });
await pr.emulateMediaType('print');
await new Promise((r) => setTimeout(r, 200));
const printed = await pr.evaluate(() => {
  const g = (sel) => { const e = document.querySelector(sel); return e ? getComputedStyle(e) : null; };
  const chrome = ['.site-head', '.site-foot', '.pager', '.skip', '.tick', '.actions'];
  const present = chrome.filter((sel) => document.querySelector(sel));
  return {
    cardShadow: (g('.card') ?? g('body'))?.boxShadow,
    heroShadow: g('.hero')?.boxShadow,
    heroBorder: g('.hero')?.borderTopWidth,
    bodySize: getComputedStyle(document.body).fontSize,
    hidden: present.filter((sel) => getComputedStyle(document.querySelector(sel)).display === 'none').length,
    present: present.length,
  };
});
check('print drops the card shadow', printed.cardShadow === 'none', printed.cardShadow);
check('print drops the hero shadow', printed.heroShadow === 'none', printed.heroShadow);
check('print hides the chrome', printed.hidden === printed.present && printed.present > 0,
  `${printed.hidden}/${printed.present}`);
check('print type is the 12px floor', parseFloat(printed.bodySize) >= 12, printed.bodySize);
await pr.emulateMediaType(null);
const pdf = await pr.pdf({ format: 'A4', printBackground: true });
check('print renders a real page', pdf.length > 3000, `${Math.round(pdf.length / 1024)} KB`);
await pr.close();

await browser.close();
console.log(`\n${fails.length ? `${fails.length} FAILED of ${fails.length + passes}:\n` +
  fails.map((f) => '  - ' + f).join('\n') : `all ${passes} browser checks passed`}`);
process.exit(fails.length ? 1 : 0);
