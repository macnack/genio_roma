# DEEPX DX-M1 troubleshooting catalogue

Scope: symptom -> cause -> fix, drawn from the DX-AllSuite FAQ (Q1-Q11), driver/DX-RT docs, firmware notes and kit guides. Fix commands modify the system (kernel modules, services, firmware): read `installation.md` impact notes first.

## Officially documented facts

### A. Device not detected / driver

| Symptom | Cause | Fix | Citation |
|---|---|---|---|
| `lspci -d 1ff4:` prints nothing | PCIe link not up / not enumerated; physical connection or BIOS setting | Check seating, slot, BIOS; on RPi5 enable PCIe Gen 3 in `raspi-config`, check M.2 HAT FPC cable, reboot | [dx_rt_npu_linux_driver@8455be6254 v2.7.0: README.md#L47-L53], [dx_rt@f997363c97 v3.5.0: docs/source/docs/02_Installation_on_Linux.md#L636-L637], [dx-all-suite@51d81fe2ef v2.5.0: dx-edge/docs/source/04_Getting_Started_Guide_for_AWS_IoT_Greengrass_DX-M1-RPi5-DevKit.md#L277] |
| `lspci` shows a bare ID, no DEEPX name | PCI ID DB old | `sudo update-pciids` (Ubuntu) | [dx_rt_npu_linux_driver@8455be6254 v2.7.0: README.md#L55-L59] |
| `dxcli -s` fails to detect hardware | Driver not loaded or PCIe handshake error | `lsmod \| grep dx`; `dmesg \| grep -i deepx` (or `dmesg \| grep -i dx_rt`) | [dx_stream@c575ed2896 v3.2.0: docs/source/docs/Appendix_Build_on_OrangePi5Plus.md#L190-L200], [dx_stream@c575ed2896 v3.2.0: docs/source/docs/Appendix_Build_on_OrangePi5Plus.md#L331-L336] |
| `dxrt-cli` / `dxcli` not found | Driver + DX-RT not installed | Install per installation guide; confirm `dxrt_driver` in `lsmod` | [dx-all-suite@51d81fe2ef v2.5.0: dx-edge/docs/source/04_Getting_Started_Guide_for_AWS_IoT_Greengrass_DX-M1-RPi5-DevKit.md#L278] |
| Need a full diagnostic for support | - | `sudo ./sanity_check.sh` in the driver repo; send `sanity/result/` files (`sanity_check_result_*.log`, `dmesg_*.log`, `pcie_*.log`, `dxrt_issue_bundle_*.tar.gz`) to DEEPX | [dx_rt_npu_linux_driver@8455be6254 v2.7.0: README.md#L230-L250] |
| Sanity output "Fail to initialize device" | Device unstable/not initialized | Cold boot: power off completely, wait 10-30 s, power on, re-check `dxrt-cli -s` | [dx-runtime@73ff9904f5 v2.5.0: install.sh#L195-L219] |
| "dx_dma module in use ... old modules still loaded" during package upgrade | Modules busy, cannot unload | New modules active only after reboot | [dx_rt_npu_linux_driver@8455be6254 v2.7.0: debian/postinst#L62-L71] |
| `apt install dxrt-driver-dkms` aborts with "Manual installation detected" | Manual modules in `/lib/modules/<ver>/extra` | `cd modules; sudo ./build.sh -c uninstall`, then DKMS install | [dx_rt_npu_linux_driver@8455be6254 v2.7.0: debian/postinst#L73-L104] |
| Installing from source fails while DKMS package present | DKMS and manual installs conflict | `sudo dpkg -r dxrt-driver-dkms` | [dx_rt_npu_linux_driver@8455be6254 v2.7.0: README.md#L207-L212] |
| `apt` note "Download is performed unsandboxed as root ... _apt ... Permission denied" | Local .deb install under `sudo` | Harmless; installation succeeded | [dx_rt@f997363c97 v3.5.0: docs/source/docs/02_Installation_on_Linux.md#L545-L557] |
| Shared library errors after `libdxrt-bin` install | ldconfig cache | `sudo ldconfig`; `ldconfig -p \| grep libdxrt` | [dx_rt@f997363c97 v3.5.0: docs/source/docs/02_Installation_on_Linux.md#L318-L324] |
| `malloc(): corrupted top size`, `free(): invalid pointer`, `double free or corruption (out)` | `dx_engine` built for a different Python version than the one in use | Rebuild/install `dx_engine` with the same interpreter (venv with matching Python, bundled cpXY wheel) | [dx_rt@f997363c97 v3.5.0: docs/source/docs/02_Installation_on_Linux.md#L933-L963] |
| `import dx_engine` raises `RuntimeError` | `libdxrt.so` major.minor differs from Python package | Install matching versions (bypass `DX_ENGINE_SKIP_VERSION_CHECK=1`) | [dx_rt@f997363c97 v3.5.0: RELEASE_NOTES.md#L34] |

### B. Version mismatches (FAQ Q3, Q4, Q5, Q11)

| Symptom | Cause | Fix | Citation |
|---|---|---|---|
| "The current firmware version is X. Please update your firmware to version Y or higher." (Q3) | DX-RT newer than FW on NPU | `./dx-runtime/install.sh --target=dx_fw` or `dxcli -u ./dx-runtime/dx_fw/m1/X.X.X/mdot2/fw.bin`; cold boot (or `sudo reboot` when remote); verify `dxcli -s` | [dx-all-suite@51d81fe2ef v2.5.0: docs/source/05_FAQ_Troubleshooting_Guide.md#L119-L165] |
| "The current device driver version is X. Please update ... Y or higher." (Q4) | Kernel driver below DX-RT minimum | On the HOST: `./dx-runtime/install.sh --target=dx_rt_npu_linux_driver`, `sudo reboot`, `dxcli -s`. Not fixable from inside a container | [dx-all-suite@51d81fe2ef v2.5.0: docs/source/05_FAQ_Troubleshooting_Guide.md#L169-L210] |
| "The model's compiler version(X) is not compatible with this RT library." (Q5) | DX-COM vs DX-RT mismatch | Recompile with a DX-COM compatible with RT (recommended) or change DX-RT (then re-verify driver/FW) | [dx-all-suite@51d81fe2ef v2.5.0: docs/source/05_FAQ_Troubleshooting_Guide.md#L214-L244] |
| `[dxrt-exception] Invalid operation exception {"The current device driver version is 2.6.0. Please update ... 2.7.0 or higher."...}` after rebuilding a Docker image (Q11) | Container DX-RT newer than host driver | Check `dxcli --status \| grep -A2 Version`, `git submodule status dx-runtime/dx_rt_npu_linux_driver`, run `./getting-started/runtime-0_install_dx-runtime.sh`, verify `dxcli --status \| grep "RT Driver version"` | [dx-all-suite@51d81fe2ef v2.5.0: docs/source/05_FAQ_Troubleshooting_Guide.md#L453-L491] |
| `.dxnn` v9 fails to load | DX-RT <= 3.4.2 | Use DX-RT >= 3.5.0 | [dx-compiler@a087726ead v2.5.0: source/docs/02_01_System_Requirements_of_DX-COM.md#L13] |
| DX-APP example stops with an error and hint | RT < 3.5.0 or model format < v7 | Upgrade RT/recompile | [dx_app@375de0344f v3.3.0: README.md#L287] |

### C. Docker (Q1, Q2, Q6, Q10)

| Symptom | Cause | Fix | Citation |
|---|---|---|---|
| Container `Restarting (255)`; logs "Other instance of dxrtd is running" (Q1) | `dxrtd` singleton already on host | `sudo systemctl stop dxrt.service` and rerun; or set container entrypoint to idle and start `dxrtd &` manually | [dx-all-suite@51d81fe2ef v2.5.0: docs/source/05_FAQ_Troubleshooting_Guide.md#L21-L64], [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L696-L720] |
| X11 warning / `error mounting /tmp/.docker.xauth` (Q2) | Wayland session | Set `WaylandEnable=false` in `/etc/gdm3/custom.conf`, restart GDM/reboot, `docker compose -f docker/docker-compose.yml down --remove-orphans`, rerun | [dx-all-suite@51d81fe2ef v2.5.0: docs/source/05_FAQ_Troubleshooting_Guide.md#L68-L115] |
| `[ResourceError]: Insufficient shared memory (shm)...` (Q6) | Docker default `/dev/shm` 64 MB, DX-COM uses shared memory | `docker run --shm-size=256m` (or `1g`), or `shm_size: '1gb'` for service `dx-compiler` | [dx-all-suite@51d81fe2ef v2.5.0: docs/source/05_FAQ_Troubleshooting_Guide.md#L248-L282] |
| `docker exec` fails "not a directory" on `dummy_xauthority` (Q10) | Bind-mounted host path recreated | `rmdir dummy_xauthority && touch dummy_xauthority`; restart container with `docker_run.sh` | [dx-all-suite@51d81fe2ef v2.5.0: docs/source/05_FAQ_Troubleshooting_Guide.md#L421-L449] |

### D. ModelZoo / compiler (Q7, Q8, Q9)

| Symptom | Cause | Fix | Citation |
|---|---|---|---|
| `dxmz: command not found`; `ImportError: dx_engine is required ...`; `ImportError: dx_com is not installed`; `TypeError: compile() got an unexpected keyword argument 'calibration'` (Q7) | `dxmz`, `dx_engine`, `dx_com` not in same env; old `dx_com` | Run `runtime-0_install_dx-runtime.sh`, `modelzoo-0_install_dx-modelzoo.sh`, `modelzoo-2_run_first_npu_model.sh` (installs `dx_com` at `COM_VERSION`); or `--skip-onnx --skip-compile` for NPU-only eval | [dx-all-suite@51d81fe2ef v2.5.0: docs/source/05_FAQ_Troubleshooting_Guide.md#L286-L337] |
| Model download times out (`SessionCreationError ... urlopen error`) (Q8) | Outbound TCP 443 to `sdk.deepx.ai` blocked, no proxy | Allow egress or `HTTPS_PROXY`/`HTTP_PROXY`; or place models manually in `getting-started/modelzoo/models/<model>/`; set `DXMZ_MODEL_URL` | [dx-all-suite@51d81fe2ef v2.5.0: docs/source/05_FAQ_Troubleshooting_Guide.md#L341-L385] |
| "To enable auto-download, set DXMZ_MODEL_URL" | `.env` missing | Create `dx-modelzoo/.env` | [dx-all-suite@51d81fe2ef v2.5.0: docs/source/05_FAQ_Troubleshooting_Guide.md#L360-L364] |
| `DatasetValidationError: Dataset not found: ILSVRC2012` (Q9) | ModelZoo does not download datasets | Place dataset under `getting-started/modelzoo/datasets/...` or symlink | [dx-all-suite@51d81fe2ef v2.5.0: docs/source/05_FAQ_Troubleshooting_Guide.md#L389-L417] |
| Compile/model pip failures with GPU | onnxruntime vs onnxruntime-gpu conflict | `--extra gpu` removes `onnxruntime`; do not combine gpu with all | [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L369-L370] |
| `unsatisfied condition: cuda>=12.8` | NVIDIA driver too old for CUDA 12.8.1 image (non-datacenter GPUs) | Driver R570+ or choose `--cuda_version` | [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L479-L481] |
| `cv2` import fails after installing `dx-com` | Missing OpenGL/glib apt libs | Install `libgl1`/`libglib2.0-0` (or `libgl1-mesa-dev` per one-liner) | [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L51-L54] |
| One-line install: firmware step skipped | No NPU detected at install time | Reboot, rerun same command | [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L57-L60] |

### E. Runtime behaviour documented in release notes

- `dxrun --max-throughput`: an NPU memory overflow terminates `dxrun`; reduce the upper bound with `--buffer-count <low>-<high>`; a critical runtime event gives no recommendation. [dx_rt@f997363c97 v3.5.0: docs/source/docs/05_Command_Line_Interface.md#L194-L197]
- Large multi-model graphs can hit DX-M1 device-memory limits (`MODEL_LOAD` failure; see "Device Memory" section in DX-APP docs). [dx_app@375de0344f v3.3.0: docs/source/docs/06a_DX-APP_Multi_Model_Graph.md#L160]
- FW v2.7.6 reports HW op-timeout as NPU hang (HW timeout 2 s, SW timeout 3 s) and adds recovery for PCIe EQ failure; driver v2.5.0 added automatic recovery for critical runtime errors. [dx_fw@a72406f3ca v2.7.6: RELEASE_NOTES.md#L2-L12], [dx_rt_npu_linux_driver@8455be6254 v2.7.0: RELEASE_NOTES.md#L25-L33]
- DX-RT v3.5.0 added `DXRT_ERR_DEVICE_REMOVED` (-10) / `DeviceRemovedException`. [dx_rt@f997363c97 v3.5.0: RELEASE_NOTES.md#L46]
- Check service state: `sudo systemctl status dxrt.service`, `sudo journalctl -u dxrt.service`. [dx_rt@f997363c97 v3.5.0: docs/source/docs/02_Installation_on_Linux.md#L993-L1001]
- GStreamer plugin not found: `rm -rf ~/.cache/gstreamer-1.0/` then `gst-inspect-1.0 dxstream`. [dx_stream@c575ed2896 v3.2.0: docs/source/docs/Appendix_Build_on_OrangePi5Plus.md#L338-L346]

## Experimentally verified facts

None yet (no DX-M1 available on host as of 2026-11-05).

## Hypotheses needing validation

- H1. Kernel 6.17 DKMS build failure is a plausible failure mode on our host (no documented symptom); expected evidence would be `dkms build` errors referencing kernel API changes. Settle with `dkms build` in a disposable VM with `linux-headers-6.17.0-41-generic`.
- H2. On Genio 700, "device not detected" may stem from PCIe root-complex quirks (MSI, IOMMU, link training). Similar issues were fixed for other SoCs (i.MX8, RZ/G3E, RPi4/5) but none is documented for Genio. Settle: `lspci -nn -d 1ff4:`, `dmesg | grep -iE "pcie|dx|iommu|aer"`, driver `sanity_check.sh`.
- H3. The FAQ gives no symptom/cause for thermal throttling slowdowns beyond firmware notes; the "Thermal Throttling Control Guide" (v1.0.0) on developer.deepx.ai was not read. Settle: read it and watch `dxcli -s` temperature/clock under load. [developer.deepx.ai/document-download/, fetched 2026-11-05]
- H4. The `libgl1-mesa-glx` package named in the suite guide may not exist on newer Ubuntu releases; the compiler docs use `libgl1`. Settle: `apt-cache policy libgl1-mesa-glx libgl1` on the host.
- H5. Whether warm `sudo reboot` is enough to apply new firmware on our board (docs conflict). Settle: flash, reboot, check `dxcli -s` FW version; if stale, cold boot.
- H6. No documented fix list for `/dev/dxrt0` permission errors beyond 0666 default and the optional udev helper; if a hardened kernel/udev setup overrides modes, apply the helper rule. Settle: `ls -l /dev/dxrt*`.
