/* Library filter (PRD R19, as decided by the owner): Document 3's section and the
   card's confirmed cost label. The choice lives in the URL query, so a filtered
   list can be shared. Without JS the form stays hidden and every card shows. */
(function (win, doc) {
  "use strict";
  function start() {
    var form = doc.querySelector("[data-lib-filter]");
    if (!form) return;
    var sel = { section: form.querySelector("select[name=section]"), cost: form.querySelector("select[name=cost]") };
    var cards = Array.prototype.slice.call(doc.querySelectorAll(".res-card"));
    var groups = Array.prototype.slice.call(doc.querySelectorAll("[data-lib-section]"));
    var count = form.querySelector("[data-lib-count]");
    function allowed(s, v) {
      for (var i = 0; i < s.options.length; i++) if (s.options[i].value === v) return v;
      return "";
    }
    function apply(push) {
      var want = { section: sel.section.value, cost: sel.cost.value }, shown = 0;
      cards.forEach(function (c) {
        var ok = (!want.section || c.getAttribute("data-section") === want.section) &&
          (!want.cost || c.getAttribute("data-cost") === want.cost);
        c.hidden = !ok;
        if (ok) shown++;
      });
      groups.forEach(function (g) { g.hidden = !g.querySelector(".res-card:not([hidden])"); });
      count.textContent = want.section || want.cost ? shown + " of " + cards.length + " resources shown." : "";
      if (push) {
        var q = [];
        if (want.section) q.push("section=" + encodeURIComponent(want.section));
        if (want.cost) q.push("cost=" + encodeURIComponent(want.cost));
        try { win.history.replaceState(null, "", win.location.pathname + (q.length ? "?" + q.join("&") : "")); } catch (e) { return; }
      }
    }
    var params = new win.URLSearchParams(win.location.search);
    sel.section.value = allowed(sel.section, params.get("section") || "");
    sel.cost.value = allowed(sel.cost, params.get("cost") || "");
    form.addEventListener("change", function () { apply(true); });
    form.hidden = false;
    apply(false);
  }
  if (doc.readyState === "loading") doc.addEventListener("DOMContentLoaded", start); else start();
})(window, document);
