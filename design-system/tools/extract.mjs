#!/usr/bin/env node
/**
 * extract.mjs — mine a downloaded Next.js/Tailwind site for design-system evidence.
 *
 * Input : ref/main.css (the site's stylesheet) + ref/page-*.html (rendered HTML)
 * Output: ref/evidence.json (machine) + ref/REPORT.md (human)
 *
 * This only measures what is actually in the shipped CSS/HTML. No guessing.
 */
import { readFileSync, writeFileSync, readdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const REF = join(ROOT, "ref");
const css = readFileSync(join(REF, "main.css"), "utf8");
const htmlFiles = readdirSync(REF).filter(
  (f) => /^(page-|card-|raw)/.test(f) && f.endsWith(".html")
);
const htmls = htmlFiles.map((f) => [f, readFileSync(join(REF, f), "utf8")]);

const uniq = (a) => [...new Set(a)];
const count = (arr) => {
  const m = new Map();
  for (const x of arr) m.set(x, (m.get(x) || 0) + 1);
  return [...m.entries()].sort((a, b) => b[1] - a[1]);
};

/* ---------- 1. custom properties ---------- */
const customProps = {};
const blockRe = /(:root(?:\s*,\s*:host)?|\.dark|\[data-[^\]]*\])\s*\{([^}]*)\}/g;
let m;
while ((m = blockRe.exec(css))) {
  const sel = m[1].replace(/\s+/g, "");
  const body = m[2];
  const declRe = /(--[a-z0-9-]+)\s*:\s*([^;}]+)/g;
  let d;
  while ((d = declRe.exec(body))) {
    const name = d[1];
    const value = d[2].trim();
    if (!customProps[name]) customProps[name] = { value, selectors: [] };
    if (!customProps[name].selectors.includes(sel))
      customProps[name].selectors.push(sel);
  }
}

/* ---------- 2. @font-face ---------- */
const fontFaces = [];
const ffRe = /@font-face\s*\{([^}]*)\}/g;
while ((m = ffRe.exec(css))) {
  const b = m[1];
  const g = (k) => (b.match(new RegExp(k + ":([^;}]+)")) || [, ""])[1].trim();
  fontFaces.push({
    family: g("font-family").replace(/"/g, ""),
    style: g("font-style"),
    weight: g("font-weight"),
    stretch: g("font-stretch"),
    display: g("font-display"),
    unicodeRange: (b.match(/unicode-range:([^;}]+)/) || [, ""])[1].trim(),
  });
}

/* ---------- 3. @keyframes ---------- */
const keyframes = {};
const kfRe = /@keyframes\s+([a-zA-Z0-9_-]+)\s*\{/g;
while ((m = kfRe.exec(css))) {
  const name = m[1];
  let i = kfRe.lastIndex,
    depth = 1;
  while (i < css.length && depth > 0) {
    if (css[i] === "{") depth++;
    else if (css[i] === "}") depth--;
    i++;
  }
  keyframes[name] = css.slice(kfRe.lastIndex, i - 1).replace(/\s+/g, " ").trim();
}

/* ---------- 4. literal colors in CSS ---------- */
const hexRe = /#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b/g;
const funcColorRe = /\b(?:rgba?|hsla?|oklch|lab|color-mix)\([^)]{0,90}\)/g;
const cssColors = count(css.match(hexRe)?.concat(css.match(funcColorRe) || []) || []);

/* ---------- 5. utility-class usage in shipped HTML ---------- */
const classTokens = [];
for (const [, h] of htmls) {
  const attrRe = /\sclass="([^"]*)"/g;
  let c;
  while ((c = attrRe.exec(h))) {
    for (const t of c[1].split(/\s+/)) if (t) classTokens.push(t);
  }
}
const classCounts = count(classTokens);
const byPrefix = (re) =>
  classCounts.filter(([k]) => re.test(k)).slice(0, 60);

/* ---------- 6. raw declaration values for shape props ---------- */
const grab = (prop) =>
  count(
    [...css.matchAll(new RegExp(`(?:^|[;{])\\s*${prop}:([^;}]+)`, "g"))].map(
      (x) => x[1].trim()
    )
  ).slice(0, 40);

