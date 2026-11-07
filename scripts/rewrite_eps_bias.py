#!/usr/bin/env python3
"""ONNX: Gemm -> Reshape -> Add(scalar const) (the LayerNorm variance + eps) => Gemm with bias=eps, Add removed. Math-identical.
Test for an MDLA (ncc-tflite 6.x) mis-compute seen on the last 64 of 384 channels. usage: rewrite_eps_bias.py in.onnx out.onnx"""
import sys, onnx, numpy as np
from onnx import numpy_helper as nh
m = onnx.load(sys.argv[1]); g = m.graph
prod = {o: n for n in g.node for o in n.output}
const = {n.output[0]: nh.to_array(n.attribute[0].t) for n in g.node if n.op_type == "Constant"}
const.update({i.name: nh.to_array(i) for i in g.initializer})
init = {i.name: i for i in g.initializer}
rm, done = [], 0
for a in g.node:
    if a.op_type != "Add": continue
    cs = [x for x in a.input if x in const and const[x].size == 1]; ot = [x for x in a.input if x not in cs]
    if len(cs) != 1 or len(ot) != 1: continue
    r = prod.get(ot[0]); 
    if r is None or r.op_type != "Reshape": continue
    gm = prod.get(r.input[0])
    if gm is None or gm.op_type != "Gemm" or len(gm.input) < 3: continue
    bname = gm.input[2]; b = nh.to_array(init[bname]) + float(const[cs[0]].ravel()[0])
    newb = bname + "_eps"; g.initializer.append(nh.from_array(b.astype(np.float32), newb)); gm.input[2] = newb
    # rewire consumers of Add output to Reshape output
    for n in g.node:
        for k, x in enumerate(n.input):
            if x == a.output[0]: n.input[k] = r.output[0]
    for o in g.output:
        if o.name == a.output[0]: o.name = r.output[0]
    rm.append(a); done += 1
for a in rm: g.node.remove(a)
onnx.checker.check_model(m); onnx.save(m, sys.argv[2]); print("eps folded into Gemm bias:", done)
