#!/usr/bin/env node
/**
 * build-tokens.mjs — compile tokens/tokens.json into everything else.
 *
 *   artifacts/wakeout.css            custom properties (--wk-*) + @font-face + base layer
 *   artifacts/wakeout.theme.css      Tailwind v4 @theme inline bridge + generated component classes
 *   artifacts/tokens.dtcg.json       W3C Design Tokens (Figma / Tokens Studio import)
 *   artifacts/tokens.js              ESM object for CSS-in-JS / charts
 *   artifacts/tailwind.preset.cjs    Tailwind v3 preset for legacy consumers
 *   artifacts/manifest.json          what was generated, from what
 */
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { execSync } from "node:child_process";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const TOKENS = JSON.parse(readFileSync(join(ROOT, "tokens/tokens.json"), "utf8"));
const DIST = join(ROOT, "artifacts");
mkdirSync(DIST, { recursive: true });

/* ---------------------------------------------------------------- naming */
const GROUP_PREFIX = {
  "color.primitive": "wk",
  "color.semantic": "wk",
  "typography.fontFamily": "wk-font",
  "typography.fontWeight": "wk-weight",
  "typography.fontSize": "wk-text",
  "typography.lineHeight": "wk-leading",
  "typography.letterSpacing": "wk-tracking",
  "dimension.space": "wk-space",
  "dimension.radius": "wk-radius",
  "dimension.borderWidth": "wk-border",
  "dimension.container": "wk-container",
  "dimension.aspect": "wk-aspect",
  "dimension.blur": "wk-blur",
  "elevation": "wk-shadow",
  "motion.duration": "wk-duration",
  "motion.easing": "wk-ease",
  "motion.tilt": "wk-tilt",
  "color.gradient": "wk-gradient",
  "color.texture": "wk-texture",
};
const OVERRIDE = {
  "dimension.base.spacing": "--wk-space-unit",
  "motion.lift": "--wk-lift",
  "motion.transition.interactive": "--wk-ease-interactive",
};
const SKIP = new Set(["$meta", "component", "rule", "alphaSteps", "base", "note", "styles", "fontStyle"]);
const NO_VAR = new Set(["motion.keyframes", "motion.accessibility", "color.gradient", "color.texture"]);
const NON_TOKEN = new Set(["value", "usage", "evidence", "note", "role", "inferred", "fallbacks", "offset", "size", "paint", "background", "ink", "css", "class", "variants", "padding", "tilt", "overlay", "knob", "lights", "container", "states", "variant", "size", "base", "responsive", "marginBottom", "textTransform", "fontFamily", "fontSize", "lineHeight", "letterSpacing", "fontWeight", "color", "border", "shadow", "reducedMotion", "accessibility", "transition", "lift", "press", "keyframes", "easing", "duration", "title"]);

const flat = new Map(); // "color.primitive.ink" -> {value, meta}
const cssVarOf = new Map(); // path -> --wk-name

function walk(obj, path) {
  for (const [k, v] of Object.entries(obj)) {
    if (k.startsWith("$") || SKIP.has(path.length === 1 ? "" : "")) {
      /* handled below */
    }
    const p = [...path, k.replace(/\./g, "-")].join(".");
    if (v && typeof v === "object" && !Array.isArray(v)) {
      if ("value" in v && !NO_VAR.has(path.join("."))) {
        flat.set(p, v);
        cssVarOf.set(p, "--" + varNameFor(p, k));
      } else walk(v, [...path, k]);
    } else if (typeof v === "string" || typeof v === "number") {
      // leaf groups like elevation.offset or color.texture.*.value already covered
    }
  }
}
function varNameFor(path, key) {
  if (OVERRIDE[path]) return OVERRIDE[path].slice(2);
  const group = path.split(".").slice(0, -1).join(".");
  const prefix = GROUP_PREFIX[group];
  const g = group.startsWith("color.") ? "wk" : prefix;
  return `${g}-${key}`
    .replace(/\./g, "-")
    .replace(/([a-z])([A-Z])/g, "$1-$2")
    .toLowerCase();
}
walk(TOKENS, []);

