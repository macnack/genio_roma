# DEEPX version compatibility matrix (compact)

> Compact of docs/deepx/version_compatibility.md. Full text and extended citations are in the source file.

Scope: COM / RT / driver / FW / APP / Stream / ModelZoo compatibility, check commands, and documented contradictions.

## Officially documented facts

### Release matrix (DX-AllSuite 04_Version_Compatibility)

The SDK "maintains strict version dependencies between modules"; the matrix lists validated combinations. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/04_Version_Compatibility.md#L3] Columns: DX-COM, DX-TRON (removed from v2.5.0), DX-FW, NPU Driver, DX-RT, DX-STREAM, DX-APP, DX-ModelZoo.

| Release date | AllSuite | DX-COM | FW | Driver | DX-RT | Stream | APP | ModelZoo |
|---|---|---|---|---|---|---|---|---|
| 2026-10-23 | v2.5.0 | v2.5.0 | v2.7.6 | v2.7.0 | v3.5.0 | v3.2.0 | v3.3.0 | v1.0.0 |
| 2026-09-03 | v2.4.3 | v2.4.1 | v2.7.4 | v2.6.0 | v3.4.2 | v3.1.2 | v3.2.2 | - |
| 2026-08-14 | v2.4.2 | v2.4.0 | v2.7.4 | v2.6.0 | v3.4.2 | v3.1.2 | v3.2.2 | - |
| 2026-08-03 | v2.4.1 | v2.4.0 | v2.7.4 | v2.6.0 | v3.4.1 | v3.1.1 | v3.2.1 | - |
| 2026-07-22 | v2.4.0 | v2.4.0 | v2.7.3 | v2.5.1 | v3.4.0 | v3.1.0 | v3.2.0 | - |
| 2026-05-14 | v2.3.3 | v2.3.0 | v2.5.6 | v2.4.1 | v3.3.2 | v3.0.1 | v3.1.1 | - |
| 2026-04-10 | v2.3.0 | v2.3.0 | v2.5.6 | v2.4.1 | v3.3.0 | v3.0.0 | v3.1.0 | - |
| 2026-02-26 | v2.2.2 | v2.2.1 | v2.5.0 | v2.1.0 | v3.2.0 | v2.2.1 | v3.0.2 | - |
| 2026-01-16 | v2.2.0 | v2.2.0 | v2.5.0 | v2.1.0 | v3.2.0 | v2.2.0 | v3.0.0 | - |
| 2025-11-28 | v2.1.0 | v2.1.0 | v2.4.0 | v1.8.0 | v3.1.0 | v2.1.0 | v2.1.0 | - |
| 2025-09-08 | v2.0.0 | v2.0.0 | v2.1.4 | v1.7.1 | v3.0.0 | v2.0.0 | v2.0.0 | - |
| 2025-07-23 | v1.0.0 | v1.60.1 | v2.1.0 | v1.5.0 | v2.9.5 | v1.7.0 | v1.11.0 | - |

