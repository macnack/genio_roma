# Genio-700 APU (MediaTek MDLA 3.0) via ONNX Runtime NeuronExecutionProvider: result 2026-11-06

**Result: NOT usable on this board with the packages available from apt. No model ran on the APU.**
The stack installs and the provider loads, but the very first call into `/dev/apusys` fails, even for a 3-conv toy CNN.

## What was installed (user-approved, reversible)
Board has no network (Ethernet down), so the `.deb` files were downloaded on the laptop and installed with `dpkg -i`:
`libneuropilot8` / `-mdw` / `-nhw` 8.2.16-0ubuntu3, `libonnxruntime-neuron` + `python3-onnxruntime-neuron` 1.20.2-0ubuntu1
(PPA `baoshan-team/baoshan-release`), `clinfo`, and dependencies `libc++1(-18)`, `libc++abi1-18`, `libunwind-18`, `python3-numpy` 1.26.4.
Undo: `sudo apt remove python3-onnxruntime-neuron libonnxruntime-neuron libneuropilot8 libneuropilot8-mdw libneuropilot8-nhw clinfo python3-numpy libc++1 libc++1-18 libc++abi1-18 libunwind-18`.
The module lives in a non-default path: `PYTHONPATH=/usr/lib/onnxruntime-neuron/python`. The provider also needs a writable temp dir: with
`TMPDIR` unset it fails with `filesystem error: temp_directory_path: No such file or directory [/data/local/tmp]`; `TMPDIR=/home/ubuntu/tmpn` fixed that.

## Experimentally verified (this board, kernel `6.8.0-9003-mtk` Grinn build)
1. `ort.get_available_providers()` -> `['NeuronExecutionProvider', 'XnnpackExecutionProvider', 'CPUExecutionProvider']`; the Neuron runtime opens
   (`dlopen libneuronusdk_adapter.mtk.so`, `NeuronApi version: 8.2.16`, devices `mtk-dsp`, `mtk-mdla`).
2. A provider being listed does NOT mean nodes run on it. With FP32 ConvNeXt-Tiny and no flags the Neuron compiler rejects the model
   (`MDLA: Cannot support Float32 input`, `VPU: unsupported data type: Float32`, `EP_FAIL: Failed to Compile`). Log: `reports/acc/neuron_fp32_tiny.log`.
3. Feeding an FP16-converted ONNX gave `All nodes placed on [CPUExecutionProvider]. Number of nodes: 615` — the session "worked" (248 ms) but ran 100% on CPU.
   This is a false positive if only `get_providers()` is checked. Log: `reports/acc/neuron_fp16_tiny.log`.
4. With the documented options on the FP32 model (`NEURON_FLAG_USE_FP16=1`, `NEURON_FLAG_MIN_GROUP_SIZE=1`; MediaTek ORT docs) the graph reaches the APU
   compiler, then fails: `[apusys][error]memAlloc: alloc mem(64/4096/0/0x5) fail(Bad address)` -> `Failed to allocate eDMA code buffer` -> segmentation fault.
   Log: `reports/acc/neuron_fp16flag_tiny.log`.
5. Not model-related: a 3-conv/BN/ReLU toy CNN (`scripts/make_toy_cnn.py`) fails identically.
6. Syscall level (`strace -f -e ioctl,openat`): the first ioctls on `/dev/apusys` return `EFAULT`:
   `ioctl(3, _IOC(_IOC_READ|_IOC_WRITE, 0x41, 0, 0x28), ...) = -1 EFAULT` and `ioctl(3, _IOC(.., 0x41, 0x21, 0x30), ...) = -1 EFAULT`.
7. Kernel side is alive: `dmesg` shows the APU firmware handshake (`mtk-apu 190e1000.apusys_rv`, `[reviser] ... Done`, `mdw dev init`), `/dev/apusys` is `root:render 0660`.
   The library reads `/etc/apusys/mt8188/nhw`. Only one `libneuropilot8` version (8.2.16) is published in the PPA, so no alternative to try.

