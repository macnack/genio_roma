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
- Settled 2026-11-06 (former H1): DX-COM 2.4.1 output is `.dxnn` v8 and loads/runs on RT 3.4.2; 2.5.0 emits v9 (documented), not tested on the board. (`reports/ops.md`, "Board check")
- Settled 2026-11-06 (former H2): `dx_engine` 3.4.2 installs from the shipped cp312 wheel into a user-space venv (`/home/ubuntu/dxenv`); system packages untouched. `InferenceEngine(model).run([uint8 HWC])` works. (`scripts/eval_dx_board.py`)
- Settled 2026-11-06 (former H3, partly): the `dxrun` flags we used on RT 3.4.2 exist and work: `-m -b -s -v -n -l -t -w -d -f --use-ort --profiler --buffer-count`. Flags we did not use are unchecked. (`scripts/sweep_dxrun.sh`)
- Settled 2026-11-06 (former H4): RAM/disk are tight but workable: a 602 MB eval array, 200 MB models and ORT in a user venv fit; free disk fell from 3.6 GB to 1.2-2.4 GB after our files. (`reports/cross_device.md`)

## Hypotheses needing validation

- The versions match the documented release rows v2.4.2/v2.4.3 (see `board_discovery.md`, "Consistency with documented release sets"). Whether that means no firmware update is needed is an inference. It has not been confirmed against the release notes.
