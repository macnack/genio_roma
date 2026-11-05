# docs/deepx index

Local documentation set on the DEEPX DX-M1 NPU toolchain (PyTorch -> ONNX -> DX-COM -> DXNN -> DX-RT), written for the ConvNeXt-Tiny pipeline in this project. Every doc separates officially documented facts, experimentally verified facts and hypotheses; read [CONVENTIONS.md](CONVENTIONS.md) first for the rules, citation format and pinned source versions.

Reading order for a first pass: architecture, installation, onnx_compatibility, compiler, calibration, quantization, runtime, python_api, performance_optimization, troubleshooting, tricks_and_best_practices.

## Officially documented facts

Index of documents (this table is an index only; the claims live in the linked docs, each with its own citations). Pinned sources are listed in [CONVENTIONS.md](CONVENTIONS.md) (dx-all-suite v2.5.0, dx-compiler v2.5.0, dx-runtime v2.5.0, DX-RT v3.5.0, dx_app v3.3.0, driver v2.7.0, firmware v2.7.6).

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

[developer.deepx.ai/tech-docs/, fetched 2026-11-05] is the web entry point to the same SDK documentation (DX-AllSuite, DXNN SDK: DX-COM, DX-RT, DX-STREAM, DX-APP).

## Experimentally verified facts

None yet (no DX-M1 available on host as of 2026-11-05).

## Hypotheses needing validation

- Document set completeness: `troubleshooting.md` was not present when this index was written (other documents were being produced concurrently); re-list `docs/deepx/` and fix links once all files exist.
- Doc contents were written independently from sources pinned on 2026-11-05; cross-doc contradictions (for example on `quantization_device`, DX-RT CLI tool names) are flagged inside the individual docs, see "Hypotheses" in [tricks_and_best_practices.md](tricks_and_best_practices.md). A consistency pass across all docs would settle remaining mismatches.