Condensed from the source table (intermediate releases v2.3.1, v2.3.2, v2.4.x subsets, v2.2.1 are in the source). [dx-all-suite@51d81fe2ef v2.5.0: docs/source/04_Version_Compatibility.md#L29-L298]
- Header rows give DX-Compiler / DX-Runtime sub-versions per release (e.g. 2026-10-23: Compiler v2.5.0, Runtime v2.5.0), distinct from component versions. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/04_Version_Compatibility.md#L29-L46]
- DX-TRON removed as of DX-Compiler v2.5.0. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/04_Version_Compatibility.md#L302-L306]
- Our pinned clones match the 2026-10-23 row: COM 2.5.0, FW 2.7.6, driver 2.7.0, RT 3.5.0, Stream 3.2.0, APP 3.3.0, ModelZoo 1.0.0 (see `CONVENTIONS.md` pinned-source table; each repo's `release.ver`).

### Hard minimums stated by components

- DX-RT v3.5.0 raised minimums: Linux driver 2.5.0 -> 2.7.0; Linux PCIe driver 2.4.0 -> 2.7.0; Firmware 2.7.0 -> 2.7.6. [dx_rt@f997363c97 v3.5.0: RELEASE_NOTES.md#L11-L15]
- DX-RT Linux: Driver >= v2.7.0, PCIe Driver >= v2.7.0, Firmware >= v2.7.6. [dx_rt@f997363c97 v3.5.0: docs/source/docs/02_Installation_on_Linux.md#L32-L34]
- Runtime error texts: "The current firmware version is X. Please update your firmware to version Y or higher."; "The current device driver version is X ... update to version Y or higher"; "The model's compiler version(X) is not compatible with this RT library ...". [dx-all-suite@51d81fe2ef v2.5.0: docs/source/05_FAQ_Troubleshooting_Guide.md#L126-L129], [dx-all-suite@51d81fe2ef v2.5.0: docs/source/05_FAQ_Troubleshooting_Guide.md#L176-L179], [dx-all-suite@51d81fe2ef v2.5.0: docs/source/05_FAQ_Troubleshooting_Guide.md#L221-L224]
- DX-COM v2.5.0 outputs `.dxnn` v9; v9 requires DX-RT >= 3.5.0. [dx-compiler@a087726ead v2.5.0: source/docs/02_01_System_Requirements_of_DX-COM.md#L13]
- DX-APP: C++ runners need DX-RT >= 3.5.0 and model format >= v7; Python runners need DX-RT >= 3.0.0; ModelZoo 2_5_0 `.dxnn` (container v9) need DX-RT >= 3.5.0. [dx_app@375de0344f v3.3.0: README.md#L285-L288]
- DX-STREAM: "DX-RT version 3.5.0 or higher must be installed". [dx_stream@c575ed2896 v3.2.0: docs/source/docs/02_DX-STREAM_Installation.md#L14]
- `import dx_engine` fails if `libdxrt.so` major.minor differs from the Python package (bypass `DX_ENGINE_SKIP_VERSION_CHECK=1`). [dx_rt@f997363c97 v3.5.0: RELEASE_NOTES.md#L34]
- Driver v2.0.0 note: "Should be used above DX-RT SDK v3.2.0 for stability". [dx_rt_npu_linux_driver@8455be6254 v2.7.0: RELEASE_NOTES.md#L96-L100]
- DX-COM pin used by ModelZoo: `COM_VERSION=2.5.0` in `dx-compiler/compiler.properties`. [dx-compiler@a087726ead v2.5.0: compiler.properties#L1]
- Downgrading DX-RT: driver and firmware compatibility must be re-verified. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/05_FAQ_Troubleshooting_Guide.md#L240-L241]
- Docker: host driver and container RT/ModelZoo must be upgraded together; container reuses host driver via `/dev`. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/05_FAQ_Troubleshooting_Guide.md#L490-L491]

### Check commands (as documented)

| Component | Command | Citation |
|---|---|---|
| FW, RT driver, PCIe driver, RT | `dxcli -s` (or `dxcli --status \| grep -A2 Version`, `dxcli --status \| grep "RT Driver version"`) | [dx-all-suite@51d81fe2ef v2.5.0: docs/source/04_Version_Compatibility.md#L314-L319], [dx-all-suite@51d81fe2ef v2.5.0: docs/source/05_FAQ_Troubleshooting_Guide.md#L468-L488] |
| DX-COM | `dxcom -v` (04) / `dxcom --version` (02, compiler docs); `python3 -c "import dx_com; print(dx_com.__version__)"` | [dx-all-suite@51d81fe2ef v2.5.0: docs/source/04_Version_Compatibility.md#L325-L331], [dx-compiler@a087726ead v2.5.0: source/docs/02_02_Installation_of_DX-COM.md#L111-L114] |
| ModelZoo | `python3 -c "from importlib.metadata import version; print(version('dx-modelzoo'))"` | [dx-all-suite@51d81fe2ef v2.5.0: docs/source/04_Version_Compatibility.md#L334-L338] |
| `dx_engine` | `python3 -c "import dx_engine; print(dx_engine.__version__)"` | [dx_rt@f997363c97 v3.5.0: docs/source/docs/02_Installation_on_Linux.md#L313-L316] |
| Driver module versions | `modinfo -F version dxrt_driver`, `modinfo -F version dx_dma` (driver sanity script) | [dx_rt_npu_linux_driver@8455be6254 v2.7.0: sanity/sanity.sh#L581-L582] |
| DKMS state | `dkms status` | [dx_rt@f997363c97 v3.5.0: docs/source/docs/02_Installation_on_Linux.md#L559-L575] |
| Pinned driver in suite | `git submodule status dx-runtime/dx_rt_npu_linux_driver` | [dx-all-suite@51d81fe2ef v2.5.0: docs/source/05_FAQ_Troubleshooting_Guide.md#L475-L478] |
| Everything at once | `sudo ./SanityCheck.sh` (dx_rt) prints Runtime, Driver, PCIe Driver, Firmware, ONNX Runtime versions; `./dx-runtime/scripts/sanity_check.sh` | [dx_rt@f997363c97 v3.5.0: docs/source/docs/02_Installation_on_Linux.md#L1071-L1077], [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L411-L416] |
| Firmware image version | `dxrt-cli -g <fw.bin>` (README) | [dx_fw@a72406f3ca v2.7.6: README.md#L4-L6] |

Expected `dxcli -s` header for the 2026-10-23 set: `DXRT v3.5.0`, RT Driver v2.7.0, PCIe Driver v2.7.0, FW v2.7.6. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L741-L749]

### Documented contradictions and inconsistencies

1. **dxcom version flag**: `dxcom -v` vs `dxcom --version`. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/04_Version_Compatibility.md#L325], [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L289]
2. **CLI name**: `dxcli` (suite, DX-RT docs) vs `dxrt-cli` (dx_fw README, `install.sh`, dx-edge guide, benchmark report); both valid, latter a legacy alias. [dx_fw@a72406f3ca v2.7.6: README.md#L6], [dx-runtime@73ff9904f5 v2.5.0: install.sh#L516], [dx_rt@f997363c97 v3.5.0: docs/source/docs/05_Command_Line_Interface.md#L7-L15]
3. **PCIe device ID**: FW v2.7.2 `0x0000` vs driver README `0x0100/0x0110/0x0101`. [dx_fw@a72406f3ca v2.7.6: RELEASE_NOTES.md#L42-L45], [dx_rt_npu_linux_driver@8455be6254 v2.7.0: README.md#L65-L70]
4. **Supported device list**: dx_rt README lists DX_M1 and DX_H1; DX-RT install docs also list DX-M1M. [dx_rt@f997363c97 v3.5.0: README.md#L14-L18], [dx_rt@f997363c97 v3.5.0: docs/source/docs/02_Installation_on_Linux.md#L35]
5. **Website vs repos**: tech-docs page shows SDK v2.4.2 as "current" (Oct 15, 2026); download page lists AllSuite 2.5.0 docs dated Nov 4, 2026; repos are v2.5.0. [developer.deepx.ai/tech-docs/, fetched 2026-11-05], [developer.deepx.ai/document-download/, fetched 2026-11-05]
6. **Firmware dir gap**: FW release notes list v2.7.5, but `m1/` and `m1m/` have no 2.7.5 directory (2.7.4 then 2.7.6). [dx_fw@a72406f3ca v2.7.6: RELEASE_NOTES.md#L14-L22] (directory listing of the clone)
7. **Reboot vs cold boot** after FW update: cold boot "strongly recommended" vs reboot "sufficient in most standard scenarios". [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L341-L342], [dx-all-suite@51d81fe2ef v2.5.0: docs/source/05_FAQ_Troubleshooting_Guide.md#L156-L157]
8. **Python support wording**: DX-RT "Python 3.8.10 or later" vs DX-COM 3.8-3.14 explicit; DX-RT wheels bundled 3.8-3.14. Not contradictory, different bounds. [dx_rt@f997363c97 v3.5.0: docs/source/docs/02_Installation_on_Linux.md#L879], [dx-compiler@a087726ead v2.5.0: source/docs/02_01_System_Requirements_of_DX-COM.md#L12]
9. **dx_rt doc says** "DX-RT targets the x86_64 architecture" while other sections cover aarch64 equally. [dx_rt@f997363c97 v3.5.0: docs/source/docs/02_Installation_on_Linux.md#L105]

## Experimentally verified facts

- DX-COM 2.4.1 (PyPI `dx-com==2.4.1`) emits `.dxnn` **format v8** (`dxparse` on the board: "DX-COM v2.4.1-rc.1", 1 task `npu_0 [NPU]`, no CPU task). RT 3.4.2 loads and runs it. So the older-compiler/older-runtime pair works, and a board upgrade to RT 3.5.0 is not needed for 2.4.1 output. (`reports/ops.md`, section "Board check"; `models/A_fb_in1k/real_ptq13/compiler.log`)
- Documented (not tested here): DX-COM 2.5.0 emits only format v9, which needs RT >= 3.5.0. We compiled with 2.5.0 on the laptop (dw7 toy, A opset 13) but never pushed a v9 file to the board. (`reports/ops.md`)
- Release dates: the 2.5.0 change log says 2026-10-16, the PyPI upload and suite matrix row say 2026-10-23; unreconciled. (`reports/ops.md` session notes; GitHub issue #1)

## Hypotheses needing validation

- H1. DX-STREAM and DX-APP have no documented version-print command in files read. Settle: `gst-inspect-1.0 dxstream` (documented only for plugin registration [dx_stream@c575ed2896 v3.2.0: docs/source/docs/Appendix_Build_on_OrangePi5Plus.md#L342-L346]) and `release.ver`/`--help` of installed packages.
- H2. Whether `.dxnn` v8 files from DX-COM <= 2.4.x load on RT 3.5.0 is untested (v8 on RT 3.4.2 is verified); settle by loading an older `.dxnn` with `dxparse`/`dxrun` on RT 3.5.0.
- H3. Whether FW/driver newer than the matrix row (e.g. `latest` pointers in `dx_fw`, one-liner tracking `main`) is safe is unspecified; docs warn only that combos may be unvalidated. Pin versions (`DX_RT_VERSION`, `DX_DRIVER_VERSION`, `DX_FW_VERSION`).
- H4. Which of `dxcom -v` / `--version` works: run both on the installed DX-COM.
- H5. Whether the Python 3.13 ABI of the bundled `dx_engine` wheel (cp313) matches RT 3.5.0 exactly. Settle: `pip install` the staged cp313 wheel, then `import dx_engine`.
