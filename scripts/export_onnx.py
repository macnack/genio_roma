#!/usr/bin/env python3
"""Export a model to a static-shape ONNX file and check parity with PyTorch.

Model-agnostic: add a loader to LOADERS (returns (nn.Module in eval mode, example input)).
Preprocessing (mean/std, resize) is NOT baked in: the ONNX input is the already-normalised
NCHW float32 tensor (DX-COM applies preprocessing from its JSON config; see docs/deepx).

  A  facebookresearch/ConvNeXt convnext_tiny, ImageNet-1K EMA weights (classifier, 1000 logits)
  B  HF transformers facebook/dinov3-convnext-tiny-pretrain-lvd1689m (backbone, pooled feature)

Usage: python scripts/export_onnx.py --model A --opset 17 [--dynamo]
"""
import argparse, hashlib, json, sys, types
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
HF_B = (Path.home() / ".cache/huggingface/hub/models--facebook--dinov3-convnext-tiny-pretrain-lvd1689m"
        / "snapshots/10d30274b4d445111e2d5bf75ac93bbd94db274b")
OUT_DIR = {"A": ROOT / "models/A_fb_in1k", "B": ROOT / "models/B_dinov3"}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def load_A():
    # third_party/ConvNeXt/models/convnext.py imports timm.models.registry (removed in recent
    # timm). Shim ONLY that import; model code itself is used unmodified.
    import timm.models
    if not hasattr(timm.models, "registry"):
        reg = types.ModuleType("timm.models.registry")
        reg.register_model = lambda fn: fn
        sys.modules["timm.models.registry"] = reg
        timm.models.registry = reg
    sys.path.insert(0, str(ROOT / "third_party/ConvNeXt"))
    from models.convnext import convnext_tiny  # noqa: E402

    ckpt_path = ROOT / "weights/convnext_tiny_1k_224_ema.pth"
    ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=True)
    sd = ckpt["model"] if "model" in ckpt else ckpt
    model = convnext_tiny(pretrained=False)  # num_classes=1000
    missing, unexpected = model.load_state_dict(sd, strict=True), None
    return model.eval(), torch.zeros(1, 3, 224, 224), {"weights": str(ckpt_path), "weights_sha256": sha256(ckpt_path)}


class _PooledWrapper(torch.nn.Module):
    def __init__(self, m):
        super().__init__()
        self.m = m

    def forward(self, x):
        return self.m(pixel_values=x).pooler_output


def load_B():
    from transformers import AutoModel
    m = AutoModel.from_pretrained(str(HF_B), local_files_only=True, torch_dtype=torch.float32).eval()
    st = HF_B / "model.safetensors"
    return _PooledWrapper(m).eval(), torch.zeros(1, 3, 224, 224), {
        "weights": str(st.resolve()), "weights_sha256": sha256(st.resolve()), "hf_class": type(m).__name__}


LOADERS = {"A": load_A, "B": load_B}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, choices=LOADERS)
    ap.add_argument("--opset", type=int, required=True)
    ap.add_argument("--dynamo", action="store_true", help="use torch.export-based exporter (default: legacy tracer)")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    torch.manual_seed(a.seed)
    model, _, meta = LOADERS[a.model]()
    x = torch.randn(1, 3, 224, 224)
    out_dir = OUT_DIR[a.model]
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = f"{'dynamo' if a.dynamo else 'trace'}_opset{a.opset}"
    path = out_dir / f"{a.model}_convnext_tiny_{tag}.onnx"

    with torch.no_grad():
        ref = model(x).numpy()
        torch.onnx.export(model, x, str(path), opset_version=a.opset, input_names=["input"],
                          output_names=["output"], dynamic_axes=None, dynamo=a.dynamo)

    import onnx, onnxruntime as ort
    m = onnx.load(str(path))
    onnx.checker.check_model(m)
    sess = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
    got = sess.run(None, {"input": x.numpy()})[0]
    d = np.abs(ref - got)
    cos = float((ref.ravel() @ got.ravel()) / (np.linalg.norm(ref) * np.linalg.norm(got)))
    report = {
        "model": a.model, "onnx": str(path.relative_to(ROOT)), "onnx_sha256": sha256(path), "opset": a.opset,
        "exporter": "dynamo" if a.dynamo else "trace", "torch": torch.__version__, "onnx_pkg": onnx.__version__,
        "onnxruntime": ort.__version__, "input": [d_.dim_value for d_ in m.graph.input[0].type.tensor_type.shape.dim],
        "output_shape": list(got.shape), "max_abs_diff": float(d.max()), "mean_abs_diff": float(d.mean()),
        "cosine": cos, "seed": a.seed, **meta,
    }
    (out_dir / f"{path.stem}.export.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    if not (report["max_abs_diff"] < 1e-3 and cos > 0.99999):
        print("PARITY FAIL", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
