#!/usr/bin/env python3
"""Toy control models to isolate DX-COM behaviour: stem conv -> depthwise KxK -> GAP -> Gemm.
Diagnostic only (NOT a replacement for model A). Usage: probe_dwconv.py K out.onnx"""
import sys, torch
k, out = int(sys.argv[1]), sys.argv[2]
torch.manual_seed(0)
m = torch.nn.Sequential(
    torch.nn.Conv2d(3, 96, 4, 4), torch.nn.Conv2d(96, 96, k, padding=k // 2, groups=96),
    torch.nn.AdaptiveAvgPool2d(1), torch.nn.Flatten(), torch.nn.Linear(96, 10)).eval()
torch.onnx.export(m, torch.zeros(1, 3, 224, 224), out, opset_version=13, input_names=["input"],
                  output_names=["output"], dynamo=False)
