# Evo-Harness RSI Toolkit

Version `2026.10.28.6` retains learning commit `1b56cb777e515564fd6b2059818ae165242bb560` (.6): negative feedback in the original Solver Session, one batch Evolver, and topic bodies plus general descriptions. No candidate retest or score gate is added.

Install the complete plugin (Skill and hooks) in a compatible Harness. This checkout includes the required native `prompt_file`, scoped Solver hooks and lifecycle-wait interfaces; copying only the Skill into a stock installation does not supply them. Evo's protocol/registration/acceptance tools ship in this plugin's `scripts/runtime/`; the official Benchmark repository is fetched as an unmodified resource cache, not an Evo-specific checkout. Install host Python 3.11+ and `python3 -m pip install -r skills/evo-harness-rsi-toolkit/scripts/requirements.txt`. Credentials stay in the Project's existing secure configuration.

With the Project's experiment settings and imported packages selected, tell the main Penguin:

> 使用 GDPevo CRM 子集进行 RSI，沿用本项目已有实验配置。

The deterministic `scripts/resources.py` entry reads installed packages and `evo-experiment.json`, fetches each declared official source, and locks its actual commit and content inventory. It follows [the adapter guide](skills/evo-harness-rsi-toolkit/references/adapters.md), pins the repository commit, checks the actual Project copy, prepares configuration. The main Penguin owns the native learning/evaluation workflow. Source paths and launch arguments are derived without user script edits. Missing domain, train/test split, runtime or budget inputs are collected once. One controller binds one resolved domain.

| Backend | Learning capability | Validation delivered |
| --- | --- | --- |
| GDPevo | One continuous training Case; original Solver reflection; independent test Cases | Actual manifest integration and zero-model native loading |
| Workspace | Original native Solver feedback continuation | Synthetic native Session and capture/compile/export |
| Other Harbor with only a post-exit verifier | Frozen evaluation; full learning requires a live-feedback adapter | Package discovery and explicit pre-dispatch capability rejection |

No paid autonomous end-to-end run or score improvement is claimed. A post-exit-only Harbor backend is not made compatible by substituting a new Reflector. Keep its learning request blocked until an adapter can supply complete authorized feedback to the original Solver; evaluation results remain usable within their declared scope.

Project identity checks include all non-dot regular files in native `CASE-*` trees and non-origin manifest values. Private grading attachments are hashed, never placed in learner prompts. Native import metadata and runtime scoreboards/jobs are excluded. New verification records do not replace historical experiment verdicts.

Historical .6 packages are verified in their original byte format, including the old absolute read-plan paths. Read-plan relocation returns new calls only; it does not edit the package or State. A compatibility report preserves the original experiment identity and verdict, and does not regrade scores or change costs. Unknown older layouts and missing raw evidence remain explicitly unsupported.

The built-in GDPevo domain pairs and Sec A–E keep their own official source and
runner settings. No dataset conversion or scoring code is copied into this
plugin. The SkillAdam plugin from PR #1374 remains separate: Evo does not use its
S0 initialization, candidate retests or score acceptance gate. Each domain trains once; its frozen Base and learned State are tested three
times by default. Aggregate domains within each complete repetition before
computing mean, sample variance and sample standard deviation; keep domain
results separately. See [reporting](skills/evo-harness-rsi-toolkit/references/reporting.md).

For a native Workspace package not previously known to Evo, supply its path and
the held-out package in the public experiment configuration. Workspace packages
need no Git repository; their complete file/configuration hashes are frozen.
For a new Harbor package, native Case source/launch metadata is resolved in the
same way. A post-exit verifier still needs an original-session feedback adapter
before it can perform Evo learning. An available launcher is not that adapter.
