# Evo-Harness RSI Toolkit

Run Evo on an installed Project Benchmark by name or package path:

> 使用 GDPevo DataAnalysis 进行 Evo RSI，沿用本项目已有模型和预算，训练一次，冻结后完成 Base／Skill 三轮测试。

The controller resolves the selected package's Train/Test mapping and follows its
documented task sources and runner. Source revisions are fixed before launch.
The plugin supplies learning instructions and a standard-library Python helper
for batch decisions, independent Skill folders and measured score reports.
It uses existing `run_subagent`, `input_subagent`, Agent State and evaluation
interfaces. No additional hooks or Harness runtime patches are required.

The learning method retains the `.6` baseline: negative feedback reaches the
original Solver conversation, then one independent Evolver compiles the batch.
All matching topic bodies and all general descriptions are loaded. Each domain
trains once; both frozen States receive three complete test repetitions.

Training requires authorized feedback while the original Solver Session is
still available. A verifier that runs only after that Session is destroyed
supports frozen evaluation, but cannot supply Evo's in-session reflection.
Report that missing capability before training. Do not substitute a new Agent.

This is an instruction-based plugin. The helper checks data structure, references,
loading size and measurement completeness; it does not enforce tool permissions
or prove that an Agent followed the learning method. Inspect native traces for
that evidence. Historical experiment tooling and archives are outside this
package. A real model-backed experiment is separate from its local tests.

Run local tests with `pnpm --filter @penguinharness/evo-harness-rsi-toolkit test`.
See [the controller](skills/evo-harness-rsi-toolkit/SKILL.md) for the workflow.
