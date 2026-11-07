#!/usr/bin/env python3
"""Board: run a compiled DLA on images with NeuroPilot 6 `neuronrt -m hw` (one process per image), save FP16 logits as FP32 npy.
usage: python3 eval_neuronrt_board.py --dla m.dla --x eval_u8.npy --out name [--n 4000]  (needs LD_LIBRARY_PATH for np6/lib in env)"""
import argparse, json, subprocess, time, numpy as np
ap = argparse.ArgumentParser(); ap.add_argument("--dla", required=True); ap.add_argument("--x", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--n", type=int, default=4000); a = ap.parse_args()
M = np.array([0.485, 0.456, 0.406], np.float32); S = np.array([0.229, 0.224, 0.225], np.float32)
x = np.load(a.x, mmap_mode="r")[:a.n]; out = []; t0 = time.time(); bad = 0
for i in range(len(x)):
    ((x[i].astype(np.float32) / 255 - M) / S).astype(np.float16).tofile("/home/ubuntu/_in.bin")
    r = subprocess.run(["/home/ubuntu/np6/bin/neuronrt", "-m", "hw", "-a", a.dla, "-i", "/home/ubuntu/_in.bin", "-o", "/home/ubuntu/_out.bin"], capture_output=True, text=True)
    o = np.fromfile("/home/ubuntu/_out.bin", np.float16).astype(np.float32)
    if r.returncode != 0 or o.size != 1000: bad += 1; o = np.full(1000, np.nan, np.float32)
    out.append(o)
    if i % 200 == 0: print(i, round(time.time() - t0), "bad", bad, flush=True)
np.save(a.out + "_out.npy", np.stack(out)); json.dump(dict(dla=a.dla, n=len(x), wall_s=time.time() - t0, failed=bad), open(a.out + ".json", "w")); print("done", bad)
