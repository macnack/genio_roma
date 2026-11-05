# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

There is no code, build, or test setup. The repo holds a Markdown copy of the Grinn GenioBoard-700 documentation, scraped from https://developer.grinn-global.com/boards/grinn-genio-700-sbc/ (a Docusaurus site), so agents can read it cheaply. Everything lives in `grinn-genio-700-sbc-docs/`; start from its `README.md` index.

## Board tooling (direnv)

`.envrc` (direnv, already `allow`ed) puts `bin/` and `~/.local/bin` on PATH and sets `BOARD_TTY` (default `/dev/genio-board`, falls back to `/dev/ttyUSB0`; the symlink comes from `bin/board-symlink`), `BOARD_BAUD` (921600) and `BOARD_DOCS`. Per-machine overrides go in the git-ignored `.envrc.local`. Helpers in `bin/`: `board-setup` (one-time sudo install of tio/adb/fastboot/udev rules), `board-check` (status), `board-console` (tio serial console), `board-flash <image-dir>` (genio-flash). Full agent reference, including the board changes made so far (serial autologin, passwordless sudo) and how to undo them: `bin/README.md`.

## Layout

- `ubuntu/`: the OS the user works with. Read this first.
  - `host-setup.md` is the one-page, run-in-order host PC setup (apt, fastboot, pipx, genio-tools, udev rules, dialout). `getting-started/flash-prerequisites.md` is only a pointer to it.
- `yocto/`: the Yocto docs, kept for reference. Its `flash-prerequisites.md` still has the original mixed layout and has not been split like the Ubuntu one.
- `shared/hardware-resources.md`: OS-independent hardware page (datasheet link; the file table was empty on the site).

## Conventions and caveats

- Pages are compressed, not verbatim: images are replaced with `[Image: alt]`, callouts are single lines (`**Note:** ...`), tab labels and image captions are dropped, and code blocks carry language tags.
- Ubuntu cross-links are relative. Links to the original site stay absolute, and same-page anchor links were reduced to plain text.
- The prebuilt-images and hardware file tables show "No images/files available" because the site rendered them empty when scraped.
- The scrape came from the sitemap (16 pages). The converter script (BeautifulSoup + lxml) was not saved in the repo; if the docs need refreshing, re-fetch the pages and regenerate rather than hand-editing large sections.
- Keep Ubuntu pages short: the point of the Ubuntu/Yocto split is to save tokens when working only with Ubuntu.
