#!/usr/bin/env python3
"""Audit prose for the flat, machine-written voice, then rewrite what it flags.

  python3 style_audit.py FILE.md [more.md ...] [--fix]

Reports: throat-clearing openers, puffed-up adjectives, "it's not X, it's Y"
turns, jargon, and the rule-of-three rhythm (x, y and z) — with the offending
snippet and a count, so you can decide which hits are real lists (fine) and
which are a tic (rewrite). --fix prints nothing about style but fails loudly on
mechanical problems: unbalanced ** and markdown-link syntax that the renderer
will leak into the output.
"""
import re, sys

BANNED = {
    "throat-clearing": [
        r"it is (?:important|worth noting|crucial|essential|vital) to",
        r"\bit'?s worth (?:noting|mentioning|saying)\b", r"needless to say",
        r"at the end of the day", r"make no mistake", r"let'?s (?:dive|start|explore|take a)",
        r"in today'?s (?:fast-paced|world)", r"look no further", r"the part (?:most|few) people (?:miss|skip)",
        r"before we (?:begin|start)", r"without further ado", r"as we all know",
    ],
    "puffed-up": [
        r"\brevolutionary\b", r"\btransformative\b", r"\bgame.?chang", r"\bseamless",
        r"\brobust\b", r"\bholistic\b", r"\bcomprehensive\b", r"\bmeticulous", r"\bpowerful\b",
        r"\bultimate\b", r"\bworld.?class\b", r"\bdeep dive\b", r"\bunlock", r"\bdelve\b",
        r"\btapestry\b", r"\bindisputab", r"\bundeniable\b",
    ],
    "negative framing": [
        r"\bit'?s not (?:just|only|really)? ?a\b[^.]{0,60}\bit'?s\b",
        r"\bnot (?:because|a problem)[^.]{0,70}\b(?:but|rather)\b",
        r"\bx rather than y\b", r"\bthis (?:isn'?t|is not) \w+, (?:it'?s|this is)\b",
    ],
    "consultant speak": [
        r"\bstakeholder", r"\bleverage", r"\bparadigm", r"\bsynerg", r"\butiliz",
        r"\bmove the needle\b", r"\blow.hanging fruit\b", r"\bnew normal\b",
        r"\bjourney of a thousand miles\b", r"\bempower", r"\bfoster a culture\b",
    ],
}


def tricolons(text):
    text = strip_code(text)
    hits = []
    for ln, line in enumerate(text.split("\n"), 1):
        if line.strip().startswith(("|", "```", "> ")):
            continue
        for seg in re.split(r"(?<=[.;])\s+", line):
            if re.search(r"\b\w+[^,.;:]{0,32}, \w+[^,.;:]{0,32} and \w+", seg):
                hits.append((ln, seg.strip()[:120]))
    return hits


def strip_code(text):
    """Blank out fenced blocks and inline code so examples like `**` inside a
    code span are not mistaken for unbalanced emphasis."""
    text = re.sub(r"```.*?```", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    return re.sub(r"`[^`\n]*`", "", text)


def mechanical(text):
    text = strip_code(text)
    probs = []
    for ln, line in enumerate(text.split("\n"), 1):
        if line.count("**") % 2:
            probs.append(f"line {ln}: unbalanced ** (renders as stray asterisks)")
        for m in re.finditer(r"\[[^\]]*\]\(([^)]*)\)", line):
            if not m.group(1).startswith("http") or " " in m.group(1).strip():
                probs.append(f"line {ln}: suspicious link target '{m.group(1)[:40]}'")
    fences = sum(1 for l in text.split("\n") if l.strip().startswith("```"))
    if fences % 2:
        probs.append(f"odd number of ``` fences ({fences}) — code block will swallow the rest")
    return probs


def main(argv):
    fix = "--fix" in argv
    files = [a for a in argv if not a.startswith("--")]
    total = 0
    for f in files:
        text = open(f, encoding="utf-8").read()
        print(f"\n=== {f}")
        probs = mechanical(text)
        for p in probs:
            print("  MECHANICAL:", p)
        if fix:
            continue
        for cat, pats in BANNED.items():
            hits = []
            for pat in pats:
                for m in re.finditer(pat, text, re.I):
                    s = max(0, m.start() - 45)
                    hits.append(text[s:m.end() + 45].replace("\n", " ").strip())
            print(f"  {cat}: {len(hits)}")
            for h in hits[:8]:
                print(f"     … {h}")
        tri = tricolons(text)
        print(f"  rule-of-three candidates: {len(tri)}  (check each: real lists are fine, tics are not)")
        for ln, seg in tri[:10]:
            print(f"     p{ln}: {seg}")
        total += len(probs)
    print("\nmechanical problems:", total)
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
