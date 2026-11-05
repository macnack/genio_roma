# docs/deepx conventions

These docs consolidate DEEPX DX-M1 knowledge for this project. Rules:

## Claim classes (every technical statement belongs to exactly one)

Each doc has three sections, in this order, using these exact headings:

1. `## Officially documented facts` — stated in official DEEPX source. Every bullet ends with a citation.
2. `## Experimentally verified facts` — observed by us on real hardware/tools in this project. Each bullet cites a log/script path under `/home/maciej/Github/geniu_aeroma`. **Until Phases 3-6 run, this section reads: `None yet (no DX-M1 available on host as of 2026-11-05).`**
3. `## Hypotheses needing validation` — inferences, gaps, or things the sources leave ambiguous. Each says what experiment would settle it.

## Citation format

- Repo file: `[dx-compiler@a087726ead v2.5.0: source/docs/02_04_ONNX_File_Configuration.md#L40-L57]`
- Web page: `[developer.deepx.ai/<path>, fetched 2026-11-05]`
- Always cite the narrowest location you actually read. Never cite something you did not read.

## Pinned sources (cloned 2026-11-05, shallow)

| Repo | Commit | release.ver |
|---|---|---|
| dx-all-suite | 51d81fe2ef | v2.5.0 |
| dx-compiler | a087726ead | v2.5.0 (COM_VERSION=2.5.0) |
| dx-runtime | 73ff9904f5 | v2.5.0 |
| dx_rt (DX-RT) | f997363c97 | v3.5.0 |
| dx_app | 375de0344f | v3.3.0 |
| dx_rt_npu_linux_driver | 8455be6254 | v2.7.0 |
| dx_fw | a72406f3ca | v2.7.6 |
| dx_stream | c575ed2896 | v3.2.0 |
| dx-modelzoo | ab3e3a4234 | v1.0.0 |
| dx-tutorials | 5619593307 | - |

## Hard rules

- Do not invent API calls, config keys, CLI flags, or compiler options. If a source doesn't show it, it goes under Hypotheses or is omitted.
- Code snippets must be copied from sources (with citation), not paraphrased from memory.
- Mark source contradictions explicitly (e.g. two docs disagree on a version).
