// Built by sitegen.py: __CACHE__ becomes this build's cache name and __PRECACHE__
// becomes the list of URLs saved on install. Nothing else here is templated.
//
// The cache name changes on every build, and that is what retires an old version:
// activate deletes every cache that is not this one. Pages are served from this
// cache first and refreshed quietly in the background, so a page opens at once on
// a slow connection and is current the next time it is opened. Downloads under
// /files/ are never cached: they are large, and anyone fetching one is online.
var CACHE = "__CACHE__";
var PRECACHE = __PRECACHE__;

self.addEventListener("install", function (e) {
  e.waitUntil(caches.open(CACHE).then(function (c) {
    // A single failed URL rejects addAll, and a rejected install leaves the
    // reader with no offline site at all. Better to install with a partial
    // cache and let runtime caching fill the gaps as they read.
    return c.addAll(PRECACHE).catch(function () {});
  }));
  self.skipWaiting();
});

self.addEventListener("activate", function (e) {
  e.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.map(function (k) {
      return k === CACHE ? 0 : caches.delete(k);
    }));
  }).then(function () {
    return self.clients.claim();
  }));
});

self.addEventListener("fetch", function (e) {
  var r = e.request;
  if (r.method !== "GET") return;
  var u = new URL(r.url);
  if (u.origin !== self.location.origin) return;
  if (u.pathname.indexOf("/files/") === 0) return;
  e.respondWith(caches.open(CACHE).then(function (c) {
    return c.match(r).then(function (hit) {
      if (hit) {
        fetch(r).then(function (res) {
          if (res.ok) c.put(r, res.clone());
        }).catch(function () {});
        return hit;
      }
      return fetch(r).then(function (res) {
        if (res.ok) c.put(r, res.clone());
        return res;
      });
    });
  }));
});
