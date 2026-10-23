// Registers the service worker. R28: the "new version" nudge must never interrupt
// mid-read, so it never reloads the page by itself, and the bar is fixed to the
// bottom of the window - it pushes no text around and covers nothing being read.
// The offline line appears on its own, because a reader who has lost signal
// deserves to be told why a page they have not opened yet will not load.
(function () {
  if (!("serviceWorker" in navigator)) return;
  var b;
  function hide() { if (b) { b.remove(); b = 0; } }
  function say(t, r) {
    if (!b) {
      b = document.createElement("div");
      b.className = "sw-note";
      b.setAttribute("role", "status");
      document.body.appendChild(b);
    }
    b.textContent = t;
    if (r) {
      b.insertAdjacentHTML("beforeend", '<button class="btn btn-sm">Refresh</button>');
      b.lastChild.onclick = function () { location.reload(); };
    }
    b.insertAdjacentHTML("beforeend", '<button class="sw-note-x" aria-label="Dismiss">\u00d7</button>');
    b.lastChild.onclick = hide;
  }
  function off() { say("Offline - pages you have already opened still work.", 0); }
  window.addEventListener("offline", off);
  window.addEventListener("online", hide);
  if (!navigator.onLine) off();
  window.addEventListener("load", function () {
    navigator.serviceWorker.register("/sw.js").then(function (g) {
      g.addEventListener("updatefound", function () {
        var w = g.installing;
        if (!w) return;
        w.addEventListener("statechange", function () {
          if (w.state === "installed" && navigator.serviceWorker.controller) say("A new version is ready.", 1);
        });
      });
    }).catch(function () {});
  });
})();
