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

## MDLA test with NeuroPilot 6 (2026-11-07, after approval to create `/etc/nhw`)

System change made with the user's approval: installed the 944 B `nhw` file (from the `mediatek-genio-...` firmware deb, extracted on the laptop, not via dpkg) to `/lib/firmware/mediatek/mt8390/nhw` and symlinked `/etc/nhw` to it. Undo: `sudo rm /etc/nhw /lib/firmware/mediatek/mt8390/nhw`.

Verified:
- `ncc-tflite --arch=?` now lists `mdla3.0`, `tflite_cpu`, `vpu`.
- Toolchain sanity: `mobilenet_v2_1.0_224_quant.tflite` compiles with `--arch=mdla3.0` to a 3.67 MB DLA; `neuronrt -m hw -a mnv2.dla -i in0.bin -o out0.bin -c 20` ran 20 inferences in 23 ms total, and `dmesg` shows `mt8188_apu_top_on`/`power off done` around the run (`reports/acc/np6_mdla_run_mnv2.log`). Input was zeros, so this proves execution on the APU path, not output correctness. Per-op MDLA placement was not inspected.
- ConvNeXt-Tiny, raw TFLite (`onnx2tf`, no rewrites): `--check-target-only` rejects all 74 `BATCH_MATMUL` nodes ("input rank is invalid"), same 4Dx2D pattern as on the GPU.
- ConvNeXt-Tiny with the logged GPU rewrites (`A_tiny_gpu`, `A_tiny_gpuB`, FP32): passes verification, but MDLA reports "Cannot support Float32 input/output" on every op; `--relax-fp32` does not change the check-only report.
- With FP16 weights (`A_tiny_gpuB_float16.tflite`): `--check-target-only` exits 0 with no unsupported-op report.

Blocker (verified): the real compile `ncc-tflite --arch=mdla3.0 [-O0|--no-verify|--relax-fp32] -d out.dla <model>` **segfaults** inside the compiler (after "Map FULLY_CONNECTED Done" with `--verbose`) for both the FP32+`--relax-fp32` and the FP16 model. gdb backtrace has no symbols (`reports/acc/np6_mdla_compile_gdb_bt.log`). `--arch=vpu` fails: "unsupported data type: Float16".
Unknown: which op or tensor triggers the crash; whether INT8 TFLite compiles; whether the jammy-built compiler on noble is the cause. Hypothesis only.
ConvNeXt has NOT run on the MDLA.

## ConvNeXt-Tiny on the MDLA: bisect, root causes, result (2026-11-07)

**Result (verified):** A-tiny FP16 runs on the MDLA (`ncc-tflite --arch=mdla3.0` -> `neuronrt -m hw`, NeuroPilot 6.2.3): **56.0 ms/inference** (11200 ms / 200 runs, 3 repeats, `reports/acc/np6_mdla_timing_At16.log`; model-only, excludes preprocessing and process start), Top-1 **82.03%** / Top-5 95.78% on the 4000-image subset (reference 81.93 / 95.93; agreement 99.2%; `reports/acc/mdla_At16.*`), 0 failed runs. One image of 4000 yields `inf` logits (FP16 overflow on that image; counted in the scores as-is). Placement: compiled for `mdla3.0` only, so an op the MDLA cannot run would have failed the compile ("Cannot find an execution plan"), as happened for `--arch=vpu`; APU power-on/off lines in `dmesg` during runs. Per-op placement from `--show-exec-plan` was not captured (that flag prints and exits without writing a DLA).

**Graph changes needed (each ORT-parity checked; scripts in `scripts/`):**
1. 4D x 2D const MatMul -> Reshape/MatMul/Reshape (`rewrite_matmul_reshape.py`, as for the GPU), minimal channels-first mean set and GELU(erf)->tanh (`make_gpu_tflite.sh`), LayerNorm variance rescale for FP16 (`rewrite_ln_scale.py`).
2. **MatMul -> Gemm** (`rewrite_matmul_gemm.py`, max abs diff 0.0). Root cause #1: prefix bisect (`np6_mdla_bisect*.log`) shows `ncc-tflite` **segfaults** whenever the model contains a 2D `BATCH_MATMUL` with constant weights (first at node 13); with `Gemm` (TFLite `FULLY_CONNECTED`) the full model compiles to an 83 MB DLA. Cause inside the compiler: Unknown (no symbols).
3. **Fold the LayerNorm epsilon into the Gemm bias** (`rewrite_eps_bias.py`, 18 LNs, ORT diff 3.6e-7). Root cause #2: correctness bisect (`bisect_ncc_acc.py`, `np6_mdla_acc_bisect*.log`) shows the model is exact through node 227 and node 228 (`var + 1e-6`, `Add` after the `Gemm`) is wrong for exactly the last 64 of 384 channels at every position (negative "variances"), giving NaN downstream. Cause: Unknown; a fused FC+Add tiling bug for C=384 is only a hypothesis. After the fold: cosine 0.998 / 0.997 on two images, matching top-1.
Without 2 the compile crashes; without 3 the output is NaN/garbage while the run still returns OK.

**INT8 (blocked, verified):** `onnx2tf -oiqt -tb tf_converter` (100 calibration images) produces `full_integer_quant` / `integer_quant` / `dynamic_range_quant` TFLites; `ncc-tflite` 6.2.3 rejects all three with "Fail to create tflite context". `ncc-tflite --show-builtin-ops` (`np6_ncc_builtin_ops.txt`) lists SQRT and EXP only at version 1, while the INT8 model uses SQRT v2 and EXP v2 (all other ops used are within the supported versions). Not tried: replacing SQRT/EXP (e.g. x*RSQRT(x) for the std, a non-exp GELU) so the quantized graph only uses supported op versions. Each would be a further logged graph change, and INT8 accuracy is a separate risk (ORT MinMax PTQ collapsed to 20.9% Top-1 on the CPU, `reports/cross_device.md`).

Not done: A-small on the MDLA, model B, per-op MDLA placement dump, the A-tiny FP16 inf image investigation, throughput with multiple MDLA cores (single-process `-c` only).

### Update: minimal rewrite set (supersedes the A-tiny numbers above)
Built like the GPU minimal set: `rewrite_matmul_reshape` + `rewrite_mean --broadcast --only nchw_c,gap` + `rewrite_ln_scale` (FP16) + `rewrite_matmul_gemm` -> `onnx2tf` FP16 -> `ncc-tflite --arch=mdla3.0`. Stage LayerNorm means stay native TFLite `MEAN`, so the faulty `FULLY_CONNECTED`->`ADD` pattern never appears and the epsilon fold (`rewrite_eps_bias.py`) is not needed.

| Model | ms/inference (3 x 200 runs) | Top-1 / Top-5 (4000 imgs) | ref Top-1 | agreement | KL | non-finite |
|---|---|---|---|---|---|---|
| A-tiny (`mdla_AtM16.*`) | 54.8 | 81.95 / 95.90 | 81.93 | 99.88% | 1.4e-5 | 0 |
| A-small (`mdla_As16.*`) | 105.0 | 83.13 / 96.18 | 83.13 | 99.90% | 1.4e-5 | 0 |
| A-tiny, earlier full-mean set + eps fold (`mdla_At16.*`) | 56.0 | 82.03 / 95.78 | 81.93 | 99.18% | - | 1 image |

The earlier variant's lower fidelity and the one inf image are therefore attributable to the extra Gemm-based means, not to the MDLA FP16 path in general (verified only for these two models).
