# Grinn GenioBoard-700: full hardware and software specs

> Compact of docs/deepx/board_specs.md. Measured 2026-11-05 (read-only `adb shell`, `dxrt-cli`); commands in brackets. See [board_discovery.md](board_discovery.md), [board_summary.md](board_summary.md), [hardware.md](hardware.md).

## Officially documented facts

- DX-M1 (M.2 2280 M-Key): 25 TOPS INT8, 4 GB LPDDR5 (5600 MT/s), 1-5 W. [dx-all-suite@51d81fe2ef v2.5.0: dx-edge/docs/source/04_Getting_Started_Guide_for_AWS_IoT_Greengrass_DX-M1-RPi5-DevKit.md#L58-L62]
- DX-M1 supports PCIe Gen 1/2/3, x1/x2/x4. [dx-all-suite@51d81fe2ef v2.5.0: dx-edge/docs/source/04_Getting_Started_Guide_for_AWS_IoT_Greengrass_DX-M1-RPi5-DevKit.md#L58-L62]
- DX-RT requires a DX-M1, DX-M1M or DX-H1 Quattro attached via an M.2 slot or a PCIe slot. [dx_rt@f997363c97 v3.5.0: docs/source/docs/02_Installation_on_Linux.md#L35-L42]

## Experimentally verified facts

### SoC and CPU

- Device tree model: `Grinn GenioSBC-700`. Compatible: `grinn,genio-700-sbc`, `mediatek,mt8390`, `mediatek,mt8188`. [`cat /proc/device-tree/model`, `/proc/device-tree/compatible`]
- 8 CPU cores, aarch64, 1 thread per core, 1 NUMA node. [`lscpu`]
  - 6 × Cortex-A55 (implementer 0x41, part 0xd05, r2p0), 500–2000 MHz. [`lscpu`, `/proc/cpuinfo`]
  - 2 × Cortex-A78 (part 0xd41, r1p0), 650–2200 MHz. [`lscpu`]
- Caches: L1d 320 KiB (8 instances), L1i 320 KiB (8), L2 384 KiB (2 instances), L3 2 MiB (1). [`lscpu`]

### Memory

- RAM: 3.7 GiB total (MemTotal 3873052 kB). MemAvailable 2924688 kB at idle. [`free -h`, `/proc/meminfo`]
- Swap: none (SwapTotal 0 kB). [`/proc/meminfo`]
- CMA: 32 MB total, 31 MB free. HugePages_Total 0. [`/proc/meminfo`]

### Storage

- Main storage: eMMC `mmcblk0`, 14.6 GB. Name `MW2816`, 03/2025, manfid `0x000070`. [`lsblk`, `/sys/block/mmcblk0/device/*`]
- Partition table: p1 4 MB, p2 4 MB, p3 32 MB vfat, p4 32 MB vfat, p5 512 KB, p6 1 MB, p7 32 MB vfat, p8 500 MB vfat (`/boot/efi`), p9 14 GB ext4 (`/`). [`lsblk`]
- Root filesystem: ext4, 14 GB, 9.5 GB used, 3.6 GB free (73%). [`df -hT /`]

### Graphics, I/O and network

- GPU: Mali via `libmali-mtk` 48p0 (`/dev/dri/card0`, `renderD128`). GPU model not confirmed. [`ls /dev/dri`, `dpkg -l`]
- USB: 2 × USB 3.0 root hubs and 1 × USB 2.0 root hub. Others: TI 0451:8027, 0451:8025, Microchip 0424:2513. [`lsusb`]
- Ethernet: `end0`, MAC 8c:1f:64:15:60:b1, DOWN (no carrier). No Wi-Fi or Bluetooth interface seen. [`ip -br link`]

### NPU (DEEPX DX-M1, M.2 Rev 1.0)

- 3 NPU cores (NPU 0–2), 750 mV, 1000 MHz at idle, 33–34 °C at idle. [`dxrt-cli -s`]
- Memory: LPDDR5 5600 Mbps, 3.92 GiB. [`dxrt-cli -s`]
- PCIe: Gen2 x1, bus address `01:00:00`. Device nodes `/dev/dxrt0`, `dx_dma`, `dxrt` present. Modules `dxrt_driver`, `dx_dma` loaded. [`dxrt-cli -s`, `ls /dev`, `lsmod`]

### OS and software versions

- OS: Ubuntu 24.04.5 LTS (Noble). [`/etc/os-release`]
- Kernel: `6.8.0-9003-mtk`, Grinn build `6.8.0-9003.1+grinn`, built 2026-09-29, GCC 13.3. [`uname -a`, `/proc/version`]
- Bootloader: u-boot-tools 2025.10; `/boot/grub` present, `/boot/efi` mounted. [`dpkg -l`, `ls /boot`, `lsblk`]
- Python: 3.12.3 (system). `dx_engine` not installed. [`dpkg -l`]
- NPU stack: DX-RT 3.4.2+d803450 (`libdxrt-bin` 3.4.2), RT driver 2.6.0 (`dxrt-driver-dkms` 2.6.0-2), PCIe driver 2.5.0, firmware 2.7.4. [`dxrt-cli -s`, `dpkg -l`]
- Runtime minimums enforced by this DX-RT: driver ≥ 2.5.0, PCIe driver ≥ 2.4.0, firmware ≥ 2.7.0, compiler ≥ 1.18.1, `.dxnn` format ≥ v6. [`dxrt-cli -v`]
- GPU driver: `libmali-mtk` 48p0+git20250724. ADB daemon `adbd` 34.0.5-12~grinn5. DKMS 3.0.11. [`dpkg -l`]

## Hypotheses needing validation

- PCIe lane count and generation on the Genio 700 M.2/PCIe slot: the board reports Gen2 x1, but the dev-kit sources describe Gen3 with x2/x4 lanes. Settle with `sudo lspci -vv -d 1ff4:` on the board (LnkCap vs LnkSta). Related to [hardware.md](hardware.md) H2.
- DX-M1 memory variant: the board reports 3.92 GiB, which fits the 4 GB LPDDR5 described in the dev-kit sources. M1 vs M1M datasheet option unreadable. Related to [hardware.md](hardware.md) H3.
- GPU model: the Mali GPU's exact model is not in any source checked here. Settle with the `libmali-mtk` package contents or the SoC datasheet.
- eMMC manufacturer: the manfid `0x000070` is not decoded here. Settle with the eMMC datasheet or the vendor table.
- The A78 and A55 clock ranges are from `lscpu` and not checked against the SoC datasheet.