/* surfaceTheme / gradient / texture / component extras need explicit vars too */
const extra = [];
for (const [name, t] of Object.entries(TOKENS.color.surfaceTheme)) {
  extra.push([`--wk-surface-${name}`, t.paint]);
  extra.push([`--wk-surface-${name}-foreground`, t.ink]);
}
for (const [name, g] of Object.entries(TOKENS.color.gradient))
  extra.push([`--wk-gradient-${name}`, g.value]);
for (const [name, tx] of Object.entries(TOKENS.color.texture)) {
  extra.push([`--wk-texture-${name}`, tx.value]);
  extra.push([`--wk-texture-${name}-size`, tx.size]);
}
extra.push(["--wk-press-x", TOKENS.motion.press.x]);
extra.push(["--wk-press-y", TOKENS.motion.press.y]);
extra.push(["--wk-radius", "var(--wk-radius-lg)"]);

/* ---------------------------------------------------------- ref resolution */
const REF_RE = /\{([a-zA-Z0-9.$-]+)\}/g;
function resolvePath(p) {
  let cur = TOKENS;
  for (const seg of p.split(".")) {
    cur = cur?.[seg];
    if (cur === undefined) return undefined;
  }
  return typeof cur === "object" && cur !== null && "value" in cur ? cur.value : cur;
}
/** refs -> literal (for JS/JSON) */
function literals(v) {
  if (typeof v !== "string") return v;
  let out = v,
    guard = 0;
  while (REF_RE.test(out) && guard++ < 8)
    out = out.replace(REF_RE, (_, p) => String(literals(resolvePath(p)) ?? ""));
  return out;
}
/** refs -> var() chain (for CSS); keeps indirection so themes can override */
function varFor(p) {
  return cssVarOf.get(p) ?? cssVarOf.get(p.replace(/\.value$/, "")) ?? null;
}
function toCss(v) {
  if (typeof v !== "string") return String(v);
  const whole = v.match(/^\{([a-zA-Z0-9.$-]+)\}$/);
  if (whole) {
    const name = varFor(whole[1]);
    if (name) return `var(${name})`;
    return String(literals(resolvePath(whole[1])) ?? "");
  }
  let out = v,
    guard = 0;
  while (out.match(REF_RE) && guard++ < 8)
    out = out.replace(REF_RE, (_, p) => {
      const name = varFor(p);
      return name ? `var(${name})` : String(literals(resolvePath(p)) ?? "");
    });
  return out;
}

