# DEEPX DX-M1 installation (as documented) with system impact

Scope: install procedures exactly as the sources document them, with each step's system impact. NOTHING here has been run on our hosts. Do not execute any step without reading the impact column; several steps build and load kernel modules, add apt sources, or flash device firmware.

## Officially documented facts

### Requirements

- DX-RT (Linux): CPU amd64/aarch64; RAM 8 GB (16 GB recommended); 4 GB disk; Ubuntu 20.04/22.04/24.04/26.04 (x64, arm64), Debian 12/13 (x64, arm64); Driver >= v2.7.0; PCIe Driver >= v2.7.0; Firmware >= v2.7.6; a DX-M1/M1M/H1 Quattro in an M.2 or PCIe slot. [dx_rt@f997363c97 v3.5.0: docs/source/docs/02_Installation_on_Linux.md#L25-L42]
- Prebuilt `libdxrt-bin` needs glibc >= 2.27 and libstdc++ from GCC 10+, i.e. Ubuntu >= 20.04, Debian >= 12. [dx_rt@f997363c97 v3.5.0: docs/source/docs/02_Installation_on_Linux.md#L265-L273]
- Python for DX-RT: `dx_engine` supports Python >= 3.8.10; the `libdxrt-bin` package bundles wheels for Python 3.8-3.14 in `/usr/share/libdxrt-bin/python/`. [dx_rt@f997363c97 v3.5.0: docs/source/docs/02_Installation_on_Linux.md#L879], [dx_rt@f997363c97 v3.5.0: docs/source/docs/02_Installation_on_Linux.md#L308-L309]
- DX-COM (host): x86_64 only (aarch64 NOT supported); RAM >= 16 GB; disk >= 8 GB; Ubuntu 20.04-26.04, Fedora 42-45, RHEL 9-10, CentOS Stream 9-10; glibc >= 2.31; Python 3.8-3.14. [dx-compiler@a087726ead v2.5.0: source/docs/02_01_System_Requirements_of_DX-COM.md#L5-L12]
- Driver build prerequisites: `git build-essential linux-headers-$(uname -r) pciutils`; for Debian packages also `dkms dpkg-dev debhelper rsync`. [dx_rt_npu_linux_driver@8455be6254 v2.7.0: README.md#L34-L45]
- `dxrt-driver-dkms` depends on `dkms`, `build-essential`; recommends `linux-headers-generic | linux-headers-amd64 | linux-headers-arm64 | linux-headers-armmp | raspberrypi-kernel-headers`. [dx_rt_npu_linux_driver@8455be6254 v2.7.0: debian/control#L10-L11]
- The driver repository states no explicit supported-kernel list; see Applicability section for evidence.

### Route 1: APT repository (driver + runtime, amd64/arm64)

Commands exactly as documented. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L95-L111]
```
wget -O deepx-archive-keyring.asc https://apt.releases.deepx.ai/gpg
gpg --show-keys deepx-archive-keyring.asc
sudo gpg --dearmor -o /usr/share/keyrings/deepx-archive-keyring.gpg deepx-archive-keyring.asc
rm deepx-archive-keyring.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/deepx-archive-keyring.gpg] https://apt.releases.deepx.ai $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") main" | sudo tee /etc/apt/sources.list.d/deepx.list
sudo apt update
sudo apt install dxrt-driver-dkms
sudo apt install libdxrt-bin
```
- The key fingerprint must be exactly `3A20CC853C64AE328D0F58CFD816AAC6689DBDEA` before installing it; else stop. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L113-L122]
- Reboot after `dxrt-driver-dkms`; firmware is not in APT (use `./dx-runtime/install.sh --target=dx_fw`, then cold boot). [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L132-L136]
- `libdxrt-bin` does not install `dx_engine` into a venv; wheels are staged in `/usr/share/libdxrt-bin/python`. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L138-L143]
- Remove: `sudo apt purge libdxrt-bin dxrt-driver-dkms`. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L145-L147]

### Route 2: one-line installers

- `curl -fsSL https://raw.githubusercontent.com/DEEPX-AI/dx-compiler/main/oneline-install.sh | sh` (host) and `.../dx-runtime/main/oneline-install.sh | sh` (target). Overrides: `DX_VERSION`, `DX_RT_VERSION`, `DX_DRIVER_VERSION`, `DX_FW_VERSION`, `DX_INSTALL_DIR`. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L25-L39]
- Warnings: DX-Runtime tracks `main`, artifacts not checksum-verified, combination may be unvalidated; reboot mandatory; firmware step skipped if no NPU detected; one-liner covers only dx_fw, dx_rt, driver. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L41-L65]
- The compiler one-liner installs `dx-com` from PyPI into `$DX_INSTALL_DIR/venv-dx-compiler` (default `~/deepx`), links `dxcom` into `~/.local/bin`, and apt-installs `libgl1-mesa-dev` and `libglib2.0-0` (needs root/sudo, Debian/Ubuntu). [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L48-L55]
- Uninstall one-liners exist; flashed firmware is not reverted; `dx_engine` wheel is left in place. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L67-L87]

