#!/usr/bin/env python3
"""Inspect a TFLite model (op histogram, I/O) and check parity against the source ONNX on one seeded input (laptop, CPU)."""
import sys, collections, numpy as np, onnxruntime as ort
from ai_edge_litert.interpreter import Interpreter
tfl, onx = sys.argv[1], sys.argv[2]
it = Interpreter(model_path=tfl); it.allocate_tensors()
ops = collections.Counter(d["op_name"] for d in it._get_ops_details())
print("ops:", dict(ops))
i, o = it.get_input_details()[0], it.get_output_details()[0]
print("input", i["shape"], i["dtype"].__name__, "output", o["shape"], o["dtype"].__name__)
x = np.random.RandomState(0).randn(1, 3, 224, 224).astype(np.float32)
xin = x.transpose(0, 2, 3, 1) if list(i["shape"][1:]) == [224, 224, 3] else x
it.set_tensor(i["index"], xin.astype(i["dtype"])); it.invoke(); yt = it.get_tensor(o["index"]).astype(np.float32)
s = ort.InferenceSession(onx, providers=["CPUExecutionProvider"]); yo = s.run(None, {s.get_inputs()[0].name: x})[0]
cos = float((yt * yo).sum() / (np.linalg.norm(yt) * np.linalg.norm(yo)))
print(f"tflite vs onnx: max_abs={np.abs(yt-yo).max():.4g} cosine={cos:.6f} top1_same={yt.argmax()==yo.argmax()}")