/* --------------------------------------------------------------- wakeout.css */
const lines = [
  "/* Generated by tools/build-tokens.mjs — DO NOT EDIT.",
  `   Source: tokens/tokens.json (extracted from ${TOKENS.$meta.reference}) */`,
  "",
  "@font-face{",
  '  font-family:"Fredoka";font-style:normal;font-weight:400 700;font-display:swap;',
  "  src:url('/fonts/fredoka-latin.woff2') format('woff2'),",
  "      url('/fonts/fredoka-latin-ext.woff2') format('woff2');",
  "}",
  "@font-face{",
  '  font-family:"Space Grotesk";font-style:normal;font-weight:300 700;font-display:swap;',
  "  src:url('/fonts/space-grotesk-latin.woff2') format('woff2'),",
  "      url('/fonts/space-grotesk-latin-ext.woff2') format('woff2');",
  "}",
  "",
  ":root{",
];
const groups = {};
for (const [p, tok] of flat) {
  const g = p.split(".").slice(0, -1).join(".");
  (groups[g] ??= []).push([p, tok]);
}
const ORDER = [
  ["color.primitive", "brand primitives"],
  ["color.semantic", "semantic aliases"],
  ["typography.fontFamily", "typefaces"],
  ["typography.fontWeight", "weights"],
  ["typography.fontSize", "sizes"],
  ["typography.lineHeight", "leading"],
  ["typography.letterSpacing", "tracking"],
  ["dimension.base", "spacing unit"],
  ["dimension.space", "spacing (index × 4px)"],
  ["dimension.radius", "radius"],
  ["dimension.borderWidth", "border widths"],
  ["dimension.container", "containers"],
  ["dimension.aspect", "aspect ratios"],
  ["dimension.blur", "blur"],
  ["elevation", "elevation = hard ink offset"],
  ["motion.duration", "durations"],
  ["motion.easing", "easing"],
  ["motion.transition", "interaction transition"],
  ["motion.tilt", "tilt"],
  ["motion", "interaction offsets"],
];
for (const [g, label] of ORDER) {
  if (!groups[g]) continue;
  lines.push(`  /* ${label} */`);
  for (const [p, tok] of groups[g]) {
    const note = tok.usage ? ` /* ${tok.usage}× in 15 sampled pages */` : "";
    let val = toCss(tok.value);
    if (g === "typography.fontFamily" && Array.isArray(tok.fallbacks) && tok.fallbacks.length)
      val += ", " + tok.fallbacks.filter((f) => !f.endsWith("Fallback")).join(", ");
    lines.push(`  ${cssVarOf.get(p)}: ${val};${note}`);
  }
}
lines.push("  /* surfaces / textures / gradients */");
for (const [k, v] of extra) lines.push(`  ${k}: ${toCss(v)};`);
lines.push(
  "}",
  "",
  "/* base layer, as extracted: body paints the surface, ink is the default text */",
  "html{background:var(--wk-background);-webkit-text-size-adjust:100%;-webkit-tap-highlight-color:transparent}",
  "body{background:var(--wk-background);color:var(--wk-foreground);font-family:var(--wk-font-body),var(--wk-font-cjk,ui-sans-serif),ui-sans-serif,system-ui,sans-serif;line-height:1.5}",
  ":focus-visible{outline:none;box-shadow:0 0 0 4px var(--wk-focus-ring)}",
  "@media (prefers-reduced-motion: reduce){*,*::before,*::after{animation-duration:.001ms!important;animation-iteration-count:1!important;transition-duration:.001ms!important}}",
  ""
);
writeFileSync(join(DIST, "wakeout.css"), lines.join("\n"));

/* ----------------------------------------------------------- wakeout.theme.css */
const t = TOKENS.typography;
const display = t.fontFamily.display;
const theme = [
  "/* Generated by tools/build-tokens.mjs — Tailwind v4 bridge over --wk-* tokens. */",
  "@import './wakeout.css';",
  "",
  "@theme inline{",
  "  /* palette */",
];
for (const [p, tok] of groups["color.primitive"] || [])
  theme.push(`  --color-${p.split(".").pop()}: var(${cssVarOf.get(p)});`);
for (const [p, tok] of groups["color.semantic"] || []) {
  const key = p.split(".").pop();
  if (["background", "foreground", "surface", "border", "ring", "muted", "accent", "card"].includes(key)) continue;
  theme.push(`  --color-${key}: var(${cssVarOf.get(p)});`);
}
theme.push("  --color-background: var(--wk-background);");
theme.push("  --color-foreground: var(--wk-foreground);");
theme.push("  --color-surface: var(--wk-surface);");
theme.push("  --color-popover: var(--wk-popover);");
theme.push("  --color-card: var(--wk-surface);");
theme.push(
  "  --color-border: var(--wk-border);",
  "  --color-ring: var(--wk-ring);",
  "  --color-input: var(--wk-input);",
  "",
  "  /* type */",
  `  --font-sans: var(--wk-font-body);`,
  `  --font-mono: var(--wk-font-mono);`,
  `  --default-font-family: var(--wk-font-body);`
);
for (const [p, tok] of groups["typography.fontWeight"] || [])
  theme.push(`  --font-weight-${p.split(".").pop()}: var(${cssVarOf.get(p)});`);
