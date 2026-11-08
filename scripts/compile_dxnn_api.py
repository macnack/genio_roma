#!/usr/bin/env python3
"""Compile via the dx_com Python API (2.4.1), where calibration_method / calibration_num ARE honoured.
The CLI + config.json route ignored both keys (md5-identical .dxnn for ema/100 vs iqr/1000).
Usage: .venv-dxcom/bin/python scripts/compile_dxnn_api.py model.onnx out_dir config.json METHOD NUM [--q_pro]"""
import sys, time, dx_com
onnx, out, cfg, method, num = sys.argv[1:6]
t = time.time()
dx_com.compile(model=onnx, output_dir=out, config=cfg, calibration_method=method,
               calibration_num=int(num), use_q_pro="--q_pro" in sys.argv, gen_log=True)
print(f"compile_seconds={time.time()-t:.0f}")
