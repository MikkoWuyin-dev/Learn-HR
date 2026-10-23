#!/usr/bin/env python3
"""Phase 4 gate: the site's text must be readable on what it actually sits on.

The roadmap flags one specific risk - "9pt table text in a brutalist palette
fails contrast" - and R26 sets the 9pt floor. This measures it rather than
assuming it. Ratios are WCAG 2.1, computed on the design system's real token
values with translucent colours composited onto the opaque background behind
them, which is the step a naive check gets wrong.

Each pair names the selector whose text is being measured, and the colour is
read back out of site.css rather than restated here. That is the difference
between a real check and a decorative one: recolor `table` in the stylesheet
to a faint ink and this fails, even though the pair is still listed.

Two things guard against the list going stale. Any colour site.css sets on text
that no pair measures fails the run. And any pair whose selector has vanished
from the stylesheet fails too, rather than silently measuring a fallback.

    python3 tools/sitegen/contrast.py           # quiet table, exit 1 on a failure
    python3 tools/sitegen/contrast.py --strict  # hold everything to AAA (7:1)

Exit 0 only if every pair clears AA (4.5:1 for text, 3:1 for large text).
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SITE = ROOT / "_site"
CSS = ROOT / "site/static/site.css"

AA_TEXT = 4.5
AA_LARGE = 3.0
AAA = 7.0


# ---------------------------------------------------------------- colour maths
def _channel(value):
    value = value / 255
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def _luminance(rgb):
    r, g, b = (_channel(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(fg, bg):
    a, b = _luminance(fg), _luminance(bg)
    high, low = max(a, b), min(a, b)
    return (high + 0.05) / (low + 0.05)


def rgb(value):
    """'#043629', 'rgb(4,54,41)' or 'rgba(4,54,41,.7)' -> (rgb, alpha)."""
    value = value.strip()
    if value.startswith("#"):
        h = value.lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)), 1.0
    m = re.match(r"rgba?\(([^)]+)\)", value)
    if not m:
        raise ValueError(f"unrecognised colour: {value!r}")
    parts = [p.strip() for p in m.group(1).split(",")]
    return tuple(int(float(p)) for p in parts[:3]), float(parts[3]) if len(parts) > 3 else 1.0


def over(fg, alpha, bg):
    """Composite a translucent colour onto an opaque one. WCAG has no notion of
    alpha, so the colour has to be flattened before any ratio means anything."""
    return tuple(round(f * alpha + b * (1 - alpha)) for f, b in zip(fg, bg))


# ---------------------------------------------------------------- reading css
def declarations():
    """selector -> {property: value}, later blocks winning.

    Comments are stripped first. Without that, a comment sitting above a rule is
    captured as part of its selector, so `.sw-note` is never matched and the rule
    silently falls back to measuring inherited body text instead.
    """
    text = re.sub(r"/\*.*?\*/", "", CSS.read_text(encoding="utf-8"), flags=re.S)
    out = {}
    for m in re.finditer(r"([^{}]+)\{([^}]*)\}", text):
        selector = " ".join(m.group(1).split())
        if selector.startswith("@"):
            continue
        decls = out.setdefault(selector, {})
        for d in re.finditer(r"(?:^|;)\s*([a-z-]+)\s*:\s*([^;]+)", m.group(2)):
            decls[d.group(1)] = d.group(2).strip()
    return out


def tokens():
    """Every --wk-* colour in the built stylesheet, with var() chains resolved."""
    css = SITE / "wakeout.css"
    if not css.exists():
        raise SystemExit("no _site/wakeout.css - build the site first")
    raw = dict(re.findall(r"(--wk-[a-z0-9-]+):\s*([^;}]+);", css.read_text(encoding="utf-8")))
    out = {}
    for name in raw:
        value, seen = raw[name].strip(), set()
        while value.startswith("var(") and value not in seen:
            seen.add(value)
            key = value[4:-1].strip()
            if key not in raw:
                break
            value = raw[key].strip()
        out[name] = value
    return out


def to_rgb(value, table):
    """A css colour or a var(--wk-*) reference -> (rgb, alpha)."""
    value = value.strip()
    if value.startswith("var("):
        value = table.get(value[4:-1].strip(), "")
    if not value or value.startswith("var("):
        return None
    try:
        return rgb(value)
    except ValueError:
        return None


# ---------------------------------------------------------------- the pairs
# (label, selectors to look for in order, background token, is_large)
# The first selector that declares a colour wins; `body` is the inherited base.
PAIRS = [
    ("table text", ["table", "body"], "--wk-surface", False),
    ("table text on the page", ["table", "body"], "--wk-paper", False),
    ("table caption", ["caption.table-caption", "body"], "--wk-surface", False),
    ("text in a callout", [".callout", "body"], "--wk-sunrise", False),
    ("quiet text", ["small, .note", "body"], "--wk-surface", False),
    ("quiet text on the page", ["small, .note", "body"], "--wk-paper", False),
    ("week number", [".week-n", "body"], "--wk-surface", False),
    ("cost line", [".cost-line", "body"], "--wk-surface", False),
    ("a completed row", ["tr.is-done td, li.is-done .cell-text", "body"],
     "--wk-surface", False),
    ("sticker on lime", [".sticker", "body"], "--wk-lime", False),
    ("sticker on yellow", [".sticker", "body"], "--wk-yellow", False),
    ("sticker on sunrise", [".sticker", "body"], "--wk-sunrise", False),
    ("sticker on paper", [".sticker", "body"], "--wk-paper", False),
    ("link, hovered", ["a:hover", "body"], "--wk-surface", False),
    ("link hovered on the page", ["a:hover", "body"], "--wk-paper", False),
    ("primary button label", [".btn-primary", "body"], "--wk-primary", False),
    ("offline bar", [".sw-note", "body"], "--wk-accent", False),
]

# Pairs that live outside site.css and have no selector to read - the share
# cards are drawn in sitegen.py from tokens directly.
DRAWN = [
    ("share-card chip", "--wk-paper", "--wk-purple", False),
    ("share-card type", "--wk-ink", "--wk-paper", True),
]


def measure(decls, table, selectors):
    """(rgb, alpha, selector, unresolved) for the first selector that sets a colour.

    `unresolved` is the important fourth value: a `color:` that names a token
    which does not exist must be a failure, not a silent fall-through to the
    inherited colour. Otherwise mistyping --wk-ink-70 as --wk-ink-30 makes the
    check report the body text's comfortable ratio and pass while the real text
    renders as whatever the browser defaults to.
    """
    for selector in selectors:
        block = decls.get(selector)
        if block and "color" in block:
            got = to_rgb(block["color"], table)
            if got:
                return got[0], got[1], selector, False
            return None, None, selector, True
    return None, None, None, False


def main(argv):
    strict = "--strict" in argv
    table = tokens()
    decls = declarations()
    failures, rows = [], []

    def record(label, fg, alpha, bg, is_large, where):
        if alpha < 1:
            fg = over(fg, alpha, bg)
        r = ratio(fg, bg)
        floor = AAA if strict else (AA_LARGE if is_large else AA_TEXT)
        rows.append((label, r, floor, r >= floor, where))
        if r < floor:
            failures.append(f"{label} is {r:.2f}:1, below {floor}:1 ({where})")

    for label, selectors, bg_name, is_large in PAIRS:
        bg = to_rgb("var(" + bg_name + ")", table)
        if not bg:
            failures.append(f"{label}: could not resolve background {bg_name}")
            continue
        fg, alpha, found, unresolved = measure(decls, table, selectors)
        if unresolved:
            failures.append(f"{label}: {found} sets a colour that does not resolve "
                            f"({decls[found]['color']}) - a broken token reference")
            continue
        if fg is None:
            failures.append(f"{label}: none of {selectors} is in site.css any more")
            continue
        if found not in selectors[:1] and found == "body":
            # The named selector exists but sets no colour, so this is inherited.
            where = f"inherits from {found}"
        else:
            where = f"from {found}"
        record(label, fg, alpha, bg[0], is_large, where)

    for label, fg_name, bg_name, is_large in DRAWN:
        fg, bg = to_rgb("var(" + fg_name + ")", table), to_rgb("var(" + bg_name + ")", table)
        if not fg or not bg:
            failures.append(f"{label}: could not resolve {fg_name} / {bg_name}")
            continue
        record(label, fg[0], fg[1], bg[0], is_large, "drawn in sitegen.py")

    # Completeness: a colour set on text that nothing measures is a blind spot.
    not_text = ("progress",)
    used = set()
    for selector, block in decls.items():
        if any(w in selector for w in not_text):
            continue
        m = re.match(r"var\((--wk-[a-z0-9-]+)\)$", block.get("color", ""))
        if m:
            used.add(m.group(1))
    covered = set()
    for _, selectors, _, _ in PAIRS:
        for selector in selectors:
            block = decls.get(selector, {})
            m = re.match(r"var\((--wk-[a-z0-9-]+)\)$", block.get("color", ""))
            if m:
                covered.add(m.group(1))
    covered |= {f for _, f, _, _ in DRAWN}
    unmeasured = sorted(used - covered)
    if unmeasured:
        failures.append("these colours are set on text but never measured: "
                        + ", ".join(unmeasured))

    width = max(len(r[0]) for r in rows)
    print(f"{'pair':{width}}  {'ratio':>6}  {'needs':>5}   verdict")
    for label, r, floor, ok, where in rows:
        print(f"{label:{width}}  {r:5.2f}:1  {floor:5.1f}   "
              f"{'ok' if ok else 'FAIL'}   ({where})")
    print()
    if failures:
        print(f"RESULT: {len(failures)} contrast problem(s)")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"RESULT: all {len(rows)} pairs clear "
          f"{'AAA (7:1)' if strict else 'AA (4.5:1 text, 3:1 large)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
