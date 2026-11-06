#!/usr/bin/env python3
"""Build a small, seeded, labelled ImageNet-1K *validation* subset.

Source: HF dataset mrm8488/ImageNet1K-val (ungated, 14 parquet shards, class-sorted, label = index in
sorted-wnid order). Shards are fetched one at a time, K images per class are kept by a seeded hash
ranking (deterministic, independent of shard boundaries), then the shard is deleted.

Output (data/ is git-ignored):
  data/imagenet_subset/calib/<label>_<hash>.jpg   N_CALIB per class  (DX-COM calibration)
  data/imagenet_subset/eval/<label>_<hash>.jpg    N_EVAL per class   (accuracy; disjoint from calib)
  data/imagenet_subset/manifest.json              seed, shard sha256, per-file label and sha256

Usage: python scripts/make_imagenet_subset.py [--seed 0] [--calib-per-class 1] [--eval-per-class 4]
"""
import argparse, hashlib, json, os, shutil, subprocess, sys
from pathlib import Path

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw"
OUT = ROOT / "data/imagenet_subset"
URL = "https://huggingface.co/datasets/mrm8488/ImageNet1K-val/resolve/main/data/train-{i:05d}-of-00014.parquet"
MIN_FREE_GB = 16


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def free_gb():
    return shutil.disk_usage(ROOT).free / 1e9


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--calib-per-class", type=int, default=1)
    ap.add_argument("--eval-per-class", type=int, default=4)
    a = ap.parse_args()
    keep = a.calib_per_class + a.eval_per_class
    RAW.mkdir(parents=True, exist_ok=True)
    best = {}  # label -> list[(rank, jpeg_bytes)]
    shard_sha = {}
    for i in range(14):
        p = RAW / f"shard{i:02d}.parquet"
        legacy = RAW / "imagenet_val_shard00.parquet"
        if i == 0 and legacy.exists() and not p.exists():
            legacy.rename(p)
        if not p.exists():
            if free_gb() < MIN_FREE_GB:
                sys.exit(f"STOP: only {free_gb():.1f} GB free (< {MIN_FREE_GB})")
            print(f"download shard {i}", flush=True)
            subprocess.run(["curl", "-fL", "--retry", "5", "--retry-delay", "5", "-C", "-", "-sS",
                            "-o", str(p), URL.format(i=i)], check=True)
        shard_sha[i] = sha256_file(p)
        t = pq.ParquetFile(p).read().to_pydict()
        for row, (img, lab) in enumerate(zip(t["image"], t["label"])):
            b = img["bytes"]
            rank = hashlib.sha256(f"{a.seed}:{lab}:{hashlib.sha256(b).hexdigest()}".encode()).hexdigest()
            lst = best.setdefault(lab, [])
            lst.append((rank, b))
            lst.sort(key=lambda x: x[0])
            del lst[keep:]
        del t
        p.unlink()
        print(f"shard {i} done: {len(best)} classes so far, free {free_gb():.1f} GB", flush=True)

    manifest = {"source": "mrm8488/ImageNet1K-val (ImageNet-1K validation, label = sorted-wnid index)",
                "seed": a.seed, "calib_per_class": a.calib_per_class, "eval_per_class": a.eval_per_class,
                "shard_sha256": shard_sha, "files": []}
    for split in ("calib", "eval"):
        (OUT / split).mkdir(parents=True, exist_ok=True)
    for lab in sorted(best):
        for k, (rank, b) in enumerate(best[lab]):
            split = "calib" if k < a.calib_per_class else "eval"
            name = f"{lab:04d}_{rank[:8]}.jpg"
            (OUT / split / name).write_bytes(b)
            manifest["files"].append({"split": split, "file": f"{split}/{name}", "label": lab,
                                      "sha256": hashlib.sha256(b).hexdigest()})
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1))
    n = {s: sum(1 for f in manifest["files"] if f["split"] == s) for s in ("calib", "eval")}
    print("classes", len(best), "files", n)


if __name__ == "__main__":
    main()
