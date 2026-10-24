#!/usr/bin/env node
/**
 * build-tokens.mjs - compile tokens/fieldnotes.tokens.json into
 * artifacts/fieldnotes.css, the custom-property layer the site links.
 *
 *   node design-system/tools/build-tokens.mjs
 *
 * The token file is the only source. Every value the site paints with comes
 * through here, so a value that is not in the token file cannot reach the page.
 *
 * Two things are deliberate.
 *
 * No @font-face is emitted. Fieldnotes ships system fonts only, which is what
 * the family's reference site does. The Wakeout token set this replaced paid
 * 48,628 B of woff2 for two faces, 68% of a cold first visit, and the owner
 * chose to drop them on 2026-10-24.
 *
 * No Tailwind bridge. The repo forbids Tailwind, so there is no preset, no
 * @theme block and no generated utility classes. This emits variables and
 * nothing else.
 */
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const TOKENS = JSON.parse(readFileSync(join(ROOT, "tokens/fieldnotes.tokens.json"), "utf8"));
const DIST = join(ROOT, "artifacts");
mkdirSync(DIST, { recursive: true });

/* ---------------------------------------------------------------- naming */
const GROUP_PREFIX = {
  "color.primitive": "",
  "color.status": "status",
  "color.tag": "tag",
  "color.semantic": "",
  "typography.fontFamily": "font",
  "typography.fontWeight": "weight",
  "typography.fontSize": "text",
  "typography.lineHeight": "leading",
  "typography.letterSpacing": "tracking",
  "dimension.space": "space",
  "dimension.radius": "radius",
  "dimension.borderWidth": "border",
  "dimension.container": "container",
  "elevation": "shadow",
  "motion.duration": "duration",
  "motion.easing": "ease",
  "motion.press": "press",
  "motion.lift": "lift",
  "component.hero": "hero",
};

/** Keys that are documentation, not tokens. */
const NOT_A_TOKEN = new Set(["value", "evidence", "meaning", "inferred"]);

function varName(group, key) {
  const prefix = GROUP_PREFIX[group];
  return "--fn-" + (prefix ? prefix + "-" : "") + key;
}

/* ------------------------------------------------------------ references */
const REF_RE = /\{([a-zA-Z0-9._-]+)\}/;

/** Every literal, addressed by dotted path: "color.primitive.ink" -> "#11142B". */
const literals = new Map();
(function collect(node, path) {
  if (!node || typeof node !== "object") return;
  if (typeof node.value === "string") literals.set(path.join("."), node.value);
  for (const [key, child] of Object.entries(node)) {
    if (key === "$meta") continue;
    collect(child, [...path, key]);
  }
})(TOKENS, []);

let unresolved = [];
function resolve(value, seen = new Set()) {
  let out = value;
  let guard = 0;
  while (REF_RE.test(out) && guard++ < 8) {
    const path = out.match(REF_RE)[1];
    if (seen.has(path)) break;
    seen.add(path);
    const lit = literals.get(path);
    if (lit === undefined) { unresolved.push(path); return out; }
    out = out.replace(REF_RE, lit);
  }
  return out;
}

/* ------------------------------------------------------------------- emit */
const lines = [];
lines.push(`/*! Fieldnotes Design System - generated, do not edit.`);
lines.push(`    Source: design-system/tokens/fieldnotes.tokens.json`);
lines.push(`    Built by design-system/tools/build-tokens.mjs`);
lines.push(`    Origin: ${TOKENS.$meta.source} (${TOKENS.$meta.capturedAt})`);
lines.push(`    System fonts only: no @font-face is emitted, by design. */`);
lines.push(``);
lines.push(`:root {`);

const emitted = [];

/** The longest prefix of `path` that names a known group, or null. */
function knownPrefix(path) {
  for (let n = path.length; n > 0; n--) {
    const candidate = path.slice(0, n).join(".");
    if (candidate in GROUP_PREFIX) return { group: candidate, rest: path.slice(n) };
  }
  return null;
}

/**
 * Walk the whole tree. A node holding a string `value` is a token, and its
 * name comes from the longest known group above it: "color.status.live.bg"
 * sits under "color.status", so it becomes --fn-status-live-bg. That is what
 * lets status pairs nest a level deeper than the primitives without a
 * special case.
 */
(function walk(node, path) {
  if (!node || typeof node !== "object") return;

  if (typeof node.value === "string") {
    const hit = knownPrefix(path);
    if (hit && hit.rest.length) {
      const name = varName(hit.group, hit.rest.join("-"));
      lines.push(`  ${name}: ${resolve(node.value)};`);
      emitted.push(name);
    }
    return;
  }

  for (const [key, child] of Object.entries(node)) {
    if (key === "$meta" || NOT_A_TOKEN.has(key)) continue;
    walk(child, [...path, key]);
  }
})(TOKENS, []);


lines.push(``);
lines.push(`  /* aliases - what a browser needs that the primitives do not name */`);
lines.push(`  --fn-font-body: var(--fn-font-prose);`);
lines.push(`  --fn-font-display: var(--fn-font-mono);`);
lines.push(`}`);

const css = lines.join("\n") + "\n";
writeFileSync(join(DIST, "fieldnotes.css"), css);

console.log(`fieldnotes.css: ${emitted.length} tokens, ${css.length} B`);
if (unresolved.length) {
  console.error(`unresolved references: ${[...new Set(unresolved)].join(", ")}`);
  process.exit(1);
}
