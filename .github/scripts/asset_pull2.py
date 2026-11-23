#!/usr/bin/env python3
"""Pass 2: capture remaining ACNIRET brand assets and exhaustively scan CSS/JS.

Saves everything under _assetpull2/ plus a human-readable report.txt.
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
ASSET_DIR = BASE + "/__l5e/assets-v1/5275e09e-f13b-4b47-aa55-7c65bca73044"
UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

OUT = "_assetpull2"
MAX_FILE = 4_000_000


def fetch(url, timeout=45):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
            return r.status, r.headers.get("Content-Type", ""), r.read()
    except urllib.error.HTTPError as e:
        return e.code, (e.headers.get("Content-Type", "") if e.headers else ""), b""
    except Exception as e:  # noqa: BLE001
        return 0, f"ERR {type(e).__name__}", b""


def sniff(b):
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        w, h = struct.unpack(">II", b[16:24])
        return "PNG", f"{w}x{h}"
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
        return "JPEG", f"{w}x{h}"
    head = b[:600].lstrip()
    if head.startswith(b"<svg") or b"<svg" in head[:300]:
        return "SVG", "vector"
    if b[:4] == b"\x00\x00\x01\x00":
        n = struct.unpack("<H", b[4:6])[0]
        return "ICO", f"{n} images"
    if b[:4] == b"RIFF" and b[8:12] == b"WEBP":
        return "WEBP", "?"
    if b[:6] in (b"GIF87a", b"GIF89a"):
        return "GIF", "?"
    return "OTHER", ""


KINDS = {"PNG", "JPEG", "SVG", "ICO", "WEBP", "GIF"}
report = []
found = {}


def say(*a):
    line = " ".join(str(x) for x in a)
    print(line)
    report.append(line)


def add(url, data, label=""):
    k, d = sniff(data)
    if not data or k not in KINDS or url in found:
        return
    found[url] = (data, k, d)
    ext = {"PNG": "png", "JPEG": "jpg", "SVG": "svg", "ICO": "ico",
           "WEBP": "webp", "GIF": "gif"}[k]
    base = os.path.basename(urllib.parse.urlparse(url).path) or "asset"
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", base)
    if not base.lower().endswith("." + ext):
        base += "." + ext
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", label + "_" + base) if label else base
    safe = f"{len(found):02d}_{safe}"
    os.makedirs(f"{OUT}/files", exist_ok=True)
    open(f"{OUT}/files/{safe}", "wb").write(data)
    say(f"  + {k:4} {d:>10} {len(data):>8}  {url}")


def main():
    os.makedirs(OUT, exist_ok=True)

    say("###### PHASE A: root + asset-dir probes ######")
    probes = [
        BASE + "/favicon.png",
        BASE + "/favicon.ico",
        BASE + "/favicon-16x16.png",
        BASE + "/favicon-32x32.png",
        BASE + "/favicon-48x48.png",
        BASE + "/favicon-96x96.png",
        BASE + "/apple-touch-icon.png",
        BASE + "/apple-touch-icon-180x180.png",
        BASE + "/apple-touch-icon-precomposed.png",
        BASE + "/mstile-150x150.png",
        BASE + "/og.png",
        BASE + "/og-image.png",
        BASE + "/social.png",
        BASE + "/logo.png",
        BASE + "/logo.svg",
        BASE + "/brand.png",
    ]
    for n in [
        "acniret-care-logo.png",
        "acniret-care-logo.svg",
        "acniret-care-logo.webp",
        "acniret-care-logo@2x.png",
        "acniret-care-logo@3x.png",
        "acniret-care-logo-2x.png",
        "acniret-care-logo-3x.png",
        "acniret-care-logo-dark.png",
        "acniret-care-logo-light.png",
        "acniret-care-logo-white.png",
        "acniret-care-logo-black.png",
        "acniret-care-logo-alt.png",
        "acniret-care-logo-stacked.png",
        "acniret-care-logo-horizontal.png",
        "acniret-care-logo-square.png",
        "acniret-care-mark.png",
        "acniret-care-mark.svg",
        "acniret-care-icon.png",
        "acniret-care-icon.svg",
        "acniret-care-wordmark.png",
        "acniret-care-wordmark.svg",
        "acniret-care-symbol.png",
        "acniret-care-favicon.png",
        "acniret-logo.png",
        "acniret-logo.svg",
        "acniret-mark.png",
    ]:
        probes.append(f"{ASSET_DIR}/{n}")

    for u in probes:
        st, ct, body = fetch(u)
        k, d = sniff(body)
        if st == 200 and k in KINDS:
            add(u, body, "probe")
        else:
            say(f"  - {st:>3} {ct[:32]:32} {u}")

    say("")
    say("###### PHASE B: og:image / social cards ######")
    st, ct, home = fetch(BASE + "/")
    txt = home.decode("utf-8", "replace")
    og = set(re.findall(r'<meta[^>]+(?:property|name)="(?:og:image|twitter:image)"[^>]+content="([^"]+)"', txt))
    og |= set(re.findall(r'<meta[^>]+content="([^"]+)"[^>]+(?:property|name)="(?:og:image|twitter:image)"', txt))
    for u in sorted(og):
        st2, ct2, b2 = fetch(u)
        k, d = sniff(b2)
        say(f"  og candidate {st2} {ct2[:30]} {k} {d} {u}")
        add(u, b2, "ogimage")

    say("")
    say("###### PHASE C: bundles - full scan ######")
    bundles = sorted(set(re.findall(r'["\'](/assets/[^"\']+\.(?:css|js))["\']', txt)))
    say(f"bundle count: {len(bundles)}")
    css_texts = []
    logo_hits = set()
    url_hits = set()
    for b in bundles:
        st3, ct3, body = fetch(BASE + b)
        if not body:
            say(f"  ! {st3} {b}")
            continue
        t = body.decode("utf-8", "replace")
        if b.endswith(".css"):
            css_texts.append((b, t))
        for m in re.findall(r"url\(\s*['\"]?([^)'\"]{1,300})['\"]?\s*\)", t):
            if re.search(r"logo|brand|mark|icon|favicon", m, re.I):
                url_hits.add(urllib.parse.urljoin(BASE + "/", m))
        for m in re.findall(r"[\w./:@%?=&+~-]{0,90}(?:logo|wordmark|brandmark)[\w./:@%?=&+~-]{0,90}", t, re.I):
            if len(m) > 10:
                logo_hits.add(f"{b}  ->  {m}")

    say("")
    say("--- url() refs matching logo/brand/icon ---")
    for u in sorted(url_hits)[:80]:
        say("   ", u)
        st4, ct4, b4 = fetch(u)
        k, d = sniff(b4)
        if st4 == 200 and k in KINDS:
            add(u, b4, "bundleurl")

    say("")
    say("--- explicit logo/wordmark/brandmark strings in bundles ---")
    for h in sorted(logo_hits)[:120]:
        say("   ", h)

    say("")
    say("--- CSS rules mentioning brand-logo / brand ---")
    for b, t in css_texts:
        for rule in re.findall(r"[^{}]{0,80}\.brand[^{}]{0,120}\{[^}]{0,400}\}", t):
            say(f"   [{b}] {rule.strip()[:400]}")

    say("")
    say("###### PHASE D: every distinct /assets image in all pages ######")
    pages = {}
    for p in ["/", "/safety", "/pricing", "/faq", "/how-it-works", "/patient",
              "/clinician", "/sign-in", "/auth", "/journey", "/assessment",
              "/labs", "/messages", "/staging", "/clinician/index"]:
        st5, ct5, b5 = fetch(BASE + p)
        if b5 and "html" in ct5:
            pages[p] = b5.decode("utf-8", "replace")
    refs = set()
    for p, t in pages.items():
        for m in re.findall(r'["\'](/[^"\']+\.(?:png|jpg|jpeg|svg|webp|ico))["\']', t):
            refs.add(m)
    for r in sorted(refs):
        say(f"   page-ref {r}")
        st6, ct6, b6 = fetch(BASE + r)
        k, d = sniff(b6)
        if k in KINDS and re.search(r"logo|brand|mark|favicon|icon", r, re.I):
            add(BASE + r, b6, "pageref")

    say("")
    say("###### SUMMARY ######")
    for u, (data, k, d) in found.items():
        say(f"{k:5} {d:>12} {len(data):>9}  {u}")

    say("")
    say("###### PAYLOAD ######")
    total = 0
    for u, (data, k, d) in found.items():
        if len(data) > MAX_FILE:
            say(f"===SKIP:{u}===")
            continue
        blk = base64.b64encode(data).decode()
        if total + len(blk) > 3_200_000:
            say(f"===TRUNCATED:{u}===")
            continue
        total += len(blk)
        say(f"===FILE:{u}|{k}|{d}|{len(data)}===")
        if k == "SVG":
            say("===TEXT===")
            say(data.decode("utf-8", "replace"))
        else:
            say("===B64===")
            for i in range(0, len(blk), 3000):
                say(blk[i:i + 3000])
        say("===ENDFILE===")
    say(f"###### TOTAL B64: {total} ######")

    with open(f"{OUT}/report.txt", "w") as fh:
        fh.write("\n".join(report) + "\n")
    with open(f"{OUT}/manifest.tsv", "w") as fh:
        fh.write("file\tkind\tdims\tbytes\tsource_url\n")
        for f in sorted(os.listdir(f"{OUT}/files")):
            b = open(f"{OUT}/files/{f}", "rb").read()
            k, d = sniff(b)
            fh.write(f"{f}\t{k}\t{d}\t{len(b)}\t\n")
    say("###### DONE ######")


if __name__ == "__main__":
    main()
