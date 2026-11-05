# Build Prerequisites

Before building the image, you must set up your development environment with the necessary tools and system resources. This section outlines the required system specifications and installation steps for essential tools.

## System Requirements

To successfully build the image, ensure your system meets the following requirements:

- Linux-based operating system
- Minimum 200 GB of free disk space
- At least 16 GB of RAM
- Internet connection

## Install git

The `git` tool is essential for cloning the repository that contains the board support package for Grinn hardware. To install `git`, follow the instructions on the [official Git website](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git).

## Install docker

The `docker` tool is required to build the image using the `kas-container` script. It lets you run the build process inside a containerized environment, which ensures consistency and isolation from your host system. To install `docker`, follow the instructions on the [official Docker website](https://docs.docker.com/engine/install/).

## Set up kas-container

Grinn uses the `kas` build tool to manage the build process. It significantly simplifies the process of building Yocto-based images by abstracting away the complexities of the underlying build system.

To ensure the same build environment across different systems, the `kas-container` command is used. It is a simple wrapper around the `docker` command that runs `kas` inside a container. This approach eliminates the need to install `kas` directly on your host system.

To install the `kas-container` script, run the following commands in your terminal:

```bash
wget -qO kas-container \
https://raw.githubusercontent.com/siemens/kas/refs/tags/5.3/kas-container
chmod +x kas-container
sudo mv kas-container /usr/local/bin/
```
