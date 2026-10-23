// Exercises the service worker's real code against fake caches and a fake
// network. This is not a browser: it cannot prove the install event fires or
// that a page reloads offline. What it does prove is the logic - what gets
// cached, what is refused, what is served from where, and what is thrown away
// when a new build arrives. Those are the parts that can be silently wrong.
"use strict";
const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const ROOT = path.resolve(__dirname, "../../..");
const CACHE = "hrsite-test";
const PRECACHE = ["/", "/2/plan/week/0/", "/2/plan/week/1/"];
// Global: the comment at the top of sw.js names both tokens, and JS replace
// with a string only hits the first match. Python's replace hits all, which is
// why the sitegen side needs no such care.
const SRC = fs.readFileSync(path.join(ROOT, "site/static/sw.js"), "utf8")
  .replace(/__CACHE__/g, CACHE)
  .replace(/__PRECACHE__/g, JSON.stringify(PRECACHE));

const ORIGIN = "https://learnhr.test";

function response(url, ok) {
  return { url: url, ok: ok !== false, clone: function () { return response(url, ok); } };
}

// A cache close enough to the real thing: keyed by URL, returns undefined on a
// miss, and remembers what was put in it.
function fakeCache() {
  const map = new Map();
  return {
    map: map,
    match: (r) => Promise.resolve(map.get(r.url)),
    put: (r, res) => { map.set(r.url, res); return Promise.resolve(); },
    addAll: (list) => { list.forEach((u) => map.set(ORIGIN + u, response(ORIGIN + u))); return Promise.resolve(); }
  };
}

function loadWorker(opts) {
  const o = opts || {};
  const stores = o.stores || {};
  const seen = [];
  const handlers = {};
  const sandbox = {
    caches: {
      open: (name) => {
        if (!stores[name]) stores[name] = fakeCache();
        return Promise.resolve(stores[name]);
      },
      keys: () => Promise.resolve(Object.keys(stores)),
      delete: (name) => { delete stores[name]; return Promise.resolve(true); }
    },
    fetch: (r) => {
      seen.push(r.url);
      return o.offline ? Promise.reject(new Error("offline"))
                       : Promise.resolve(response(r.url));
    },
    URL: URL,
    Promise: Promise,
    console: console
  };
  sandbox.self = {
    location: { origin: ORIGIN },
    addEventListener: (name, fn) => { handlers[name] = fn; },
    skipWaiting: () => { sandbox.self._waited = true; },
    clients: { claim: () => Promise.resolve() }
  };
  vm.createContext(sandbox);
  vm.runInContext(SRC, sandbox);
  return {
    handlers: handlers,
    stores: stores,
    seen: seen,
    // waitUntil tells us when the event's work has settled.
    fire: (name, request) => {
      const waits = [];
      handlers[name]({
        request: request,
        waitUntil: (p) => waits.push(Promise.resolve(p))
      });
      return Promise.all(waits);
    }
  };
}

const req = (u, method) => ({ url: ORIGIN + u, method: method || "GET" });

test("install precaches the list", async () => {
  const w = loadWorker();
  await w.fire("install");
  const cache = w.stores[CACHE];
  for (const u of PRECACHE) {
    assert.ok(await cache.match(req(u)), u + " was not precached");
  }
});

test("install survives one bad URL rather than leaving no offline site", async () => {
  // addAll rejects as a whole if any URL 404s. Swallowing that keeps the worker
  // installed with a partial cache, which beats having no worker at all.
  const w = loadWorker();
  let rejected = false;
  w.stores[CACHE] = {
    match: () => Promise.resolve(undefined),
    put: () => Promise.resolve(),
    addAll: () => { rejected = true; return Promise.reject(new Error("404")); }
  };
  await w.fire("install");
  assert.ok(rejected, "a failing addAll was not exercised");
});

test("activate throws away every cache that is not this build", async () => {
  const stores = {};
  stores[CACHE] = fakeCache();
  stores["hrsite-old"] = fakeCache();
  stores["hrsite-older"] = fakeCache();
  const w = loadWorker({ stores: stores });
  await w.fire("activate");
  assert.deepStrictEqual(Object.keys(w.stores), [CACHE]);
});

test("a cached page is served from the cache", async () => {
  const w = loadWorker();
  await w.fire("install");
  const hit = await w.handlers.fetch.newResponse ? null : null;
  const res = await new Promise((resolve) => {
    w.handlers.fetch({
      request: req("/2/plan/week/0/"),
      respondWith: (p) => p.then(resolve)
    });
  });
  assert.strictEqual(res.url, ORIGIN + "/2/plan/week/0/");
});

test("a page not yet cached is fetched and then remembered", async () => {
  const w = loadWorker();
  await w.fire("install");
  const res = await new Promise((resolve) => {
    w.handlers.fetch({
      request: req("/3/library/"),
      respondWith: (p) => p.then(resolve)
    });
  });
  assert.strictEqual(res.url, ORIGIN + "/3/library/");
  assert.ok(await w.stores[CACHE].match(req("/3/library/")), "not cached after fetch");
});

test("a failed response is never cached", async () => {
  const w = loadWorker({ offline: true });
  await w.fire("install");
  await new Promise((resolve) => {
    w.handlers.fetch({
      request: req("/broken/"),
      respondWith: (p) => p.catch(() => resolve())
    });
  });
  assert.strictEqual(await w.stores[CACHE].match(req("/broken/")), undefined);
});

test("a cached page is served while the network is down", async () => {
  // The whole point of the worker: offline, a page already in the cache still
  // opens, and nothing is fetched.
  const w = loadWorker({ offline: true });
  await w.fire("install");
  const res = await new Promise((resolve) => {
    w.handlers.fetch({
      request: req("/2/plan/week/0/"),
      respondWith: (p) => p.then(resolve)
    });
  });
  assert.strictEqual(res.url, ORIGIN + "/2/plan/week/0/");
});

test("downloads under /files/ are left to the network", async () => {
  const w = loadWorker();
  await w.fire("install");
  let answered = false;
  w.handlers.fetch({
    request: req("/files/HR_Doc1_Start_Here.docx"),
    respondWith: () => { answered = true; }
  });
  assert.strictEqual(answered, false, "/files/ must not be handled");
  assert.strictEqual(w.seen.length, 0, "/files/ must not even be fetched here");
});

test("another origin is left to the network", async () => {
  const w = loadWorker();
  await w.fire("install");
  let answered = false;
  w.handlers.fetch({
    request: { url: "https://someone.example/page", method: "GET" },
    respondWith: () => { answered = true; }
  });
  assert.strictEqual(answered, false, "cross-origin must not be handled");
});

test("only GET is handled", async () => {
  const w = loadWorker();
  await w.fire("install");
  let answered = false;
  w.handlers.fetch({
    request: req("/", "POST"),
    respondWith: () => { answered = true; }
  });
  assert.strictEqual(answered, false, "a POST must not be handled");
});
