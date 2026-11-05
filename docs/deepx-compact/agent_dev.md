# DEEPX dx-agent-dev (`.deepx/`) system and reuse plan

> Compact of docs/deepx/agent_dev.md. Full text and extended citations are in the source file.

Maps the DEEPX dx-agent-dev (Beta) system and gives a reuse plan for our PyTorch -> ONNX -> DX-COM -> DXNN -> DX-RT ConvNeXt-Tiny pipeline. Nothing installed or executed.

## Officially documented facts

### 1. What the system is

- `.deepx/` is the canonical source. `dx-agent-gen` (package `dx_agent_dev_gen`, in `.deepx/tools`) generates files for Claude Code, GitHub Copilot, Cursor, OpenCode, and Codex CLI (via `AGENTS.md` + Codex skill). [dx-all-suite@51d81fe2ef v2.5.0: .deepx/docs/dx-agent-dev-overview.md#L8-L33] [dx-all-suite@51d81fe2ef v2.5.0: .deepx/docs/dx-agent-dev-overview.md#L65-L83]
- Repos with `.deepx/`: dx-all-suite, dx-runtime, dx_app, dx_stream, dx-compiler. Dirs: `agents/` (domain agents), `skills/` (slash-commands), `templates/` (`fragments/` only at suite root), `memory/` (pitfalls, API grounding), `instructions/`, `knowledge/` (YAML), `toolsets/` (SDK API reference), `contextual-rules/`, `prompts/`, `scripts/`; suite-only `docs/`, `tools/`, `tests/`, `e2e/`. [dx-all-suite@51d81fe2ef v2.5.0: .deepx/docs/dx-agent-dev-overview.md#L85-L103]
- Overview is dated 2026-05-12 (branch `merge2.3.2`); its counts are stale (14 suite skills, 16 fragments). Pinned tree has 19 skills in `.deepx/skills/` (incl. `dx-agent-showcase-build`, `dx-internal-*`); `.deepx/README.md` says 22 EN + 22 KO fragments. Paths and mechanisms were checked against the pinned tree. [dx-all-suite@51d81fe2ef v2.5.0: .deepx/docs/dx-agent-dev-overview.md#L1-L4] [dx-all-suite@51d81fe2ef v2.5.0: .deepx/README.md#L243-L243]

### 2. Agents (definitions)

- Markdown + YAML frontmatter: `name`, `description`, `argument-hint`, abstract `capabilities` (`read`, `edit`, `search`, `execute`, `sub-agent`, `ask-user`, `todo`), `routes-to` (label, target, description). Example: `dx-compiler-builder` routes to `dx-model-converter`, `dx-dxnn-compiler`. [dx-compiler@a087726ead v2.5.0: .deepx/agents/dx-compiler-builder.md#L1-L20]
- Hierarchy: `dx-suite-builder` -> `dx-compiler-builder` -> `dx-model-converter` / `dx-dxnn-compiler`; `dx-runtime-builder` -> `dx-app-builder` (-> python/cpp/benchmark/model-manager/validator) or `dx-stream-builder`. Validators: `dx-suite-validator`, `dx-validator` (runtime, dx_app, dx_stream). [dx-all-suite@51d81fe2ef v2.5.0: .deepx/docs/dx-agent-dev-overview.md#L35-L43]
- dx-compiler: `dx-compiler-builder` (router, 691 lines), `dx-model-converter` (PT -> ONNX, 247 lines), `dx-dxnn-compiler` (ONNX -> DXNN, 1235 lines). [dx-compiler@a087726ead v2.5.0: .deepx/agents/dx-compiler-builder.md#L1-L20] [dx-compiler@a087726ead v2.5.0: .deepx/agents/dx-model-converter.md#L1-L17] [dx-compiler@a087726ead v2.5.0: .deepx/agents/dx-dxnn-compiler.md#L104-L110]
- dx-runtime: `dx-runtime-builder` (router; Step 0 prerequisites gate, brainstorming gate, PPU routing) and `dx-validator` (5 steps: identify scope, run validation, collect feedback, apply approved feedback, verify). [dx-runtime@73ff9904f5 v2.5.0: .deepx/agents/dx-runtime-builder.md#L1-L20] [dx-runtime@73ff9904f5 v2.5.0: .deepx/agents/dx-validator.md#L39-L117]
- dx_app: `dx-app-builder`, `dx-python-builder` (sync, async, cpp_postprocess, async_cpp_postprocess), `dx-cpp-builder`, `dx-benchmark-builder`, `dx-model-manager`, `dx-validator`. [dx-all-suite@51d81fe2ef v2.5.0: .deepx/docs/dx-agent-dev-overview.md#L274-L283]
- Common rules: outputs under `dx-agent-dev/<session_id>/`; session id `YYYYMMDD-HHMMSS_<agent>_<coding_model>_<target_model>_<task>` (local time); START/DONE sentinel lines; fresh session id every run (never reuse prior session dirs); `sanity_check.sh --dx_rt` hard gate. [dx-all-suite@51d81fe2ef v2.5.0: .deepx/docs/dx-agent-dev-overview.md#L45-L61] [dx-compiler@a087726ead v2.5.0: .deepx/agents/dx-dxnn-compiler.md#L17-L30]
- Target device is always DX-M1 (`dx_m1`); compiler router says to ignore any DX-M1A mention (discontinued). [dx-compiler@a087726ead v2.5.0: .deepx/agents/dx-compiler-builder.md#L25-L28]

### 3. Skills and the skill router

- Name prefixes: `dx-swe-*` (general SWE process, self-contained), `dx-agent-*` (end-user build skills referencing `dx-swe-*`), `dx-harness-*` (internal `.deepx/` maintenance); meta `dx-skill-router`; `dx-internal-*` at suite level. Domain skills: `dx-agent-{subproject}-*`. [dx-all-suite@51d81fe2ef v2.5.0: .deepx/docs/skill-architecture.md#L5-L32]
- Suite skills in pinned tree: dx-agent-brainstorm, dx-agent-showcase-build, dx-agent-tdd, dx-agent-verify, dx-harness-validate, dx-harness-writing-skills, dx-internal-model-eval, dx-internal-pr-review-apply, dx-skill-router, dx-swe-{brainstorm,debugging,executing-plans,parallel-agents,receiving-review,requesting-review,subagent-dev,tdd,verify,writing-plans}. [dx-all-suite@51d81fe2ef v2.5.0: .deepx/skills]
- Domain skills: compiler `dx-agent-compiler-convert`, `-compile`, `-validate`, `-pre-optimize` (YOLO/RTMDet helper); runtime `dx-agent-runtime-validate`; dx_app `dx-agent-app-build-python`, `-build-cpp`, `-build-async`, `-model-management`, `-validate`. [dx-all-suite@51d81fe2ef v2.5.0: .deepx/docs/skill-architecture.md#L92-L115] [dx-compiler@a087726ead v2.5.0: .deepx/skills/dx-agent-compiler-pre-optimize/SKILL.md#L1-L12]
- Router says: if there is even a 1% chance a skill applies, invoke it before any response, incl. clarifying questions. Precedence: user instructions (CLAUDE.md, AGENTS.md, direct requests) > dx-* skills > default system prompt. [dx-all-suite@51d81fe2ef v2.5.0: .deepx/skills/dx-skill-router/SKILL.md#L8-L24]
- Fragment "Skill Router - Universal Pre-Flight (HARD GATE)" makes `/dx-skill-router` the absolute first action for every user message. [dx-all-suite@51d81fe2ef v2.5.0: .deepx/templates/fragments/en/skill-router-mandatory.md#L1-L12]
- Scenario by path: `dx-agent-dev/<session_id>/` -> `dx-skill-router -> dx-agent-brainstorm -> dx-swe-writing-plans -> dx-agent-tdd -> dx-agent-{subproject}-* -> dx-agent-verify`; `.deepx/`, `tests/`, `tools/` -> harness sequence; anything else -> SDK-dev `brainstorm -> writing-plans -> tdd -> verify`. [dx-all-suite@51d81fe2ef v2.5.0: .deepx/docs/skill-architecture.md#L125-L184]
- 5-step workflow for every code-generation session (also autopilot): router, `/dx-agent-brainstorm`, `/dx-swe-writing-plans`, `/dx-agent-tdd`, `/dx-agent-verify`. [dx-all-suite@51d81fe2ef v2.5.0: .deepx/docs/dx-agent-dev-overview.md#L465-L475]

### 4. Instructions, memory, toolsets

- `instructions/`: compiler `compilation-workflow.md`, `coding-standards.md`; runtime `agent-protocols.md`, `integration.md`. [dx-compiler@a087726ead v2.5.0: .deepx/instructions/compilation-workflow.md#L1-L55] [dx-all-suite@51d81fe2ef v2.5.0: .deepx/docs/dx-agent-dev-overview.md#L245-L250]
- `memory/common_pitfalls.md` (Symptom / Cause / Fix; tags `[UNIVERSAL]`, `[DX_COMPILER]`, `[QUANTIZATION]`, ...); update protocol in `MEMORY.md`. [dx-compiler@a087726ead v2.5.0: .deepx/memory/MEMORY.md#L1-L27]
- `memory/sdk_grounding_reference.md` (suite) is the anti-hallucination registry: any API name in `.deepx/` instructions must appear there or be verifiable in SDK source. [dx-all-suite@51d81fe2ef v2.5.0: .deepx/memory/sdk_grounding_reference.md#L1-L21]
- dx-compiler `toolsets/` (`dxcom-cli.md`, `dxcom-api.md`, `config-schema.md`, `qat.md`, `paddlepaddle-deepx.md`, `ultralytics-*.md`): agents must read before calling dxcom. [dx-compiler@a087726ead v2.5.0: .deepx/memory/common_pitfalls.md#L824-L834]
- dx-runtime: `knowledge/feedback_rules.yaml`; scripts `validate_framework.py`, `validate_app.py`, `feedback_collector.py`, `apply_feedback.py` implement validate -> collect feedback -> apply -> re-verify. [dx-all-suite@51d81fe2ef v2.5.0: .deepx/docs/dx-agent-dev-overview.md#L252-L264]

### 5. How adapters are generated from `.deepx/`

- Entry points: `dx-agent-gen generate`, `dx-agent-gen check` (drift), `run_all.sh generate|check|lint|prune` across 5 repos, `install-hooks.sh` (pre-commit). Install: `pipx install --force --editable .deepx/tools`. [dx-all-suite@51d81fe2ef v2.5.0: .deepx/docs/dx-agent-dev-overview.md#L531-L542]
- `generator.py`: `_generate_copilot`, `_generate_claude`, `_generate_opencode`, `_generate_cursor`, `_generate_instructions` (CLAUDE.md, AGENTS.md, copilot-instructions.md from `templates/{en,ko}/*.tmpl` + fragments). [dx-all-suite@51d81fe2ef v2.5.0: .deepx/tools/src/dx_agent_dev_gen/generator.py#L488-L637]
- Capability expansion: Claude `read` -> Read/Grep/Glob, `edit` -> Write/Edit, `execute` -> Bash, `sub-agent` -> Agent, `ask-user` -> AskUserQuestion, `web` -> WebFetch; OpenCode `mode: subagent` / `tools: {bash, edit, write}`; Copilot VS Code tool IDs; `routes-to` -> Copilot `handoffs`. [dx-all-suite@51d81fe2ef v2.5.0: .deepx/tools/src/dx_agent_dev_gen/constants.py#L5-L63] [dx-all-suite@51d81fe2ef v2.5.0: .deepx/tools/src/dx_agent_dev_gen/transformers.py#L71-L101]
- Copilot rewrites `.deepx/agents/*.md` -> `.github/agents/*.agent.md` and `.deepx/skills/` -> `.github/skills/`; `toolsets/`, `instructions/`, `memory/`, `knowledge/` are not rewritten. [dx-all-suite@51d81fe2ef v2.5.0: .deepx/tools/src/dx_agent_dev_gen/transformers.py#L8-L50]
- Output per tool (suite level):

  | Tool | Auto-loaded | Agents | Skills |
  |---|---|---|---|
  | Claude Code | `CLAUDE.md` | `.claude/agents/*.md` (generated copies, `tools:` frontmatter, AUTO-GENERATED header) | `.claude/skills/<name>/SKILL.md` thin wrapper: "Read and follow ... `.deepx/skills/<name>/SKILL.md`" |
  | Copilot | `.github/copilot-instructions.md` | `.github/agents/*.agent.md` | `.github/skills/` inline copies |
  | Cursor | `.cursor/rules/dx-*.mdc` | agent `.mdc` files in `.cursor/rules/` | `skill-*.mdc` stubs -> `.deepx/skills/...` |
  | OpenCode | `AGENTS.md` + `opencode.json` | `.opencode/agents/*.md` (`mode: subagent`) | `.deepx/skills/*/SKILL.md` via `"skills": {"paths": [".deepx/skills"]}` |
  | Codex CLI | `AGENTS.md` + `.codex/skills/dx-codex-identity/SKILL.md` | read `.deepx/agents/*.md` directly | read `.deepx/skills/<name>/SKILL.md` directly |

  [dx-all-suite@51d81fe2ef v2.5.0: docs/source/00_Agent_Driven_Development.md#L204-L226] [dx-all-suite@51d81fe2ef v2.5.0: .claude/skills/dx-skill-router/SKILL.md#L1-L9] [dx-all-suite@51d81fe2ef v2.5.0: opencode.json#L1-L9] [dx-all-suite@51d81fe2ef v2.5.0: .codex/skills/dx-codex-identity/SKILL.md#L1-L30]
- Git submodule boundary: Copilot, Claude Code, Codex see only files at the current git root; opened at dx-all-suite they do not auto-load sub-repos' instruction files. OpenCode bridges this via `opencode.json` instructions. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/00_Agent_Driven_Development.md#L253-L261] [dx-all-suite@51d81fe2ef v2.5.0: opencode.json#L1-L9]
- Claude Code hooks (`.claude/settings.json`): `PreToolUse` on `Edit|Write` exits 2 to block direct edits to generator-output paths (`.claude/agents`, `.claude/skills`, `.cursor/rules`, `.github/agents|skills`, `.opencode/agents`, `CLAUDE.md`, `AGENTS.md`, `copilot-instructions.md`) inside a tree with `.deepx/`. `PostToolUse` reports drift via `dx-agent-gen check`, never regenerates. [dx-all-suite@51d81fe2ef v2.5.0: .claude/settings.json#L1-L26] [dx-all-suite@51d81fe2ef v2.5.0: .claude/hooks/pre-edit-generator-guard.sh#L1-L80] [dx-all-suite@51d81fe2ef v2.5.0: .claude/hooks/post-edit-dx-agent-gen.sh#L1-L91]
- Drift defence: pre-commit hook, CI sub-repo gate (`subrepo_check.sh`), CI suite gate, generator hard-fail, ~600 static conformance tests, agent instruction-verification loop; E2E harness (~586 tests) drives each CLI in autopilot. [dx-all-suite@51d81fe2ef v2.5.0: .deepx/docs/dx-agent-dev-overview.md#L105-L139] [dx-all-suite@51d81fe2ef v2.5.0: .deepx/docs/dx-agent-dev-overview.md#L479-L500]

### 6. The compile / convert / validate workflow (dx-compiler)

- Router `dx-compiler-builder` loads context first (`.github/copilot-instructions.md`, `.deepx/memory/common_pitfalls.md`, `source/docs/` guides, `toolsets/*`), then classifies PT -> ONNX vs ONNX -> DXNN. [dx-compiler@a087726ead v2.5.0: .deepx/agents/dx-compiler-builder.md#L28-L42]
- Convert (`dx-model-converter` / `dx-agent-compiler-convert`): P1 load model + `model.eval()`; P2 `torch.onnx.export` with batch 1, `opset_version=13`, `dynamic_axes=None`; P3 validate (`onnx.checker`, input shape, single output); P4 simplify only on explicit request. Skill adds P0 path selection (Ultralytics shortcut), P-1 model acquisition, P0 working dir, P2a Ultralytics handling. [dx-compiler@a087726ead v2.5.0: .deepx/agents/dx-model-converter.md#L29-L197] [dx-compiler@a087726ead v2.5.0: .deepx/skills/dx-agent-compiler-convert/SKILL.md#L16-L287]
- Compile (`dx-dxnn-compiler` / `dx-agent-compiler-compile`): P-1 dxcom install pre-flight; P0 working dir + calibration data (symlink); P1 inspect ONNX; P2 config.json; P3 compile (background, `compile.pid`); P4 PPU (detection only); P5 validate output (`*_summary.html`, compiler.log); 5.5 mandatory artifacts (`setup.sh`, `run.sh`, `README.md`, `verify.py`, `session.log`); 5.6 TDD gate; 5.7 cross-validation with a precompiled reference model; 5.8 pre-DONE `.dxnn` existence check; P6 final report. [dx-compiler@a087726ead v2.5.0: .deepx/agents/dx-dxnn-compiler.md#L109-L1033]
- Validate (`dx-agent-compiler-validate`): check artifacts, inspect summary report, review compiler.log (errors, warnings, NPU vs CPU partition, quantization summary), optional cross-validation with a precompiled reference, report. Also documents QAT outputs. [dx-compiler@a087726ead v2.5.0: .deepx/skills/dx-agent-compiler-validate/SKILL.md#L21-L174]
- Runtime validation (`dx-agent-runtime-validate`): run, collect feedback proposals, review, apply approved fixes (dry run supported), re-validate. [dx-runtime@73ff9904f5 v2.5.0: .deepx/skills/dx-agent-runtime-validate/SKILL.md#L31-L52]
- Compiler agent verifies `dxcom` (P-1), tries `pip install dx-com` in a venv, then `dx-compiler/install.sh`, and stops if still missing. [dx-compiler@a087726ead v2.5.0: .deepx/agents/dx-dxnn-compiler.md#L111-L150]
- Cross-project suite tasks create two session dirs: `dx-compiler/dx-agent-dev/<id>_compile/` and `dx-runtime/dx_app/dx-agent-dev/<id>_inference/`. [dx-all-suite@51d81fe2ef v2.5.0: .deepx/docs/dx-agent-dev-overview.md#L52-L54]

### 7. Risky instructions found in agent files (implication notes)

Each item is what the file literally instructs; the "implication" is ours.

- `dx-runtime-builder` Step 0 runs `bash install.sh --all --exclude-app --exclude-stream --skip-uninstall --venv-reuse` automatically when `sanity_check.sh --dx_rt` fails. [dx-runtime@73ff9904f5 v2.5.0: .deepx/agents/dx-runtime-builder.md#L56-L69] That `install.sh` uses `sudo` (`sudo ./build.sh -c install --reload`, `sudo systemctl disable|stop|start|enable dxrt.service`). [dx-runtime@73ff9904f5 v2.5.0: install.sh#L88-L135] Implication: changes host kernel driver and services; not wanted on our host (no DX-M1). Do not auto-run; keep installs manual.
- `dx-dxnn-compiler` Phase -1 and `dx-compiler-builder` fall back to `bash $COMPILER_DIR/install.sh` and `pip install dx-com`. [dx-compiler@a087726ead v2.5.0: .deepx/agents/dx-dxnn-compiler.md#L127-L141] `dx-compiler/install.sh` contains `sudo apt-get update`, `sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y tzdata`, `sudo apt-get install -y python3 python3-venv python3-dev` (and `sudo dnf install` on another path). [dx-compiler@a087726ead v2.5.0: install.sh#L274-L276] [dx-compiler@a087726ead v2.5.0: install.sh#L321-L321] Implication: root package installs; pre-install dx-com in our own venv so the fallback never triggers.
- Generated `setup.sh` template runs `dx-runtime/install.sh --all ...`, `dx-compiler/install.sh`, `pip install` of `dx_engine` wheel and `opencv-python numpy onnxruntime`. [dx-compiler@a087726ead v2.5.0: .deepx/instructions/compilation-workflow.md#L296-L335] Implication: the mandatory `setup.sh` is an install script; review before running.
- Calibration fallback downloads data via `example/2-download_sample_calibration_dataset.sh` from `https://sdk.deepx.ai/`; model acquisition may `wget` an arbitrary "official" URL or `pip install huggingface_hub`. [dx-compiler@a087726ead v2.5.0: .deepx/agents/dx-dxnn-compiler.md#L205-L233] [dx-compiler@a087726ead v2.5.0: example/2-download_sample_calibration_dataset.sh#L33-L33] [dx-compiler@a087726ead v2.5.0: .deepx/skills/dx-agent-compiler-compile/SKILL.md#L59-L96] Implication: untrusted-input fetches; data is not representative ImageNet-quality for ConvNeXt (see Hypotheses).
- Official E2E harness runs each CLI unattended: Claude Code `-p --dangerously-skip-permissions`, Codex `exec --json -s danger-full-access`, Copilot `--yolo --no-ask-user`. [dx-all-suite@51d81fe2ef v2.5.0: .deepx/docs/dx-agent-dev-overview.md#L492-L498] Implication: test-harness settings; do not copy into daily workflow.
- Fragments define an "autopilot" mode: ask-user prompts replaced by knowledge-base defaults, gates still apply. [dx-all-suite@51d81fe2ef v2.5.0: CLAUDE.md#L254-L254] [dx-all-suite@51d81fe2ef v2.5.0: CLAUDE.md#L363-L363] Implication: an agent may proceed without confirming choices such as calibration data or quantization options.
- Shipped `CLAUDE.md` overrides: forced `/dx-skill-router` first on every message; `[DX-AGENT-DEV: START]` / `[DX-AGENT-DEV: DONE ...]` sentinels; model-notice banner for non-Sonnet/Opus 4.6+ models; `dx-agent-dev/<session_id>/` isolation; never `git add`/`git commit` under `docs/superpowers/`; ban on referencing previous sessions. [dx-all-suite@51d81fe2ef v2.5.0: CLAUDE.md#L13-L40] [dx-all-suite@51d81fe2ef v2.5.0: CLAUDE.md#L494-L494] [dx-all-suite@51d81fe2ef v2.5.0: CLAUDE.md#L1073-L1073] [dx-all-suite@51d81fe2ef v2.5.0: .deepx/docs/dx-agent-dev-overview.md#L56-L61] Implication: dropping `CLAUDE.md` into our project would alter all Claude sessions there, and could conflict with our own CLAUDE.md and `docs/` workflow.
- Pre-edit hook blocks edits (exit 2) to `.claude/agents|skills`, `CLAUDE.md`, `AGENTS.md` anywhere under a tree containing `.deepx/`. [dx-all-suite@51d81fe2ef v2.5.0: .claude/hooks/pre-edit-generator-guard.sh#L38-L81] Implication: copying `.deepx/` plus the hook would make our own `CLAUDE.md` read-only for Claude.
- Agent rules: never reference prior sessions, always re-download/re-export/recompile from scratch; `ls dx-agent-dev/` is prohibited. [dx-compiler@a087726ead v2.5.0: .deepx/memory/common_pitfalls.md#L516-L545] Implication: conflicts with caching ONNX/DXNN artifacts across our phases; our docs workflow must override explicitly.

### 8. Reuse plan for PyTorch -> ONNX -> DX-COM -> DXNN -> DX-RT (ConvNeXt-Tiny)

Derived from sections 1-7 (officially documented content, with our selection). Installation is described only; nothing in `/tmp/.../repos` or the system is modified; sources stay read-only. Paths are inside the pinned clones, relative to `repos/`.

**Reuse as-is (knowledge/reference, no execution risk)**

| What | Exact path | Use for us |
|---|---|---|
| dxcom CLI/API/config toolsets | `dx-compiler-dir/dx-compiler/.deepx/toolsets/dxcom-cli.md`, `dxcom-api.md`, `config-schema.md` | Ground truth for flags/keys; read before any compile call |
| Compiler pitfalls | `dx-compiler-dir/dx-compiler/.deepx/memory/common_pitfalls.md` | Pitfalls #1, #2, #3, #4, #5, #7, #9, #13, #18, #20, #21, #22, #24 apply directly (see [tricks_and_best_practices.md](tricks_and_best_practices.md)) |
| Compile workflow reference | `dx-compiler-dir/dx-compiler/.deepx/instructions/compilation-workflow.md` | Calibration best practice, accuracy-improvement order, troubleshooting checklist |
| SDK grounding registry | `dx-all-suite-dir/dx-all-suite/.deepx/memory/sdk_grounding_reference.md` | Anti-hallucination check (note stale `quantization_device` entry) |
| Converter agent rules | `dx-compiler-dir/dx-compiler/.deepx/agents/dx-model-converter.md` Phases 1-3 | Export checklist: eval(), batch 1, opset 13, static shape, validate |
| Validate skill | `dx-compiler-dir/dx-compiler/.deepx/skills/dx-agent-compiler-validate/SKILL.md` | Post-compile checks: `.dxnn` exists, summary report, compiler.log partition review |
| QAT/Q-PRO/quant diagnosis | `dx-compiler-dir/dx-compiler/.deepx/toolsets/qat.md`, `dxcom-cli.md` | Only if INT8 accuracy misses target |
| Runtime API grounding | `dx_app-dir/dx_app/.deepx/toolsets/dx-engine-api.md`, `.deepx/memory/platform_api.md`, `performance_patterns.md` | dx_engine call names, benchmark and profiling, `DXRT_DYNAMIC_CPU_THREAD` |
| Runtime pitfalls | `dx-runtime-dir/dx-runtime/.deepx/memory/common_pitfalls.md` | sanity-check gate, build order, headless; skip entries flagged as unverified |
| Process skills | `dx-all-suite-dir/dx-all-suite/.deepx/skills/dx-swe-{brainstorm,writing-plans,tdd,verify,debugging}/SKILL.md` | Optional general process discipline; self-contained, not DEEPX-specific |

**Reuse with adaptation (agents/skills that would run)**

| What | Exact path | Adaptation needed |
|---|---|---|
| `dx-agent-compiler-convert` skill | `dx-compiler-dir/dx-compiler/.deepx/skills/dx-agent-compiler-convert/SKILL.md` | Use Phases -1 to 3 for torchvision `convnext_tiny`; skip Phase 0 Ultralytics and 2a; agent writes `session.log`/`README.md` we may not want |
| `dx-agent-compiler-compile` skill | `dx-compiler-dir/dx-compiler/.deepx/skills/dx-agent-compiler-compile/SKILL.md` | Phases 0-5 with our own ImageNet calibration folder; skip Phase 4 PPU and 5.7 (no reference ConvNeXt DXNN known); drop mandatory `setup.sh`/`run.sh`/`verify.py` template or supply ours |
| `dx-dxnn-compiler` agent | `dx-compiler-dir/dx-compiler/.deepx/agents/dx-dxnn-compiler.md` | Heavy (1235 lines), YOLO-centric; reuse background-compile pattern (L450-L513) and Phase 5 validation; disable Phase -1 install fallbacks (section 7) |
| `dx-compiler-builder` router | `dx-compiler-dir/dx-compiler/.deepx/agents/dx-compiler-builder.md` | Optional; only routing between the two agents above |
| `dx-agent-runtime-validate` / `dx-validator` | `dx-runtime-dir/dx-runtime/.deepx/skills/dx-agent-runtime-validate/SKILL.md`, `.deepx/agents/dx-validator.md` | Validates dx_app/dx_stream framework structure, not custom code; use only if we build on dx_app |
| dx_app Python builder (if deploying via dx_app) | `dx_app-dir/dx_app/.deepx/agents/dx-app-builder.md`, `dx-python-builder.md`, skill `dx-agent-app-build-python` | Classification uses IFactory + SyncRunner skeleton; requires model registry entry; ConvNeXt is not a registry model (only a `"convnext"` postprocessor mapping under `dx-ai-studio`) |

**How to install/enable (description only, not to be performed by us on the system)**

1. Claude Code reads `CLAUDE.md` at project root and agents from `.claude/agents/*.md`; skills at `.claude/skills/<name>/SKILL.md` are thin wrappers pointing to `.deepx/skills/<name>/SKILL.md`. Enabling a skill means placing the wrapper dir and `.deepx/skills/<name>/` in the same relative layout in our project (or user-level Claude dirs), then starting `claude` there. [dx-all-suite@51d81fe2ef v2.5.0: .claude/skills/dx-skill-router/SKILL.md#L7-L9] [dx-all-suite@51d81fe2ef v2.5.0: docs/source/00_Agent_Driven_Development.md#L217-L226]
2. Agent bodies in `.claude/agents/` instruct reading `.github/copilot-instructions.md`, `.deepx/memory/common_pitfalls.md`, `.deepx/toolsets/*` and `source/docs/*` relative to the compiler repo root. These paths must exist in our project (copy a `.deepx/` subset; `source/docs/` is the DX-COM manual in dx-compiler), or the "MANDATORY context loading" step fails or is skipped. [dx-compiler@a087726ead v2.5.0: .deepx/agents/dx-compiler-builder.md#L30-L42]
3. Do not copy hooks and `CLAUDE.md` unless wanted (section 7). Without `.deepx/tools` and `dx-agent-gen`, the post-edit hook only prints a warning; the pre-edit hook blocks edits wherever a `.deepx/` directory exists above the file.
4. Alternative with no coupling: do not install the agents; read the `.deepx/` files above as reference and encode the relevant rules in our own project skills/CLAUDE.md.

## Experimentally verified facts

None yet (no DX-M1 available on host as of 2026-11-05).

## Hypotheses needing validation

- **Gaps not covered by official agents (must be built by us, inferred from the sources):**
  1. A torchvision `convnext_tiny` PyTorch -> ONNX export script and PyTorch vs ONNX numeric parity test (converter has only generic and YOLO examples).
  2. Operator-support check of the exported ConvNeXt graph (LayerNorm, depthwise 7x7 Conv, GELU, layer-scale Mul) against `source/docs/03_Building_Models.md`; no agent does this. [dx-compiler@a087726ead v2.5.0: source/docs/03_Building_Models.md#L49]
  3. ImageNet-representative calibration set and `default_loader` config (resize/centercrop/normalize chain for ConvNeXt); agents default to the generic 100-image sample set.
  4. Accuracy evaluation of DXNN vs ONNX/PyTorch (top-1/top-5 on labelled subset); official `verify.py` checks YOLO-style detections, not classification accuracy.
  5. Runtime deployment against DX-RT (Python `dx_engine` or C++ API) with input-format auto-detection from `get_input_tensors_info()`, plus latency/throughput benchmark plan.
  6. Hardware-absent handling: official gates stop when `sanity_check.sh` fails; only compile-only work may proceed, with verification marked SKIPPED. [dx-compiler@a087726ead v2.5.0: .deepx/memory/common_pitfalls.md#L909-L915]
  7. Provenance logging matching our `docs/deepx` claim classes (agents' `session.log` is a command transcript, not a claim ledger).
- **Compatibility of shipped adapters with current Claude Code**: hook scripts state they were measured against Claude Code 2.110.0 / agent-sdk 0.3.271; behaviour in our installed version is unverified. [dx-all-suite@51d81fe2ef v2.5.0: .claude/hooks/pre-edit-generator-guard.sh#L11-L16] Experiment: run in a scratch project copy with the hooks and attempt an edit to a generated path.
- **Suitability of `dx-dxnn-compiler` for a non-YOLO classifier**: 1235-line agent is YOLO/PPU-centric and may push irrelevant steps (PPU question, Phase 5.6 TDD gate, mandatory demo artifacts). Experiment: dry-read the agent against a ConvNeXt prompt in a scratch session, or use the skills only.
- **Usability of `.deepx/skills/` on Codex/Copilot without adaptation** (docs say Codex reads them via `cat`; Copilot uses inline copies): untested; irrelevant unless we change tools.
- **Version drift between overview text and pinned tree** (counts; DX-RT 3.0.x references vs pinned DX-RT v3.5.0): we trust file contents over overview prose. Experiment: re-run `ls` counts after each source refresh.
- **Web docs**: https://developer.deepx.ai/tech-docs/ (fetched 2026-11-05) lists DX-AllSuite, DXNN SDK, DX-COM Quick Start, DX-RT, DX-STREAM and DX-APP overview pages for v2.4.x but does not mention the agent-dev system or ConvNeXt guidance; not used for any claim above. [developer.deepx.ai/tech-docs/, fetched 2026-11-05]