### Route 3: full-suite local install (git clone)

- Clone with submodules: `git clone --recurse-submodules https://github.com/DEEPX-AI/dx-all-suite.git`. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L156-L167]
- DX-COM: `sudo apt-get install -y --no-install-recommends libgl1-mesa-glx libglib2.0-0 make` then `./dx-compiler/install.sh`; verify with `dxcom --version`. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L260-L294]
- DX-COM direct: `pip install dx-com` (wheel tag `manylinux_2_31_x86_64`) or `uv pip install dx-com`. [dx-compiler@a087726ead v2.5.0: source/docs/02_02_Installation_of_DX-COM.md#L55-L61], [dx-compiler@a087726ead v2.5.0: source/docs/02_02_Installation_of_DX-COM.md#L95-L99]
- DX-Runtime: `./dx-runtime/install.sh --all` / `--all --exclude-fw` / `--target=<module>`; then firmware: `./dx-runtime/install.sh --target=dx_fw` or `dxcli -u ./dx-runtime/dx_fw/m1/X.X.X/mdot2/fw.bin`; cold boot recommended; then `sudo reboot`. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L316-L345]
- Verify: `dxcli -s` then `./dx-runtime/scripts/sanity_check.sh`. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L399-L416]

### Driver install variants (dx_rt_npu_linux_driver)

