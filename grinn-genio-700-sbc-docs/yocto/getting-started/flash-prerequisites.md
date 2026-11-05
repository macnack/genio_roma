# Flash Prerequisites

This section provides step-by-step instructions for preparing your development host for flashing the image to the device. Follow the guide that matches your operating system.

**Note:** The instructions below assume a Debian-based Linux distribution and were verified on Ubuntu 24.04 LTS.

## Create udev Rules

To enable USB device access for your user account, create new udev rules, reload the udev rules, and trigger them.

```bash
echo -n 'SUBSYSTEM=="usb", ATTR{idVendor}=="0e8d", ATTR{idProduct}=="201c", MODE="0660", TAG+="uaccess"
SUBSYSTEM=="usb", ATTR{idVendor}=="0e8d", ATTR{idProduct}=="0003", MODE="0660", TAG+="uaccess"
SUBSYSTEM=="usb", ATTR{idVendor}=="0403", MODE="0660", TAG+="uaccess"
SUBSYSTEM=="gpio", MODE="0660", TAG+="uaccess"
' | sudo tee /etc/udev/rules.d/72-aiot.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

## Enable UART Access

Your user account must be in the `dialout` group to access UART devices.

Check your group memberships:

```bash
groups
```

If `dialout` is not listed, add your user to the group:

```bash
sudo usermod -a -G dialout $USER
```

**Note:** You must log out and log back in for the new group membership to take effect.

## Ensure System is Updated

```bash
sudo apt update
sudo apt upgrade -y
```

## Install fastboot

Fastboot is used by Genio tools to flash the image.

Install it using the following command:

```bash
sudo apt install android-tools-fastboot
```

## Install pipx

`pipx` is a tool for installing and running Python applications in isolated environments.

Install `pipx`:

```bash
sudo apt install pipx
```

Ensure `pipx` installation path is added to your shell's `PATH`:

```bash
pipx ensurepath
```

Open a new terminal or re-login for the PATH changes to take effect.

## Install genio-tools

Install the `genio-tools` package:

```bash
pipx install genio-tools
```

Verify the installation and development host setup by running:

```bash
genio-config
```

Expected output:

```text
fastboot: OK
udev rules: OK
Serial device write access: OK
```

If any checks fail, follow the tool guidance or consult the [MediaTek IoT Yocto (Linux)](https://mediatek.gitlab.io/aiot/doc/aiot-dev-guide/master/sw/yocto/get-started/env-setup/flash-env-linux.html) documentation.

To prepare your Windows host for flashing, follow the official MediaTek guide:

[MediaTek IoT Yocto (Windows) - Flash Environment Setup](https://mediatek.gitlab.io/aiot/doc/aiot-dev-guide/master/sw/yocto/get-started/env-setup/flash-env-windows.html)

The vendor documentation provides the full setup process, including driver installation, fastboot configuration, and environment preparation.

If you encounter issues during setup or flashing, refer to the official troubleshooting guide:

[MediaTek IoT Yocto - Troubleshooting](https://mediatek.gitlab.io/aiot/doc/aiot-dev-guide/master/sw/yocto/get-started/troubleshooting.html)
