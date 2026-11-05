# DX-COM INT8 quantization

Scope: quantization modes, Q-Lite / Q-Pro naming, QAT (Q-Master), tuning workflow. Follows [CONVENTIONS.md](CONVENTIONS.md).

## Officially documented facts

Basics
- DX-ModelZoo benchmarks "quantized INT8 models on DEEPX NPU" against FP32 on CPU/GPU. [dx-compiler@a087726ead v2.5.0: source/docs/01_DXNN_Compiler_Overview.md#L12]
- Default path is post-training quantization (PTQ) driven by calibration images (see calibration.md); Q-Master/QAT is the fine-tuning escalation. [dx-compiler@a087726ead v2.5.0: source/docs/02_08_Quantization_Aware_Training.md#L28-L34]
- Quantization runs on GPU by default when CUDA is available, else CPU; `--use_gpu False` forces CPU. GPU shortens Q-Pro/DXQ time 2-5x but is not required. [dx-compiler@a087726ead v2.5.0: source/docs/02_05_JSON_File_Configuration.md#L136-L140] [dx-compiler@a087726ead v2.5.0: source/docs/02_05_JSON_File_Configuration.md#L175]

Q-Lite vs Q-Pro (naming)
- The DX-COM manual in the repo does not use the term "Q-Lite". It documents "Q-PRO" = DXQ-P0..P5 enhancement schemes (manual, `enhanced_scheme`, since v2.1.0) and automatic Q-PRO (`--use_q_pro`). [dx-compiler@a087726ead v2.5.0: source/docs/02_05_JSON_File_Configuration.md#L153-L158] [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L116-L134]
- dx-modelzoo defines profiles: `q-lite` = "NPU profile with standard calibration"; `q-pro` = profile with `calibration.use_q_pro: true` and `num: 1024`; `c-lite` = `opt_level: 0`. [dx-modelzoo@ab3e3a4234 v1.0.0: docs/source/02_03_YAML_Configuration.md#L270-L314]
- Hence, by dx-modelzoo's definition, Q-Lite = plain PTQ compile, Q-Pro = automatic Q-PRO compile. Model Zoo artifacts are published per variant with the compiler version used (e.g. Q-Lite built with DX-COM 2.5.0, Q-Pro with 2.4.0 for one CLIP model; Q-Lite top1 69.74 vs Q-Pro 69.43 vs ONNX 71.36). [dx_app@375de0344f v3.3.0: src/python_example/zero_shot_image_classification/clip/clip-img_vit-b32_256x256_datacomp-s34b-b86k/model.html#L94] [dx_app@375de0344f v3.3.0: src/python_example/zero_shot_image_classification/clip/clip-img_vit-b32_256x256_datacomp-s34b-b86k/model.html#L98]
- Web: release notes say v2.4.0 adds "next-gen quantization (Q-PRO / QAT)"; Q-Lite/Q-Pro are not defined on the developer pages fetched. [developer.deepx.ai/, fetched 2026-11-05]

DXQ schemes (manual Q-PRO)
- DXQ-P0 very fast/low gain; P1 very slow/low-middle; P2 very slow/middle-high; P3, P4, P5 very slow/high; try P3/P4 first; results not guaranteed to improve. [dx-compiler@a087726ead v2.5.0: source/docs/02_05_JSON_File_Configuration.md#L163-L179]
- JSON keys as documented:
  ```json
  {
    "enhanced_scheme": {
      "DXQ-P3": {
        "num_samples": 1024
      }
    }
  }
  ```
  [dx-compiler@a087726ead v2.5.0: source/docs/02_05_JSON_File_Configuration.md#L224-L232] P0 takes `alpha`; P1 is `true`; P2 takes `alpha`, `beta`, `cosim_num`. [dx-compiler@a087726ead v2.5.0: source/docs/02_05_JSON_File_Configuration.md#L182-L219]
- Automatic Q-PRO: `dxcom -m model.onnx -c config.json -o ./output --use_q_pro` ; Python `use_q_pro=True`; mutually exclusive with a manual `enhanced_scheme`; ONNX compile path only. [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L120-L131]
- `enhanced_scheme` not supported for multi-input models. [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L512]
- Version availability: DXQ >= v2.1.0; automatic Q-PRO listed in the v2.4.0 changelog; `quant_diagnosis`/QXNN resume >= v2.4.0; Q-Master >= v2.4.0. [dx-compiler@a087726ead v2.5.0: source/docs/02_05_JSON_File_Configuration.md#L155-L156] [dx-compiler@a087726ead v2.5.0: source/docs/Appendix_Change_Log.md#L95] [dx-compiler@a087726ead v2.5.0: source/docs/02_07_Quantization_Tuning_Workflow.md#L8-L9] [dx-compiler@a087726ead v2.5.0: source/docs/02_08_Quantization_Aware_Training.md#L9-L11]

Tuning workflow (diagnose then resume)
- `--quant_diagnosis` writes `quant_diagnosis/diagnosis_report.html` (per-region OK/Warning/Critical, Cosine Similarity and QSNR, candidate recompile snippets) and `quant_diagnosis/{model}.qxnn`. [dx-compiler@a087726ead v2.5.0: source/docs/02_07_Quantization_Tuning_Workflow.md#L25-L36] [dx-compiler@a087726ead v2.5.0: source/docs/02_07_Quantization_Tuning_Workflow.md#L75-L82]
- QXNN resume re-runs `Quantization -> Optimize -> Codegen -> SingleArtifact` from a `.qxnn`; no ONNX/config needed; options `--checkpoint`, `--recalibration_method {minmax,ema,iqr}`, `--enhanced_scheme`, `--dataset_path`, and `-o` required; `--checkpoint` excludes `-m`; `--use_q_pro` excludes `--enhanced_scheme`. Output `{checkpoint_stem}.dxnn`. [dx-compiler@a087726ead v2.5.0: source/docs/02_07_Quantization_Tuning_Workflow.md#L91-L157]
  ```bash
  dxcom \
    --checkpoint output/large_model/quant_diagnosis/large_model.qxnn \
    -o output/large_model_iqr \
    --recalibration_method iqr
  ```
  [dx-compiler@a087726ead v2.5.0: source/docs/02_07_Quantization_Tuning_Workflow.md#L111-L115]
- Harness-recommended escalation order (not the manual): calibration method ema -> minmax -> iqr; Q-PRO; quant_diagnosis/resume; QAT. [dx-compiler@a087726ead v2.5.0: .deepx/instructions/compilation-workflow.md#L80-L89]

QAT (Q-Master)
- A `qmaster` block in the same JSON switches PTQ to QAT automatically; no extra CLI flag. Needs a CUDA GPU and hundreds to thousands of training images; no labels needed with default KD (FP32 teacher, MSE). [dx-compiler@a087726ead v2.5.0: source/docs/02_08_Quantization_Aware_Training.md#L5-L7] [dx-compiler@a087726ead v2.5.0: source/docs/02_08_Quantization_Aware_Training.md#L28-L34] [dx-compiler@a087726ead v2.5.0: source/docs/02_08_Quantization_Aware_Training.md#L121-L123]
- Example `qmaster` block: `{"batch_size": 16, "train_limit": 2000, "val_limit": 200, "epochs": 10}` [dx-compiler@a087726ead v2.5.0: source/docs/02_08_Quantization_Aware_Training.md#L68-L73]. Full key list (batch_size, train_limit, epochs, lr, optimizer, kd_loss, kd_alpha, criterion, stage1_mode, fast_run, ...) at [dx-compiler@a087726ead v2.5.0: source/docs/02_08_Quantization_Aware_Training.md#L218-L290].
- Outputs: `<model>.dxnn`, `qat_checkpoint/qat_checkpoint.qxnn`. `train_cpu_fp` (default false) controls whether CPU (non-NPU) parts are also trained; otherwise CPU subgraph weights stay frozen. [dx-compiler@a087726ead v2.5.0: source/docs/02_08_Quantization_Aware_Training.md#L95-L99] [dx-compiler@a087726ead v2.5.0: source/docs/02_08_Quantization_Aware_Training.md#L228]
- In v2.5.0 Python uses `qmaster=QMasterConfig(...)`; old `qat_*` args removed. [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L271-L282]
- QAT and Q-PRO re-quantization are mutually exclusive (`EnhancementSchemeError`). [dx-compiler@a087726ead v2.5.0: .deepx/toolsets/dxcom-api.md#L143]
- Recipe for classifiers with labels uses `criterion: cross_entropy`, `kd_loss: kl_div`, ImageFolder layout. [dx-compiler@a087726ead v2.5.0: source/docs/02_08_Quantization_Aware_Training.md#L140-L155]

## Experimentally verified facts

None yet (no DX-M1 available on host as of 2026-11-05).

## Hypotheses needing validation

- Quantization scheme details (per-tensor vs per-channel weights, symmetric vs asymmetric activations, INT8 only vs mixed precision, how CPU-partition ops are computed - FP32?) are not stated in any source read. Settle by reading the `quant_diagnosis` "Evidence Summary" (weight/activation details) on a real compile.
- Q-Lite as a DX-COM concept is inferred from dx-modelzoo profile names; DX-COM itself has no "Q-Lite" flag. Confirm that a plain `dxcom` compile equals the Model Zoo Q-Lite DXNN (e.g. compare with the published JSON under `q-lite-json`).
- The two Model Zoo CLIP rows show Q-Pro (2.4.0) slightly below Q-Lite (2.5.0), so Q-Pro is not guaranteed to be better; for ConvNeXt-Tiny, A/B test ema, iqr, minmax, `--use_q_pro`.
- Quantization sensitivity of LayerNorm and GELU in ConvNeXt on this NPU is unknown; use `--quant_diagnosis` to see which regions are Warning/Critical.
- QAT feasibility for ConvNeXt (training on GPU with CPU-placed LayerNorm if any, `train_cpu_fp`) is untested.
- Exact tolerances for Cosine Similarity / QSNR severity tiers are in report images only; unread.
