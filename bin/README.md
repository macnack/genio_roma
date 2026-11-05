# Board tools (for agents)

Helpers for the Grinn GenioBoard-700 connected to this PC. Loaded by direnv from the repo root (`.envrc`), so `bin/` is on PATH and these variables are set:

- `BOARD_TTY`: `/dev/genio-board` (udev symlink to the FTDI UART, serial `BK014LEL`). Falls back to `/dev/ttyUSB0` if the symlink is missing.
- `BOARD_BAUD`: `921600`
- `BOARD_DOCS`: path to `grinn-genio-700-sbc-docs/`

Per-machine overrides go in `.envrc.local` (git-ignored).

## Scripts

| Script | Purpose | Needs sudo |
|---|---|---|
| `board-setup` | One-time host install: tio, adb, fastboot, pipx, genio-tools, udev rules, `dialout` group. Calls `board-symlink`. | yes |
| `board-symlink [serial]` | Writes `/etc/udev/rules.d/73-genio-board.rules` so `/dev/genio-board` always points to the adapter. | yes |
| `board-check` | Status: tools present, serial rw access, USB IDs 0403/0e8d, `adb devices`, `genio-config`. Read-only. | no |
| `board-console [tty]` | Opens a serial console with `tio` at `BOARD_BAUD`. Exit: `Ctrl-t q`. | no |
| `board-flash <image-dir>` | `cd` into an unpacked image directory and run `genio-flash`. | no (fastboot needs the udev rules) |

## Board access

- **Serial:** `board-console`. Board boots to a logged-in root-level bash on `ttyS0` (autologin as `ubuntu`).
- **ADB:** `adb shell` over the board's USB gadget (`18d1:0100`). `adb devices` lists it when connected. ADB is Android Debug Bridge, not Bluetooth.
- **Fastboot:** used by `genio-flash` and `genio-config` during flashing.

## Board state changed by us (not in stock image)

Applied on the board through adb, on the user's request:

1. `/etc/systemd/system/serial-getty@ttyS0.service.d/autologin.conf`: serial console autologins as `ubuntu`.
2. `/etc/sudoers.d/91-ubuntu-nopasswd`: `ubuntu` has passwordless sudo.
3. `ubuntu` account password removed (`passwd -S ubuntu` shows `NP`).

Undo:
```
adb shell 'rm /etc/systemd/system/serial-getty@ttyS0.service.d/autologin.conf /etc/sudoers.d/91-ubuntu-nopasswd; systemctl daemon-reload; passwd ubuntu'
```

Security: anyone with serial or adb access gets root. Only use on a bench/dev board.

## Gotchas

- Only one process can hold the serial port. If `tio` is open, do not `cat` or `stty` the same port from another shell; reopen `tio` instead.
- Console output can look frozen while the board is idle: press Enter. Check with `adb devices` and `adb shell uptime` before concluding the board hung.
- Serial autologin changes take effect on the next getty start or reboot.
- `board-symlink` needs an active sudo password; run it yourself with `! bin/board-symlink`.
