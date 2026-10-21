#!/usr/bin/env python3
"""Check every external link in the five documents and record what happened.

    python3 tools/sitegen/linkcheck.py              # all links, writes checks/links.json
    python3 tools/sitegen/linkcheck.py --dry-run    # list what would be checked, no requests
    python3 tools/sitegen/linkcheck.py --strict     # exit 1 if any link failed (for CI)

Run it by hand (the roadmap's quarterly sweep) or from CI, then rebuild the site:
/check/ shows the recorded results. Visitors never trigger a request.

Politeness: one request at a time, a pause between requests (default 2 s), a HEAD
first and a GET only when the HEAD is refused, a clear User-Agent, no retries.

Honesty, because a link checker is easy to over-read:
  ok            the server answered 2xx at the URL we asked for
  redirected    2xx, but only after a redirect — worth a look, not broken
  failed        404 or 410: the server says the page is gone
  inconclusive  anything that does not prove either way — 401/403/429/5xx, timeouts,
                DNS or TLS errors, connection refused. Sites block bots; networks fail.
A 2xx proves the page answered, not that the course, price or certificate is unchanged.
"""
import argparse
import datetime as dt
import json
import pathlib
import socket
import ssl
import sys
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "checks" / "links.json"
UA = "HRLibrary-linkcheck/1.0 (static-site maintenance; one request per link)"

FAILED_CODES = {404, 410}


def classify(status=None, error=None, redirected=False):
    """Map one observation to an outcome. Only a 404/410 counts as failed."""
    if error is not None or status is None:
        return "inconclusive"
    if 200 <= status < 300:
        return "redirected" if redirected else "ok"
    if status in FAILED_CODES:
        return "failed"
    return "inconclusive"


class _Redirects(urllib.request.HTTPRedirectHandler):
    max_redirections = 5


def fetch(url, timeout=20.0, method="HEAD"):
    """One request. Returns (status, final_url, error_text)."""
    req = urllib.request.Request(url, method=method, headers={"User-Agent": UA, "Accept": "*/*"})
    opener = urllib.request.build_opener(_Redirects())
    try:
        with opener.open(req, timeout=timeout) as resp:
            if method == "GET":
                resp.read(1024)
            return resp.status, resp.geturl(), None
    except urllib.error.HTTPError as e:
        return e.code, e.geturl() or url, None
    except (urllib.error.URLError, socket.timeout, TimeoutError, ssl.SSLError,
            ConnectionError, OSError) as e:
        reason = getattr(e, "reason", e)
        return None, url, f"{type(reason).__name__}: {reason}"[:160]


def check_one(url, timeout=20.0):
    status, final, error = fetch(url, timeout, "HEAD")
    # Many servers refuse or mishandle HEAD; only then is a GET worth sending.
    if error is not None or status in (403, 405, 501, 400):
        status, final, error = fetch(url, timeout, "GET")
    redirected = bool(final) and final.rstrip("/") != url.rstrip("/")
    return {
        "url": url,
        "outcome": classify(status, error, redirected),
        "status": status,
        "final_url": final if redirected else None,
        "error": error,
        "checked_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    }


def load_previous(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {r["url"]: r for r in data.get("links", [])}
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return {}


def sweep(urls_with_sources, out_path=OUT, delay=2.0, timeout=20.0, log=print):
    previous = load_previous(out_path)
    started = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    results = []
    for i, (url, sources) in enumerate(urls_with_sources):
        if i:
            time.sleep(delay)
        r = check_one(url, timeout)
        r["sources"] = sources
        prev = previous.get(url)
        r["previous"] = ({k: prev.get(k) for k in ("outcome", "status", "checked_at")}
                         if prev else None)
        results.append(r)
        log(f"{r['outcome']:<12} {r['status'] or '-':<4} {url}"
            + (f"  ({r['error']})" if r["error"] else ""))
    counts = {}
    for r in results:
        counts[r["outcome"]] = counts.get(r["outcome"], 0) + 1
    data = {"run": {"started": started,
                    "finished": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                    "tool": "tools/sitegen/linkcheck.py", "user_agent": UA,
                    "delay_seconds": delay, "timeout_seconds": timeout, "counts": counts},
            "links": results}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return data


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--delay", type=float, default=2.0, help="seconds between requests")
    ap.add_argument("--timeout", type=float, default=20.0)
    ap.add_argument("--dry-run", action="store_true", help="list the links, send nothing")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any link failed")
    args = ap.parse_args(argv)

    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import sitegen  # noqa: E402  (reads the markdown; writes nothing)
    sources = sitegen.link_sources()
    items = [(u, s) for u, s in sources.items()]
    if args.dry_run:
        for u, s in items:
            print(u, "←", "; ".join(f"{x['file']} › {x['section']}" for x in s))
        print(f"{len(items)} links; nothing requested")
        return 0
    data = sweep(items, delay=args.delay, timeout=args.timeout)
    c = data["run"]["counts"]
    print("\n" + ", ".join(f"{k}: {v}" for k, v in sorted(c.items())) + f"  → {OUT.relative_to(ROOT)}")
    print("Rebuild the site to publish these results on /check/.")
    return 1 if args.strict and c.get("failed") else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
