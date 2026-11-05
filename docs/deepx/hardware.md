# DEEPX DX-M1 hardware

Scope: DX-M1 specs as documented in the cloned repos and developer.deepx.ai, form factors, detection (lspci IDs, /dev nodes, CLI). The official datasheets (DX-M1 M.2 Datasheet v1.6.0 etc.) were only listed, not readable, so numeric specs below come from secondary kit/board guides inside the repos.

## Officially documented facts

### Product family and PCI IDs

- Driver-supported products and PCI device IDs (vendor `1ff4`): `0x0000` DX_M1 "Legacy"; `0x0100` M1 [Series] (DX-M1, DX-M1 M.2 module); `0x0110` M1M [Series] (DX-M1M, DX-M1M M.2); `0x0101` M1 [H1] (DX-H1 Quattro). [dx_rt_npu_linux_driver@8455be6254 v2.7.0: README.md#L61-L70]
- The driver sanity script accepts device IDs `0000 0100 0110 0101 0111` for vendor `1ff4`. [dx_rt_npu_linux_driver@8455be6254 v2.7.0: sanity/sanity.sh#L23-L25]
- Source defines `DX_M1`=0x0100, `DX_M1M`=0x0110, `DX_H1`=0x0101, `DX_H1M`=0x0111 PCI device IDs. [dx_rt_npu_linux_driver@8455be6254 v2.7.0: modules/pci_deepx/dw-edma-pcie.c#L50-L53]
- DX-RT requires a DX-M1, DX-M1M or DX-H1 Quattro attached via an M.2 slot or a PCIe slot. [dx_rt@f997363c97 v3.5.0: docs/source/docs/02_Installation_on_Linux.md#L35-L42]
- Firmware v2.7.2 "Revert M1/M1M IC and M.2 module and DX-H1 Quattro board products PCIe device id to `0x0000`". [dx_fw@a72406f3ca v2.7.6: RELEASE_NOTES.md#L42-L45]
- Firmware ships separate `m1` and `m1m` trees; `m1/<ver>/` has `mdot2` (M.2) and `h1`; `m1m/<ver>/` has only `mdot2`. [dx_fw@a72406f3ca v2.7.6: README.md#L4-L15] (directory layout read from the clone: `m1/2.7.6/{h1,mdot2}`, `m1m/2.7.6/mdot2`)
- Firmware release set: M1, M1M and H1 are released together as one firmware set. [dx-runtime@73ff9904f5 v2.5.0: README.md#L91-L94]

### Specs (from DEEPX kit guides in the suite)

- DX-M1 Edge AI Dev Kit (Raspberry Pi 5): "DX-M1 (M.2 2280 M-Key), 25 TOPS INT8, 4 GB LPDDR5 (5600 MT/s), 1-5 W"; accelerator interface PCIe Gen 3 via M.2 HAT; "DX-M1 supports Gen 1/2/3, x1/x2/x4". [dx-all-suite@51d81fe2ef v2.5.0: dx-edge/docs/source/04_Getting_Started_Guide_for_AWS_IoT_Greengrass_DX-M1-RPi5-DevKit.md#L58-L62]
- DX-AIPlayer N97: DX-M1 M.2 2280 module, 25 TOPS INT8, 4 GB LPDDR5, max 5 W. [dx-all-suite@51d81fe2ef v2.5.0: dx-edge/docs/source/03_Getting_Started_Guide_for_AWS_IoT_Greengrass_DX-AIPlayer-N97.md#L57]
- Orange Pi 5 Plus guide: M.2 form factor DX-M1, "DEEPX DX-M1 (25 TOPS)". [dx_stream@c575ed2896 v3.2.0: docs/source/docs/Appendix_Build_on_OrangePi5Plus.md#L22], [dx_stream@c575ed2896 v3.2.0: docs/source/docs/Appendix_Build_on_OrangePi5Plus.md#L313]
- NPU cores: `dxrun -n` offers NPU_0, NPU_1, NPU_2 (three NPU cores), consistent with `dxcli -s` printing NPU 0-2. [dx_rt@f997363c97 v3.5.0: docs/source/docs/05_Command_Line_Interface.md#L78-L85], [dx_stream@c575ed2896 v3.2.0: docs/source/docs/Appendix_Build_on_OrangePi5Plus.md#L186-L188]
- Thermal: firmware has thermal throttling; `dxrun --max-throughput` waits for NPU temperature below `--cool-down-temp` (default 45 'C) before each measurement to avoid throttling skew. [dx_rt@f997363c97 v3.5.0: docs/source/docs/05_Command_Line_Interface.md#L126-L129], [dx_rt@f997363c97 v3.5.0: docs/source/docs/05_Command_Line_Interface.md#L179]
- Observed (DEEPX benchmark report, DX-AIPlayer-N97 + M1): "NPU Memory LPDDR5 5600 Mbps, 3.92GiB"; "Board M.2, Rev 1.0"; "PCIe Gen3 X2". [dx-all-suite@51d81fe2ef v2.5.0: dx-benchmark/results/DX-AIPlayer-N97_M1/20261022_152931/REPORT.md#L108-L114]
- Orange Pi 5 Plus sample output: "LPDDR5 6000 MHz, 3.92GiB", "Board: M.2, Rev 1.5", "PCIe: Gen3 X4". [dx_stream@c575ed2896 v3.2.0: docs/source/docs/Appendix_Build_on_OrangePi5Plus.md#L180-L183]
- Official hardware documents exist on developer.deepx.ai (not fetched in full): DX-M1 M.2 Datasheet v1.6.0, DX-M1M (2G) M.2 Datasheet v1.5.0, DX-M1 M.2 HW Application Note v1.0.0, DX-M1 NPU Thermal Throttling Control Guide v1.0.0, DX-M1 Multi-MSI BIOS Guide v1.0.0, DX-M1 & DX-M1M M.2 Thermal Implementation Guide v1.0.0, Boot Firmware Programming & Recovery User Guide v1.1.0. [developer.deepx.ai/document-download/, fetched 2026-11-05]
- The developer site's front page and tech-docs page contain no DX-M1 specs. [developer.deepx.ai/, fetched 2026-11-05], [developer.deepx.ai/tech-docs/, fetched 2026-11-05]

### Detection (documented commands only)

- PCIe enumeration: `lspci -d 1ff4:` (no output means link not up/enumerated). [dx_rt_npu_linux_driver@8455be6254 v2.7.0: README.md#L47-L53]
- DX-RT doc: `lspci -vn | grep 1ff4` -> example `0b:00.0 1200: 1ff4:0000`; if empty, check physical connection and BIOS settings. [dx_rt@f997363c97 v3.5.0: docs/source/docs/02_Installation_on_Linux.md#L631-L637]
- Names in `lspci` require `sudo update-pciids`; examples: `DEEPX Co., Ltd. DX_M1`, `M1 [Series]`, `M1M [Series]`, `M1 [H1]`. [dx_rt_npu_linux_driver@8455be6254 v2.7.0: README.md#L55-L79]
- Raspberry Pi 5 example: `0001:01:00.0 Processing accelerators: DEEPX Co., Ltd. DX_M1 (rev 01)`; PCIe Gen 3 must be enabled via `raspi-config`. [dx-all-suite@51d81fe2ef v2.5.0: dx-edge/docs/source/04_Getting_Started_Guide_for_AWS_IoT_Greengrass_DX-M1-RPi5-DevKit.md#L131-L142]
- Device nodes: `/dev/dxrt*` (char devices; sanity expects mode 0666); kernel module checks `lsmod | grep dx` / `dxrt_driver`, `dx_dma`; PCIe driver in use: `dx_dma_pcie`. [dx_rt_npu_linux_driver@8455be6254 v2.7.0: README.md#L238-L244], [dx_rt@f997363c97 v3.5.0: docs/source/docs/02_Installation_on_Linux.md#L1054-L1063], [dx_rt_npu_linux_driver@8455be6254 v2.7.0: sanity/sanity.sh#L150]
- Driver sets 0666 on device nodes by default "so device is accessible without udev". [dx_rt_npu_linux_driver@8455be6254 v2.7.0: modules/rt/dxrt_drv_cdev.c#L497], [dx_rt_npu_linux_driver@8455be6254 v2.7.0: modules/rt/dxrt_drv_cdev.c#L540]
- `dxcli -s` / `dxcli --status`: success = `Device 0: M1`, valid RT Driver / PCIe Driver / FW versions, live voltage/clock/temperature. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L399-L409]
- Sample `dxcli -s` output (fields: Device N: M1, RT Driver version, PCIe Driver version, FW version, Memory, Board, Chip Offset, PCIe, per-NPU voltage/clock/temperature). [dx_stream@c575ed2896 v3.2.0: docs/source/docs/Appendix_Build_on_OrangePi5Plus.md#L168-L188]
- Diagnostics when undetected: `lsmod | grep dx`, `dmesg | grep -i deepx`; also `lspci | grep -i deepx`, `dmesg | grep -i dx_rt`. [dx_stream@c575ed2896 v3.2.0: docs/source/docs/Appendix_Build_on_OrangePi5Plus.md#L196-L200], [dx_stream@c575ed2896 v3.2.0: docs/source/docs/Appendix_Build_on_OrangePi5Plus.md#L331-L336]
- `sudo ./sanity_check.sh` in the driver repo checks PCIe link-up (vendor 1ff4), `/dev/dxrt*`, modules, install state, ioctl; results in `sanity/result/`. [dx_rt_npu_linux_driver@8455be6254 v2.7.0: README.md#L230-L250]
- `dxtop` is a DX-RT monitor tool (DDR type shown in its device-variant string since v3.5.0). [dx_rt@f997363c97 v3.5.0: RELEASE_NOTES.md#L7]

### Hardware-related caveats from release notes

- Driver v2.3.0 fixed 64-bit PCIe TLP incompatibility on Raspberry Pi 4 (BCM2711) with 32-bit-only MMIO; v2.4.0 fixed DMA cache coherency on ARM64 IOMMU; v1.8.0 added safe link-up on Raspberry Pi 5; v1.3.3 fixed a DMA error on NXP i.MX8 (kernel v6.6.23). [dx_rt_npu_linux_driver@8455be6254 v2.7.0: RELEASE_NOTES.md#L55-L61], [dx_rt_npu_linux_driver@8455be6254 v2.7.0: RELEASE_NOTES.md#L67-L72], [dx_rt_npu_linux_driver@8455be6254 v2.7.0: RELEASE_NOTES.md#L117], [dx_rt_npu_linux_driver@8455be6254 v2.7.0: RELEASE_NOTES.md#L184-L188]
- FW v2.7.3 "Solving PCIe enumeration issue on RZ/G3E". [dx_fw@a72406f3ca v2.7.6: RELEASE_NOTES.md#L33-L40]
- Firmware v2.7.0/2.7.1 changes relate to PCIe link EQ timeouts and Preset 10 disabling (link training behavior). [dx_fw@a72406f3ca v2.7.6: RELEASE_NOTES.md#L52-L70]

## Experimentally verified facts

None yet (no DX-M1 available on host as of 2026-11-05).

## Hypotheses needing validation

- H1. **Contradiction on PCI device ID**: driver README lists `0x0100` for M1 and `0x0110` for M1M, whereas FW v2.7.2 reverts IDs to `0x0000` and DX-RT docs/RPi5 guide show `1ff4:0000` / "DX_M1". Probably the ID reported depends on the flashed FW version. Settle: `lspci -nn -d 1ff4:` on the real device before and after FW update.
- H2. Lane/speed capability on our board is unknown: the dev-kit text says Gen1/2/3 x1/x2/x4 supported, but boards observed in DEEPX data show x2 (N97) and x4 (OPi5+). The Genio 700 M.2/PCIe slot lane count and gen are not in any source. Settle: `sudo lspci -vv -d 1ff4:` (LnkCap/LnkSta) on the board.
- H3. DDR size: all secondary sources say 4 GB LPDDR5 (3.92 GiB usable). The datasheet numbers (M1 vs M1M DDR options, "M1M (2G)") were not readable. Settle: `dxcli -s` Memory line, and read the datasheet PDFs.
- H4. Power/thermal envelope "1-5 W" is quoted only from kit guides; M.2 power rail requirements and thermal limits are in datasheets/Thermal guides we did not read. Settle: download those PDFs and cross-check; measure with `dxcli -s` temperature under load.
- H5. Which M.2 key (M-Key per the RPi5 kit text) our Genio 700 carrier exposes is unconfirmed. Settle: board schematic/EVK docs.
- H6. Whether the board is detected at all behind the Genio 700 root complex (MSI/IOMMU behaviour; cf. the "Multi-MSI BIOS Guide" and ARM64 IOMMU fixes) is unknown. Settle: run `dxrt` driver sanity (`sudo ./sanity_check.sh`) on the board.
