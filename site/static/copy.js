/* Copy buttons for the reusable templates (PRD R5). The text copied is the
   source's own words, from the button's data-copy, with no interface text.
   Order of attempts: Clipboard API, then execCommand, then select the text so
   the learner can long-press it. Every outcome is announced. */
(function (doc) {
  "use strict";
  function status(btn, text) {
    var s = btn.nextElementSibling;
    if (s && s.classList.contains("copy-status")) s.textContent = text;
    clearTimeout(btn._t);
    btn._t = setTimeout(function () { if (s) s.textContent = ""; }, 4000);
  }
  function legacy(text) {
    var ta = doc.createElement("textarea"), ok = false;
    ta.value = text;
    ta.setAttribute("readonly", "");
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    doc.body.appendChild(ta);
    ta.select();
    try { ok = doc.execCommand("copy"); } catch (e) { ok = false; }
    doc.body.removeChild(ta);
    return ok;
  }
  function selectBlock(btn) {
    var fig = btn.closest(".copyable"), target = fig && fig.querySelector("blockquote, pre");
    if (!target || !window.getSelection) return;
    var r = doc.createRange();
    r.selectNodeContents(target);
    var sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(r);
  }
  function fallback(btn, text) {
    if (legacy(text)) return status(btn, "Copied.");
    selectBlock(btn);
    status(btn, "Couldn't copy automatically. The text is selected: press and hold it, then choose Copy.");
  }
  doc.addEventListener("click", function (e) {
    var btn = e.target.closest ? e.target.closest(".copy-btn") : null;
    if (!btn) return;
    var text = btn.getAttribute("data-copy") || "";
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(function () { status(btn, "Copied."); },
        function () { fallback(btn, text); });
    } else {
      fallback(btn, text);
    }
  });
  function show() { Array.prototype.forEach.call(doc.querySelectorAll(".copy-btn"), function (b) { b.hidden = false; }); }
  if (doc.readyState === "loading") doc.addEventListener("DOMContentLoaded", show); else show();
})(document);
