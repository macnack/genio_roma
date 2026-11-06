#!/usr/bin/env python3
"""Lossless ONNX rewrite for Arm NN's TFLite parser: MatMul(x[1,H,W,C] , W_const[C,K])  ->
Reshape(x,[H*W,C]) -> MatMul(.,W) -> Reshape(.,[1,H,W,K]).   (Arm NN 23.08 cannot load the 4D x 2D BATCH_MATMUL form.)
Logs every rewritten node; checks ORT parity vs the original on seeded input."""
import sys, numpy as np, onnx, onnxruntime as ort
from onnx import helper as h, numpy_helper as nh, shape_inference
src, dst = sys.argv[1], sys.argv[2]
m = shape_inference.infer_shapes(onnx.load(src))
shapes = {v.name: [d.dim_value for d in v.type.tensor_type.shape.dim] for v in list(m.graph.value_info) + list(m.graph.input)}
init = {i.name for i in m.graph.initializer}
new_nodes, n_rw = [], 0
for n in m.graph.node:
    s = shapes.get(n.input[0]) if n.op_type == "MatMul" else None
    if n.op_type == "MatMul" and s and len(s) == 4 and n.input[1] in init and s[0] == 1:
        _, H, W, C = s; K = next(i for i in m.graph.initializer if i.name == n.input[1]).dims[1]
        a, b = n.name + "_rs_in", n.name + "_rs_out"
        s1, s2 = n.name + "_shp1", n.name + "_shp2"
        m.graph.initializer.append(nh.from_array(np.array([H * W, C], np.int64), s1))
        m.graph.initializer.append(nh.from_array(np.array([1, H, W, K], np.int64), s2))
        new_nodes += [h.make_node("Reshape", [n.input[0], s1], [a], name=n.name + "_pre"),
                      h.make_node("MatMul", [a, n.input[1]], [b], name=n.name),
                      h.make_node("Reshape", [b, s2], [n.output[0]], name=n.name + "_post")]
        n_rw += 1; print(f"rewrote {n.name}: [1,{H},{W},{C}] x [{C},{K}]")
    else:
        new_nodes.append(n)
del m.graph.node[:]; m.graph.node.extend(new_nodes)
for vi in list(m.graph.value_info): m.graph.value_info.remove(vi)
onnx.checker.check_model(m); onnx.save(m, dst); print("rewritten MatMuls:", n_rw)
x = np.random.RandomState(0).randn(1, 3, 224, 224).astype(np.float32)
ya, yb = [ort.InferenceSession(p, providers=["CPUExecutionProvider"]).run(None, {"input": x})[0] if False else None for p in (src, dst)]
sa, sb = ort.InferenceSession(src, providers=["CPUExecutionProvider"]), ort.InferenceSession(dst, providers=["CPUExecutionProvider"])
ya = sa.run(None, {sa.get_inputs()[0].name: x})[0]; yb = sb.run(None, {sb.get_inputs()[0].name: x})[0]
print(f"parity: max_abs={np.abs(ya-yb).max():.3g} cosine={float((ya*yb).sum()/(np.linalg.norm(ya)*np.linalg.norm(yb))):.8f}")
