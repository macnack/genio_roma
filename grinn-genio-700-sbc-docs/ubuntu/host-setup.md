# Host Setup (Ubuntu / Debian-based Linux)

Prepare your development PC once before flashing. Run the steps in order.
Verified on Ubuntu 24.04 LTS.

## 1. Update the system

```bash
sudo apt update
sudo apt upgrade -y
```

## 2. Install fastboot and pipx

```bash
sudo apt install -y android-tools-fastboot pipx
pipx ensurepath
```

Then open a new terminal (or log out and back in) so the PATH change applies.

## 3. Install genio-tools

```bash
pipx install genio-tools
```

## 4. Add USB/UART permissions

Create the udev rules:

```bash
echo -n 'SUBSYSTEM=="usb", ATTR{idVendor}=="0e8d", ATTR{idProduct}=="201c", MODE="0660", TAG+="uaccess"
SUBSYSTEM=="usb", ATTR{idVendor}=="0e8d", ATTR{idProduct}=="0003", MODE="0660", TAG+="uaccess"
SUBSYSTEM=="usb", ATTR{idVendor}=="0403", MODE="0660", TAG+="uaccess"
SUBSYSTEM=="gpio", MODE="0660", TAG+="uaccess"
' | sudo tee /etc/udev/rules.d/72-aiot.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Add your user to the `dialout` group (skip if `groups` already lists it):

```bash
groups
sudo usermod -a -G dialout $USER
```

**Note:** Log out and back in for the group change to take effect.

## 5. Verify

```bash
genio-config
```

Expected output:

```text
fastboot: OK
udev rules: OK
Serial device write access: OK
```

If a check fails, see the MediaTek troubleshooting guide:
https://mediatek.gitlab.io/aiot/doc/aiot-dev-guide/master/sw/yocto/get-started/troubleshooting.html

Next step: [Flash the Image](flash-the-image.md).
