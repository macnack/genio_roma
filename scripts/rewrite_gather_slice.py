#!/usr/bin/env python3
"""Gather(data, constant scalar index, axis) -> Slice [i:i+1] on that axis + Reshape to the Gather output shape.
Value-identical. Needed for DINOv3 B on MDLA: ncc-tflite 6.2.3 'Cannot find an execution plan' for the final GATHER (token 0)
even though GATHER is in its op list (bisect: model compiles up to the LayerNorm output, fails on adding the Gather).
usage: rewrite_gather_slice.py in.onnx out.onnx"""
import sys, numpy as np, onnx, onnxruntime as ort
from onnx import helper, numpy_helper, shape_inference
m = onnx.load(sys.argv[1]); g = m.graph
mi = shape_inference.infer_shapes(m)
sh = {v.name: [d.dim_value for d in v.type.tensor_type.shape.dim] for v in list(mi.graph.value_info) + list(mi.graph.output)}
cst = {i.name: numpy_helper.to_array(i) for i in g.initializer}
for n in g.node:
    if n.op_type == "Constant": cst[n.output[0]] = numpy_helper.to_array(n.attribute[0].t)
new = []
for n in list(g.node):
    if n.op_type == "Gather" and n.input[1] in cst and cst[n.input[1]].ndim == 0:
        ax = next((a.i for a in n.attribute if a.name == "axis"), 0); i = int(cst[n.input[1]]); t = n.name
        for nm, arr in ((t+"_st", [i]), (t+"_en", [i+1]), (t+"_ax", [ax]), (t+"_shp", sh[n.output[0]])):
            g.initializer.append(numpy_helper.from_array(np.array(arr, np.int64), nm))
        s = helper.make_node("Slice", [n.input[0], t+"_st", t+"_en", t+"_ax"], [t+"_sl"], name=t+"_slice")
        r = helper.make_node("Reshape", [t+"_sl", t+"_shp"], list(n.output), name=t+"_rs")
        idx = list(g.node).index(n); g.node.remove(n); g.node.insert(idx, r); g.node.insert(idx, s); print("Gather", t, "axis", ax, "idx", i, "->", sh[n.output[0]])
onnx.save(m, sys.argv[2])
x = np.random.RandomState(0).randn(1, 3, 224, 224).astype(np.float32); inp = g.input[0].name
a = ort.InferenceSession(sys.argv[1], providers=["CPUExecutionProvider"]).run(None, {inp: x})[0]
b = ort.InferenceSession(sys.argv[2], providers=["CPUExecutionProvider"]).run(None, {inp: x})[0]
print("parity: max_abs=%.3g cosine=%.8f" % (np.abs(a-b).max(), (a*b).sum()/np.linalg.norm(a)/np.linalg.norm(b)))
