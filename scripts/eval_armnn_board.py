#!/usr/bin/env python3
"""Arm NN (PyArmNN) TFLite evaluation on the board over uint8 NHWC RGB images (same eval_u8.npy as the DX-M1 run).
Preprocessing here: float32 = (u8/255 - mean)/std (ImageNet), NHWC. Saves logits and timing.
usage: eval_armnn_board.py --model m.tflite --x eval_u8.npy --out prefix --backends GpuAcc,CpuAcc [--n N] [--fp16]"""
import argparse, json, time, numpy as np, pyarmnn as ann
ap = argparse.ArgumentParser()
ap.add_argument("--model", required=True); ap.add_argument("--x", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--backends", default="GpuAcc,CpuAcc"); ap.add_argument("--n", type=int, default=0); ap.add_argument("--fp16", action="store_true")
a = ap.parse_args()
mean = np.array([0.485, 0.456, 0.406], np.float32) * 255; std = np.array([0.229, 0.224, 0.225], np.float32) * 255
x = np.load(a.x, mmap_mode="r"); n = a.n or len(x)
p = ann.ITfLiteParser(); net = p.CreateNetworkFromBinaryFile(a.model)
ib = p.GetNetworkInputBindingInfo(0, p.GetSubgraphInputTensorNames(0)[0]); ob = p.GetNetworkOutputBindingInfo(0, p.GetSubgraphOutputTensorNames(0)[0])
rt = ann.IRuntime(ann.CreationOptions()); oo = ann.OptimizerOptions(); oo.m_ReduceFp32ToFp16 = a.fp16
opt, _ = ann.Optimize(net, [ann.BackendId(b) for b in a.backends.split(",")], rt.GetDeviceSpec(), oo)
nid, _ = rt.LoadNetwork(opt); ot = ann.make_output_tensors([ob])
outs, lat = [], []; t0 = time.time()
for i in range(n):
    xi = np.ascontiguousarray(((x[i].astype(np.float32) - mean) / std)[None])
    t = time.perf_counter(); rt.EnqueueWorkload(nid, ann.make_input_tensors([ib], [xi]), ot); lat.append((time.perf_counter() - t) * 1e3)
    outs.append(ann.workload_tensors_to_ndarray(ot)[0].reshape(-1).copy())
    if i % 200 == 0: print(i, f"{time.time()-t0:.0f}s", flush=True)
outs = np.stack(outs); np.save(a.out + "_out.npy", outs)
res = {"model": a.model, "backends": a.backends, "fp16": a.fp16, "n": n, "wall_s": time.time() - t0, "run_ms_mean": float(np.mean(lat)),
       "run_ms_p50": float(np.percentile(lat, 50)), "run_ms_p95": float(np.percentile(lat, 95))}
json.dump(res, open(a.out + ".json", "w"), indent=1); print(res)
