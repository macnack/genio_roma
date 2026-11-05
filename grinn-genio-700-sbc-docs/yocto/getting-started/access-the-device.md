# Access the Device

Choose the access method that best fits your workflow after the board is flashed and booted.

**Info:** The default user is root, with an empty password.

## Graphical Environment

This is the recommended access method for users with limited embedded Linux experience, as it provides a more familiar way to interact with the board.

The image includes a graphical environment. To access it, connect a monitor to the device and power it on. Once the system finishes booting, the graphical session should start automatically. You can then connect a keyboard and mouse to interact with the system directly.

## Android Debug Bridge (ADB)

Android Debug Bridge (ADB) is a command-line tool that lets you communicate with the development board from your host computer. For most users, it is the recommended way to access the board in headless mode.

**Note:** ADB is available only after the board starts successfully and the ADB daemon is running. Because of this, it can only be used to interact with a running Linux system. For example, it cannot be used to interact with U-Boot.

**Important:** Make sure that the board is connected as described in the Connect the Board section.

To use ADB, follow the instructions below:

**Note:** The instructions below assume a Debian-based Linux distribution and were verified on Ubuntu 24.04 LTS.

To install ADB, run the following command:

```bash
sudo apt update
sudo apt install android-tools-adb
```

To access the board using ADB, run the following command in the terminal:

```bash
adb shell
```

After running the command, you should see a shell prompt from the board.

ADB can also be used to copy files to and from the board. To copy the file from the host to the board, run the following command:

```bash
adb push <host-path> <board-path>
```

To copy the file from the board to the host, run the following command:

```bash
adb pull <board-path> <host-path>
```

To set up ADB on Windows, follow the instructions below:

1. Download the latest Platform Tools package from the
 official URL .
2. Extract the downloaded ZIP file to a location of your choice.
3. Open a terminal in the extracted directory.

To access the board using ADB, run the following command in the terminal:

```bash
./adb shell
```

After running the command, you should see a shell prompt from the board.

ADB can also be used to copy files to and from the board. To copy the file from the host to the board, run the following command:

```bash
./adb push <host-path> <board-path>
```

To copy the file from the board to the host, run the following command:

```bash
./adb pull <board-path> <host-path>
```

## Serial Connection

The serial connection is a method of communication between the host computer and the development board using a serial interface. It allows you to monitor the output and interact with the board during the boot process and after the Linux system has started. This method is particularly useful when modifying the bootloader or the Linux kernel, as it provides access to the board even if the system is not fully operational.

**Important:** Make sure that the board is connected as described in the Connect the Board section.

**Note:** The instructions below assume a Debian-based Linux distribution and were verified on Ubuntu 24.04 LTS.

The recommended way to access the serial console on Linux is to use the `tio` utility. Any other terminal emulator that supports serial communication can also be used.

To install `tio`, run the following command:

```bash
sudo apt update
sudo apt install tio
```

To list the available serial devices, run the following command:

```bash
tio --list
```

Choose the appropriate serial device from the list (e.g., `/dev/ttyUSB0`) and run the following command to access the board:

```bash
tio /dev/ttyUSB0 -b 921600
```

After running the command, you should be able to interact with the board through the serial console.

To set up PuTTY on Windows, follow the instructions below:

1. Download the latest PuTTY installer from the
 Microsoft Store .
2. Install PuTTY on your computer by running the downloaded installer and
following the installation prompts.
3. Open PuTTY and configure the serial connection in the
 Connection/Serial settings:

| Setting | Value |
|---|---|
| Speed (baud rate) | 921600 |
| Data bits | 8 |
| Stop bits | 1 |
| Parity | None |
| Flow control | None |

1. Click the Open button to start the serial connection.

After opening the connection, you should be able to interact with the board.
