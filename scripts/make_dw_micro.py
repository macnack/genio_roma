#!/usr/bin/env python3
"""Depthwise conv micro-models, static NCHW [1,C,H,W], kernel k, to test accelerator support per kernel size."""
import sys, torch, torch.nn as nn
C, H, k, out = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
torch.manual_seed(0)
m = nn.Sequential(nn.Conv2d(C, C, k, 1, k // 2, groups=C)).eval()
torch.onnx.export(m, torch.randn(1, C, H, H), out, opset_version=13, input_names=["x"], output_names=["y"], dynamo=False)
