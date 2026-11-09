# DX-M1 on Grinn GenioBoard-700: status summary

> Compact of docs/deepx/board_summary.md. Commands and detail: [board_discovery.md](board_discovery.md) (Phase 3, 2026-11-05, read-only `adb shell`).

## Experimentally verified facts

- **Detection:** `lspci`: DX-M1 `01:00.0` `[1ff4:0000]`, PCIe Gen2 x1; driver loaded, `/dev/dxrt0` exists (`lspci -nn`, `dxrt-cli -s`, `ls /dev`, `lsmod`).
- **Versions:** DX-RT `3.4.2`, RT driver `2.6.0`, PCIe driver `2.5.0`, firmware `2.7.4` (`dxrt-cli -s`, `dpkg -l`).
- **Status:** 3 NPU cores, 1000 MHz, 36 °C idle, 3.92 GiB device memory (`dxrt-cli -s`).
- **System:** Ubuntu 24.04.5 LTS aarch64, kernel `6.8.0-9003-mtk`, 8 cores, 3782 MB RAM, `/` 14G with 3.6G free (`uname -a`, `free -m`, `df -h /`).
- **Runtime tools:** `dxrun`, `dxparse`, `dxtop`, `dxbenchmark` in `/usr/local/bin`; only `.dxnn` on the board: `YOLOV5S_1.dxnn` (`command -v`, `find / -name '*.dxnn'`).
- **Python:** system 3.12.3 has only `pillow 10.2.0`; `dx_engine` not installed; cp312 aarch64 wheel at `/usr/share/libdxrt-bin/python/` (`pip3 list`, `dpkg -L`).
- **Runtime minimums:** driver ≥ 2.5.0, PCIe driver ≥ 2.4.0, firmware ≥ 2.7.0, compiler ≥ 1.18.1, `.dxnn` format ≥ v6 (`dxrt-cli -v`).
- Settled 2026-11-06 (H1): DX-COM 2.4.1 emits `.dxnn` v8, loads/runs on RT 3.4.2; 2.5.0 emits v9 (documented), not tested on the board. (`reports/ops.md`, "Board check")
- Settled 2026-11-06 (H2): `dx_engine` 3.4.2 installs from the shipped cp312 wheel into a user-space venv (`/home/ubuntu/dxenv`); system packages untouched; `InferenceEngine(model).run([uint8 HWC])` works. (`scripts/eval_dx_board.py`)
- Settled 2026-11-06 (H3, partly): `dxrun` flags used on RT 3.4.2 exist and work: `-m -b -s -v -n -l -t -w -d -f --use-ort --profiler --buffer-count`; unused flags unchecked. (`scripts/sweep_dxrun.sh`)
- Settled 2026-11-06 (H4): RAM/disk tight but workable (602 MB eval array, 200 MB models, ORT in a user venv); free disk fell from 3.6 GB to 1.2-2.4 GB. (`reports/cross_device.md`)

## Hypotheses needing validation

- The versions match documented release rows v2.4.2/v2.4.3 (`board_discovery.md`, "Consistency with documented release sets"). That no firmware update is needed is an inference, not confirmed against release notes.
