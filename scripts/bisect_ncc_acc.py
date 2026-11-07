#!/usr/bin/env python3
"""Prefix cuts of an ONNX model -> onnx2tf FP16 TFLite -> ncc-tflite (mdla3.0) -> neuronrt -m hw on image 0 -> cosine vs ORT FP32 prefix output.
usage: bisect_ncc_acc.py model.onnx workdir idx...   needs /home/ubuntu/in0.bin (fp16 NHWC normalised image 0) and np6 on the board."""
import sys, os, subprocess, onnx, numpy as np, onnxruntime as ort
from onnx import utils
src, wd, idxs = sys.argv[1], sys.argv[2], [int(i) for i in sys.argv[3:]]
os.makedirs(wd, exist_ok=True)
m = onnx.load(src); inp = m.graph.input[0].name; ns = [n for n in m.graph.node if n.op_type != "Constant"]
x8 = np.load("data/imagenet_subset/eval_u8.npy", mmap_mode="r")[0]
M = np.array([0.485, 0.456, 0.406], np.float32); S = np.array([0.229, 0.224, 0.225], np.float32)
xn = ((x8.astype(np.float32) / 255 - M) / S).transpose(2, 0, 1)[None].astype(np.float32)
ENV = "export LD_LIBRARY_PATH=/home/ubuntu/np6/lib:$(find /home/ubuntu/np6/lib -type d | tr '\\n' ':'); cd /home/ubuntu;"
def cos(a, b): return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-30))
for i in idxs:
    o = f"{wd}/p{i}.onnx"; utils.extract_model(src, o, [inp], [ns[i].output[0]])
    ref = ort.InferenceSession(o).run(None, {inp: xn})[0].astype(np.float32)
    subprocess.run([".venv-tflite/bin/onnx2tf", "-i", o, "-o", f"{wd}/t{i}", "-n", "-rtpo", "gelu", "erf"], capture_output=True, text=True)
    t = f"{wd}/t{i}/p{i}_float16.tflite"
    if not os.path.exists(t): print(i, ns[i].op_type, "CONVERT-FAIL", flush=True); continue
    subprocess.run(["adb", "push", t, "/home/ubuntu/ncc_p.tflite"], capture_output=True)
    r = subprocess.run(["adb", "shell", f"{ENV} rm -f ncc_p.dla pout.bin; ./np6/bin/ncc-tflite --arch=mdla3.0 -d ncc_p.dla ncc_p.tflite >/dev/null 2>&1; echo c=$?; ./np6/bin/neuronrt -m hw -a ncc_p.dla -i in0.bin -o pout.bin 2>&1 | tail -1"], capture_output=True, text=True).stdout.split()
    subprocess.run(["adb", "pull", "/home/ubuntu/pout.bin", f"{wd}/pout.bin"], capture_output=True)
    try: d = np.fromfile(f"{wd}/pout.bin", np.float16).astype(np.float32)
    except Exception: d = np.zeros(0, np.float32)
    nf = int((~np.isfinite(d)).sum()); res = {"flat": None, "nchw<-nhwc": None}
    if d.size == ref.size and nf == 0:
        res["flat"] = cos(d, ref.ravel())
        if ref.ndim == 4: res["nchw<-nhwc"] = cos(d, ref.transpose(0, 2, 3, 1).ravel())
    print(i, ns[i].op_type, ns[i].name[-34:], tuple(ref.shape), "compile", r[:1], "size", d.size, "nonfinite", nf, "cos", res, "refmax", float(np.abs(ref).max()), flush=True)