for (const [p, tok] of groups["typography.fontSize"] || []) {
  const key = p.split(".").pop();
  theme.push(`  --text-${key}: var(${cssVarOf.get(p)});`);
  if (tok.lineHeight !== undefined)
    theme.push(`  --text-${key}--line-height: ${toCss(String(tok.lineHeight))};`);
  if (tok.letterSpacing !== undefined)
    theme.push(`  --text-${key}--letter-spacing: ${toCss(tok.letterSpacing)};`);
  if (tok.fontWeight !== undefined)
    theme.push(`  --text-${key}--font-weight: ${tok.fontWeight};`);
}
for (const [p, tok] of groups["typography.lineHeight"] || [])
  theme.push(`  --leading-${p.split(".").pop()}: var(${cssVarOf.get(p)});`);
for (const [p, tok] of groups["typography.letterSpacing"] || [])
  theme.push(`  --tracking-${p.split(".").pop()}: var(${cssVarOf.get(p)});`);
theme.push("", "  /* spacing + size */", `  --spacing: ${TOKENS.dimension.base.spacing.value};`);
for (const [p, tok] of groups["dimension.space"] || [])
  theme.push(`  --spacing-${p.split(".").pop()}: var(${cssVarOf.get(p)});`);
for (const [p, tok] of groups["dimension.radius"] || [])
  theme.push(`  --radius-${p.split(".").pop()}: var(${cssVarOf.get(p)});`);
for (const [p, tok] of groups["dimension.container"] || [])
  theme.push(`  --container-${p.split(".").pop()}: var(${cssVarOf.get(p)});`);
for (const [p, tok] of groups["dimension.aspect"] || [])
  theme.push(`  --aspect-${p.split(".").pop()}: var(${cssVarOf.get(p)});`);
for (const [p, tok] of groups["dimension.blur"] || [])
  theme.push(`  --blur-${p.split(".").pop()}: var(${cssVarOf.get(p)});`);
theme.push("", "  /* elevation */");
for (const [p, tok] of groups["elevation"] || []) {
  const key = p.split(".").pop();
  if (key === "note") continue;
  theme.push(`  --shadow-${key}: var(${cssVarOf.get(p)});`);
}
theme.push("", "  /* motion */");
for (const [p, tok] of groups["motion.duration"] || [])
  theme.push(`  --duration-${p.split(".").pop()}: var(${cssVarOf.get(p)});`);
for (const [p, tok] of groups["motion.easing"] || [])
  theme.push(`  --ease-${p.split(".").pop()}: var(${cssVarOf.get(p)});`);
theme.push("  --default-transition-duration: var(--wk-duration-quick);");
theme.push("  --default-transition-timing-function: var(--wk-ease-out);");
for (const [name, kf] of Object.entries(TOKENS.motion.keyframes)) {
  const dur = {
    wiggle: "900ms",
    wobble: "3s",
    float: "5s",
    "spin-slow": "12s",
    "notif-pop": "5s",
    "shape-burst": "5s",
  }[name];
  const ease = name === "spin-slow" ? "linear" : "ease-in-out";
  theme.push(`  --animate-${name}: ${name} ${dur} ${ease} infinite;`);
}
theme.push("}", "", "/* keyframes copied verbatim from the reference stylesheet */");
for (const [name, kf] of Object.entries(TOKENS.motion.keyframes))
  theme.push(`@keyframes ${name}{${typeof kf === "object" ? kf.value : kf}}`);

