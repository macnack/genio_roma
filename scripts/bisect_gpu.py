#!/usr/bin/env python3
"""Bisect Arm NN GpuAcc faults: cut ONNX prefixes at non-Constant node indices, convert (onnx2tf), run once on the board.
usage: bisect_gpu.py model.onnx workdir idx1 idx2 ...   (needs .venv-tflite, adb, scripts/armnn_runonce.py on the board)"""
import sys, os, subprocess, onnx
from onnx import utils
src, wd, idxs = sys.argv[1], sys.argv[2], [int(i) for i in sys.argv[3:]]
os.makedirs(wd, exist_ok=True)
m = onnx.load(src); inp = m.graph.input[0].name; ns = [n for n in m.graph.node if n.op_type != "Constant"]
for i in idxs:
    o = f"{wd}/p{i}.onnx"; utils.extract_model(src, o, [inp], [ns[i].output[0]])
    r = subprocess.run([".venv-tflite/bin/onnx2tf", "-i", o, "-o", f"{wd}/t{i}", "-n", "-rtpo", "gelu", "erf"], capture_output=True, text=True)
    t = f"{wd}/t{i}/p{i}_float32.tflite"
    if not os.path.exists(t): print(i, ns[i].op_type, "CONVERT-FAIL"); continue
    subprocess.run(["adb", "push", t, f"/home/ubuntu/bis_p{i}.tflite"], capture_output=True)
    r = subprocess.run(["adb", "shell", f"cd /home/ubuntu; timeout 300 python3 -W ignore armnn_runonce.py bis_p{i}.tflite GpuAcc,CpuAcc 2>&1 | tail -3"], capture_output=True, text=True)
    ok = "OK (" in r.stdout
    print(f"{i:3d} {ns[i].op_type:16s} {ns[i].name.split('/')[-2]+'/'+ns[i].name.split('/')[-1]:40s} {'PASS' if ok else 'FAIL'}", flush=True)
