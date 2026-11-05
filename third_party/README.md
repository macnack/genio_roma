# third_party (reference code, not committed)

`ConvNeXt/` is a shallow clone, git-ignored:

    git clone --depth 1 https://github.com/facebookresearch/ConvNeXt third_party/ConvNeXt
    git -C third_party/ConvNeXt checkout 048efce   # 2022-07-23

Used unmodified by `scripts/export_onnx.py` (which shims the removed `timm.models.registry` import).
Weights: `weights/convnext_tiny_1k_224_ema.pth` (symlink; sha256 14f3164e3ea6ac32ab3f574f528ce817696c9176fad4221e0a77a905a7360595).
