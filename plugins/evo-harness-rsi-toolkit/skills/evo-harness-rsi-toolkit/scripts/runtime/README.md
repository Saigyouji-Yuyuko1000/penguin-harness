# Evo benchmark binding v2

This is a deterministic adaptation layer for Penguin’s main Agent, not a runner.
It never invokes models, Harbor, learning roles, or a next stage. The main Penguin
reads the Evo Skill and owns the full experiment through native workers.

The method starts from actual .6 commit `1b56cb777e515564fd6b2059818ae165242bb560`.
Learning roles, reflection, compilation operations and loading policy stay .6;
engineering version is `2026.10.28.6`. Roles/algorithm file hashes are recorded
separately from the combined Harness and Benchmark commits.

Use the installed Skill’s `references/adapters.md` first. `benchmarks.py` reads
public packages/task manifests and freezes repository refs and explicit mappings.
Verify actual Project imports, then save its ready bootstrap plan. One total budget
is split across the plan’s contracts; per-benchmark budgets require that explicit
scope. Never replicate one total authorization into several independent budgets.

`protocol.py` operation `prepare-config` requires `plan`, `plan_sha256`, `contract`
(the returned benchmark name), `repo`, `project`, `evo_tool`, `output`, and existing
public deployment `settings`. It derives Agent and experiment Benchmark IDs, Case
mappings, paths, member roster and allocated budget. Missing nested configuration
is returned together; no old CLI version or model is silently inherited. Preserve
source package IDs separately from registered experiment aliases and source commit.

The continuous adapter executes exactly one training Case/container, with the
manifest’s sequential members and original-Solver reflection, then one Evolver,
export/freeze, complete Base matrix and complete final matrix. `prepare-trainer`,
`pack-state`, `prepare-benchmarks`, `verify-benchmarks`, export/freeze verification
and original-trial matrix validation are the existing requested single operations.
Snapshot tar entries are rooted at `agent_state/`; Harbor transport entries are
rooted at the State contents. Vault, memory and schedule are excluded consistently.

Native Workspace uses the installed `workspace.py` prepare-profile/prepare-solver/
prepare-feedback/capture/prepare-export operations and the same data compiler and
State/evaluation helpers. Its held-out roster, original Session continuation and
loading policy must be bound before learning. A post-exit-only Harbor verifier
supports frozen evaluation but lacks original-Solver live learning; state this
limitation instead of substituting a fresh reflection Agent.

A branch/tag package statement is resolved to the pinned execution checkout at
preparation. Runtime bindings retain original public statements and rubric bytes,
never use a mutable ref during an experiment, and do not overwrite source Project
Benchmarks or earlier scores. Unknown costs stay null/pending with reservations;
whole training-trial costs already contain child roles. Native scoreboard schema
is unchanged. All old results and verdicts remain historical; no retrospective
compatibility pass replaces them.

Offline and zero-model checks do not demonstrate score improvement or a paid
end-to-end experiment. Use only authorized training evidence for learning.
