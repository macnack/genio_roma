# ONNX compatibility with DX-COM (compact)

> Compact of docs/deepx/onnx_compatibility.md. Full text and extended citations are in the source file.

Scope: ONNX export requirements and operator support for DX-COM v2.5.0. The full operator table is in the repo (`03_Building_Models.md`, "Supported ONNX Operators").

## Officially documented facts

### Export requirements

- `torch.onnx.export()` example uses `opset_version=17`; "ONNX opset version (11~21 supported, 17 recommended)". [dx-compiler@a087726ead v2.5.0: source/docs/02_04_ONNX_File_Configuration.md#L31-L48]
- Opset 22 and above not supported. [dx-compiler@a087726ead v2.5.0: source/docs/Appendix_Change_Log.md#L220]
- Batch size 1; static input shapes; no `dynamic_axes`; call `model.eval()` before export. [dx-compiler@a087726ead v2.5.0: source/docs/02_04_ONNX_File_Configuration.md#L52-L55]
- JSON `inputs` name must exactly match ONNX input name; shape `[1,C,H,W]` style; single input only via `dxcom` CLI. [dx-compiler@a087726ead v2.5.0: source/docs/02_05_JSON_File_Configuration.md#L31-L43]
- All ops: width, height < 8,192; channels < 32,768; dynamic shapes not supported. [dx-compiler@a087726ead v2.5.0: source/docs/03_Building_Models.md#L13-L17]
- Broadcasting: in element-wise Add/Div/Mul/Sub, channel-wise broadcasting not supported when channel dim > 1 (example: 1x24x24x1 NHWC cannot broadcast to 1x24x24x32). [dx-compiler@a087726ead v2.5.0: source/docs/03_Building_Models.md#L19-L22]
- Doc caveat: "operator support may vary depending on how operations are combined within a model... a general guideline." [dx-compiler@a087726ead v2.5.0: source/docs/03_Building_Models.md#L97-L98]

### Unsupported ops and CPU fallback

- Models "must use only the supported operations to ensure successful compilation and optimal performance on our NPU." [dx-compiler@a087726ead v2.5.0: source/docs/03_Building_Models.md#L3]
- Some rows say outside stated conditions the op "runs on CPU" (Conv 5D input, ConvTranspose 5D, LayerNormalization with D >= 4080, LayerNorm built from primitives reduced over multiple dims). [dx-compiler@a087726ead v2.5.0: source/docs/03_Building_Models.md#L38-L49]
- `NodeNotFoundError` = "ONNX model contains a node that is unsupported by the compiler"; `NotSupportError` covers dynamic input shape etc. [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L772-L776]
- Summary HTML shows per-partition CPU-fallback reasons; `--aggressive_partitioning` (experimental) pushes more ops to NPU. [dx-compiler@a087726ead v2.5.0: source/docs/04_Compilation_Summary_Report.md#L13] [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L80]
- Agent-harness checklist (harness note, not manual): verify opset 11-21; try `--aggressive_partitioning` for unsupported ops. [dx-compiler@a087726ead v2.5.0: .deepx/instructions/compilation-workflow.md#L429-L432]

### Operator table: "Normal Operations" (condensed; conditions beyond these are in the source) [dx-compiler@a087726ead v2.5.0: source/docs/03_Building_Models.md#L28-L64]

| Operator | Documented condition |
|---|---|
| Add, Sub, Mul, Div | element-wise / constant scalar / input normalization (Div also in Softmax and LayerNorm) |
| ArgMax | only as final op; preceding output 2D or 4D; along channel dim |
| AveragePool | kernel_shape < 32, strides < 32 |
| BatchNormalization, Concat, ConstantOfShape, Flatten, Gemm, GlobalAveragePool, Identity, MatMul, Reshape, Slice, Split, Squeeze, Transpose | No restrictions |
| Clip | only as activation (e.g. ReLU6) |
| Constant | numeric constants only |
| Conv | dilations < 64, pads < 64, strides < 16; standard: kernel_shape < 16; depth-wise: kernel_shape < 16, dilations [1,1] (except 3x3 with [2,2]), constant weights only; 5D input needs group=1, dilations [1,1,1], auto_pad NOTSET, constant weight; otherwise CPU |
| ConvTranspose | dilations [1,1], output_padding [0,0], pads <= 14, strides in [2,8] symmetric, kernel_shape < 16, group=1; 5D extra limits; otherwise CPU |
| Dropout | removed during inference |
| Einsum | two-input equations reducing to (batched) matmul only |
| Erf | only as part of GELU |
| Gather | indices 0-D, 1-D, or 2-D (2-D new in v2.5.0) |
| LayerNormalization | last-dim only (axis=-1); Scale/B shape [D]; D < 4080 else CPU; multi-dim (e.g. `nn.LayerNorm([C,H,W])`) not supported. Primitive-built LayerNorm (ReduceMean, Sub, Pow, Sqrt, Div, Mul, Add) supported if mean/variance over single dim: last dim, or channel dim of NCHW "such as ConvNeXt `LayerNorm2d`"; multi-dim runs on CPU |
| MaxPool | kernel_shape < 16, strides < 16 |
| Pad | mode=constant only; must precede a Pool or Conv |
| ReduceMean | only along channel dim, or (W,H) dims |
| ReduceSum | only along channel dim |
| Resize | pytorch_half_pixel; nearest/linear; limited scale factors (see source) |
| Shape | cannot be a model output |
| Softmax | axis size < 4080 |

Activations (no restrictions unless noted): Elu, Gelu, HardSwish, HardSigmoid, LeakyRelu, Mish, PRelu (known FPS degradation in v2.4.0), Relu, Selu, Sigmoid, Silu (Swish), Softplus, Tanh. [dx-compiler@a087726ead v2.5.0: source/docs/03_Building_Models.md#L70-L84] Deprecated: Upsample only when N and C scales are 1. [dx-compiler@a087726ead v2.5.0: source/docs/03_Building_Models.md#L93-L95]

### ConvNeXt-relevant ops: documented status

| Op | Status in docs |
|---|---|
| Depthwise Conv 7x7 | Documented: depth-wise Conv requires kernel_shape < 16 (7 qualifies), dilations [1,1], constant weights [L38 above]. 7x7 not named explicitly. |
| LayerNorm / LayerNorm2d | Documented as supported over single (last or NCHW-channel) dim; ConvNeXt `LayerNorm2d` named explicitly [L49 above]. |
| GELU | `Gelu` no restrictions; `Erf` only as part of GELU [L43, L73 above]. |
| Transpose | No restrictions [L64]. |
| Reshape | No restrictions [L56]. |
| Linear (Gemm/MatMul) | No restrictions [L46, L50]. |
| GlobalAveragePool | No restrictions [L47]. |
| Dropout | Removed at inference [L41]. |
| "permute" | No ONNX op by that name; PyTorch `permute` exports as Transpose (general ONNX knowledge, not from DEEPX docs). |

## Experimentally verified facts

- Both opset 13 (primitive LayerNorm chain) and opset 17 (`LayerNormalization`) ConvNeXt-Tiny exports compile on DX-COM 2.4.1; the GELU `Erf` chain, 36 MatMul, Transpose chains, layer-scale Mul and 18 depthwise 7x7 convs are all accepted and end up on the NPU. (`reports/ops.md`)
- Accuracy after INT8 PTQ (EMA, 100 calib images, 4000 ImageNet-val images): A-tiny 81.9% -> 80.8% Top-1, A-small 83.1% -> 82.0%. (`reports/accuracy.md`)
- B-tiny (DINOv3) PTQ feature fidelity is poor (cosine 0.734 vs FP32) while B-small is good (0.984); cause unknown. (`reports/acc/B13_ptq_compare.json`, `reports/acc/BS13_ptq_compare.json`)

## Hypotheses needing validation

- The docs do not say whether an op outside the table fails compilation (NodeNotFoundError) or is placed on CPU. Some rows say "runs on CPU"; the errors table says an unsupported node raises an error. Settle: compile a toy ONNX with an unlisted op (e.g. `Where`); check log / HTML report.
- Whether the ConvNeXt LayerNorm exported by torch (opset 17 may emit fused `LayerNormalization`; lower opsets emit the primitive chain) compiles on NPU. Settle: try both exports, compare partition report. Which form the exporter emits is an assumption.
- ConvNeXt layer-scale (`gamma`, shape [C,1,1] times 1xCxHxW) may collide with the "channel-wise broadcasting not supported when channel > 1" rule; the rule's example is NHWC and the interpretation for constant per-channel operands is unclear. Settle: compile a Mul with constant [1,C,1,1].
- Depthwise 7x7 padding 3: `pads < 64` is satisfied, but the symmetric-padding requirement (NotsupportedPaddingError mentions asymmetric W/H) must be confirmed in the exported graph; a `Pad` before Conv is allowed only in constant mode.
- Stem (4x4 stride 4 Conv) and downsample (2x2 stride 2 Conv) satisfy `kernel_shape < 16`, `strides < 16` on paper. Confirm.
- ReduceMean restriction (channel or W,H only) matters for LayerNorm2d built from primitives. Confirm exported ConvNeXt reduces only over channel.
- Contradiction on recommended opset: 02_04 says 17 recommended [dx-compiler@a087726ead v2.5.0: source/docs/02_04_ONNX_File_Configuration.md#L36]; agent-harness pitfalls file says 13 recommended [dx-compiler@a087726ead v2.5.0: .deepx/memory/common_pitfalls.md#L122-L131]. Both within 11-21. Settle: test both.
- A PDF "DX-COM User Manual 2.5.0" is listed on the Document Download page [developer.deepx.ai/document-download/, fetched 2026-11-05] but links were placeholders; not read. Web operator list at `developer.deepx.ai/tech-docs/DXNN-SDK/DX-COM/Building_Models/` (nav link seen in [developer.deepx.ai/tech-docs/DXNN-SDK/DX-COM/Quick_Start/, fetched 2026-11-05]); only the repo copy was checked. Compare if needed.

## Open questions for ConvNeXt-Tiny

1. Does torch-exported ConvNeXt-Tiny (opset 17 vs 13) use `LayerNormalization` or the primitive chain, and does the compiler keep it on NPU?
2. Does layer-scale multiply pass the broadcast rule?
3. Does `permute`-based LayerNorm (channels-last trick from original ConvNeXt) produce Transpose chains that stay on NPU?
4. Are exact-Erf GELU nodes recognized as `Gelu`, or does a standalone `Erf` appear (documented as unsupported outside GELU)?
5. What fraction of nodes is CPU-placed (HTML report); does `--aggressive_partitioning` improve it?
6. Do width/height < 8192 and channels < 32768 hold at all stages (yes at 224x224 on paper; Tiny max channels 768)?
7. INT8 accuracy after EMA calibration for LayerNorm/GELU-heavy nets (see quantization.md).
