#!/usr/bin/env python3
"""Run a .dxnn on the DX-M1 via dx_engine (board, RT 3.4.2) over uint8 HWC images; save outputs + timings.
Input must already be resized/cropped RGB uint8 [N,224,224,3] (see scripts/preproc.py); div/normalize/transpose
are fused in the NPU graph by DX-COM (see compiler.log 'INPUT PREPROCESSING GUIDANCE').
Usage (on board): python eval_dx_board.py --model m.dxnn --x eval_u8.npy --out out_prefix [--n N]"""
import argparse, json, time
import numpy as np
from dx_engine import InferenceEngine

ap = argparse.ArgumentParser()
ap.add_argument("--model", required=True); ap.add_argument("--x", required=True)
ap.add_argument("--out", required=True); ap.add_argument("--n", type=int, default=0)
a = ap.parse_args()

x = np.load(a.x, mmap_mode="r")
n = a.n or len(x)
ie = InferenceEngine(a.model)
print("inputs", ie.get_input_tensors_info()); print("outputs", ie.get_output_tensors_info(), flush=True)
outs, lat, npu = [], [], []
t0 = time.time()
for i in range(n):
    o = ie.run([np.ascontiguousarray(x[i])])
    outs.append(np.asarray(o[0]).reshape(-1).astype(np.float32))
    lat.append(ie.get_latency()); npu.append(ie.get_npu_inference_time())
wall = time.time() - t0
outs = np.stack(outs)
np.save(a.out + "_out.npy", outs)
res = {"model": a.model, "n": n, "out_shape": list(outs.shape), "wall_s": wall, "wall_ms_per_img": 1000 * wall / n,
       "latency_us_mean": float(np.mean(lat)), "latency_us_p95": float(np.percentile(lat, 95)),
       "npu_us_mean": float(np.mean(npu))}
json.dump(res, open(a.out + ".json", "w"), indent=1); print(res)
