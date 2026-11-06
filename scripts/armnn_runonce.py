#!/usr/bin/env python3
"""Run a TFLite model once in Arm NN on the given backends; prints OK + output shape (used for GPU fault bisecting)."""
import sys, numpy as np, pyarmnn as ann
p = ann.ITfLiteParser(); net = p.CreateNetworkFromBinaryFile(sys.argv[1])
i = p.GetNetworkInputBindingInfo(0, p.GetSubgraphInputTensorNames(0)[0]); o = p.GetNetworkOutputBindingInfo(0, p.GetSubgraphOutputTensorNames(0)[0])
rt = ann.IRuntime(ann.CreationOptions())
opt, _ = ann.Optimize(net, [ann.BackendId(b) for b in sys.argv[2].split(",")], rt.GetDeviceSpec(), ann.OptimizerOptions())
nid, _ = rt.LoadNetwork(opt)
shp = i[1].GetShape(); x = np.random.RandomState(0).randn(*shp).astype(np.float32)
it = ann.make_input_tensors([i], [x]); ot = ann.make_output_tensors([o]); rt.EnqueueWorkload(nid, it, ot)
y = ann.workload_tensors_to_ndarray(ot)[0]; print("OK", y.shape, float(np.abs(y).mean()))
