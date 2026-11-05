# Build the Image

This section provides step-by-step instructions for setting up the workspace and starting the image build process. Ensure that you complete the [Build Prerequisites](https://developer.grinn-global.com/boards/grinn-genio-700-sbc/software/yocto/getting-started/build-prerequisites) section before proceeding.

**Note:** The build process may take a while, depending on your system's resources.

## Initialize the Workspace

Clone the repository and enter the directory containing the `kas` configuration files.

```bash
git clone https://github.com/grinn-global/meta-grinn-genio.git genio/meta-grinn-genio
cd genio/meta-grinn-genio/kas
```

## Build the Image

Our boards support a variety of additional features, which can be enabled by adding specific kas configuration files to the build command. Each configuration file corresponds to a specific feature or set of features. Features can be combined.

Here is the [list of all the available image configurations](https://developer.grinn-global.com/boards/grinn-genio-700-sbc/software/yocto/getting-started/image-configurations).

Choose the features you want to include in your image by selecting the corresponding options below. If you are unsure which features you need, do not select any options, as the default image will include the most commonly used features.

```bash
KAS_MACHINE=grinn-genio-700-sbc KAS_CONTAINER_IMAGE_DISTRO=debian-bookworm KAS_WORK_DIR=../.. \
kas-container \
build default.yml
```

To enter the folder containing the generated image, run the following command:

```bash
cd ../../build/tmp/deploy/images/grinn-genio-700-sbc/
```
