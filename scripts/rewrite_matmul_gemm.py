#!/usr/bin/env python3
"""ONNX: MatMul(2D activation, 2D constant weight) -> Gemm (onnx2tf emits FULLY_CONNECTED instead of BATCH_MATMUL). Math-identical.
Used to test whether NeuroPilot 6 ncc-tflite crashes on 2D BATCH_MATMUL. usage: rewrite_matmul_gemm.py in.onnx out.onnx"""
import sys, onnx
from onnx import helper, numpy_helper
m = onnx.load(sys.argv[1]); init = {i.name: i for i in m.graph.initializer}; n_ok = 0
for n in m.graph.node:
    if n.op_type == "MatMul" and n.input[1] in init and len(init[n.input[1]].dims) == 2:
        n.op_type = "Gemm"; n.attribute.extend([helper.make_attribute("alpha", 1.0), helper.make_attribute("beta", 1.0)]); n_ok += 1
        b = n.name + "_zb"; 
        if b not in init:
            m.graph.initializer.append(numpy_helper.from_array(__import__("numpy").zeros(init[n.input[1]].dims[1], "float32"), b))
        n.input.append(b)
onnx.checker.check_model(m); onnx.save(m, sys.argv[2]); print("MatMul->Gemm:", n_ok)
