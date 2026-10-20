#!/usr/bin/env node
/**
 * contrast.mjs — measure every foreground/background pair the system approves,
 * using the actual extracted hex values. Writes ref/contrast.json for the docs.
 * WCAG 2.1 relative luminance + ratio.
 */
import { readFileSync, writeFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const T = JSON.parse(readFileSync(join(ROOT, "tokens/tokens.json"), "utf8"));

function parse(c) {
  c = c.trim();
  if (c.startsWith("#")) {
    let h = c.slice(1);
    if (h.length === 3 || h.length === 4) h = h.split("").map((x) => x + x).join("");
    const a = h.length === 8 ? parseInt(h.slice(6, 8), 16) / 255 : 1;
    return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16), a];
  }
  const m = c.match(/rgba?\(([^)]+)\)/);
  if (m) {
    const p = m[1].split(/[\s,/]+/).filter(Boolean).map(Number);
    return [p[0], p[1], p[2], p[3] ?? 1];
  }
  return null;
}
const lum = ([r, g, b]) => {
  const f = (v) => {
    v /= 255;
    return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
};
function ratio(fgStr, bgStr) {
  const bg = parse(bgStr);
  let fg = parse(fgStr);
  if (!bg || !fg) return null;
  if (fg[3] < 1) {
    const a = fg[3];
    fg = [fg[0] * a + bg[0] * (1 - a), fg[1] * a + bg[1] * (1 - a), fg[2] * a + bg[2] * (1 - a), 1];
  }
  const L1 = lum(fg),
    L2 = lum(bg);
  return +(((Math.max(L1, L2) + 0.05) / (Math.min(L1, L2) + 0.05))).toFixed(2);
}
const grade = (r) => (r === null ? "n/a" : r >= 7 ? "AAA" : r >= 4.5 ? "AA" : r >= 3 ? "AA-large" : "fail");

/** resolve {a.b.c} refs so semantic tokens can be measured */
function lit(v) {
  if (typeof v !== "string") return v;
  let out = v, g = 0;
  while (/\{[a-zA-Z0-9.$-]+\}/.test(out) && g++ < 8)
    out = out.replace(/\{([a-zA-Z0-9.$-]+)\}/g, (_, p) => {
      let c = T;
      for (const s2 of p.split(".")) c = c?.[s2];
      return String(typeof c === "object" ? c?.value : c) ?? "";
    });
  return out;
}
const P = T.color.primitive,
  S = T.color.semantic;
const surfaces = {
  paper: P.paper.value,
  surface: "#ffffff",
  muted: P.muted.value,
  lime: P.lime.value,
  pink: P.pink.value,
  yellow: P.yellow.value,
  cyan: P.cyan.value,
  orange: P.orange.value,
  ember: P.ember.value,
  purple: P.purple.value,
  ink: P.ink.value,
  stage: P.stage.value,
  dusk: P.dusk.value,
  sunrise: P.sunrise.value,
  "orange-soft": P["orange-soft"].value,
};
const inks = {
  ink: P.ink.value,
  "ink/85": "rgba(4,54,41,.85)",
  "ink/70": "rgba(4,54,41,.7)",
  "ink/60": "rgba(4,54,41,.6)",
  paper: P.paper.value,
  "paper/80": "rgba(255,248,230,.8)",
  white: "#ffffff",
  "muted-foreground": P["muted-foreground"].value,
  "ink-morning": P["ink-morning"].value,
  purple: P.purple.value,
  "lime-deep": P["lime-deep"].value,
  "ember-deep": P["ember-deep"].value,
  red: P.red.value,
};

const pairs = [];
for (const [sb, sv] of Object.entries(surfaces))
  for (const [sn, snv] of Object.entries(inks)) {
    const r = ratio(snv, sv);
    pairs.push({ surface: sb, ink: sn, ratio: r, grade: grade(r), fg: snv, bg: sv });
  }

/* the specific pairs the system actually ships as semantic roles */
const approved = [
  ["foreground on background", lit(S.foreground.value), lit(S.background.value)],
  ["--wk-primary-foreground on --wk-primary", "#043629", "#68be00"],
  ["--wk-secondary-foreground on --wk-secondary", "#043629", "#f66f8e"],
  ["--wk-accent-foreground on --wk-accent", "#fff8e6", "#8a38f5"],
  ["--wk-muted-foreground on --wk-muted", "#3f5c52", "#f3ead3"],
  ["--wk-surface-foreground on --wk-surface", "#043629", "#ffffff"],
  ["paper on ink (inverse surfaces)", "#fff8e6", "#043629"],
  ["paper/80 on ink (body copy on ink)", "rgba(255,248,230,.8)", "#043629"],
  ["ink on yellow sticker", "#043629", "#ffc629"],
  ["ink/70 eyebrow on paper", "rgba(4,54,41,.7)", "#fff8e6"],
  ["ink/60 on paper", "rgba(4,54,41,.6)", "#fff8e6"],
  ["white/50 on ink (dark panel meta)", "rgba(255,255,255,.5)", "#043629"],
  ["purple link on paper", "#8a38f5", "#fff8e6"],
  ["ember text on paper", "#ff6b3e", "#fff8e6"],
  ["lime-deep text on paper", "#498500", "#fff8e6"],
  ["red destructive on paper", "#e5484d", "#fff8e6"],
  ["red destructive on white", "#e5484d", "#ffffff"],
].map(([name, fg, bg]) => {
  const r = ratio(fg, bg);
  return { name, fg, bg, ratio: r, grade: grade(r), aaLarge: r >= 3, aa: r >= 4.5, aaa: r >= 7 };
});

// no timestamp: byte-for-byte reproducible from tokens/tokens.json
const out = { source: "tokens/tokens.json", standard: "WCAG 2.1 relative luminance", approved, fullMatrix: pairs };
writeFileSync(join(ROOT, "ref/contrast.json"), JSON.stringify(out, null, 2));

const fails = approved.filter((a) => !a.aa);
console.log(`✓ contrast: ${approved.length} approved pairs, ${approved.length - fails.length} pass AA(4.5:1)`);
for (const f of fails) console.log(`  ⚠ ${f.name}: ${f.ratio}:1 (${f.grade})`);