/* brand utilities + generated component classes */
theme.push(
  "",
  "@utility border-3{border-width:var(--wk-border-base)}",
  "@utility border-t-3{border-top-width:var(--wk-border-base)}",
  "@utility border-b-3{border-bottom-width:var(--wk-border-base)}",
  "@utility border-x-3{border-inline-width:var(--wk-border-base)}",
  "@utility border-2px{border-width:var(--wk-border-thin)}",
  "@utility border-4px{border-width:var(--wk-border-thick)}",
  "@utility bg-dots{background-image:var(--wk-texture-dots);background-size:var(--wk-texture-dots-size)}",
  "@utility bg-grid{background-image:var(--wk-texture-grid);background-size:var(--wk-texture-grid-size)}",
  "@utility bg-energy{background-image:var(--wk-gradient-energy)}",
  "@utility bg-sunrise{background-color:#ffe7d2;background-image:linear-gradient(180deg,#fff1e3 0%,#ffe7d2 100%)}",
  "@utility bg-dusk{background-color:#331c45;background-image:linear-gradient(180deg,#331c45 0%,#221230 100%)}",
  "@utility lift{transform:translateY(var(--wk-lift))}",
  `@utility font-display{font-family:var(--wk-font-display);font-weight:${display.impliedWeight};letter-spacing:${display.impliedLetterSpacing}}`,
  "@utility font-body{font-family:var(--wk-font-body)}",
  "@utility font-app-ui{font-family:var(--wk-font-display);font-weight:500;letter-spacing:0em}",
  ""
);
theme.push("/* generated component classes — for non-React consumers of the system */");
const C = TOKENS.component;
const press = TOKENS.motion.press;
theme.push(
  `.wk-button{display:inline-flex;align-items:center;justify-content:center;gap:var(--wk-space-2);`,
  `  font-family:var(--wk-font-display);font-weight:var(--wk-weight-bold);letter-spacing:var(--wk-tracking-wide);`,
  `  border:var(--wk-border-base) solid var(--wk-ink);border-radius:var(--wk-radius-2xl);`,
  `  box-shadow:var(--wk-shadow-sticker);background:var(--wk-surface);color:var(--wk-ink);`,
  `  padding:var(--wk-space-3) var(--wk-space-6);font-size:var(--wk-text-body);cursor:pointer;user-select:none;`,
  `  transition:var(--wk-ease-interactive);text-decoration:none}`,
  `.wk-button:hover{transform:translateY(var(--wk-lift)) rotate(-1deg);box-shadow:var(--wk-shadow-sticker-lg)}`,
  `.wk-button:active{transform:translate(${press.x},${press.y});box-shadow:var(--wk-shadow-sticker-sm)}`,
  `.wk-button:focus-visible{outline:none;box-shadow:0 0 0 4px var(--wk-focus-ring),var(--wk-shadow-sticker)}`,
  `.wk-button[disabled]{opacity:.5;box-shadow:none;transform:none;cursor:not-allowed}`
);
for (const [name, v] of Object.entries(C.button.variant))
  theme.push(
    `.wk-button--${name}{background:${toCss(v.background)};color:${toCss(v.color)}${
      v.border === "none" ? ";border-color:transparent;box-shadow:none" : ""
    }}`
  );
for (const [name, s] of Object.entries(C.button.size))
  theme.push(`.wk-button--${name}{padding:${literals(s.padding)};font-size:${literals(s.fontSize)}}`);
theme.push(
  `.wk-button--pill{border-radius:var(--wk-radius-full)}`,
  `.wk-card{border:var(--wk-border-base) solid var(--wk-ink);border-radius:var(--wk-radius-3xl);`,
  `  background:var(--wk-surface);box-shadow:var(--wk-shadow-sticker);overflow:hidden}`,
  `.wk-card__body{padding:var(--wk-space-6)}`,
  `.wk-pill{display:inline-flex;align-items:center;gap:var(--wk-space-2);padding:var(--wk-space-2) var(--wk-space-6);`,
  `  border:var(--wk-border-base) solid var(--wk-ink);border-radius:var(--wk-radius-full);background:var(--wk-yellow);`,
  `  box-shadow:var(--wk-shadow-sticker-sm);font-size:var(--wk-text-caption);font-weight:var(--wk-weight-bold);`,
  `  text-transform:uppercase;letter-spacing:var(--wk-tracking-widest);transform:rotate(-6deg)}`,
  `.wk-chip{display:inline-flex;padding:var(--wk-space-1) var(--wk-space-2);border:1px solid color-mix(in oklab,var(--wk-ink) 20%,transparent);`,
  `  border-radius:var(--wk-radius-full);font-size:var(--wk-text-eyebrow);font-weight:var(--wk-weight-bold);`,
  `  text-transform:uppercase;letter-spacing:var(--wk-tracking-widest);color:color-mix(in oklab,var(--wk-ink) 70%,transparent)}`,
  `.wk-eyebrow{display:flex;align-items:center;gap:var(--wk-space-2);font-size:var(--wk-text-caption);`,
  `  font-weight:var(--wk-weight-bold);text-transform:uppercase;letter-spacing:var(--wk-tracking-widest);`,
  `  color:color-mix(in oklab,var(--wk-ink) 70%,transparent)}`,
  `.wk-bg-dots{background-image:var(--wk-texture-dots);background-size:var(--wk-texture-dots-size)}`,
  `.wk-bg-grid{background-image:var(--wk-texture-grid);background-size:var(--wk-texture-grid-size)}`,
  `.wk-bg-energy{background-image:var(--wk-gradient-energy)}`,
  ""
);
writeFileSync(join(DIST, "wakeout.theme.css"), theme.join("\n"));

