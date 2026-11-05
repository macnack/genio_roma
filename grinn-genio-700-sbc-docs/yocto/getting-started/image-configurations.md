# Image Configurations

This section describes the supported image configurations.

| Type | KAS Config | Description |
|---|---|---|
| Default Image | `default.yml` | The default image is the baseline configuration and is designed to be extensible. It sets up the required meta-layers, selects the default distro and image, and applies the necessary settings in `local.conf`. All extensions are layered on top of the default image and can be combined with each other. |
| NDA Extension | `nda.yml` | The NDA extension provides access to components that are protected by a Non-Disclosure Agreement (NDA) with MediaTek. The full list of all the features included by the NDA-enabled image is available in the [Yocto Feature Table](https://download.mediatek.com/aiot/download/release-note/v26.0/v26.0_IoT_Yocto_Scarthgap_Feature_Table_v1.0.pdf).  Signing the NDA is only required if you plan to build the NDA-enabled image. You can test the NDA-enabled image without signing the NDA by downloading the prebuilt image with NDA extension enabled.  To be able to build the NDA-enabled image, follow the instructions in the [Git01 Setup Guide](https://mediatek.gitlab.io/aiot/doc/aiot-dev-guide/master/sw/yocto/get-started/account-setup.html). Make sure to configure your git credentials using the `genio-account-setup.py` to access the NDA repositories. |
| DEEPX Extension | `deepx.yml` | The DEEPX extension adds support for the DX-M1 accelerator. It is a high-performance AI inference accelerator designed for edge devices. It connects to the host system via PCIe. For more information about DEEPX, refer to the [DeepX M1 Accelerator](https://developer.grinn-global.com/boards/grinn-genio-700-sbc/software/yocto/guides/deepx/) guide. |
| Netboot Extension | `netboot.yml` | The netboot extension adds support for booting the board over the network. For setup details, see the [Network Boot](https://developer.grinn-global.com/boards/grinn-genio-700-sbc/software/yocto/guides/netboot/) guide. |
