/* Progress, kept in this browser only (PRD R9-R13). No network, no cookies.
   State: localStorage "hrsite:v1" = {v:1, ts, done:{key:1}, last:key}.
   Every count is derived from the build's path manifest, never stored, so a
   changed curriculum cannot leave a stale total behind. Unknown keys are kept
   (the row may come back) but never counted. */
(function (root) {
  "use strict";
  var KEY = "hrsite:v1";

  function empty() { return { v: 1, ts: 0, done: {}, last: "" }; }

  // Accept only the shape we wrote; anything else reads as a first visit.
  function parse(raw) {
    var s = empty(), o;
    if (typeof raw !== "string" || !raw) return s;
    try { o = JSON.parse(raw); } catch (e) { return s; }
    if (!o || typeof o !== "object" || o.v !== 1 || !o.done || typeof o.done !== "object") return s;
    Object.keys(o.done).forEach(function (k) { if (o.done[k] === 1 || o.done[k] === true) s.done[k] = 1; });
    s.ts = typeof o.ts === "number" ? o.ts : 0;
    s.last = typeof o.last === "string" ? o.last : "";
    return s;
  }

  // Idempotent: setting a key to the state it already has changes nothing.
  function setDone(s, k, on, now) {
    if (on) { s.done[k] = 1; s.last = k; } else { delete s.done[k]; }
    s.ts = now || 0;
    return s;
  }

  function order(m) {
    var out = [];
    m.weeks.forEach(function (w, wi) { w[2].forEach(function (k, ai) { out.push({ k: k, w: wi, a: ai }); }); });
    return out;
  }

  function summary(m, s) {
    var all = order(m), d = s.done, weeksDone = 0, blocks = 0;
    all.forEach(function (x) { if (d[x.k]) blocks++; });
    m.weeks.forEach(function (w) { if (w[2].length && w[2].every(function (k) { return d[k]; })) weeksDone++; });
    function count(list) { return list.filter(function (k) { return d[k]; }).length; }
    var r = {
      blocks: blocks, blocksTotal: all.length, weeksDone: weeksDone,
      weeksTotal: m.weeks.filter(function (w) { return w[2].length; }).length,
      artefacts: count(m.artefacts), artefactsTotal: m.artefacts.length,
      courses: count(m.courses), coursesTotal: m.courses.length
    };
    r.lastWeek = m.weeks.length ? m.weeks[m.weeks.length - 1][0] : 0;
    r.any = r.blocks + r.artefacts + r.courses > 0;
    return r;
  }

  // Next = the first open block after the one ticked most recently (where the
  // learner stopped); if everything after it is done, the first open block overall.
  function next(m, s) {
    var all = order(m), i = -1, j;
    if (!all.some(function (x) { return s.done[x.k]; })) return null;
    for (j = 0; j < all.length; j++) if (all[j].k === s.last) i = j;
    if (i < 0) for (j = 0; j < all.length; j++) if (s.done[all[j].k]) i = j;
    for (j = i + 1; j < all.length; j++) if (!s.done[all[j].k]) return all[j];
    for (j = 0; j < all.length; j++) if (!s.done[all[j].k]) return all[j];
    return { done: true };
  }

  var api = { KEY: KEY, parse: parse, setDone: setDone, summary: summary, next: next };
  if (typeof module === "object" && module.exports) { module.exports = api; return; }

  /* ------------------------------------------------------------ browser */
  var doc = root.document, store = null, state, m, live;
  doc.documentElement.className += " js";
  try { store = root.localStorage; store.getItem(KEY); } catch (e) { store = null; }
  function read() { try { return parse(store ? store.getItem(KEY) : ""); } catch (e) { return empty(); } }
  function write() {
    if (!store) return false;
    try { store.setItem(KEY, JSON.stringify(state)); return true; } catch (e) { store = null; return false; }
  }
  function $(sel, el) { return Array.prototype.slice.call((el || doc).querySelectorAll(sel)); }
  function say(t) { if (live) { live.textContent = ""; setTimeout(function () { live.textContent = t; }, 50); } }
  function el(tag, attrs, text) {
    var e = doc.createElement(tag);
    Object.keys(attrs || {}).forEach(function (a) { e.setAttribute(a, attrs[a]); });
    if (text) e.textContent = text;
    return e;
  }
  function weekLabel(w) { return "Week " + w[0] + " · " + w[1]; }
  function weekUrl(w) { return "/2/plan/week/" + w[0] + "/"; }

  function render() {
    var sum = summary(m, state), nx = next(m, state);
    $("[data-tick]").forEach(function (b) {
      var on = !!state.done[b.getAttribute("data-tick")];
      b.hidden = false;
      b.setAttribute("aria-pressed", on ? "true" : "false");
      var row = b.closest("tr, li");
      if (row) { row.classList.toggle("is-done", on); row.classList.remove("is-next"); row.removeAttribute("aria-current"); }
    });
    if (nx && nx.k) {
      var cur = doc.getElementById(nx.k);
      if (cur) { cur.classList.add("is-next"); cur.setAttribute("aria-current", "step"); }
    }
    $("[data-week-progress]").forEach(function (p) {
      var w = m.weeks.filter(function (x) { return String(x[0]) === p.getAttribute("data-week-progress"); })[0];
      if (!w || !w[2].length) return;
      var n = w[2].filter(function (k) { return state.done[k]; }).length;
      p.hidden = false;
      p.textContent = n === w[2].length ? "Week passed: every output exists (" + n + " of " + n + ")."
        : n + " of " + w[2].length + " outputs done this week. Tick a block only when its output exists.";
    });
    $("[data-week-state]").forEach(function (sp) {
      var w = m.weeks.filter(function (x) { return String(x[0]) === sp.getAttribute("data-week-state"); })[0];
      if (!w || !w[2].length) return;
      var n = w[2].filter(function (k) { return state.done[k]; }).length;
      sp.textContent = n === w[2].length ? "✓ passed" : n ? n + "/" + w[2].length : "";
      var li = sp.closest("li");
      if (li) li.classList.toggle("is-current", !!(nx && nx.k && m.weeks[nx.w] === w));
    });
    var resumeHref = "", resumeText = "";
    if (nx && nx.k) { resumeHref = weekUrl(m.weeks[nx.w]) + "#" + nx.k; resumeText = weekLabel(m.weeks[nx.w]); }
    $("[data-resume]").forEach(function (p) {
      p.textContent = "";
      p.hidden = !resumeHref;
      if (!resumeHref) return;
      p.appendChild(doc.createTextNode("You left off at "));
      p.appendChild(el("a", { href: resumeHref }, resumeText));
    });
    $("[data-start]").forEach(function (a) {
      if (!a.getAttribute("data-label")) a.setAttribute("data-label", a.textContent);
      if (nx && nx.k) { a.textContent = "Resume: Week " + m.weeks[nx.w][0]; a.href = resumeHref; }
      else if (nx && nx.done) { a.textContent = "Getting the job"; a.href = "/5/getting-the-job/"; }
      else { a.textContent = a.getAttribute("data-label"); a.href = "/2/plan/week/0/"; }
    });
    $("[data-next]").forEach(function (sec) {
      var body = $("[data-next-body]", sec)[0], w, act;
      sec.hidden = !nx;
      if (!nx || !body) return;
      body.textContent = "";
      if (nx.done) {
        body.appendChild(el("p", {}, "Every block in Weeks 0–" + sum.lastWeek + " is ticked."));
        body.appendChild(el("a", { href: "/5/getting-the-job/", "class": "btn btn-primary" }, "Open Getting the job"));
        return;
      }
      w = m.weeks[nx.w]; act = w[3] && w[3][nx.a];
      body.appendChild(el("p", { "class": "eyebrow" }, weekLabel(w) + " · block " + (nx.a + 1) + " of " + w[2].length));
      if (act) {
        if (act[0]) body.appendChild(el("p", { "class": "next-time" }, act[0]));
        body.appendChild(el("p", {}, act[1]));
        body.appendChild(el("p", { "class": "note" }, "Output: " + act[2]));
      }
      body.appendChild(el("a", { href: resumeHref, "class": "btn btn-primary" }, "Open Week " + w[0]));
    });
    $("[data-progress]").forEach(function (sec) {
      var body = $("[data-progress-body]", sec)[0];
      sec.hidden = !sum.any && !!store;
      if (!body) return;
      body.textContent = "";
      if (!store) body.appendChild(el("p", { "class": "note" },
        "This browser is not saving progress (private browsing or storage turned off). Ticks last until you leave the page."));
      if (!sum.any) return;
      [["Blocks done", sum.blocks, sum.blocksTotal],
       ["Weeks passed (Weeks 0–" + sum.lastWeek + ")", sum.weeksDone, sum.weeksTotal],
       ["Portfolio artefacts", sum.artefacts, sum.artefactsTotal],
       ["Courses and credentials", sum.courses, sum.coursesTotal]].forEach(function (r) {
        var p = el("p", { "class": "meter" });
        p.appendChild(el("span", {}, r[0] + ": " + r[1] + " of " + r[2]));
        var bar = el("progress", { max: String(r[2] || 1), value: String(r[1]) });
        bar.setAttribute("aria-hidden", "true");
        p.appendChild(bar);
        body.appendChild(p);
      });
    });
  }

  function onClick(e) {
    var t = e.target.closest ? e.target.closest("button") : null, k;
    if (!t) return;
    if ((k = t.getAttribute("data-tick"))) {
      var on = t.getAttribute("aria-pressed") !== "true";
      setDone(state, k, on, Date.now());
      var saved = write();
      render();
      var s = summary(m, state);
      say((on ? "Marked done. " : "Unmarked. ") + s.blocks + " of " + s.blocksTotal + " blocks done" +
        (saved ? "." : ". Not saved in this browser."));
    } else if (t.hasAttribute("data-reset-ask")) {
      $("[data-reset-confirm]").forEach(function (c) { c.hidden = false; });
      var yes = $("[data-reset-yes]")[0]; if (yes) yes.focus();
    } else if (t.hasAttribute("data-reset-no")) {
      $("[data-reset-confirm]").forEach(function (c) { c.hidden = true; });
    } else if (t.hasAttribute("data-reset-yes")) {
      state = empty();
      try { if (store) store.removeItem(KEY); } catch (err) { /* nothing to clear */ }
      $("[data-reset-confirm]").forEach(function (c) { c.hidden = true; });
      render();
      say("Progress cleared on this device.");
    }
  }

  function start() {
    var node = doc.getElementById("hr-path");
    live = doc.getElementById("hr-live");
    try { m = JSON.parse(node.textContent); } catch (e) { return; }
    state = read();
    render();
    doc.addEventListener("click", onClick);
    root.addEventListener("storage", function (e) { if (e.key === KEY || e.key === null) { state = read(); render(); } });
  }
  if (doc.readyState === "loading") doc.addEventListener("DOMContentLoaded", start); else start();
})(this);
