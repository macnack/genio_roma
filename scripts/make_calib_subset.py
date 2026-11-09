#!/usr/bin/env python3
"""Seeded random calibration subset from the 1000-image calib pool (one image per ImageNet class; disjoint from the eval set).
Copies N jpgs into data/imagenet_subset/calib_sub/s<seed>_n<N>/ (copies, not symlinks: no loader surprises) and writes manifest.json
(seed, N, file list, sha256 per file). Deterministic: same seed + N -> identical list.
usage: make_calib_subset.py --seed S [--n 100] [--out DIR]   prints the output dir"""
import argparse, hashlib, json, random, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POOL = ROOT / "data/imagenet_subset/calib"
ap = argparse.ArgumentParser(); ap.add_argument("--seed", type=int, required=True); ap.add_argument("--n", type=int, default=100)
ap.add_argument("--out"); a = ap.parse_args()
files = sorted(p.name for p in POOL.glob("*.jpg"))
assert len(files) >= a.n, f"pool has {len(files)} < {a.n}"
pick = sorted(random.Random(a.seed).sample(files, a.n))
out = Path(a.out) if a.out else ROOT / f"data/imagenet_subset/calib_sub/s{a.seed}_n{a.n}"
if out.exists(): shutil.rmtree(out)
out.mkdir(parents=True)
man = {"seed": a.seed, "n": a.n, "pool": str(POOL.relative_to(ROOT)), "pool_size": len(files), "files": []}
for f in pick:
    shutil.copy2(POOL / f, out / f)
    man["files"].append({"file": f, "sha256": hashlib.sha256((out / f).read_bytes()).hexdigest()})
(out / "manifest.json").write_text(json.dumps(man, indent=1))
print(out)