const report = {
  source: {
    cssBytes: css.length,
    htmlPages: htmls.length,
    classAttributeCount: classTokens.length,
  },
  customProps,
  fontFaces,
  keyframes,
  cssColorValues: cssColors.slice(0, 60),
  declarations: {
    borderRadius: grab("border-radius"),
    boxShadow: grab("box-shadow"),
    borderWidth: grab("border-width"),
    border: grab("border"),
    letterSpacing: grab("letter-spacing"),
    lineHeight: grab("line-height"),
    fontWeight: grab("font-weight"),
    textTransform: grab("text-transform"),
    transitionDuration: grab("transition-duration"),
    animation: grab("animation"),
    transform: grab("transform"),
    insetShadow: grab("box-shadow").filter(([v]) => v.includes("inset")),
  },
  usage: {
    font: byPrefix(/^(font-|text-\[)/),
    text: byPrefix(/^text-(xs|sm|base|lg|xl|\dxl)/),
    bg: byPrefix(/^bg-/),
    border: byPrefix(/^(border|ring)-/),
    radius: byPrefix(/^r/),
    shadow: byPrefix(/^shadow/),
    spacing: byPrefix(/^(p|m)([tblrxy])?-/),
    gap: byPrefix(/^gap-/),
    effects: byPrefix(/^(backdrop|blur|opacity|mix-blend|outline|rotate|translate|scale|skew|transition|duration|animate|drop-shadow|shadow)-?/),
    layout: byPrefix(/^(grid|flex|columns|aspect|object|max-w|min-w|w-|h-|container)/),
    top50: classCounts.slice(0, 50),
  },
};

writeFileSync(join(REF, "evidence.json"), JSON.stringify(report, null, 2));

/* ---------- human report ---------- */
const L = [];
const p = (s = "") => L.push(s);
p("# wakeout.app — extracted evidence");
p();
p(`CSS ${(css.length / 1024).toFixed(1)} kB · ${htmls.length} pages · ${classTokens.length} class tokens`);
p();
p("## Semantic brand tokens (from :root)");
for (const [k, v] of Object.entries(customProps)) {
  if (/^--(color-ink|color-paper|color-cream|color-lime|color-pink|color-purple|color-orange|color-cyan|color-sky|color-yellow|color-sun|color-ember|color-dusk|color-plum|color-red|color-sunrise|color-orange-soft|color-muted)/.test(k))
    p(`- \`${k}: ${v.value}\``);
}
p();
p("## shadcn-style aliases");
for (const [k, v] of Object.entries(customProps))
  if (/^--(background|foreground|card|popover|primary|secondary|muted|accent|destructive|border|input|ring|chart|sidebar|radius)/.test(k))
    p(`- \`${k}: ${v.value}\``);
p();
p("## Fonts");
for (const f of uniq(fontFaces.map((x) => x.family + " w" + x.weight + " " + x.style + " display:" + x.display))) p(`- ${f}`);
p();
p("## Keyframes");
for (const [k, v] of Object.entries(keyframes)) p(`- **${k}**: \`${v.slice(0, 300)}\``);
p();
p("## border-radius values in CSS");
for (const [v, n] of report.declarations.borderRadius) p(`- \`${v}\` ×${n}`);
p();
p("## box-shadow values in CSS");
for (const [v, n] of report.declarations.boxShadow) p(`- \`${v}\` ×${n}`);
p();
p("## letter-spacing / text-transform / font-weight");
for (const key of ["letterSpacing", "textTransform", "fontWeight"])
  p(`- ${key}: ${report.declarations[key].map(([v, n]) => `\`${v}\`×${n}`).join(", ")}`);
p();
p("## animation / transition");
for (const key of ["animation", "transitionDuration"])
  p(`- ${key}: ${report.declarations[key].slice(0, 20).map(([v, n]) => `\`${v}\`×${n}`).join(", ")}`);
p();
p("## most-used literal colors in CSS");
for (const [v, n] of report.cssColorValues.slice(0, 30)) p(`- \`${v}\` ×${n}`);
p();
p("## top utility classes in shipped HTML");
for (const [k, n] of report.usage.top50) p(`- \`${k}\` ×${n}`);
p();
p("## bg-* usage");
for (const [k, n] of report.usage.bg.slice(0, 40)) p(`- \`${k}\` ×${n}`);
p();
p("## text size usage");
for (const [k, n] of report.usage.text.slice(0, 30)) p(`- \`${k}\` ×${n}`);
p();
p("## radius / shadow / border usage");
for (const key of ["radius", "shadow", "border", "gap", "spacing"])
  p(`- ${key}: ${report.usage[key].slice(0, 22).map(([k, n]) => `\`${k}\`×${n}`).join(" ")}`);
p();
p("## font-* usage");
for (const [k, n] of report.usage.font.slice(0, 25)) p(`- \`${k}\` ×${n}`);

writeFileSync(join(REF, "REPORT.md"), L.join("\n"));
console.log(L.join("\n"));
