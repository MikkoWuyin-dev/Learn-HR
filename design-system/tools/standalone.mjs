#!/usr/bin/env node
/**
 * standalone.mjs — build artifacts/standalone.html: the whole design system in ONE file.
 *
 * No build step, no network, no React. Inlines wakeout.css, converts the Tailwind-only
 * parts of wakeout.theme.css into plain CSS (@theme dropped, @utility foo -> .foo),
 * and embeds the two latin font subsets as base64. Hand this to a human or an agent that
 * just needs to SEE and COPY-FROM the system.
 */
import { readFileSync, writeFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const D = join(ROOT, "artifacts");
const tokens = JSON.parse(readFileSync(join(ROOT, "tokens/tokens.json"), "utf8"));

const base = readFileSync(join(D, "wakeout.css"), "utf8");
const theme = readFileSync(join(D, "wakeout.theme.css"), "utf8");

/* fonts: point at inlined data URIs instead of /fonts/*.woff2 */
const b64 = (f) => {
  try {
    return readFileSync(join(ROOT, "public/fonts", f)).toString("base64");
  } catch {
    return null; // subset not shipped (e.g. the tokens-only bundle) -> drop that src entry
  }
};
const fontCss = base
  .replace(/url\('\/fonts\/([^']+)'\) format\('woff2'\)/g, (_, f) => {
    const b = b64(f);
    return b ? `url(data:font/woff2;base64,${b}) format('woff2')` : "__DROP__";
  })
  .replace(/url\((?!data:)[^)]*\)/g, "__DROP__")
  .replace(/__DROP__,?\s*/g, "")
  .replace(/src:\s*;\s*/g, "");

/* plain-CSS transform of the Tailwind layer */
const stripAt = (src, name) => {
  let out = "",
    i = 0;
  const re = new RegExp(`@${name}[^{]*\\{`, "g");
  let m;
  while ((m = re.exec(src))) {
    out += src.slice(i, m.index);
    let j = re.lastIndex,
      depth = 1;
    while (j < src.length && depth > 0) {
      if (src[j] === "{") depth++;
      else if (src[j] === "}") depth--;
      j++;
    }
    i = j;
    if (name === "utility") {
      const body = src.slice(re.lastIndex, j - 1);
      const sel = m[0].slice(0, -1).replace(/@utility\s+/, "").trim();
      out += `\n.${sel}{${body}}`;
      re.lastIndex = j;
    }
  }
  return out + src.slice(i);
};
const componentCss = stripAt(stripAt(theme.replace(/@import[^;]*;/g, ""), "theme"), "utility");

/* ------------------------------- specimen ------------------------------- */
const P = tokens.color.primitive;
const lit = (v) =>
  typeof v === "string" && v.startsWith("{")
    ? v.replace(/\{([^}]+)\}/g, (_, p) => p.split(".").reduce((a, k) => a?.[k], tokens))
    : v;
const hexes = ["ink", "paper", "surface", "muted", "lime", "lime-deep", "pink", "purple", "orange", "cyan", "sky", "yellow", "sun", "ember", "dusk", "stage", "plum", "red"]
  .filter((k) => P[k])
  .map(
    (k) => `<div class="sw"><i style="background:${lit(P[k].value)}"></i><b>${k}</b><span>${lit(P[k].value)}</span>${
      P[k].usage ? `<em>${P[k].usage}×</em>` : ""
    }</div>`
  )
  .join("\n");

const ramp = Object.entries(tokens.typography.fontSize)
  .map(([k, v]) => `<div class="row"><code>${k}</code><span class="s" style="font-size:${v.value};line-height:${v.lineHeight ?? 1.4}">Reach up · 30 sec</span><code>${v.value}${v.px ? ` (${v.px}px)` : ""}</code><code class="u">${v.usage ? v.usage + "×" : "—"}</code></div>`)
  .join("\n");

const shadows = ["sticker-sm", "sticker", "sticker-lg", "sticker-pink", "sticker-purple", "sticker-lime"]
  .map((k) => `<div class="sw"><i class="box" style="box-shadow:var(--wk-shadow-${k})"></i><b>${k}</b><span>${lit(tokens.elevation[k].value)}</span></div>`)
  .join("\n");

const radii = Object.entries(tokens.dimension.radius)
  .filter(([k, v]) => k !== "none" && !v.inferred)
  .map(([k, v]) => `<div class="sw"><i class="rad" style="border-radius:${v.value.includes("%") ? v.value : `var(--wk-radius-${k})`}"></i><b>${k}</b><span>${v.value}</span><em>${v.usage ? v.usage + "×" : ""}</em></div>`)
  .join("\n");

