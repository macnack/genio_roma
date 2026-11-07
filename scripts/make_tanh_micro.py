#!/usr/bin/env python3
"""Micro-models isolating FP16 Tanh on Arm NN GpuAcc: y = Tanh(x*K) (op=tanh) or y = Mul(x,K) control (op=mul), input [1,3,224,224]. usage: make_tanh_micro.py out_dir"""
import sys, os, onnx, numpy as np
from onnx import helper as h, TensorProto as T, numpy_helper as nh
os.makedirs(sys.argv[1], exist_ok=True)
for op in ("tanh", "mul"):
    for K in (1, 2, 3, 4, 8):
        nodes = [h.make_node("Mul", ["x", "k"], ["m"])] + ([h.make_node("Tanh", ["m"], ["y"])] if op == "tanh" else [h.make_node("Identity", ["m"], ["y"])])
        g = h.make_graph(nodes, f"{op}{K}", [h.make_tensor_value_info("x", T.FLOAT, [1, 3, 224, 224])],
                         [h.make_tensor_value_info("y", T.FLOAT, [1, 3, 224, 224])], [nh.from_array(np.float32(K), "k")])
        m = h.make_model(g, opset_imports=[h.make_opsetid("", 13)]); m.ir_version = 8
        onnx.checker.check_model(m); onnx.save(m, f"{sys.argv[1]}/{op}{K}.onnx")
