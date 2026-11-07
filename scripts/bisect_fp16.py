#!/usr/bin/env python3
"""Cut ONNX prefixes, convert (onnx2tf), run fp16_compare.py on the board. usage: bisect_fp16.py model.onnx workdir idx..."""
import sys, os, subprocess, onnx
from onnx import utils
src, wd, idxs = sys.argv[1], sys.argv[2], [int(i) for i in sys.argv[3:]]
os.makedirs(wd, exist_ok=True)
m = onnx.load(src); inp = m.graph.input[0].name; ns = [n for n in m.graph.node if n.op_type != "Constant"]
for i in idxs:
    o = f"{wd}/p{i}.onnx"; utils.extract_model(src, o, [inp], [ns[i].output[0]])
    subprocess.run([".venv-tflite/bin/onnx2tf", "-i", o, "-o", f"{wd}/t{i}", "-n", "-rtpo", "gelu", "erf"], capture_output=True, text=True)
    t = f"{wd}/t{i}/p{i}_float32.tflite"
    if not os.path.exists(t): print(i, ns[i].op_type, "CONVERT-FAIL", flush=True); continue
    subprocess.run(["adb", "push", t, f"/home/ubuntu/f16_p{i}.tflite"], capture_output=True)
    r = subprocess.run(["adb", "shell", f"cd /home/ubuntu; timeout 600 python3 -W ignore fp16_compare.py f16_p{i}.tflite 2 2>&1 | tail -1; rm -f f16_p{i}.tflite"], capture_output=True, text=True)
    print(i, ns[i].op_type, ns[i].name[-45:], r.stdout.strip()[-230:], flush=True)
