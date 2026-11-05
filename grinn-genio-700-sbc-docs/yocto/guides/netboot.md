# Network Boot

During kernel development, it’s often more efficient to avoid reflashing the board every time a new kernel image is built. Instead, the kernel can be loaded directly over the network, greatly speeding up the test cycle.

Using a remote (NFS-mounted) root filesystem is also extremely helpful during board bring-up and debugging. It allows developers to make changes to the system files directly on the host machine without needing to reflash the target device, providing a faster and more flexible development workflow.

**Note:** Network boot can only be used during development of the Linux kernel and/or user-space applications. Prior boot stages (e.g. U-Boot) still require flashing the board.

## Set Up the Host

**Note:** The instructions below assume a Debian-based Linux distribution and were verified on Ubuntu 24.04 LTS.

Run the following commands to install the necessary packages:

```bash
sudo apt update
sudo apt install tftpd-hpa nfs-kernel-server
```

Run the following command to set up the TFTP server:

```bash
sudo tee /etc/default/tftpd-hpa > /dev/null <<'EOF'
TFTP_USERNAME="tftp"
TFTP_DIRECTORY="/srv/tftp"
TFTP_ADDRESS=":69"
TFTP_OPTIONS="--secure"
EOF
```

Run the following command to set up the NFS server:

```bash
sudo tee /etc/exports > /dev/null <<'EOF'
/srv/nfs *(rw,fsid=0,crossmnt,insecure,no_subtree_check,sync,no_root_squash)
EOF
```

Finally, start the TFTP and NFS servers:

```bash
sudo systemctl enable --now tftpd-hpa
sudo systemctl enable --now nfs-kernel-server
```

## Set Up the Board

Follow the instructions in the [Serial Connection](https://developer.grinn-global.com/boards/grinn-genio-700-sbc/software/yocto/getting-started/access-the-device#serial-connection) section to connect to the board’s serial console.

Ensure that the board is connected to the same network as the host machine. The simplest way to achieve this is to connect both the host and the board to the same router using Ethernet.

## Build the Image

Enter the folder containing the image configuration files:

```bash
cd genio/meta-grinn-genio/kas
```

Run the following command to build the image with the network boot extension:

```bash
KAS_MACHINE=grinn-genio-700-sbc KAS_CONTAINER_IMAGE_DISTRO=debian-bookworm KAS_WORK_DIR=../.. \
kas-container \
--runtime-args " \
-e NETBOOT_SERVER_IP=$(ip -4 route get 1.1.1.1 | awk '{print $7}') \
-e NETBOOT_SERVER_SUBDIR=$(whoami) \
" \
build default.yml:netboot.yml
```

This command automatically passes the host machine’s IP address and your desired subdirectory name to the netboot build configuration. As a result, U-Boot is configured to look for the boot files at that IP address and inside a subdirectory named after the current user during network boot.

To include additional image extensions, refer to the [Build the Image](https://developer.grinn-global.com/boards/grinn-genio-700-sbc/software/yocto/getting-started/build-the-image#build-the-image) section.

**Warning:** The build command above uses an automated method of determining the host machine’s IP address, which may not always yield the correct result.If the detected address is incorrect, determine the IP address manually using:ip aThen replace the environment variable in the build command with the correct IP address:-e NETBOOT_SERVER_IP=<your-ip-address>

## Synchronize the Image

To copy the generated boot artifacts and root filesystem into the TFTP and NFS directories, run the following command:

```bash
../../meta-grinn-common-netboot/scripts/sync \
--netboot-dir=../../build/tmp/deploy/images/grinn-genio-700-sbc/netboot \
--subdir=$(whoami) \
--tftp-path=/srv/tftp \
--nfs-path=/srv/nfs
```

This script creates the required directory structure if it does not already exist. It then copies the boot artifacts to the TFTP directory (`/srv/tftp/<subdir>/`) and extracts the root filesystem into the NFS directory (`/srv/nfs/<subdir>/`).

**Tip:** To display a help message for the synchronization script, run the following command:../../meta-grinn-common-netboot/scripts/sync --help

## Flash the Image

Before using network boot, the board must be flashed at least once to set up the bootloader. Follow the instructions in the [Flash the Image](https://developer.grinn-global.com/boards/grinn-genio-700-sbc/software/yocto/getting-started/flash-the-image) section to flash the board.

## Use Network Boot

After the board has been flashed once with a netboot-enabled image, it will attempt to boot over the network after each reset.

Each time you modify the source code, repeat the Build the Image and Synchronize the Image steps, then reboot the board to test the changes.

**Note:** To disable network boot, interrupt the boot process to access the U-Boot console, then run the following command:setenv netboot 0; saveenv; reset
