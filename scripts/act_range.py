#!/usr/bin/env python3
"""Per-node activation range of an ONNX model on N real images (ORT CPU FP32). Flags values near the FP16 limit (65504)
and tiny nonzero values below the FP16 normal minimum (6.1e-5). usage: act_range.py model.onnx N out.json"""
import sys, json, numpy as np, onnx, onnxruntime as ort
sys.path.insert(0, "scripts"); from preproc import to_nchw
m = onnx.load(sys.argv[1]); n = int(sys.argv[2])
names = []
for nd in m.graph.node:
    for o in nd.output:
        if o: names.append((o, nd.op_type, nd.name))
have = {o.name for o in m.graph.output}
for o, _, _ in names:
    if o not in have: m.graph.output.append(onnx.ValueInfoProto(name=o))
s = ort.InferenceSession(m.SerializeToString(), providers=["CPUExecutionProvider"])
x = to_nchw(np.load("data/imagenet_subset/eval_u8.npy", mmap_mode="r")[:n])
stat = {}
for i in range(n):
    outs = s.run(None, {s.get_inputs()[0].name: x[i:i+1]})
    for (o, op, nm), v in zip(names, [None]*0 or outs[0:0] or []): pass
    on = [t.name for t in s.get_outputs()]
    for nme, v in zip(on, outs):
        if v.dtype != np.float32 or v.size == 0: continue
        a = np.abs(v); nz = a[a > 0]
        st = stat.setdefault(nme, dict(max=0.0, sub=0.0))
        st["max"] = max(st["max"], float(a.max()))
        if nz.size: st["sub"] = max(st["sub"], float((nz < 6.1e-5).mean()))
info = {o: (op, nm) for o, op, nm in names}
rows = sorted(((v["max"], k) for k, v in stat.items()), reverse=True)
json.dump({k: dict(op=info.get(k, ("", ""))[0], name=info.get(k, ("", ""))[1], **v) for k, v in stat.items()}, open(sys.argv[3], "w"))
print("top 15 by max|x|:")
for mx, k in rows[:15]: print(f"{mx:12.2f} {info.get(k)}")
print("n nodes with max>1e4:", sum(1 for mx, _ in rows if mx > 1e4), " >6.5e4:", sum(1 for mx, _ in rows if mx > 6.5e4))
