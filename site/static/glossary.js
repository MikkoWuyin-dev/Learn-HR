/* Glossary search (PRD R8): filters Doc 1's term table as you type, no library.
   Matches the term and its meaning, ignoring case. The table is
   complete in the HTML; this only hides rows, so without JS every term shows. */
(function (doc) {
  "use strict";
  function norm(s) { return s.toLowerCase(); }
  function start() {
    var box = doc.querySelector("[data-glossary]"), table = doc.querySelector("[data-glossary-table]");
    if (!box || !table) return;
    var input = box.querySelector("input"), count = box.querySelector("[data-glossary-count]");
    var rows = Array.prototype.slice.call(table.querySelectorAll("tbody tr"));
    var text = rows.map(function (r) { return norm(r.textContent); });
    function run() {
      var q = norm(input.value.trim()), shown = 0;
      rows.forEach(function (r, i) {
        var hit = !q || text[i].indexOf(q) > -1;
        r.hidden = !hit;
        if (hit) shown++;
      });
      count.textContent = !q ? "" : shown ? shown + " of " + rows.length + " terms match." : "No term matches. Try fewer letters.";
    }
    input.addEventListener("input", run);
    input.addEventListener("keydown", function (e) { if (e.key === "Escape") { input.value = ""; run(); } });
    box.hidden = false;
    if (input.value) run();
  }
  if (doc.readyState === "loading") doc.addEventListener("DOMContentLoaded", start); else start();
})(document);