- Source build: `cd modules; ./build.sh; sudo ./build.sh -c install --reload`; `--reload` stops related services/processes, unloads and reloads modules - only when safe to interrupt apps. [dx_rt_npu_linux_driver@8455be6254 v2.7.0: README.md#L14-L30], [dx_rt_npu_linux_driver@8455be6254 v2.7.0: README.md#L143]
- Manual install places modules in `/lib/modules/$(KERNELRELEASE)/extra/`, plus `dx_dma.conf` (`softdep dx_dma post: dxrt_driver`) in `/etc/modprobe.d/`; then `sudo depmod -A; sudo modprobe dx_dma; sudo modprobe dxrt_driver`. [dx_rt_npu_linux_driver@8455be6254 v2.7.0: README.md#L214-L228], [dx_rt@f997363c97 v3.5.0: docs/source/docs/02_Installation_on_Linux.md#L796-L808]
- Cross compile (arm64): `make DEVICE=m1 PCIE=deepx ARCH=arm64 CROSS_COMPILE=<path>/aarch64-linux-gnu- KERNEL_DIR=<kernel-build-dir>`. [dx_rt_npu_linux_driver@8455be6254 v2.7.0: README.md#L162-L170]
- DKMS and manual installs conflict; remove one before the other (`sudo dpkg -r dxrt-driver-dkms`). [dx_rt_npu_linux_driver@8455be6254 v2.7.0: README.md#L207-L212]
- DKMS (`modules/build.sh -c install-package`, or APT) builds for the running kernel, installs to `/lib/modules/<ver>/updates/dkms/`, loads `virt_dma`/`dx_dma`/`dxrt_driver`, and rebuilds on kernel updates (`AUTOINSTALL=yes`). [dx_rt_npu_linux_driver@8455be6254 v2.7.0: README.md#L172-L197], [dx_rt_npu_linux_driver@8455be6254 v2.7.0: dkms.conf#L35-L36]

### udev / permissions / service

- `/dev/dxrt*` nodes get mode 0666 from the driver itself ("so device is accessible without udev"); sanity checks for 0666. [dx_rt_npu_linux_driver@8455be6254 v2.7.0: modules/rt/dxrt_drv_cdev.c#L497], [dx_rt@f997363c97 v3.5.0: docs/source/docs/02_Installation_on_Linux.md#L1059]
- An optional helper `modules/install-udev_rule.sh` writes `/etc/udev/rules.d/51-deepx-udev.rules` (`SUBSYSTEM=="dxrt", MODE="0666"`) and runs `udevadm control --reload-rules; udevadm trigger`. No script in the repo was found invoking it. [dx_rt_npu_linux_driver@8455be6254 v2.7.0: modules/install-udev_rule.sh#L5-L19]
- Service: copy `service/dxrt.service` to `/etc/systemd/system`, `sudo systemctl start dxrt.service` (enable/disable/status/journalctl commands documented). [dx_rt@f997363c97 v3.5.0: docs/source/docs/02_Installation_on_Linux.md#L975-L1001]

### Firmware update

- `dxcli -u <fw.bin>` flashes; `dxcli -g <fw.bin>` checks image version; stop `dxrt.service` before and start after (README uses legacy `dxrt-cli`). [dx_fw@a72406f3ca v2.7.6: README.md#L4-L15]
- After update: cold boot recommended (shutdown, unplug power); reboot acceptable for remote setups; verify with `dxcli -s`. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/05_FAQ_Troubleshooting_Guide.md#L149-L163]
- `install.sh` flashes M1, M1M and H1 firmware via `dxrt-cli` and hints to power off completely. [dx-runtime@73ff9904f5 v2.5.0: install.sh#L509-L545]
- Flashed firmware cannot be reverted by uninstall. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L82-L84]

### Docker route

- Install driver on host first (`./dx-runtime/install.sh --target=dx_rt_npu_linux_driver`); stop host `dxrt.service` (`sudo systemctl stop dxrt.service`) because `dxrtd` is a singleton. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L426-L440]
- `./docker_build.sh --all --ubuntu_version=24.04`; `./docker_run.sh --all --ubuntu_version=24.04`; verify in container with `dxcli -s`. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L444-L459], [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L565-L571]
- Optional `scripts/install_docker.sh` installs Docker and Compose. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L179-L184]

### System-impact table (what each step changes)

| Step | Impact | Basis |
|---|---|---|
| APT repo add | new `/etc/apt/sources.list.d/deepx.list`, new keyring in `/usr/share/keyrings` | [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L101-L105] |
| `apt install dxrt-driver-dkms` | pulls `dkms`, `build-essential`; DKMS compile against running kernel; installs `.ko` under `/lib/modules/<ver>/updates/dkms/`; writes `/etc/modprobe.d/dx_dma.conf`; runs `update-initramfs -u`; stops/restarts `dxrt` service if enabled; `rmmod`/`modprobe` of dx modules; fails if manual-install modules exist in `/lib/modules/<ver>/extra` | [dx_rt_npu_linux_driver@8455be6254 v2.7.0: debian/postinst#L24-L203] |
| kernel update later | DKMS auto rebuild; hook stops `dxrt`, rmmods modules, modprobes again | [dx_rt_npu_linux_driver@8455be6254 v2.7.0: dkms.conf#L10-L23] |
| `apt install libdxrt-bin` | libs/headers under `/usr/local`, CLI tools, `dxrt` service; wheels to `/usr/share/libdxrt-bin/python` | [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L124-L127] |
| `install.sh --all` | driver (DKMS or source build with `--reload`), may stop/disable then restart/enable `dxrt.service`, `apt-get install` of libdxrt-bin, installs Python/venv (may add PPA, `apt-get install` python packages), flashes FW | [dx-runtime@73ff9904f5 v2.5.0: install.sh#L82-L135], [dx-runtime@73ff9904f5 v2.5.0: install.sh#L306-L316], [dx-runtime@73ff9904f5 v2.5.0: scripts/install_python_and_venv.sh#L164-L234] |
| firmware flash | rewrites NPU firmware, irreversible by uninstall; needs cold boot | see above |
| reboot | mandatory after driver install | [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L344-L345] |
| `raspi-config` PCIe Gen3 (RPi only) | edits boot config, reboot | [dx-all-suite@51d81fe2ef v2.5.0: dx-edge/docs/source/04_Getting_Started_Guide_for_AWS_IoT_Greengrass_DX-M1-RPi5-DevKit.md#L131-L138] |
| `pip install dx-com` / venvs | user-space only; DX-COM needs apt libs `libgl1`, `libglib2.0-0`, `make` | [dx-compiler@a087726ead v2.5.0: source/docs/02_02_Installation_of_DX-COM.md#L22-L25] |

Documented contradictions: OpenGL package is `libgl1-mesa-glx` (suite guide), `libgl1` (dx-compiler docs), `libgl1-mesa-dev` (suite note on one-line installer). [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L260-L266], [dx-compiler@a087726ead v2.5.0: source/docs/02_02_Installation_of_DX-COM.md#L13-L24], [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L52-L53]

### Non-x86 / ARM64 guidance in the sources

- DX-Runtime target supports aarch64; DX-RT builds natively or cross-compiles with `--arch aarch64`; "Python for cross-compile is not supported in the current version". [dx-all-suite@51d81fe2ef v2.5.0: docs/source/01_DX-AllSuite_Architecture_Overview.md#L58-L62], [dx_rt@f997363c97 v3.5.0: docs/source/docs/02_Installation_on_Linux.md#L405-L458], [dx_rt@f997363c97 v3.5.0: docs/source/docs/02_Installation_on_Linux.md#L481-L482]
- Documented ARM64 hosts: Raspberry Pi 5 (Raspberry Pi OS 64-bit, Debian 13) and Orange Pi 5 Plus (RK3588), driver via DKMS + DX-RT. [dx-all-suite@51d81fe2ef v2.5.0: dx-edge/docs/source/04_Getting_Started_Guide_for_AWS_IoT_Greengrass_DX-M1-RPi5-DevKit.md#L25-L29], [dx_stream@c575ed2896 v3.2.0: docs/source/docs/Appendix_Build_on_OrangePi5Plus.md#L1-L5]
- Other documented kernels with M1: DEEPX benchmark reports list 6.1.43-rockchip-rk3588 (OPi5+), 6.1.43-15-rk2312 (ROCK5B+), 6.17.0-35-generic (N97, Ubuntu 24.04.4), 6.8.0-138-generic (H1 Quattro), and RPi5 on kernels 6.12 and 6.18. [dx-all-suite@51d81fe2ef v2.5.0: dx-benchmark/results/DX-AIPlayer-N97_M1/20261022_152931/REPORT.md#L93-L95], [dx-all-suite@51d81fe2ef v2.5.0: dx-benchmark/docs/ANALYSIS_EN.md#L643-L645]

## Experimentally verified facts

None yet (no DX-M1 available on host as of 2026-11-05).

## Hypotheses needing validation

### Applicability to this project

Our dev host: x86_64 AMD Ryzen AI 9 HX 370, Ubuntu kernel 6.17.0-41-generic, Python 3.13.7 system (conda + uv available). DX-M1 possibly on a separate Grinn Genio 700 (ARM64) board over SSH, location unconfirmed.

- A1. **Python 3.13.7: within documented support.** DX-COM lists 3.8-3.14; `libdxrt-bin` bundles `dx_engine` wheels for 3.8-3.14; DX-RT v2.4.0 notes mention "Python 3.13-3.14 support". Evidence: [dx-compiler@a087726ead v2.5.0: source/docs/02_01_System_Requirements_of_DX-COM.md#L12], [dx_rt@f997363c97 v3.5.0: docs/source/docs/02_Installation_on_Linux.md#L308-L309], [developer.deepx.ai/tech-docs/, fetched 2026-11-05]. Classified hypothesis only because it has not been run; settle with `pip install dx-com` in a fresh venv (conda/uv) and `dxcom --version`. Prefer a venv over the system Python.
- A2. **Kernel 6.17.0-41-generic: not covered by any explicit support list; strong indirect evidence of OK.** The driver sources have `LINUX_VERSION_CODE` guards whose highest threshold is 6.4 [dx_rt_npu_linux_driver@8455be6254 v2.7.0: modules/pci_deepx/dx_cdev.c#L546], and no document states a maximum kernel. DEEPX's own benchmark report ran driver v2.7.0 / RT v3.5.0 / FW v2.7.6 on Ubuntu 24.04.4 kernel `6.17.0-35-generic` (N97 + M1). That is close but not identical to `-41`, and not AMD. [dx-all-suite@51d81fe2ef v2.5.0: dx-benchmark/results/DX-AIPlayer-N97_M1/20261022_152931/REPORT.md#L93-L114]. Settle: `dkms build` dry run needs `linux-headers-6.17.0-41-generic`; risk is a compile error against a newer kernel API. A DX-M1 is only relevant if physically in the dev host (not confirmed).
- A3. **Host OS release unknown.** Kernel 6.17 ships with Ubuntu 24.04 HWE and Ubuntu 25.10; documented OS list is 20.04/22.04/24.04/26.04 (25.10 absent). Settle: `cat /etc/os-release`.
- A4. **DX-COM on the dev host is the clearly supported part**: x86_64, RAM >= 16 GB, glibc >= 2.31. It requires no NPU and no kernel module; only apt libs (`libgl1`, `libglib2.0-0`, `make`) and a venv. Settle by checking `ldd --version` and installing into a venv.
- A5. **If the DX-M1 is on the Genio 700 (aarch64):** DX-Runtime supports aarch64 and Debian/Ubuntu (20.04+/12+), but no source mentions Genio 700 / MediaTek (grep over all clones found nothing). Unknown: the Genio kernel version (vendor BSP kernels are commonly older than 6.17 - assumption), availability of matching kernel headers for DKMS (otherwise source/cross-compile build with `KERNEL_DIR`), the PCIe root-complex behaviour (MSI, IOMMU: several ARM SoC-specific fixes exist, e.g. i.MX8, RZ/G3E, RK3588), and whether the OS is Ubuntu/Debian at all (Yocto is a documented variant for RPi5 on developer.deepx.ai but not for Genio). Compilation must still be done on x86_64 (DX-COM is x86-only), then `.dxnn` copied to the board. Settle: on the board run `uname -r; cat /etc/os-release; lspci -nn; ls /lib/modules/$(uname -r)/build`.
- A6. For a remote board, the documented SSH-friendly steps are: driver via APT/DKMS, `dxcli -s`, firmware update with reboot (cold boot recommended; reboot allowed for remote). No remote-install guide exists in the sources.
- A7. APT route modifies the host's apt sources and installs a DKMS module that rebuilds on every kernel update; prefer a throwaway VM/container or the target board rather than the dev laptop unless an NPU is physically attached.
