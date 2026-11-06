"""Shared preprocessing (single source of truth for all backends).
ConvNeXt eval transform (facebookresearch/ConvNeXt, crop_pct 0.875): resize shorter side to 256 (bicubic),
center-crop 224, RGB. The result is a uint8 HWC array; float normalisation is applied separately so the
DX-M1 path (which fuses div/normalize into the NPU graph and takes uint8 HWC) sees identical pixels.
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SUBSET = ROOT / "data/imagenet_subset"
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def load_u8(path, resize=256, crop=224):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    s = resize / min(w, h)
    nw, nh = max(resize, round(w * s)), max(resize, round(h * s))
    im = im.resize((nw, nh), Image.BICUBIC)
    l, t = (nw - crop) // 2, (nh - crop) // 2
    return np.asarray(im.crop((l, t, l + crop, t + crop)), dtype=np.uint8)


def to_nchw(u8):  # (N,H,W,3) uint8 -> (N,3,H,W) float32 normalised
    x = (u8.astype(np.float32) / 255.0 - MEAN) / STD
    return np.ascontiguousarray(x.transpose(0, 3, 1, 2))


def split(name):
    m = json.loads((SUBSET / "manifest.json").read_text())
    files = [f for f in m["files"] if f["split"] == name]
    return [SUBSET / f["file"] for f in files], np.array([f["label"] for f in files])


def cached_u8(name):
    p = SUBSET / f"{name}_u8_224.npz"
    if p.exists():
        z = np.load(p)
        return z["x"], z["y"]
    paths, y = split(name)
    x = np.stack([load_u8(q) for q in paths])
    np.savez(p, x=x, y=y)
    return x, y
