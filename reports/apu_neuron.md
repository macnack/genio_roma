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

## Not done
- Ahead-of-time compile with `ncc-tflite` and run with `neuronrt` (NDA SDK, not available).
- INT8 QDQ model through the Neuron EP (stack fails before model-specific code, so FP16/INT8 choice is moot).
- Any APU latency or accuracy number: none exists.
