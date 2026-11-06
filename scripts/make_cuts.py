#!/usr/bin/env python3
"""Cut an ONNX model into prefixes ending at the output of the last node whose name matches each pattern, to bisect
accelerator faults. Usage: make_cuts.py model.onnx outdir pattern1 pattern2 ..."""
import sys, onnx
from onnx import utils
src, out = sys.argv[1], sys.argv[2]; pats = sys.argv[3:]
m = onnx.load(src); inp = m.graph.input[0].name
import os; os.makedirs(out, exist_ok=True)
for k, p in enumerate(pats):
    cand = [n for n in m.graph.node if p in n.name and n.op_type != "Constant"]
    if not cand: print("no match", p); continue
    t = cand[-1].output[0]
    dst = f"{out}/cut{k:02d}.onnx"
    utils.extract_model(src, dst, [inp], [t])
    print(f"cut{k:02d} {p} -> {cand[-1].op_type} {cand[-1].name}")