/* --------------------------------------------------------------- dtcg json */
const dtcg = { $description: `Generated from ${TOKENS.$meta.reference} ${TOKENS.$meta.capturedAt}` };
function toDtcg(obj, bucket) {
  for (const [k, v] of Object.entries(obj)) {
    if (SKIP.has(k)) continue;
    if (k === "$meta") continue;
    if (v && typeof v === "object" && !Array.isArray(v)) {
      if ("value" in v) {
        bucket[k] = {
          value: typeof v.value === "string" && v.value.startsWith("{") ? v.value : literals(v.value),
          type: inferType(k, v.value, literals(v.value)),
          ...(v.evidence ? { $extensions: { "wakeout.evidence": v.evidence, ...(v.usage ? { "wakeout.usage": v.usage } : {}) } } : {}),
        };
        if (v.description || v.note) bucket[k].description = v.note || v.description;
      } else {
        bucket[k] = {};
        toDtcg(v, bucket[k]);
      }
    }
  }
}
function inferType(key, raw, resolved) {
  if (typeof raw === "string" && raw.startsWith("{color.")) return "color";
  if (typeof resolved === "string") {
    if (/^#|^rgba?\(/.test(resolved) && key !== "focus-ring") return "color";
    if (/rem|px|em$/.test(resolved.trim())) return "dimension";
    if (/ms$|^cubic-bezier|^ease|^linear/.test(resolved.trim())) return /ms$/.test(resolved) ? "duration" : "cubicBezier";
    if (/^\d/.test(resolved.trim()) && /solid|gradient|radial/.test(resolved)) return "shadow";
    if (/^[0-9.]+$/.test(resolved.trim())) return "number";
  }
  return "other";
}
for (const g of ["color", "typography", "dimension", "elevation", "motion"]) {
  dtcg[g] = {};
  toDtcg(TOKENS[g], dtcg[g]);
}
writeFileSync(join(DIST, "tokens.dtcg.json"), JSON.stringify(dtcg, null, 2));

/* ------------------------------------------------------------------ tokens.js */
const jsTree = {};
for (const [p, tok] of flat) {
  const segs = p.split(".");
  // descend through the parents, then attach the leaf
  const parent = segs.slice(0, -1).reduce((o, s) => (o[s] ??= {}), jsTree);
  const cur = (parent[segs[segs.length - 1]] ??= {});
  cur.value = literals(tok.value);
  cur.cssVar = cssVarOf.get(p);
  if (tok.usage) cur.usage = tok.usage;
  if (tok.evidence) cur.evidence = tok.evidence;
  if (tok.note) cur.note = tok.note;
}
writeFileSync(
  join(DIST, "tokens.js"),
  `/* Generated by tools/build-tokens.mjs */\nexport const tokens = ${JSON.stringify(jsTree, null, 2)};\n\nexport const cssVar = (path) => path ? path.split(".").reduce((a,k)=>a?.[k],tokens)?.cssVar : undefined;\n`
);

/* --------------------------------------------------------- tailwind v3 preset */
const preset = {
  theme: {
    extend: {
      colors: Object.fromEntries(
        Object.entries(TOKENS.color.primitive).map(([k, v]) => [k, literals(v.value)])
      ),
      fontFamily: {
        display: [literals(TOKENS.typography.fontFamily.display.value), "ui-sans-serif", "system-ui"],
        body: [literals(TOKENS.typography.fontFamily.body.value), "ui-sans-serif", "system-ui"],
      },
      fontSize: Object.fromEntries(
        Object.entries(TOKENS.typography.fontSize).map(([k, v]) => [
          k,
          [literals(v.value), { lineHeight: String(v.lineHeight ?? 1.5), letterSpacing: v.letterSpacing ? literals(v.letterSpacing) : undefined }].filter(Boolean),
        ])
      ),
      borderRadius: Object.fromEntries(
        Object.entries(TOKENS.dimension.radius).map(([k, v]) => [k, literals(v.value)])
      ),
      borderWidth: Object.fromEntries(
        Object.entries(TOKENS.dimension.borderWidth).map(([k, v]) => [k, literals(v.value)])
      ),
      boxShadow: Object.fromEntries(
        Object.entries(TOKENS.elevation)
          .filter(([k]) => k !== "note" && k !== "offset")
          .map(([k, v]) => [k, literals(v.value)])
      ),
      spacing: Object.fromEntries(
        Object.entries(TOKENS.dimension.space).map(([k, v]) => [k, literals(v.value)])
      ),
      transitionDuration: Object.fromEntries(
        Object.entries(TOKENS.motion.duration).map(([k, v]) => [k, literals(v.value)])
      ),
      transitionTimingFunction: Object.fromEntries(
        Object.entries(TOKENS.motion.easing).map(([k, v]) => [k, literals(v.value)])
      ),
      keyframes: Object.fromEntries(
        Object.entries(TOKENS.motion.keyframes).map(([k, v]) => [
          k,
          Object.fromEntries(
            (typeof v === "object" ? v.value : v)
              .split(/}(?=\s*[\d,t])/)
              .map((sel) => {
                const m = sel.match(/^\s*([^%{,][^{]*?)\s*\{(.*)\}\s*$/s);
                return m ? [m[1].trim(), Object.fromEntries(m[2].split(";").filter(Boolean).map((d) => { const [p1, v1] = d.split(":"); return [p1.trim(), v1.trim()]; }))] : null;
              })
              .filter(Boolean)
          ),
        ])
      ),
      animation: Object.fromEntries(
        Object.keys(TOKENS.motion.keyframes).map((k) => [k, `${k} var(--wk-duration-loop,5s) ease-in-out infinite`])
      ),
    },
  },
};
writeFileSync(
  join(DIST, "tailwind.preset.cjs"),
  `/* Generated by tools/build-tokens.mjs — Tailwind v3 preset */\nmodule.exports = ${JSON.stringify(preset, (k, v) => (typeof v === "undefined" ? null : v), 2).replace(/: null/g, ": undefined")};\n`
);

/* ----------------------------------------------------------------- manifest */
const sourceSha = execSync(`shasum -a 256 "${join(ROOT, "tokens/tokens.json")}"`, { shell: "/bin/bash" })
  .toString()
  .split(" ")[0];
writeFileSync(
  join(DIST, "manifest.json"),
  JSON.stringify(
    {
      // deterministic on purpose: no timestamp, so a rebuild that changes nothing
      // changes nothing (integrity checks and CI diffs stay honest)
      sourceSha256: sourceSha,
      source: "tokens/tokens.json",
      reference: TOKENS.$meta.reference,
      tokenGroups: Object.fromEntries(Object.entries(groups).map(([g, arr]) => [g, arr.length])),
      totalTokens: flat.size,
      artifacts: ["wakeout.css", "wakeout.theme.css", "tokens.dtcg.json", "tokens.js", "tailwind.preset.cjs", "manifest.json"],
    },
    null,
    2
  )
);
console.log(`✓ ${flat.size} tokens → artifacts/ (${Object.keys(groups).length} groups)`);
