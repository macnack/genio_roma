#!/usr/bin/env python3
"""Compile via the dx_com Python API (2.4.1), where calibration_method / calibration_num ARE honoured.
The CLI + config.json route ignored both keys (md5-identical .dxnn for ema/100 vs iqr/1000).
Usage: .venv-dxcom/bin/python scripts/compile_dxnn_api.py model.onnx out_dir config.json METHOD NUM [--q_pro] [--dataset DIR]
  --dataset DIR  calibration images directory; written into a per-run copy of config.json
                 (default_loader.dataset_path) at out_dir/config_run.json. The template config is never modified."""
import json, os, sys, time, dx_com

args = sys.argv[1:]
ds = None
if "--dataset" in args:
    i = args.index("--dataset"); ds = os.path.abspath(args[i + 1]); del args[i:i + 2]
q_pro = "--q_pro" in args
args = [a for a in args if a != "--q_pro"]
onnx, out, cfg, method, num = args[:5]
os.makedirs(out, exist_ok=True)
if ds:
    c = json.load(open(cfg)); c["default_loader"]["dataset_path"] = ds
    cfg = os.path.join(out, "config_run.json"); json.dump(c, open(cfg, "w"), indent=1)
    print("dataset_path ->", ds, "config:", cfg, flush=True)
t = time.time()
dx_com.compile(model=onnx, output_dir=out, config=cfg, calibration_method=method,
               calibration_num=int(num), use_q_pro=q_pro, gen_log=True)
print(f"compile_seconds={time.time()-t:.0f}")
