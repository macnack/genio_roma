# DX-M1 on Grinn GenioBoard-700: status summary

Summary of [board_discovery.md](board_discovery.md) (Phase 3 run, 2026-11-05, read-only `adb shell`). Use that file for commands and full detail.

## Experimentally verified facts

- **Detection:** `lspci` shows the DX-M1 as `01:00.0`, `[1ff4:0000]`, PCIe link Gen2 x1. The driver is loaded and `/dev/dxrt0` exists (`lspci -nn`, `dxrt-cli -s`, `ls /dev`, `lsmod`).
- **Versions:** DX-RT `3.4.2`, RT driver `2.6.0`, PCIe driver `2.5.0`, firmware `2.7.4` (`dxrt-cli -s`, `dpkg -l`).
- **Status:** three NPU cores at 1000 MHz and 36 °C idle, 3.92 GiB device memory (`dxrt-cli -s`).
- **System:** Ubuntu 24.04.5 LTS on aarch64, kernel `6.8.0-9003-mtk`, 8 cores, 3782 MB RAM, `/` 14G with 3.6G free (`uname -a`, `free -m`, `df -h /`).
- **Runtime tools:** `dxrun`, `dxparse`, `dxtop`, `dxbenchmark` are installed in `/usr/local/bin`. The only `.dxnn` on the board is `YOLOV5S_1.dxnn` (`command -v`, `find / -name '*.dxnn'`).
- **Python:** system Python 3.12.3 has only `pillow 10.2.0`. `dx_engine` is not installed. A cp312 aarch64 wheel ships at `/usr/share/libdxrt-bin/python/` (`pip3 list`, `dpkg -L`).
- **Runtime minimums:** this RT enforces driver ≥ 2.5.0, PCIe driver ≥ 2.4.0, firmware ≥ 2.7.0, compiler ≥ 1.18.1, and `.dxnn` format ≥ v6 (`dxrt-cli -v`).

## Hypotheses needing validation

- The versions match the documented release rows v2.4.2/v2.4.3 (see `board_discovery.md`, "Consistency with documented release sets"). Whether that means no firmware update is needed is an inference. It has not been confirmed against the release notes.
- A model compiled with DX-COM 2.5.0 may use a `.dxnn` format newer than RT 3.4.2 loads (`board_discovery.md` H1). Settle with `dxparse`/`dxrun` on a candidate file.
- The `dx_engine` cp312 wheel should install into a venv without touching system packages (`board_discovery.md` H2). Not yet tried.
- The docs were written against RT 3.5.0 sources, and flags may differ on RT 3.4.2 (`board_discovery.md` H3). Check `dxrun --help` on the board before relying on a flag.
- 3.7 GB RAM and 3.6 GB free disk may limit tooling such as ONNX Runtime or numpy, and larger models (`board_discovery.md` H4).
