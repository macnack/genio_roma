#!/usr/bin/env python3
"""Board script: run a TFLite model in Arm NN GpuAcc twice (FP32, and with OptimizerOptions.m_ReduceFp32ToFp16) on the same real
images and print cosine / max abs / NaN-Inf counts of FP16 vs FP32. usage: fp16_compare.py model.tflite [n_images] [backends]"""
import sys, json, numpy as np, pyarmnn as ann
mp = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 2; be = (sys.argv[3] if len(sys.argv) > 3 else "GpuAcc,CpuAcc").split(",")
MEAN = np.array([0.485, 0.456, 0.406], np.float32); STD = np.array([0.229, 0.224, 0.225], np.float32)
u8 = np.load("/home/ubuntu/eval_u8.npy", mmap_mode="r")[:n]
X = ((u8.astype(np.float32) / 255 - MEAN) / STD).astype(np.float32)
def run(fp16):
    p = ann.ITfLiteParser(); net = p.CreateNetworkFromBinaryFile(mp)
    i = p.GetNetworkInputBindingInfo(0, p.GetSubgraphInputTensorNames(0)[0]); o = p.GetNetworkOutputBindingInfo(0, p.GetSubgraphOutputTensorNames(0)[0])
    rt = ann.IRuntime(ann.CreationOptions()); oo = ann.OptimizerOptions(); oo.m_ReduceFp32ToFp16 = fp16
    opt, _ = ann.Optimize(net, [ann.BackendId(b) for b in be], rt.GetDeviceSpec(), oo); nid, _ = rt.LoadNetwork(opt)
    shp = tuple(i[1].GetShape()); out = []
    for k in range(n):
        x = X[k:k+1]
        if shp != x.shape: x = x.transpose(0, 3, 1, 2) if shp[1] == 3 else x
        it = ann.make_input_tensors([i], [np.ascontiguousarray(x)]); ot = ann.make_output_tensors([o]); rt.EnqueueWorkload(nid, it, ot)
        out.append(ann.workload_tensors_to_ndarray(ot)[0].astype(np.float32).ravel().copy())
    return np.stack(out)
a = run(False); b = run(True)
cos = [float(a[k] @ b[k] / (np.linalg.norm(a[k]) * np.linalg.norm(b[k]) + 1e-30)) for k in range(n)]
print(json.dumps(dict(model=mp, cos=[round(c, 5) for c in cos], max_abs=float(np.abs(a - b).max()), fp32_absmax=float(np.abs(a).max()),
  fp16_nonfinite=int((~np.isfinite(b)).sum()), fp16_absmax=float(np.nanmax(np.abs(np.where(np.isfinite(b), b, np.nan)))) if np.isfinite(b).any() else None)))
