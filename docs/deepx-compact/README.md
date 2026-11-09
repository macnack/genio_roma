# docs/deepx compact index

> Compact of docs/deepx/README.md. Full text and citations are in the source docs.

DEEPX DX-M1 NPU toolchain (PyTorch -> ONNX -> DX-COM -> DXNN -> DX-RT), for the ConvNeXt-Tiny pipeline. Every doc separates officially documented, experimentally verified and hypothesised claims. Read [CONVENTIONS.md](CONVENTIONS.md) first.

Read order: architecture, installation, onnx_compatibility, compiler, calibration, quantization, runtime, python_api, performance_optimization, troubleshooting, tricks_and_best_practices.

## Officially documented facts

Index only; claims live in the linked docs with their own citations. Pinned sources are in [CONVENTIONS.md](CONVENTIONS.md) (dx-all-suite v2.5.0, dx-compiler v2.5.0, dx-runtime v2.5.0, DX-RT v3.5.0, dx_app v3.3.0, driver v2.7.0, firmware v2.7.6).

| Doc | Scope |
|---|---|
| [CONVENTIONS.md](CONVENTIONS.md) | Claim classes, citation format, pinned source commits, hard rules |
| [architecture.md](architecture.md) | DX-M1 toolchain architecture and how the components fit together |
| [installation.md](installation.md) | Documented install steps with their system impact |
| [hardware.md](hardware.md) | DX-M1 hardware facts |
| [version_compatibility.md](version_compatibility.md) | Version compatibility matrix across DX-COM, DX-RT, driver, firmware, dx_app |
| [onnx_compatibility.md](onnx_compatibility.md) | ONNX opsets/operators accepted by DX-COM |
| [compiler.md](compiler.md) | DX-COM compiler pipeline, CLI and Python API |
| [calibration.md](calibration.md) | Calibration data, loaders, preprocessing |
| [quantization.md](quantization.md) | INT8 quantization methods and tuning |
| [runtime.md](runtime.md) | DX-RT runtime: architecture, CLI tools, tensors, scheduling |
| [python_api.md](python_api.md) | DX-RT Python API (`dx_engine`) |
| [cpp_api.md](cpp_api.md) | DX-RT C++ API |
| [performance_optimization.md](performance_optimization.md) | Profiling, benchmarking and performance tuning |
| [troubleshooting.md](troubleshooting.md) | Errors, symptoms and fixes (written by another author; link may not exist yet) |
| [tricks_and_best_practices.md](tricks_and_best_practices.md) | Tips and pitfalls grouped by export, compile, calibration, runtime, performance, debugging |
| [agent_dev.md](agent_dev.md) | Official dx-agent-dev (`.deepx/`) agent/skill system, adapters, and reuse plan for our pipeline |

Web entry point: [developer.deepx.ai/tech-docs/, fetched 2026-11-05].

## Experimentally verified facts

Board-side results exist; the DX-M1 is on the Genio-700 board (adb), not on the laptop. See `board_discovery.md`, `board_summary.md` and `reports/` (ops, accuracy, cross_device, apu_neuron, gpu_armnn).

## Hypotheses needing validation

- Set completeness: `troubleshooting.md` was missing when this index was written; re-list `docs/deepx/` and fix links once all files exist.
- Docs were written independently from sources pinned 2026-11-05; cross-doc contradictions (e.g. `quantization_device`, DX-RT CLI tool names) are flagged inside the individual docs, see "Hypotheses" in [tricks_and_best_practices.md](tricks_and_best_practices.md). A consistency pass would settle the rest.
