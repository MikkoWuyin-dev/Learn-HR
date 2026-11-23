#!/usr/bin/env python3
"""Discover and capture ACNIRET brand/logo assets. Runs on a runner with open internet.

Outputs a human-readable report, then a base64 payload framed by markers so the
raw bytes can be reassembled downstream.
"""
import base64
import os
import re
import ssl
import struct
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://acniret.com"
ASSET_HOST = BASE + "/__l5e/assets-v1/5275e09e-f13b-4b47-aa55-7c65bca73044"
UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

PAGES = [
    "/", "/safety", "/pricing", "/faq", "/how-it-works", "/patient",
    "/clinician", "/sign-in", "/auth", "/journey", "/assessment",
    "/labs", "/messages", "/how-it-works/timeline",
]
PROBE_NAMES = [
    "acniret-care-logo.png", "acniret-care-logo@2x.png", "acniret-care-logo-2x.png",
    "acniret-care-logo.svg", "acniret-care-logo.webp", "acniret-care-logo@3x.png",
    "acniret-care-logo-dark.png", "acniret-care-logo-light.png",
    "acniret-care-logo-white.png", "acniret-care-logo-black.png",
    "acniret-care-mark.png", "acniret-care-mark.svg", "acniret-logo.png",
    "acniret-logo.svg", "acniret-care-wordmark.png", "acniret-care-icon.png",
]
ROOT_PROBES = [
    "/favicon.ico", "/favicon-32x32.png", "/favicon-16x16.png",
    "/apple-touch-icon.png", "/apple-touch-icon-precomposed.png",
    "/manifest.webmanifest", "/site.webmanifest", "/robots.txt", "/sitemap.xml",
    "/logo.png", "/logo.svg", "/brand/logo.png",
]
MAX_FILE = 3_000_000
MAX_PAYLOAD = 3_200_000


def fetch(url, timeout=45):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
            return r.status, r.headers.get("Content-Type", ""), r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Content-Type", "") if e.headers else "", e.read()
    except Exception as e:  # noqa: BLE001
        print(f"  ! fetch failed {url}: {type(e).__name__}: {e}")
        return 0, "", b""


def sniff(b):
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        w, h = struct.unpack(">II", b[16:24])
        return "PNG", f"{w}x{h}", "image/png"
    if b[:2] == b"\xff\xd8":
        i, w, h = 2, 0, 0
        while i < len(b) - 9:
            if b[i] != 0xFF:
                i += 1
                continue
            m = b[i + 1]
            if m in (0xC0, 0xC1, 0xC2, 0xC3):
                h, w = struct.unpack(">HH", b[i + 5:i + 9])
                break
            if m in (0xD8, 0xD9):
                i += 2
                continue
            i += 2 + struct.unpack(">H", b[i + 2:i + 4])[0]
        return "JPEG", f"{w}x{h}", "image/jpeg"
    head = b[:600].lstrip()
    if head.startswith(b"<svg") or b"<svg" in head[:300]:
        m = re.search(rb'viewBox="([^"]+)"', b[:2000])
        return "SVG", m.group(1).decode() if m else "?", "image/svg+xml"
    if b[:4] == b"\x00\x00\x01\x00":
        return "ICO", "multi", "image/x-icon"
    if b[:4] == b"RIFF" and b[8:12] == b"WEBP":
        return "WEBP", "?", "image/webp"
    if b[:6] in (b"GIF87a", b"GIF89a"):
        return "GIF", "?", "image/gif"
    return "OTHER", "", ""


OUT = "_assetpull"
MANIFEST = []


def dims_of(b):
    return sniff(b)[1]


def is_asset(kind):
    return kind in {"PNG", "JPEG", "SVG", "ICO", "WEBP", "GIF"}


found = {}  # url -> bytes


