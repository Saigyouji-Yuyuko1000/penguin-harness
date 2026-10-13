# SkillAdam skill evolution toolkit

- **Date:** 2026-10-13
- **Type:** feature
- **Scope:** `skills`, `docs`
- **PR:** [#1](https://github.com/Saigyouji-Yuyuko1000/penguin-harness/pull/1)

[中文版](2026-10-13-skilladam-rsi-toolkit.zh.md)

Added a local `skilladam-rsi-toolkit` plugin package with one controller Skill for evolving a Target's working Skill from execution feedback.

## Evolution and evaluation

The Skill explained the paper's initialization, evolving issue tracker and variance-controlled edit budget, followed by instructions for proposing edits, comparing results and accepting or reverting candidates. It included deterministic patch and score validation helpers and a GDPevo workflow with separate training and held-out evaluation. Penguin setup details were kept in reference files, and experiment size was resolved from the requested budget.

Evaluation used the same worker protocol and scoreboard format as OPRO and APE. The Evaluation Center's selected Benchmark was passed through explicitly. Complete baseline and candidate results were recorded on a frozen case set with coverage labels; a reporting helper rejected missing cells or changed coverage. Minibatch decisions used the corresponding subset of the reporting measurements. GDPevo sampling and acceptance rules were identified as adaptations, and source-bundle preparation and per-trial feedback receipts were documented.

The package was made available for local import. Registration in the default npm plugin library was left outside this change.
