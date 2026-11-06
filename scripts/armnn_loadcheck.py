#!/usr/bin/env python3
"""Does Arm NN (PyArmNN) parse + optimise + load a TFLite model on the given backends? Prints OK/FAIL per backend list."""
import sys, pyarmnn as ann
p = ann.ITfLiteParser(); net = p.CreateNetworkFromBinaryFile(sys.argv[1])
rt = ann.IRuntime(ann.CreationOptions())
for bl in sys.argv[2:]:
    try:
        opt, msgs = ann.Optimize(net, [ann.BackendId(b) for b in bl.split(",")], rt.GetDeviceSpec(), ann.OptimizerOptions())
        rt.LoadNetwork(opt); print(bl, "OK")
    except Exception as e:
        print(bl, "FAIL:", str(e)[:200])
