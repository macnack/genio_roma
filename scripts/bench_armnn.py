#!/usr/bin/env python3
"""Arm NN (PyArmNN 23.08) TFLite benchmark on the board. Backend order via --backends (e.g. GpuAcc,CpuAcc).
Layer->backend placement is taken from Arm NN's own profiler JSON (per-layer 'backendId'), not assumed.
GPU activity is cross-checked from /sys/class/devfreq/13000000.gpu (cur_freq samples + trans_stat deltas)."""
import argparse, json, re, time, sys, collections, glob
import numpy as np
import pyarmnn as ann

ap = argparse.ArgumentParser()
ap.add_argument("model"); ap.add_argument("--backends", default="GpuAcc,CpuAcc")
ap.add_argument("--fp16", action="store_true", help="OptimizerOptions.m_ReduceFp32ToFp16")
ap.add_argument("--runs", type=int, default=20); ap.add_argument("--warmup", type=int, default=3)
ap.add_argument("--ref"); ap.add_argument("--tag", default=""); ap.add_argument("--out"); ap.add_argument("--profile", action="store_true")
a = ap.parse_args()

def rd(p):
    try: return open(p).read().strip()
    except Exception: return None
GPU = "/sys/class/devfreq/13000000.gpu"

parser = ann.ITfLiteParser()
net = parser.CreateNetworkFromBinaryFile(a.model)
inn = parser.GetSubgraphInputTensorNames(0); outn = parser.GetSubgraphOutputTensorNames(0)
ib = parser.GetNetworkInputBindingInfo(0, inn[0]); ob = parser.GetNetworkOutputBindingInfo(0, outn[0])
rt = ann.IRuntime(ann.CreationOptions())
oo = ann.OptimizerOptions(); oo.m_ReduceFp32ToFp16 = a.fp16
t0 = time.time()
opt, msgs = ann.Optimize(net, [ann.BackendId(b) for b in a.backends.split(",")], rt.GetDeviceSpec(), oo)
opt_s = time.time() - t0
for m in msgs: print("optimize msg:", m)
print('stage: optimized', flush=True)
t0 = time.time(); nid, _ = rt.LoadNetwork(opt); load_s = time.time() - t0
print('stage: loaded', round(load_s,1), flush=True)
x = np.random.RandomState(0).randn(1, 3, 224, 224).astype(np.float32)
xin = np.ascontiguousarray(x.transpose(0, 2, 3, 1))
it = ann.make_input_tensors([ib], [xin]); ot = ann.make_output_tensors([ob])
prof = rt.GetProfiler(nid)
if a.profile: prof.EnableProfiling(True)
for _ in range(a.warmup): rt.EnqueueWorkload(nid, it, ot); print('stage: warmup run done', flush=True)
ts_before = rd(GPU + "/trans_stat"); freqs = []
ts = []
for _ in range(a.runs):
    t = time.perf_counter(); rt.EnqueueWorkload(nid, it, ot); ts.append((time.perf_counter() - t) * 1e3)
    freqs.append(rd(GPU + "/cur_freq"))
y = ann.workload_tensors_to_ndarray(ot)[0]
ts_after = rd(GPU + "/trans_stat")
r = dict(tag=a.tag, model=a.model, backends=a.backends, fp16=a.fp16, optimize_s=round(opt_s, 2), load_s=round(load_s, 2),
         mean_ms=float(np.mean(ts)), p50_ms=float(np.percentile(ts, 50)), p95_ms=float(np.percentile(ts, 95)), runs=a.runs,
         gpu_cur_freq_samples=sorted(set(freqs)), gpu_trans_stat_changed=(ts_before != ts_after))
if a.ref:
    ref = np.load(a.ref).reshape(-1)[:1000]; yy = y.reshape(-1)
    r["max_abs_vs_ref"] = float(np.abs(yy - ref).max()); r["cos_vs_ref"] = float((yy * ref).sum() / (np.linalg.norm(yy) * np.linalg.norm(ref)))
if a.profile:
    js = prof.as_json(); open('armnn_profile.json','w').write(js)
    try:
        d = json.loads(js)
        cnt = collections.Counter()
        def walk(n):
            if isinstance(n, dict):
                for k, v in n.items():
                    m = re.search(r"\((GpuAcc|CpuAcc|CpuRef)\)", k) or None
                    if m: cnt[m.group(1)] += 1
                    walk(v)
            elif isinstance(n, list):
                for v in n: walk(v)
        walk(d); r["profiler_backend_event_counts"] = dict(cnt)
    except Exception as e:
        r["profiler_parse_error"] = str(e); open("armnn_profile.json", "w").write(js)
print(json.dumps(r))
if a.out: open(a.out, "a").write(json.dumps(r) + "\n")
