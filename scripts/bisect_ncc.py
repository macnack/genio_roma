#!/usr/bin/env python3
"""Cut ONNX prefixes, convert (onnx2tf), compile each FP16 TFLite with NeuroPilot 6 ncc-tflite on the board; report rc (139 = segfault).
usage: bisect_ncc.py model.onnx workdir idx...   (idx = node index in non-Constant node list; -1 = print node count)"""
import sys, os, subprocess, onnx
from onnx import utils
src, wd, idxs = sys.argv[1], sys.argv[2], [int(i) for i in sys.argv[3:]]
os.makedirs(wd, exist_ok=True)
m = onnx.load(src); inp = m.graph.input[0].name; ns = [n for n in m.graph.node if n.op_type != "Constant"]
print("nodes", len(ns), flush=True)
ENV = "export LD_LIBRARY_PATH=/home/ubuntu/np6/lib:$(find /home/ubuntu/np6/lib -type d | tr '\\n' ':'); cd /home/ubuntu;"
for i in idxs:
    if i < 0: continue
    o = f"{wd}/p{i}.onnx"; utils.extract_model(src, o, [inp], [ns[i].output[0]])
    subprocess.run([".venv-tflite/bin/onnx2tf", "-i", o, "-o", f"{wd}/t{i}", "-n", "-rtpo", "gelu", "erf"], capture_output=True, text=True)
    t = f"{wd}/t{i}/p{i}_float16.tflite"
    if not os.path.exists(t): print(i, ns[i].op_type, "CONVERT-FAIL", flush=True); continue
    subprocess.run(["adb", "push", t, "/home/ubuntu/ncc_p.tflite"], capture_output=True)
    r = subprocess.run(["adb", "shell", f"{ENV} ./np6/bin/ncc-tflite --arch=mdla3.0 -d ncc_p.dla ncc_p.tflite >ncc_p.log 2>&1; echo rc=$?; tail -2 ncc_p.log; ls -la ncc_p.dla 2>&1|tail -1; rm -f ncc_p.dla ncc_p.tflite"], capture_output=True, text=True)
    print(i, ns[i].op_type, ns[i].name[-40:], " | ".join(r.stdout.strip().splitlines())[-260:], flush=True)