const variants = Object.keys(tokens.component.button.variant)
  .map(
    (v) => `<button class="wk-button wk-button--${v} wk-button--sm ${v === "ink" || v === "purple" || v === "cyan" || v === "ember" ? "inv" : ""}">${v}</button>`
  )
  .join("\n");

const html = `<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>${tokens.$meta.name} — offline specimen</title>
<style>
${fontCss}
:root{color-scheme:light}
${componentCss}
/* specimen scaffolding only */
*{box-sizing:border-box}
body{margin:0;padding:0}
.wrap{max-width:72rem;margin:0 auto;padding:0 1.5rem}
section{padding:2.5rem 0;border-top:3px solid color-mix(in oklab,var(--wk-ink) 12%,transparent)}
section:first-of-type{border-top:0}
h1,h2,h3{margin:0 0 .75rem}
h2{font-size:1.75rem}
p.lead{font-size:1.125rem;line-height:1.625;color:color-mix(in oklab,var(--wk-ink) 80%,transparent);max-width:60ch;margin:.25rem 0 1.5rem}
.grid{display:grid;gap:.75rem;grid-template-columns:repeat(auto-fill,minmax(9.5rem,1fr))}
.sw{border:3px solid var(--wk-ink);border-radius:1rem;background:var(--wk-surface);box-shadow:var(--wk-shadow-sticker-sm);padding:.75rem;display:flex;flex-direction:column;gap:.35rem}
.sw i{display:block;height:3.25rem;border-radius:.5rem;border:1px solid color-mix(in oklab,var(--wk-ink) 15%,transparent)}
.sw i.box{background:var(--wk-surface);border:3px solid var(--wk-ink);border-radius:.75rem;height:4.5rem}
.sw i.rad{background:var(--wk-sky);border:3px solid var(--wk-ink);height:4.5rem}
.sw b{font-family:var(--wk-font-display);font-size:.875rem}
.sw span{font-family:var(--wk-font-mono);font-size:11px;color:color-mix(in oklab,var(--wk-ink) 60%,transparent)}
.sw em{font-size:10px;text-transform:uppercase;letter-spacing:.1em;font-weight:700;color:var(--wk-purple)}
.row{display:grid;grid-template-columns:7rem 1fr 7rem 3.5rem;gap:.75rem;align-items:baseline;padding:.5rem 0;border-bottom:1px solid color-mix(in oklab,var(--wk-ink) 10%,transparent)}
.row .s{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
code{font-family:var(--wk-font-mono);font-size:11px;color:color-mix(in oklab,var(--wk-ink) 70%,transparent)}
code.u{text-align:right}
.btns{display:flex;flex-wrap:wrap;gap:.75rem;align-items:center}
.demo{border:3px solid var(--wk-ink);border-radius:var(--wk-radius-3xl);background:var(--wk-surface);box-shadow:var(--wk-shadow-sticker);overflow:hidden}
.demo .pad{padding:1.5rem}
.two{display:grid;gap:1rem;grid-template-columns:repeat(auto-fit,minmax(20rem,1fr))}
.tex{height:8rem;border:3px solid var(--wk-ink);border-radius:1.25rem;display:flex;align-items:flex-end;padding:1rem;font-family:var(--wk-font-display);font-weight:700;box-shadow:var(--wk-shadow-sticker-sm)}
.wk-button.inv{color:var(--wk-paper)}
ul.rules{margin:0;padding-left:1.1rem;font-size:.875rem;line-height:1.625;color:color-mix(in oklab,var(--wk-ink) 78%,transparent)}
ul.rules b{color:var(--wk-ink)}
.kv{font-size:11px;font-family:var(--wk-font-mono);color:color-mix(in oklab,var(--wk-ink) 55%,transparent)}
header.hero{background:var(--wk-paper);padding:3rem 0 2.5rem;background-image:var(--wk-texture-grid);background-size:var(--wk-texture-grid-size)}
</style></head>
<body class="wk-bg-grid">
<header class="hero"><div class="wrap">
  <div class="wk-eyebrow">${tokens.$meta.name} · v${tokens.$meta.version}</div>
  <h1 style="font-family:var(--wk-font-display);font-weight:700;font-size:clamp(2.25rem,7vw,4.5rem);line-height:.95;letter-spacing:-.025em;margin:.5rem 0 1rem">
    A design system pulled<br>out of a live site
  </h1>
  <p class="lead">Offline specimen of the language used on ${tokens.$meta.reference}. Every value here is read from
  that site's shipped CSS — ${tokens.$meta.method.split("+")[0].trim()}.</p>
  <div class="btns">
    <button class="wk-button wk-button--primary">Start the routine</button>
    <button class="wk-button wk-button--ink inv">Browse tokens</button>
    <span class="wk-pill">30 seconds</span>
    <span class="wk-chip">no equipment</span>
  </div>
  <p class="kv" style="margin-top:1.5rem">generated ${tokens.$meta.capturedAt} · ${tokens.$meta.counts.classTokensMeasured.toLocaleString()} class uses measured · open this file anywhere, no build, no network</p>
</div></header>
<div class="wrap">
<section><h2>Colour</h2><div class="grid">${hexes}</div></section>
<section><h2>Type ramp</h2>${ramp}
  <p class="kv" style="margin-top:.75rem">display = ${lit(tokens.typography.fontFamily.display.value)} 700 with -.02em tracking (the reference's .font-display carries all three) · body = ${lit(tokens.typography.fontFamily.body.value)}</p>
</section>
<section><h2>Buttons</h2><div class="btns">${variants}</div>
  <div class="btns" style="margin-top:.75rem">
    <button class="wk-button wk-button--primary wk-button--sm">sm</button>
    <button class="wk-button wk-button--primary">md</button>
    <button class="wk-button wk-button--primary wk-button--lg">lg</button>
    <button class="wk-button wk-button--pink wk-button--pill">pill</button>
    <button class="wk-button wk-button--primary" disabled>disabled</button>
  </div>
  <p class="kv" style="margin-top:.75rem">hover: translateY(-2px) rotate(-1deg) + 10px shadow · active: translate(4px,4px) + 3px shadow (press distance = shadow size) · 150ms ease-out on transform + box-shadow only</p>
</section>
<section><h2>Elevation &amp; shape</h2><div class="two"><div class="grid">${shadows}</div><div class="grid">${radii}</div></div></section>
<section><h2>Surfaces</h2><div class="grid">
  <div class="tex" style="background:var(--wk-surface-sunrise);color:var(--wk-surface-sunrise-foreground)">sunrise</div>
  <div class="tex" style="background:var(--wk-background);color:var(--wk-foreground)">daylight</div>
  <div class="tex" style="background:var(--wk-surface-stage);color:var(--wk-surface-stage-foreground)">stage</div>
  <div class="tex" style="background:var(--wk-surface-dusk);color:var(--wk-surface-dusk-foreground)">dusk</div>
</div></section>
<section><h2>Cards &amp; textures</h2><div class="two">
  <div class="demo"><div class="pad">
    <div class="wk-eyebrow">default card</div>
    <h3 style="font-family:var(--wk-font-display);font-size:1.25rem;line-height:1.25;margin:.5rem 0">Two-minute desk reset</h3>
    <p style="font-size:.875rem;line-height:1.625;color:color-mix(in oklab,var(--wk-ink) 70%,transparent);margin:0">Stand, reach, roll the shoulders. 48px radius, 3px ink border, 6px hard shadow, 24px padding.</p>
  </div></div>
  <div class="demo wk-bg-dots" style="background-color:var(--wk-paper)"><div class="pad">
    <div class="wk-eyebrow">bg-dots texture</div>
    <h3 style="font-family:var(--wk-font-display);font-size:1.25rem;line-height:1.25;margin:.5rem 0">radial-gradient(ink 1.2px) / 18px</h3>
    <p style="font-size:.875rem;line-height:1.625;color:color-mix(in oklab,var(--wk-ink) 70%,transparent);margin:0">Both textures are CSS-only — no image files. bg-grid is 32px at 8% ink.</p>
  </div></div>
</div></section>
<section><h2>Motion</h2><div class="grid">
  ${Object.keys(tokens.motion.keyframes)
    .map(
      (k) =>
        `<div class="sw"><i class="box" style="animation:${k} ${
          { wiggle: ".9s", wobble: "3s", float: "5s", "spin-slow": "12s", "notif-pop": "5s", "shape-burst": "5s" }[k]
        } ${k === "spin-slow" ? "linear" : "ease-in-out"} infinite;background:var(--wk-yellow)"></i><b>${k}</b><span>${tokens.motion.keyframes[k].evidence ?? ""}</span></div>`
    )
    .join("\n")}
</div></section>
<section><h2>Rules</h2><div class="two">
  <ul class="rules">${tokens.rule.principles.map((r) => `<li><b>${r.name}.</b> ${r.detail}</li>`).join("")}</ul>
  <ul class="rules">${tokens.rule.doNot.map((r) => `<li><b>✗ ${r.dont}</b><br>✓ ${r.instead}</li>`).join("")}</ul>
</div>
  <p class="kv" style="margin-top:1rem">Source of truth: tokens/tokens.json · ${tokens.$meta.fidelity}</p>
</section>
</div></body></html>`;

writeFileSync(join(D, "standalone.html"), html);
console.log(`✓ artifacts/standalone.html (${(html.length / 1024).toFixed(1)} kB, self-contained)`);
