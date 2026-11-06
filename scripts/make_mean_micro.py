#!/usr/bin/env python3
"""Mean-reduction micro-models for accelerator testing: x[1,C,H,W] -> mean over given NCHW dims (keepdim)."""
import sys, torch, torch.nn as nn
class M(nn.Module):
    def __init__(s, dims): super().__init__(); s.dims = dims
    def forward(s, x): return x.mean(s.dims, keepdim=True)
C, H, dims, out = int(sys.argv[1]), int(sys.argv[2]), [int(d) for d in sys.argv[3].split(",")], sys.argv[4]
torch.onnx.export(M(dims).eval(), torch.randn(1, C, H, H), out, opset_version=13, input_names=["x"], output_names=["y"], dynamo=False)
