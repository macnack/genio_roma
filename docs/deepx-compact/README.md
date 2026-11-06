# docs/deepx compact index

> Compact of docs/deepx/README.md. Full text and citations are in the source docs.

DEEPX DX-M1 NPU toolchain (PyTorch -> ONNX -> DX-COM -> DXNN -> DX-RT), for the ConvNeXt-Tiny pipeline. Read [CONVENTIONS.md](CONVENTIONS.md) first (claim classes, citation format, pinned sources).

Read order: architecture, installation, onnx_compatibility, compiler, calibration, quantization, runtime, python_api, performance_optimization, troubleshooting, tricks_and_best_practices.

Pinned sources (2026-11-05): dx-all-suite v2.5.0, dx-compiler v2.5.0, dx-runtime v2.5.0, DX-RT v3.5.0, dx_app v3.3.0, driver v2.7.0, firmware v2.7.6.

## Files

| File | Scope |
|---|---|
| [CONVENTIONS.md](CONVENTIONS.md) | Claim classes, citation format, pinned commits, hard rules |
| [architecture.md](architecture.md) | Toolchain components and how they fit |
| [installation.md](installation.md) | Documented install steps and their system impact |
| [hardware.md](hardware.md) | DX-M1 hardware facts |
| [version_compatibility.md](version_compatibility.md) | Compatibility matrix: DX-COM, DX-RT, driver, firmware, dx_app |
| [onnx_compatibility.md](onnx_compatibility.md) | ONNX opsets/operators accepted by DX-COM |
| [compiler.md](compiler.md) | DX-COM pipeline, CLI, Python API |
| [calibration.md](calibration.md) | Calibration data, loaders, preprocessing |
| [quantization.md](quantization.md) | INT8 quantization methods and tuning |
| [runtime.md](runtime.md) | DX-RT runtime, CLI tools, tensors, scheduling |
| [python_api.md](python_api.md) | DX-RT Python API (`dx_engine`) |
| [cpp_api.md](cpp_api.md) | DX-RT C++ API |
| [performance_optimization.md](performance_optimization.md) | Profiling, benchmarking, tuning |
| [troubleshooting.md](troubleshooting.md) | Errors, symptoms, fixes |
| [tricks_and_best_practices.md](tricks_and_best_practices.md) | Tips and pitfalls by stage |
| [agent_dev.md](agent_dev.md) | Official dx-agent-dev (`.deepx/`) agent/skill system and reuse plan |
| [board_discovery.md](board_discovery.md) | Board discovery notes |

Web entry point: [developer.deepx.ai/tech-docs/, fetched 2026-11-05].

## Experimentally verified facts

Board-side results now exist; the DX-M1 is on the Genio-700 board (adb), not on the laptop. See `board_discovery.md` and `reports/` (ops, accuracy, cross_device, apu_neuron, gpu_armnn).

## Hypotheses needing validation

- All 18 files of the set are now present in this directory (CONVENTIONS.md copied unchanged; board_discovery.md was not in the source index).
- Contradiction: the verified-facts line above says no DX-M1 is available, but `board_discovery.md` (Phase 3, 2026-11-05) records a DX-M1 (`/dev/dxrt0`, RT 3.4.2) on the board. The verified-facts line predates that run; update it.
- Docs were written independently from pinned sources; cross-doc contradictions (e.g. `quantization_device`, DX-RT CLI tool names) are flagged inside the individual docs. A consistency pass would settle the rest.
