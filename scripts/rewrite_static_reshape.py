#!/usr/bin/env python3
"""Reshape nodes whose target shape is computed at run time (Shape/Slice/Concat) -> constant shape initializer.
Needed for DINOv3 (B): onnx2tf turns the dynamic shape arithmetic into EQUAL+SELECT, which Arm NN 23.08 rejects (SELECT unsupported).
With a static [1,3,224,224] input the shapes are fixed numbers, so this is value-identical (checked: ORT parity before/after).
usage: rewrite_static_reshape.py in.onnx out.onnx"""
import sys, numpy as np, onnx, onnxruntime as ort
from onnx import numpy_helper, helper
m = onnx.load(sys.argv[1]); g = m.graph
inits = {i.name for i in g.initializer} | {o for n in g.node if n.op_type == "Constant" for o in n.output}
dyn = [n for n in g.node if n.op_type == "Reshape" and n.input[1] not in inits]
print("reshapes with computed shape:", [n.name for n in dyn])
if not dyn: onnx.save(m, sys.argv[2]); sys.exit()
probe = onnx.ModelProto(); probe.CopyFrom(m)
for n in dyn: probe.graph.output.append(helper.make_empty_tensor_value_info(n.input[1]))
x = np.random.RandomState(0).randn(1, 3, 224, 224).astype(np.float32)
inp = m.graph.input[0].name
s = ort.InferenceSession(probe.SerializeToString(), providers=["CPUExecutionProvider"])
vals = dict(zip([o.name for o in s.get_outputs()], s.run(None, {inp: x})))
for n in dyn:
    v = vals[n.input[1]].astype(np.int64); print(" ", n.name, "shape ->", v.tolist())
    g.initializer.append(numpy_helper.from_array(v, n.name + "_static_shape")); n.input[1] = n.name + "_static_shape"
# drop now-dead nodes
live = {o.name for o in g.output}
changed = True
while changed:
    used = {i for n in g.node for i in n.input} | live
    dead = [n for n in g.node if not any(o in used for o in n.output)]
    changed = bool(dead)
    for n in dead: g.node.remove(n)
onnx.save(m, sys.argv[2])
a = ort.InferenceSession(sys.argv[1], providers=["CPUExecutionProvider"]).run(None, {inp: x})[0]
b = ort.InferenceSession(sys.argv[2], providers=["CPUExecutionProvider"]).run(None, {inp: x})[0]
print("parity: max_abs=%.3g cosine=%.8f" % (np.abs(a-b).max(), (a*b).sum()/np.linalg.norm(a)/np.linalg.norm(b)))
