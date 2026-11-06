#!/usr/bin/env python3
"""Tiny conv-BN-ReLU CNN (static [1,3,64,64]) to smoke-test an accelerator path independent of ConvNeXt size/ops."""
import torch, torch.nn as nn, sys
torch.manual_seed(0)
m = nn.Sequential(nn.Conv2d(3,16,3,2,1), nn.BatchNorm2d(16), nn.ReLU(), nn.Conv2d(16,32,3,2,1), nn.BatchNorm2d(32), nn.ReLU(),
                  nn.Conv2d(32,32,3,1,1), nn.ReLU(), nn.AdaptiveAvgPool2d(1), nn.Flatten(), nn.Linear(32,10)).eval()
torch.onnx.export(m, torch.randn(1,3,64,64), sys.argv[1], opset_version=13, input_names=["x"], output_names=["y"], dynamo=False)
