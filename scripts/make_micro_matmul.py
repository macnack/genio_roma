#!/usr/bin/env python3
"""Two micro ONNX models isolating the ConvNeXt pointwise-MLP pattern (for Arm NN/TFLite parser debugging).
a: Add(x) -> MatMul(x[1,14,14,32] , W[32,64])      (4D x 2D-const MatMul, as in ConvNeXt)
b: same math via Reshape[196,32] -> MatMul -> Reshape[1,14,14,64]"""
import numpy as np, onnx
from onnx import helper as h, TensorProto as T, numpy_helper as nh
W = nh.from_array(np.random.RandomState(0).randn(32, 64).astype(np.float32), "W")
B = nh.from_array(np.random.RandomState(1).randn(64).astype(np.float32), "B")
def mk(kind):
    x = h.make_tensor_value_info("x", T.FLOAT, [1, 14, 14, 32]); y = h.make_tensor_value_info("y", T.FLOAT, [1, 14, 14, 64])
    inits = [W, B]
    if kind == "a":
        nodes = [h.make_node("MatMul", ["x", "W"], ["m"]), h.make_node("Add", ["m", "B"], ["y"])]
    else:
        inits += [nh.from_array(np.array([196, 32], np.int64), "s1"), nh.from_array(np.array([1, 14, 14, 64], np.int64), "s2")]
        nodes = [h.make_node("Reshape", ["x", "s1"], ["r"]), h.make_node("MatMul", ["r", "W"], ["m"]),
                 h.make_node("Reshape", ["m", "s2"], ["rr"]), h.make_node("Add", ["rr", "B"], ["y"])]
    g = h.make_graph(nodes, "g" + kind, [x], [y], inits)
    return h.make_model(g, opset_imports=[h.make_opsetid("", 13)])
for k in "ab": onnx.save(mk(k), f"models/tflite/micro/mm_{k}.onnx")
