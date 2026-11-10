#!/usr/bin/env python3
"""Split the 1000-image calib pool (one per class) into two disjoint halves, seeded:
  data/imagenet_subset/calib_split/src/  500 jpgs  candidate calibration source (subsets are drawn from here)
  data/imagenet_subset/calib_split/sel/  500 jpgs  held-out SELECTION set (never used for calibration; disjoint from the 4000 eval images)
Also writes sel_u8.npy (500,224,224,3 uint8, same preprocessing as eval_u8.npy), sel_y.npy (labels from the file-name prefix) and split.json.
usage: make_calib_split.py [--seed 123]"""
import argparse, json, random, shutil, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent)); import preproc
ROOT = Path(__file__).resolve().parents[1]; POOL = ROOT / "data/imagenet_subset/calib"; OUT = ROOT / "data/imagenet_subset/calib_split"
ap = argparse.ArgumentParser(); ap.add_argument("--seed", type=int, default=123); a = ap.parse_args()
files = sorted(p.name for p in POOL.glob("*.jpg")); rnd = random.Random(a.seed); rnd.shuffle(files)
h = len(files) // 2; src, sel = sorted(files[:h]), sorted(files[h:])
assert not set(src) & set(sel)
if OUT.exists(): shutil.rmtree(OUT)
for n, fl in (("src", src), ("sel", sel)):
    (OUT / n).mkdir(parents=True)
    for f in fl: shutil.copy2(POOL / f, OUT / n / f)
np.save(OUT / "sel_u8.npy", np.stack([preproc.load_u8(OUT / "sel" / f) for f in sel]))
np.save(OUT / "sel_y.npy", np.array([int(f.split("_")[0]) for f in sel]))
json.dump({"seed": a.seed, "src": src, "sel": sel}, open(OUT / "split.json", "w"), indent=1)
print(len(src), len(sel))
