// Tests for the progress rules in site/static/progress.js.
//   node --test tools/sitegen/tests/progress.test.js
// Uses the real path manifest from the built home page (run sitegen.py first).
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const ROOT = path.resolve(__dirname, "../../..");
const P = require(path.join(ROOT, "site/static/progress.js"));

function manifest() {
  const html = fs.readFileSync(path.join(ROOT, "_site/index.html"), "utf8");
  return JSON.parse(html.match(/<script type="application\/json" id="hr-path">([\s\S]*?)<\/script>/)[1]);
}
const m = manifest();
const keys = m.weeks.flatMap((w) => w[2]);
const fresh = () => P.parse("");
const tick = (s, k) => P.setDone(s, k, true, 1);

test("a first visit has no progress and no next block", () => {
  const s = fresh();
  assert.deepEqual(s.done, {});
  assert.equal(P.next(m, s), null);
  const sum = P.summary(m, s);
  assert.equal(sum.any, false);
  assert.equal(sum.blocks, 0);
});

test("unreadable, foreign or future-version storage reads as a first visit", () => {
  for (const raw of ["{", "null", "42", '"x"', "[]", '{"v":2,"done":{"w0-r1":1}}',
                     '{"v":1}', '{"v":1,"done":"w0-r1"}', undefined, null]) {
    assert.deepEqual(P.parse(raw).done, {}, String(raw));
  }
});

test("only ticks we wrote are kept from storage", () => {
  const s = P.parse(JSON.stringify({ v: 1, ts: 5, last: "w0-r2", done: { "w0-r1": 1, "w0-r2": true, "w0-r3": "yes", "w0-r4": 0 } }));
  assert.deepEqual(Object.keys(s.done).sort(), ["w0-r1", "w0-r2"]);
  assert.equal(s.last, "w0-r2");
});

test("ticking twice does not inflate anything; unticking is exact", () => {
  const s = fresh();
  tick(s, "w1-r1"); tick(s, "w1-r1"); tick(s, "w1-r1");
  assert.equal(P.summary(m, s).blocks, 1);
  P.setDone(s, "w1-r1", false, 2);
  P.setDone(s, "w1-r1", false, 3);
  assert.equal(P.summary(m, s).blocks, 0);
});

test("counts are derived from the manifest, so obsolete keys are never counted", () => {
  const s = fresh();
  tick(s, "w99-r1"); tick(s, "renamed-row");
  const sum = P.summary(m, s);
  assert.equal(sum.blocks, 0);
  assert.equal(sum.any, false);
  assert.equal(sum.blocksTotal, keys.length);
});

test("a week passes only when every output in it exists", () => {
  const s = fresh();
  const w0 = m.weeks[0][2];
  w0.slice(0, -1).forEach((k) => tick(s, k));
  assert.equal(P.summary(m, s).weeksDone, 0);
  tick(s, w0[w0.length - 1]);
  assert.equal(P.summary(m, s).weeksDone, 1);
});

test("weeks total counts only weeks with something to tick", () => {
  assert.equal(P.summary(m, fresh()).weeksTotal, m.weeks.filter((w) => w[2].length).length);
});

test("artefacts and courses are counted separately from blocks", () => {
  const s = fresh();
  tick(s, m.artefacts[0]); tick(s, m.courses[0]);
  const sum = P.summary(m, s);
  assert.equal(sum.artefacts, 1);
  assert.equal(sum.courses, 1);
  assert.equal(sum.any, true);
});

test("next is the first open block after where the learner stopped", () => {
  const s = fresh();
  tick(s, keys[0]); tick(s, keys[1]);
  assert.equal(P.next(m, s).k, keys[2]);
  tick(s, keys[5]);                     // jumped ahead
  assert.equal(P.next(m, s).k, keys[6]);
});

test("after the last block, next wraps back to the earliest gap", () => {
  const s = fresh();
  keys.forEach((k) => tick(s, k));
  P.setDone(s, keys[3], false, 9);
  tick(s, keys[keys.length - 1]);
  assert.equal(P.next(m, s).k, keys[3]);
});

test("everything ticked reports done, not a block", () => {
  const s = fresh();
  keys.forEach((k) => tick(s, k));
  assert.deepEqual(P.next(m, s), { done: true });
});

test("an obsolete last key falls back to the last done block in order", () => {
  const s = fresh();
  tick(s, keys[0]); tick(s, keys[1]); tick(s, "gone-key");
  assert.equal(s.last, "gone-key");
  assert.equal(P.next(m, s).k, keys[2]);
});

test("next carries the week and position for the resume line", () => {
  const s = fresh();
  tick(s, m.weeks[1][2][0]);
  const nx = P.next(m, s);
  assert.equal(m.weeks[nx.w][0], 1);
  assert.equal(nx.a, 1);
});

test("the shipped (squeezed) file behaves the same", () => {
  const shipped = path.join(ROOT, "_site/static/progress.js");
  const Q = require(shipped);
  const s = Q.parse(JSON.stringify({ v: 1, done: { [keys[0]]: 1 }, last: keys[0] }));
  assert.equal(Q.next(m, s).k, keys[1]);
});
