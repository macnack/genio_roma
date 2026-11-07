#!/usr/bin/env python3
"""ORT static INT8 (QDQ, per-channel weights, MinMax calibration) of an ONNX ConvNeXt, for an iso-precision CPU baseline vs the DX-M1 INT8.
Calibration: N images from data/imagenet_subset/calib (same preprocessing as everywhere). usage: quantize_ort_int8.py in.onnx out.onnx [N=100]"""
import sys, glob, numpy as np
sys.path.insert(0, "scripts"); from preproc import load_u8, to_nchw
from onnxruntime.quantization import quantize_static, CalibrationDataReader, QuantFormat, QuantType, CalibrationMethod
src, dst = sys.argv[1], sys.argv[2]; N = int(sys.argv[3]) if len(sys.argv) > 3 else 100
files = sorted(glob.glob("data/imagenet_subset/calib/*.jpg"))[::max(1, 1000 // N)][:N]
import onnxruntime as ort
name = ort.InferenceSession(src, providers=["CPUExecutionProvider"]).get_inputs()[0].name
class R(CalibrationDataReader):
    def __init__(s): s.it = iter(files)
    def get_next(s):
        f = next(s.it, None)
        return None if f is None else {name: to_nchw(load_u8(f)[None])}
quantize_static(src, dst, R(), quant_format=QuantFormat.QDQ, activation_type=QuantType.QUInt8, weight_type=QuantType.QInt8,
                per_channel=True, calibrate_method=CalibrationMethod.MinMax)
print("calibrated on", len(files), "images ->", dst)
