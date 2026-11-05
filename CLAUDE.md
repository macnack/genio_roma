# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

No code, build, or test setup. It holds documentation for the Grinn GenioBoard-700 (Docusaurus site https://developer.grinn-global.com/boards/grinn-genio-700-sbc/) and for the DEEPX DX-M1 NPU, plus helper scripts for the board connected to this PC. Remote: `origin` = https://github.com/macnack/genio_roma.git (branch `main`).

## Where to start

- Grinn board docs: `grinn-genio-700-sbc-docs/README.md`.
- DEEPX DX-M1 docs: `docs/deepx/README.md` (full, with citations; read `docs/deepx/CONVENTIONS.md` first). For agent context, use `docs/deepx-compact/` (same filenames, citations kept, ~91% of source words). Board status: `docs/deepx/board_summary.md`, detail in `board_discovery.md`.
- Board tools: `bin/README.md`.

## Board tooling (direnv)

`.envrc` (direnv, already `allow`ed) puts `bin/` and `~/.local/bin` on PATH and sets `BOARD_TTY` (default `/dev/genio-board`, falls back to `/dev/ttyUSB0`; the symlink comes from `bin/board-symlink`), `BOARD_BAUD` (921600) and `BOARD_DOCS`. Per-machine overrides go in the git-ignored `.envrc.local`. Helpers in `bin/`: `board-setup` (one-time sudo install of tio/adb/fastboot/udev rules), `board-check` (status), `board-console` (tio serial console), `board-flash <image-dir>` (genio-flash). The board's serial autologin and passwordless sudo were added by us; `bin/README.md` has the undo steps.

## Grinn board docs layout (`grinn-genio-700-sbc-docs/`)

- `ubuntu/`: the OS the user works with. Read this first.
  - `host-setup.md` is the one-page, run-in-order host PC setup. `getting-started/flash-prerequisites.md` is only a pointer to it.
- `yocto/`: kept for reference. Its `flash-prerequisites.md` still has the original mixed layout.
- `shared/hardware-resources.md`: OS-independent hardware page.

Conventions and caveats:
- Pages are compressed: images become `[Image: alt]`, callouts are one line (`**Note:** ...`), tab labels and captions are dropped, code blocks carry language tags.
- Ubuntu cross-links are relative; links to the original site stay absolute.
- Prebuilt-image and hardware file tables are empty because the site rendered them empty when scraped.
- The converter (BeautifulSoup + lxml) is not saved in the repo. To refresh, re-fetch the pages from the sitemap (16 pages) and regenerate rather than hand-editing large sections.
- Keep Ubuntu pages short: the Ubuntu/Yocto split exists to save tokens.

## DEEPX docs conventions

- Each doc has three sections in order: `## Officially documented facts`, `## Experimentally verified facts`, `## Hypotheses needing validation`. Do not invent API calls, flags or config keys. Copy citations verbatim, never alter them.
- `docs/deepx-compact/` was produced by sub-agents and checked by script: every source citation is present, and the H2 headings match. Edit the source first, then regenerate the compact copy.
- Known contradiction: `docs/deepx/README.md` says no DX-M1 is available, but `board_discovery.md` records one on the board. Update the README when resolving it.

## Repo state

- Committed: `grinn-genio-700-sbc-docs/`, `bin/`, `CLAUDE.md`, `.envrc`, `.gitignore`, `docs/` (commits `1447ade`, `b4ba070`).
- Not ours, not committed: `.gitignore.new`, `third_party/`, `weights/`. Ask before committing them.
