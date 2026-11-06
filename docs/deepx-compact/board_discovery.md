# Board discovery (Phase 3) — Grinn GenioBoard-700 + DX-M1

> Compact of docs/deepx/board_discovery.md. Full text and extended citations are in the source file.

Run 2026-11-05 via `adb shell` (read-only; nothing installed or changed). Tooling: `bin/README.md`.

## Experimentally verified facts

| Item | Observed | Command |
|---|---|---|
| Host (dev PC) | x86_64, AMD Ryzen AI 9 HX 370, Ubuntu, kernel 6.17.0-41-generic; no DEEPX device | `lscpu`, `lspci` |
| Board SoC | aarch64, 8 cores (Cortex-A55 + Cortex-A78) | `lscpu` |
| Board OS / kernel | Ubuntu 24.04.5 LTS, `6.8.0-9003-mtk #1+grinn-Ubuntu` | `uname -a`, `/etc/os-release` |
| Board RAM / disk | 3782 MB RAM; `/` 14G, 3.6G free (73% used) | `free -m`, `df -h /` |
| PCIe | `01:00.0 Processing accelerators: DEEPX Co., Ltd. DX_M1 [1ff4:0000] (rev 01)`; link Gen2 x1 | `lspci -nn`, `dxrt-cli -s` |
| Device node / modules | `/dev/dxrt0`; modules `dxrt_driver`, `dx_dma` loaded | `ls /dev`, `lsmod` |
| DX-RT | v3.4.2+d803450 (`libdxrt-bin 3.4.2`, arm64 pre-built) | `dxrt-cli -s`, `dpkg -l` |
| RT driver / PCIe driver | v2.6.0 / v2.5.0 (`dxrt-driver-dkms 2.6.0-2`) | `dxrt-cli -s` |
| Firmware | v2.7.4 | `dxrt-cli -s` |
| Device | M1, M.2 Rev 1.0, LPDDR5 5600 Mbps 3.92 GiB; NPU0-2 750 mV / 1000 MHz, 36 °C idle | `dxrt-cli -s` |
| Minimums enforced by this RT | driver 2.5.0, PCIe driver 2.4.0, FW 2.7.0, **compiler ≥ 1.18.1, `.dxnn` format ≥ v6** | `dxrt-cli -v` |
| Installed CLIs | `dxrt-cli, dxrun, dxparse, dxcli, dxtop, dxbenchmark, dxrtd` in `/usr/local/bin` | `command -v` |
| Python | system 3.12.3; **`dx_engine` not installed**; wheels shipped at `/usr/share/libdxrt-bin/python/dx_engine-3.4.2-cp312-...aarch64.whl`; `pillow 10.2.0` only (no numpy, onnx, opencv) | `pip3 list`, `dpkg -L` |
| Models on board | only `/home/ubuntu/dx-runtime/dx_rt/csharp_package/examples/models/YOLOV5S_1.dxnn` | `find / -name '*.dxnn'` |
| Extra | `/home/ubuntu/dx-runtime` (a dx-runtime checkout with `venv-dx-runtime`) exists | `ls` |

Board-side config changed earlier by the user (passwordless sudo, serial autologin): see `bin/README.md`.
- Settled 2026-11-06 (former H1): DX-COM 2.4.1 output is `.dxnn` v8 and loads/runs on RT 3.4.2; 2.5.0 emits v9 (documented), not tested on the board. (`reports/ops.md`, "Board check")
- Settled 2026-11-06 (former H2): `dx_engine` 3.4.2 installs from the shipped cp312 wheel into a user-space venv (`/home/ubuntu/dxenv`); system packages untouched. `InferenceEngine(model).run([uint8 HWC])` works. (`scripts/eval_dx_board.py`)
- Settled 2026-11-06 (former H3, partly): the `dxrun` flags we used on RT 3.4.2 exist and work: `-m -b -s -v -n -l -t -w -d -f --use-ort --profiler --buffer-count`. Flags we did not use are unchecked. (`scripts/sweep_dxrun.sh`)
- Settled 2026-11-06 (former H4): RAM/disk are tight but workable: a 602 MB eval array, 200 MB models and ORT in a user venv fit; free disk fell from 3.6 GB to 1.2-2.4 GB after our files. (`reports/cross_device.md`)

## Consistency with documented release sets

- Board versions (FW 2.7.4, driver 2.6.0, PCIe 2.5.0, RT 3.4.2) match suite release rows v2.4.2/v2.4.3 in `version_compatibility.md` (lines 14-15). Older than pinned repos (RT 3.5.0, driver 2.7.0, FW 2.7.6).

## Hypotheses needing validation

