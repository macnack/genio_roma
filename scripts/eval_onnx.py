#!/usr/bin/env python3
"""FP32 ONNX Runtime (CPU) reference on the eval split. Saves outputs for later comparison.
Usage: python scripts/eval_onnx.py --onnx model.onnx --out reports/acc/A13_fp32 [--split eval]"""
import argparse, json, sys
from pathlib import Path

import numpy as np
import onnxruntime as ort

sys.path.insert(0, str(Path(__file__).parent))
import preproc

ap = argparse.ArgumentParser()
ap.add_argument("--onnx", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--split", default="eval")
a = ap.parse_args()

x_u8, y = preproc.cached_u8(a.split)
sess = ort.InferenceSession(a.onnx, providers=["CPUExecutionProvider"])
name = sess.get_inputs()[0].name
outs = np.concatenate([sess.run(None, {name: preproc.to_nchw(x_u8[i:i + 1])})[0] for i in range(len(x_u8))])
Path(a.out).parent.mkdir(parents=True, exist_ok=True)
np.save(a.out + "_out.npy", outs)
res = {"onnx": a.onnx, "n": int(len(y)), "out_shape": list(outs.shape)}
if outs.shape[1] == 1000:
    top5 = np.argsort(-outs, 1)[:, :5]
    res["top1"] = float((top5[:, 0] == y).mean()); res["top5"] = float((top5 == y[:, None]).any(1).mean())
json.dump(res, open(a.out + ".json", "w"), indent=1); print(res)