## Interpretation (hypothesis, not verified)
The userspace `libneuropilot8` 8.2.16 and the Grinn kernel's apusys driver disagree on the ioctl interface (struct layout/size), so the first memory
request is rejected with `EFAULT`. The kernel header package contains only a skeleton of the driver tree (`ubuntu/mtk-apusys-driver`: Kconfig, Makefile, power, sapu),
so the ioctl definitions could not be compared. Resolution needs a matching kernel/userspace pair from MediaTek or Grinn (MediaTek docs say
the Neuron EP is enabled by default only on Genio 720/520 and Genio 700 needs a MediaTek representative [ORT acceleration page]).

## Follow-up 2026-11-07: wrong package generation (strongest lead, NOT yet tested on the board)
Everything above used NeuroPilot **8** (`libneuropilot8` 8.2.16, PPA `baoshan-team`, a third-party PPA, not MediaTek's). MediaTek's own Ubuntu
instructions for Genio 700 use NeuroPilot **6**: `sudo apt install mediatek-libneuron mediatek-neuron-utils` (+ `mediatek-apusys-firmware-genio700`), verified with
`sudo vpu5_test -a ks -l 10` (expected PASS) [https://genio.mediatek.com/doc/ubuntu/bsp-installation/neuropilot.html]. The same MediaTek docs say the NeuronExecutionProvider
for ONNX Runtime on Genio 700/510 needs a MediaTek representative; the baoshan PPA build was not made for it.
Facts checked on 2026-11-07 (read-only, laptop + board `dpkg`):
- The NP6 packages exist in `ppa:mediatek-genio/genio-public`, **Ubuntu 22.04 (jammy) only**, arm64: `mediatek-libneuron` 6.0+genio23.2-0genio1 (libneuronusdk 6.3.3, libapu_mdw 2.0.0,
  libvpu5), `mediatek-neuron-utils` same version (contains `neuronrt`, `ncc-tflite`, `vpu5_test`, `mdla3_player`, `apu_mdw_test`), `mediatek-apusys-firmware-genio700` 0.9+genio23.2-0genio3.
  There is no noble (24.04) build. This board runs Ubuntu 24.04 with Grinn's 6.8.0-9003-mtk kernel.
- Installed on the board: only NP8 (`libneuropilot8*`); none of `mediatek-libneuron`, `mediatek-neuron-utils`, `mediatek-apusys-firmware-genio700`. The board already has
  `linux-firmware-mediatek-genio` 25.0.4 which ships `/lib/firmware/mediatek/mt8390/apusys.sig.img` (same paths as the genio700 firmware deb, so installing that deb would conflict; it should not be installed).
- NP6 needs `libtinfo.so.5` (jammy `libtinfo5`, universe), absent on noble; NP6 `libc++` deps are already installed.
- `ncc-tflite` and `neuronrt` are therefore public (earlier note "NDA SDK" was wrong for NP6).
- NP8 reads `/etc/apusys/mt8188`, `mt8189`, `mt8195` (its own nhw blobs), not `mt8390`; NP6's firmware deb ships `mt8390/nhw` and `/etc/nhw`.
Hypothesis (unverified): the first `/dev/apusys` ioctls from NP8 userspace (struct sizes 0x28 / 0x30) do not match the apusys driver generation in this kernel, which MediaTek ships
with NP6 userspace for Genio 700; EFAULT is what a size/layout mismatch in `copy_from_user` would give. A non-invasive test (unpack the NP6 debs into a private directory,
`LD_LIBRARY_PATH` + private libtinfo5, run `vpu5_test -a ks -l 10` and `neuronrt`) was prepared in `data/board_debs_np6/np6` but NOT run: running third-party binaries
on the board needs the user's go-ahead. Nothing on the board was changed for this follow-up.

## Not done
- Ahead-of-time compile with `ncc-tflite` and run with `neuronrt` (needs the NP6 packages above).
- INT8 QDQ model through the Neuron EP (stack fails before model-specific code, so FP16/INT8 choice is moot).
- Any APU latency or accuracy number: none exists.
