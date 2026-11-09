#!/usr/bin/env python3
"""Check docs/deepx-compact/X.md against docs/deepx/X.md (rules from CLAUDE.md):
  1. every source citation token is present in the compact copy (citations are never altered),
  2. the '## ' headings are identical and in the same order,
  3. report the word ratio (target ~0.91 overall; informational).
Citation token = bracketed text containing '@<hex hash>', starting with 'RT:', or containing 'fetched'
(formats in docs/deepx/CONVENTIONS.md). usage: check_compact.py [name.md ...]   exit 0 = all pass."""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC, CMP = ROOT / "docs/deepx", ROOT / "docs/deepx-compact"
CIT = re.compile(r"\[(?:[^\[\]]*@[0-9a-f]{7,}[^\[\]]*|RT:[^\[\]]*|[^\[\]]*fetched[^\[\]]*)\]")


def check(name):
    s, c = (SRC / name).read_text(), (CMP / name).read_text() if (CMP / name).exists() else None
    if c is None:
        return ["MISSING compact file"], 0.0
    errs = []
    miss = sorted({t for t in CIT.findall(s) if t not in c})
    errs += [f"citation missing: {t[:110]}" for t in miss]
    hs = [l for l in s.splitlines() if l.startswith("## ")]
    hc = [l for l in c.splitlines() if l.startswith("## ")]
    if hs != hc:
        errs.append(f"H2 mismatch: source {hs} vs compact {hc}")
    return errs, len(c.split()) / max(1, len(s.split()))


def main():
    names = sys.argv[1:] or sorted(p.name for p in SRC.glob("*.md"))
    bad = 0
    for n in names:
        errs, ratio = check(n)
        print(f"{'FAIL' if errs else 'ok  '} {n:34s} ratio {ratio:.2f}")
        for e in errs:
            print("     -", e)
        bad += bool(errs)
    print(f"{len(names) - bad}/{len(names)} pass")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
