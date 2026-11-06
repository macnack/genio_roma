#!/usr/bin/env python3
"""ORT NeuronExecutionProvider (Genio APU) probe/benchmark, runs on the board with
PYTHONPATH=/usr/lib/onnxruntime-neuron/python. Uses only documented ORT session API; provider options are
passed through verbatim from --opt key=value (none by default). Reports which provider each node is assigned to
via ORT verbose log parsing is done by the caller; here we report get_providers() and latency."""
import argparse, json, time, sys
import numpy as np
import onnxruntime as ort

ap = argparse.ArgumentParser()
ap.add_argument("model"); ap.add_argument("--providers", default="NeuronExecutionProvider,CPUExecutionProvider")
ap.add_argument("--opt", action="append", default=[], help="key=value provider option for the first provider")
ap.add_argument("--runs", type=int, default=20); ap.add_argument("--warmup", type=int, default=3)
ap.add_argument("--ref"); ap.add_argument("--verbose", action="store_true"); ap.add_argument("--out")
ap.add_argument("--tag", default="")
a = ap.parse_args()
so = ort.SessionOptions()
if a.verbose: so.log_severity_level = 0
provs = a.providers.split(",")
popts = [dict(kv.split("=", 1) for kv in a.opt)] + [{}] * (len(provs) - 1)
t0 = time.time()
s = ort.InferenceSession(a.model, so, providers=provs, provider_options=popts)
load = time.time() - t0
print("session providers:", s.get_providers(), f"load {load:.1f}s", flush=True)
inp = s.get_inputs()[0]
x = np.random.RandomState(0).randn(*inp.shape).astype(np.float32)
for _ in range(a.warmup): y = s.run(None, {inp.name: x})[0]
ts = []
for _ in range(a.runs):
    t = time.perf_counter(); y = s.run(None, {inp.name: x})[0]; ts.append((time.perf_counter() - t) * 1e3)
r = dict(tag=a.tag, model=a.model, providers=provs, active=s.get_providers(), load_s=round(load, 2),
         mean_ms=float(np.mean(ts)), p50_ms=float(np.percentile(ts, 50)), p95_ms=float(np.percentile(ts, 95)), runs=a.runs)
if a.ref:
    ref = np.load(a.ref)
    r["max_abs_vs_ref"] = float(np.abs(y - ref[:1] if ref.ndim > 1 else y - ref).max())
print(json.dumps(r))
if a.out: open(a.out, "a").write(json.dumps(r) + "\n")
