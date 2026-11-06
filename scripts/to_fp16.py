#!/usr/bin/env python3
"""FP32 -> FP16 ONNX weights/activations (onnxconverter_common.float16.convert_float_to_float16, keep_io_types=True).
This is a deliberate, logged precision change (needed because the Genio APU MDLA/VPU reject Float32).
Prints the graph diff (op counts) and FP16-vs-FP32 output parity on seeded random input (ORT CPU, laptop)."""
import sys, collections
import numpy as np, onnx, onnxruntime as ort
from onnxconverter_common import float16
src, dst = sys.argv[1], sys.argv[2]
m = onnx.load(src)
before = collections.Counter(n.op_type for n in m.graph.node)
m16 = float16.convert_float_to_float16(m, keep_io_types=True)
onnx.save(m16, dst)
after = collections.Counter(n.op_type for n in m16.graph.node)
print("op count diff:", {k: after[k] - before.get(k, 0) for k in after if after[k] != before.get(k, 0)})
x = np.random.RandomState(0).randn(1, 3, 224, 224).astype(np.float32)
a = ort.InferenceSession(src, providers=["CPUExecutionProvider"]); b = ort.InferenceSession(dst, providers=["CPUExecutionProvider"])
ya = a.run(None, {a.get_inputs()[0].name: x})[0]; yb = b.run(None, {b.get_inputs()[0].name: x})[0]
cos = float((ya * yb).sum() / (np.linalg.norm(ya) * np.linalg.norm(yb)))
print(f"fp16 vs fp32 (ORT CPU): max_abs={np.abs(ya-yb).max():.4g} cosine={cos:.6f} top1_same={ya.argmax()==yb.argmax()}")
