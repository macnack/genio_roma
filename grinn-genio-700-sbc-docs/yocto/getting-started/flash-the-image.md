# Flash the Image

This section details the steps for flashing your device. Make sure you complete the [Flash Prerequisites](https://developer.grinn-global.com/boards/grinn-genio-700-sbc/software/yocto/getting-started/flash-prerequisites) section before proceeding.

**Note:** To obtain the latest prebuilt image, please refer to the Prebuilt Images section.

## Connect the Board

Before flashing, make sure the board is connected as follows:

- Connect the POWER port to a power source.
- Connect the DEBUG port to the host PC.
- If you plan to use serial output, connect the SERIAL port to the host PC.

**Note:** Some boards provide serial access through the DEBUG port. Others require an external USB-to-UART converter. Check your board documentation for details.

Consult the image below for the location of these ports on the Grinn GenioBoard-700 .

[Image: Grinn GenioBoard-700 PCB]

## Flashing

Prior to running the flashing tool, determine the correct path to the image and enter it in the terminal.

Run the flashing tool with the following command:

```bash
genio-flash
```

Once the tool is running, put the device into download mode as described in the Download Mode section.

**Note:** The genio-flash tool should automatically put the board into download mode.

**Caution:** Do not disconnect your device or interrupt the process until it completes successfully.

## Device Tree Overlays

Device Tree Overlays are used to configure the hardware components of the board during the flashing process. They allow you to enable or disable specific features and peripherals based on your requirements.

All available DTBOs can be listed using the following command:

```bash
genio-flash --list-dtbo
```

The output should look similar to this:

```bash
List of available DTBO:
  ( * items are automatically loaded )
    camera-imx214-csi0-imx214-csi1.dtbo
    display-dp.dtbo
  * video.dtbo
    wifi-bt-sdio-murata-1zm.dtbo
  * apusys.dtbo
    camera-imx214-csi0.dtbo
    camera-imx214-csi1.dtbo
    audio-sof.dtbo
    display-hdmi.dtbo
```

Items prefixed with `*` are loaded by default during the flashing process.

To select a DTBO, use the `--load-dtbo` flag. Multiple `--load-dtbo` flags can be used to load multiple DTBOs in a single flash session.

For example, to flash Grinn GenioBoard-700 with HDMI output and an IMX214 camera connected to the CSI0 port, use the following command:

```bash
genio-flash --load-dtbo display-hdmi.dtbo --load-dtbo camera-imx214-csi0.dtbo
```

## Download Mode

The Grinn GenioBoard-700 can be placed into download mode manually using its physical buttons.

Consult the image below for the location of the buttons on the Grinn GenioBoard-700 .

Follow the sequence below to put the board into download mode:

1. Locate the RESET and DOWNLOAD buttons on your device.
2. Press and hold the DOWNLOAD button.
3. Click the RESET button while still holding the DOWNLOAD button.
4. After a brief pause, release the DOWNLOAD button.
5. The flashing tool should now detect the board and start the flashing process.

[Image: Grinn GenioBoard-700 PCB]
