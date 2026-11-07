#!/usr/bin/env python3
"""Board: ORT CPU EP over the first N eval images (u8 NHWC -> normalised NCHW), saves logits and latency. Pin cores with taskset.
usage: taskset -c 0-7 python eval_ort_board.py --onnx m.onnx --x eval_u8.npy --out name --threads 8 [--n 4000]"""
import argparse, json, time, numpy as np, onnxruntime as ort
ap = argparse.ArgumentParser(); ap.add_argument("--onnx", required=True); ap.add_argument("--x", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--threads", type=int, required=True); ap.add_argument("--n", type=int, default=4000); a = ap.parse_args()
MEAN = np.array([0.485, 0.456, 0.406], np.float32); STD = np.array([0.229, 0.224, 0.225], np.float32)
x = np.load(a.x, mmap_mode="r")[:a.n]
so = ort.SessionOptions(); so.intra_op_num_threads = a.threads; so.inter_op_num_threads = 1
s = ort.InferenceSession(a.onnx, so, providers=["CPUExecutionProvider"]); name = s.get_inputs()[0].name
out, lat, t00 = [], [], time.time()
for i in range(len(x)):
    d = np.ascontiguousarray(((x[i].astype(np.float32) / 255 - MEAN) / STD).transpose(2, 0, 1)[None])
    t = time.perf_counter(); y = s.run(None, {name: d})[0]; lat.append((time.perf_counter() - t) * 1000); out.append(np.asarray(y, np.float32).ravel())
    if i % 400 == 0: print(i, round(time.time() - t00), flush=True)
np.save(a.out + "_out.npy", np.stack(out)); lat = np.array(lat[3:])
r = dict(onnx=a.onnx, threads=a.threads, n=len(x), run_ms_mean=float(lat.mean()), run_ms_p50=float(np.percentile(lat, 50)), run_ms_p95=float(np.percentile(lat, 95)))
json.dump(r, open(a.out + ".json", "w")); print(r)
