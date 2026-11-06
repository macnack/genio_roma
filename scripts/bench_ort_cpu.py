#!/usr/bin/env python3
"""Board CPU baseline: ONNX Runtime CPU EP, FP32, batch 1, sync. Latency (mean/p50/p95) over N timed runs after warmup,
plus parity of outputs with a saved reference on the first K images. Pin cores externally with taskset.
Usage: taskset -c 6,7 python bench_ort_cpu.py --onnx m.onnx --x eval_u8.npy --threads 2 [--ref ref_out.npy] [--runs 30]"""
import argparse, json, time
import numpy as np, onnxruntime as ort
ap = argparse.ArgumentParser()
ap.add_argument("--onnx", required=True); ap.add_argument("--x", required=True)
ap.add_argument("--threads", type=int, required=True); ap.add_argument("--runs", type=int, default=30)
ap.add_argument("--warmup", type=int, default=3); ap.add_argument("--ref"); ap.add_argument("--k", type=int, default=10)
a = ap.parse_args()
MEAN = np.array([0.485, 0.456, 0.406], np.float32); STD = np.array([0.229, 0.224, 0.225], np.float32)
x = np.load(a.x, mmap_mode="r")
prep = lambda u8: np.ascontiguousarray(((u8.astype(np.float32) / 255 - MEAN) / STD).transpose(2, 0, 1)[None])
so = ort.SessionOptions(); so.intra_op_num_threads = a.threads; so.inter_op_num_threads = 1
t0 = time.time(); s = ort.InferenceSession(a.onnx, so, providers=["CPUExecutionProvider"]); load_s = time.time() - t0
name = s.get_inputs()[0].name
inp = prep(x[0])
for _ in range(a.warmup): s.run(None, {name: inp})
lat = []
for i in range(a.runs):
    d = prep(x[i % len(x)]); t = time.perf_counter(); s.run(None, {name: d}); lat.append((time.perf_counter() - t) * 1000)
lat = np.array(lat); res = {"onnx": a.onnx, "threads": a.threads, "runs": a.runs, "load_s": load_s, "lat_ms_mean": float(lat.mean()),
       "lat_ms_p50": float(np.percentile(lat, 50)), "lat_ms_p95": float(np.percentile(lat, 95)), "fps_sync": float(1000 / lat.mean())}
if a.ref:
    ref = np.load(a.ref)[:a.k]; got = np.concatenate([s.run(None, {name: prep(x[i])})[0] for i in range(a.k)])
    res["max_abs_vs_laptop_fp32"] = float(np.abs(ref - got).max())
print(json.dumps(res))
