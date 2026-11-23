#!/usr/bin/env python3
"""Pass 3: full asset inventory from JS/CSS bundles + versioned-path resolution."""
import os
import re
import ssl
import struct
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://acniret.com"
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
OUT = "_assetpull3"
rep = []


def say(*a):
    line = " ".join(str(x) for x in a)
    print(line)
    rep.append(line)


def fetch(url, timeout=60):
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
        return "ICO", "icon"
    if b[:4] == b"RIFF" and b[8:12] == b"WEBP":
        return "WEBP", "?"
    if b[:6] in (b"GIF87a", b"GIF89a"):
        return "GIF", "?"
    return "OTHER", ""


KINDS = {"PNG", "JPEG", "SVG", "ICO", "WEBP", "GIF"}
os.makedirs(f"{OUT}/files", exist_ok=True)
captured = {}


def save(url, body, label):
    k, d = sniff(body)
    if not body or k not in KINDS or url in captured:
        return
    ext = {"PNG": "png", "JPEG": "jpg", "SVG": "svg", "ICO": "ico",
           "WEBP": "webp", "GIF": "gif"}[k]
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", os.path.basename(urllib.parse.urlparse(url).path) or "asset")
    if not base.lower().endswith("." + ext):
        base += "." + ext
    name = f"{len(captured) + 1:02d}_{label}_{base}"
    open(f"{OUT}/files/{name}", "wb").write(body)
    captured[url] = (name, k, d, len(body))
    say(f"  + {k:4} {d:>10} {len(body):>8} -> {name}   <- {url}")


def main():
    say("###### BUNDLES ######")
    st, ct, home = fetch(BASE + "/")
    html = home.decode("utf-8", "replace")
    bundles = sorted(set(re.findall(r'["\'](/assets/[^"\']+\.(?:css|js))["\']', html)))
    texts = {}
    for b in bundles:
        st2, ct2, body = fetch(BASE + b)
        if body:
            texts[b] = body.decode("utf-8", "replace")
            open(f"{OUT}/{os.path.basename(b)}.txt", "w").write(texts[b])
    say(f"bundles fetched: {len(texts)} / {len(bundles)}")

    say("")
    say("###### ALL assets-v1 REFERENCES ######")
    refs = set()
    for b, t in texts.items():
        for m in re.findall(r"[\w./@:-]*assets-v1[\w./@:-]*", t):
            refs.add(m)
    for r in sorted(refs):
        say("  ", r)

    say("")
    say("###### ALL data: IMAGE URIs (inline svg?) ######")
    datas = set()
    for b, t in texts.items():
        for m in re.findall(r"data:image/[\w+.-]{1,20};base64,([A-Za-z0-9+/=]{20,})", t):
            datas.add(m)
    say(f"inline image data URIs: {len(datas)}")

    say("")
    say("###### VERSIONED PATH CONTEXT ######")
    for b, t in texts.items():
        for m in re.finditer(r".{120}assets-v1.{160}", t):
            say(f"  [{b}] ...{m.group(0)}...")
            say("")

    say("")
    say("###### PROBE VERSIONED + LIKELY PATHS ######")
    cands = set()
    for r in refs:
        if r.startswith("/"):
            cands.add(BASE + r)
        else:
            cands.add(urllib.parse.urljoin(BASE + "/", r))
    # construct versioned forms explicitly
    for v in re.findall(r"v1/([a-f0-9-]{36})/([a-f0-9-]{36})", " ".join(refs)):
        cands.add(f"{BASE}/__l5e/assets-v1/v1/{v[0]}/{v[1]}/acniret-care-logo.png")
        cands.add(f"{BASE}/__l5e/assets-v1/{v[0]}/{v[1]}/acniret-care-logo.png")
    for u in sorted(cands):
        st3, ct3, body = fetch(u)
        k, d = sniff(body)
        status = f"{st3} {k} {d} {len(body)}"
        say(f"  {status:28} {u}")
        if st3 == 200 and k in KINDS:
            save(u, body, "cand")

    say("")
    say("###### BRAND-LOGO CSS CONTEXT ######")
    for b, t in texts.items():
        for m in re.finditer(r"[^{}]{0,60}brand[^{}]{0,80}\{[^}]{0,300}\}", t):
            say(f"  [{b}] {m.group(0)[:350]}")

    say("")
    say("###### SUMMARY ######")
    for u, (n, k, d, ln) in captured.items():
        say(f"{k:5} {d:>12} {ln:>9}  {n}  <- {u}")

    with open(f"{OUT}/report.txt", "w") as fh:
        fh.write("\n".join(rep) + "\n")
    with open(f"{OUT}/manifest.tsv", "w") as fh:
        fh.write("file\tkind\tdims\tbytes\tsource_url\n")
        for u, (n, k, d, ln) in captured.items():
            fh.write(f"{n}\t{k}\t{d}\t{ln}\t{u}\n")
    say("###### DONE ######")


if __name__ == "__main__":
    main()