def add(url, data, kind, note=""):
    if not data or not is_asset(kind):
        return False
    if url not in found:
        found[url] = data
        ext = {"PNG": "png", "JPEG": "jpg", "SVG": "svg", "ICO": "ico",
               "WEBP": "webp", "GIF": "gif"}[kind]
        base = os.path.basename(urllib.parse.urlparse(url).path) or "asset"
        base = re.sub(r"[^A-Za-z0-9._-]+", "_", base)
        if not base.lower().endswith("." + ext):
            base += "." + ext
        safe = f"{len(found):02d}_{base}"
        os.makedirs(OUT + "/files", exist_ok=True)
        open(f"{OUT}/files/{safe}", "wb").write(data)
        MANIFEST.append((safe, url, kind, dims_of(data), len(data)))
        print(f"  + {kind:4} {len(data):>8}  {url} {note}")
        return True
    return False


def main():
    print("###### PAGES ######")
    htmls = {}
    os.makedirs(OUT + "/html", exist_ok=True)
    for p in PAGES:
        st, ct, body = fetch(BASE + p)
        print(f"{p:24} {st} {len(body)} {ct}")
        if body and "html" in ct:
            htmls[p] = body
            name = p.strip("/").replace("/", "_") or "home"
            open(f"{OUT}/html/{name}.html", "wb").write(body)

    allhtml = b"\n".join(htmls.values()).decode("utf-8", "replace")

    print("\n###### <link> TAGS (icon/manifest/logo) ######")
    links = set()
    for tag in re.findall(r"<link[^>]*>", allhtml, re.I):
        if re.search(r"icon|manifest|logo", tag, re.I):
            links.add(tag)
            print(" ", tag[:300])
    print("raw link count:", len(links))

    print("\n###### <meta> og/twitter images ######")
    metas = set()
    for tag in re.findall(r"<meta[^>]*>", allhtml, re.I):
        if re.search(r"(og:image|twitter:image)", tag, re.I):
            metas.add(tag)
            print(" ", tag[:300])

    print("\n###### <img>/<source> with logo-ish attrs ######")
    for pat in (r"<img[^>]*>", r"<source[^>]*>"):
        for tag in sorted(set(re.findall(pat, allhtml, re.I))):
            if re.search(r"logo|brand|mark|wordmark|icon", tag, re.I):
                print(" ", tag[:300])

    print("\n###### absolute logo-ish urls in markup ######")
    urls = set()
    for u in re.findall(r"https?://[^\"'()<>\\ ]+", allhtml) + re.findall(
        r"/__l5e/[^\"'()<>\\ ]+", allhtml
    ):
        full = u if u.startswith("http") else BASE + u
        if re.search(r"logo|brand|mark|favicon|icon|wordmark", full, re.I):
            urls.add(full)
    for u in sorted(urls):
        print(" ", u)

    print("\n###### bundles (css/js) ######")
    bundles = set()
    for m in re.findall(r'["\'](/assets/[^"\']+\.(?:css|js))["\']', allhtml):
        bundles.add(BASE + m)
    print("bundle count:", len(bundles))
    css_js = {}
    for b in sorted(bundles):
        st, ct, body = fetch(b)
        if body:
            css_js[b] = body
    print("fetched bundles:", len(css_js))

    print("\n###### logo refs inside css/js ######")
    bundle_urls = set()
    for url, body in css_js.items():
        txt = body.decode("utf-8", "replace")
        for m in re.findall(r"url\(([^)]{1,300})\)", txt):
            m = m.strip().strip("'\"")
            if re.search(r"logo|brand|mark|icon", m, re.I):
                bundle_urls.add(urllib.parse.urljoin(url, m))
        for m in re.findall(r"[A-Za-z0-9_./:@%?=&+~-]{0,80}logo[A-Za-z0-9_./:@%?=&+~-]{0,80}", txt, re.I):
            if len(m) > 8:
                bundle_urls.add(m)
    for u in sorted(bundle_urls)[:120]:
        print(" ", u)

    # every absolute/site-relative asset reference that looks like a logo
    for u in sorted(bundle_urls):
        if re.match(r"^(https?:)?/", u) or u.startswith("__l5e"):
            full = urllib.parse.urljoin(BASE + "/", u)
            urls.add(full)

    print("\n###### probe asset-host variants ######")
    for n in PROBE_NAMES:
        u = f"{ASSET_HOST}/{n}"
        urls.add(u)

    print("\n###### probe root files ######")
    for n in ROOT_PROBES:
        urls.add(BASE + n)

    print("\n###### download candidates ######")
    for u in sorted(urls):
        if not u.startswith("http"):
            continue
        st, ct, body = fetch(u)
        kind, dims, _ = sniff(body)
        if st == 200 and kind != "OTHER":
            add(u, body, kind, f"[{dims}]")
        else:
            print(f"  - {st:>3} {ct[:40]:40} {u}")

    # follow manifest icons
    print("\n###### manifest icons ######")
    for n in ("/manifest.webmanifest", "/site.webmanifest"):
        st, ct, body = fetch(BASE + n)
        if st == 200 and b"icons" in body:
            for src in re.findall(rb'"src"\s*:\s*"([^"]+)"', body):
                u = urllib.parse.urljoin(BASE + "/", src.decode())
                st2, _, b2 = fetch(u)
                k, d, _ = sniff(b2)
                add(u, b2, k, f"[{d}] via manifest")

    print("\n###### HTML fallback captures (logo in header markup) ######")
    # capture the SPA fallback asset host images referenced by rendered pages
    for h in list(htmls.items()):
        for src in re.findall(r'<img[^>]+src="([^"]+)"', h[1].decode("utf-8", "replace"), re.I):
            if re.search(r"logo|brand|mark", src, re.I):
                u = urllib.parse.urljoin(BASE + "/", src)
                st, _, b = fetch(u)
                k, d, _ = sniff(b)
                add(u, b, k, f"[{d}] from {h[0]}")

    print("\n###### SUMMARY ######")
    rows = []
    for u, b in found.items():
        k, d, _ = sniff(b)
        rows.append((k, d, len(b), u))
    for k, d, ln, u in sorted(rows, key=lambda r: (r[0] != "SVG", -r[2])):
        print(f"{k:5} {d:>12} {ln:>9}  {u}")

    print("\n###### SIZES BY KIND ######")
    for u, b in found.items():
        k, d, _ = sniff(b)
        print(f"{u}\t{k}\t{d}\t{len(b)}")

    print("\n###### PAYLOAD ######")
    total = 0
    order = sorted(found.items(), key=lambda kv: (sniff(kv[1])[0] != "SVG", -len(kv[1])))
    for u, b in order:
        k, d, _ = sniff(b)
        if len(b) > MAX_FILE:
            print(f"===SKIP:{u}:{k}:{d}:{len(b)}===")
            continue
        blk = base64.b64encode(b).decode()
        if total + len(blk) > MAX_PAYLOAD:
            print(f"===TRUNCATED:{u}:{k}:{d}:{len(b)}===")
            continue
        total += len(blk)
        print(f"===FILE:{u}|{k}|{d}|{len(b)}===")
        if k == "SVG":
            print("===TEXT===")
            print(b.decode("utf-8", "replace"))
        else:
            print("===B64===")
            for i in range(0, len(blk), 3000):
                print(blk[i:i + 3000])
        print("===ENDFILE===")
    print(f"###### PAYLOAD TOTAL CHARS: {total} ######")

    os.makedirs(OUT, exist_ok=True)
    with open(f"{OUT}/manifest.tsv", "w") as fh:
        fh.write("file\tkind\tdims\tbytes\tsource_url\n")
        for safe, url, kind, d, ln in MANIFEST:
            fh.write(f"{safe}\t{kind}\t{d}\t{ln}\t{url}\n")
    with open(f"{OUT}/candidate_urls.txt", "w") as fh:
        for u in sorted(urls):
            fh.write(u + "\n")
    print("###### DONE ######")


if __name__ == "__main__":
    main()
