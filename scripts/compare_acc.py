#!/usr/bin/env python3
"""Compare device outputs with the FP32 ONNX reference on the same eval images.
Usage: compare_acc.py ref_out.npy dev_out.npy [--labels data/imagenet_subset/eval_y.npy] [--feature]"""
import argparse, json
import numpy as np
ap = argparse.ArgumentParser(); ap.add_argument("ref"); ap.add_argument("dev")
ap.add_argument("--labels", default="data/imagenet_subset/eval_y.npy"); ap.add_argument("--feature", action="store_true")
a = ap.parse_args()
r, d = np.load(a.ref).astype(np.float64), np.load(a.dev).astype(np.float64)
y = np.load(a.labels); n = len(r)
cos = (r * d).sum(1) / (np.linalg.norm(r, axis=1) * np.linalg.norm(d, axis=1))
res = {"n": n, "cosine_mean": float(cos.mean()), "cosine_min": float(cos.min()),
       "max_abs_diff": float(np.abs(r - d).max()), "rel_l2_mean": float((np.linalg.norm(r - d, axis=1) / np.linalg.norm(r, axis=1)).mean())}
if not a.feature:
    def acc(o):
        t5 = np.argsort(-o, 1)[:, :5]; return float((t5[:, 0] == y).mean()), float((t5 == y[:, None]).any(1).mean())
    (res["ref_top1"], res["ref_top5"]), (res["dev_top1"], res["dev_top5"]) = acc(r), acc(d)
    res["top1_agreement"] = float((r.argmax(1) == d.argmax(1)).mean())
    p = lambda o: np.exp(o - o.max(1, keepdims=True)) / np.exp(o - o.max(1, keepdims=True)).sum(1, keepdims=True)
    pr, pd_ = p(r), p(d); res["kl_ref_dev_mean"] = float((pr * (np.log(pr + 1e-12) - np.log(pd_ + 1e-12))).sum(1).mean())
    # 95% Wilson-ish binomial half-width for top1 on n images
    for k in ("ref_top1", "dev_top1"): res[k + "_ci95"] = float(1.96 * np.sqrt(res[k] * (1 - res[k]) / n))
print(json.dumps(res, indent=1))
