# Introduction

Grinn provides a Yocto-based software stack for each supported platform family, designed to give you a consistent workflow across boards and SoMs while keeping the BSP structure predictable and easy to extend.

## Meta-Layer Repository

The meta-layer repository is the main source of truth for the Yocto software stack for a given family. It contains the necessary layers and configuration required to build images for all supported platforms in that family.

The Yocto meta-layer is developed internally and synchronized with the publicly available repository on GitHub.

Click the button below to open the repository for this platform's family.

[Open Meta-Layer Repository](https://github.com/grinn-global/meta-grinn-genio)

## Architecture

Grinn develops and maintains its own meta-layer for each family.

The meta-layer repository is treated as the main source of truth for that family. It is based on the SDK provided by the SoC vendor, with Grinn layer additions applied on top.

The meta-layer repository contains both internal meta-layers and references to external meta-layers required for the build.

At minimum, it includes the following layers directly in the repository:

| Layer | Purpose |
|---|---|
| `bsp` | The main BSP layer containing devicetrees, machine configurations, and platform-specific recipes. |
| `fixes` | Patches and fixes applied on top of software that is not maintained by Grinn, typically vendor SDK layers, though not limited to them. |

System-on-modules are separated at the software level. This makes it easier to develop custom hardware based on Grinn software by adding board-specific features on top of the existing meta-layer structure.

Grinn uses [KAS Setup Tool](https://github.com/siemens/kas) as the primary interface to the Yocto build system. This reduces setup overhead and simplifies maintenance for both internal development and customer use.

## Versioning

Grinn software releases use the `major.minor.patch` versioning scheme:

| Version Part | Meaning |
|---|---|
| `major` | New vendor SDK release |
| `minor` | New features or new machine support |
| `patch` | Bug fixes |

The [CHANGELOG.md](https://github.com/grinn-global/meta-grinn-genio/blob/HEAD/CHANGELOG.md) file in the repository root tracks the changes introduced in each release.

Each release is also accompanied by a corresponding set of prebuilt images.

Due to the nature of low-level embedded software, we cannot guarantee that even patch releases will be fully backward compatible.
