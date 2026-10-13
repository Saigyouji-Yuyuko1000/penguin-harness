---
name: skilladam-rsi-toolkit
description: "Optimize an agent's working Skill with SkillAdam (Stable and Efficient Skill Evolution for Agents, 2026): learn from execution feedback, maintain an evolving issue tracker and adapt the edit budget to reward variance. Includes GDPevo training and held-out evaluation."
version: 2026.10.13.3
---

# SkillAdam

Evolve a task-solving agent's Markdown Skill using [SkillAdam: Stable and Efficient Skill Evolution for Agents](https://arxiv.org/abs/2609.08944), v1. The reference implementation is [ruc-datalab/SkillAdam](https://github.com/ruc-datalab/SkillAdam/tree/b6c9640f7a9e0d5e3a500c25bc4e6369eeca78f1). Keep the model and tools fixed: improve the procedures the agent reads before solving a task.

This Skill runs the optimizer. The **Target** is the separate agent that solves benchmark tasks using the evolving working Skill. Only that working Skill is optimized; this controller document stays fixed. GDPevo is the benchmark adaptation provided here; it was not evaluated in the paper.

## The method

SkillAdam starts by observing an agent's executions and generating an initial Skill, S0. It then repeatedly runs the current Skill on a training batch, proposes a small edit from the execution feedback, and evaluates the edited Skill on the same batch. A benchmark-specific acceptance gate decides whether to keep the edit or return to the previous Skill.

Two mechanisms carry information between iterations:

- **Evolving Issue Tracker (EIT).** Maintain a record of problems, supporting evidence and attempted fixes. For example, if an agent repeatedly misreads a required output format, record the failure, the correction tried and whether it helped. Later proposals use this history to build on useful corrections and avoid repeating failed approaches. This plays the role of first-moment memory in the paper's analogy to Adam.
- **Adaptive edit budget.** Compare the candidate's reward with the current Skill's reward on each case. If the changes vary widely across cases, reduce the next edit's allowed size; if they become consistent, the budget can recover. SkillAdam uses a moving average of this variance to set a limit on diff hunks. A hunk is one edit region in a unified diff. The acceptance gate separately checks whether the candidate actually improves performance: consistently harmful changes can also have low variance.

These are operations on text and execution feedback. There are no model-weight gradients or Adam bias-correction steps. Feedback includes the agent's trajectory and evaluation metrics; a benchmark may also provide diagnostic text. The method does not require a reference answer in every feedback packet. The GDPevo adapter here supplies training task context, Target traces and scalar scores.

## Before you start

Resolve the following from the request and the current Environment. Ask only for missing inputs needed to run the experiment.

| Input | How to resolve it |
| --- | --- |
| Target | An existing `test_agent_id` or `create: <id>`, distinct from the controller. The quick start uses `gdpevo_skilladam`. |
| Training Benchmark | Use the selected `benchmark_id`; default to `penguinharness-benchmark-gdpevo-train` when omitted. `train_benchmark_id` is an alias. |
| Training cases | Use an explicit `case_ids` subset when supplied; otherwise use all cases in the training Benchmark. Freeze this reporting set before measuring. |
| Runtime | Use the requested provider/model, or the current Environment's pair. Keep the Target's model, thinking level and tools fixed, and record the proposer and tracker models. |
| Experiment budget | Resolve the iteration count, batch size, repeats and execution ceiling before model calls. Use the GDPevo parameter defaults in `references/gdpevo.md` unless overridden. |
| Held-out evaluation | If included in the experiment, resolve `test_benchmark_id` and its cases now; evaluate them after optimization. The built-in split is `penguinharness-benchmark-gdpevo-test`. |

For GDPevo, read `references/gdpevo.md` to prepare the source-built Penguin bundle, freeze the cases and parameters, and calculate the execution budget. Read `references/initialization.md` to prepare the Target, snapshots and experiment records. These references contain the Penguin setup details; the optimization steps below describe the method.

## Initialize

1. Save the prepared Target without a generated working Skill as **Hraw**. Run it on the Stage 0 training batch and collect task context, execution traces and scores.
2. Make a fresh proposer call with those observations. Ask it to write a concise Markdown Skill containing reusable task-solving procedures drawn from the successes and failures. Save the prompt and reply; use the generated body as **S0**.
3. Install S0 as the Target's working Skill using `references/initialization.md`. Start an empty EIT, set the running variance to zero, and set the first edit budget to `base_budget`.
4. Measure S0 on the frozen training reporting set. Keep Hraw and S0 separate in the results so that initialization gains are distinguishable from later optimization gains.

In Penguin, use `run_subagent` without `agent_id` for a fresh proposer or tracker call. Pass the required text in its prompt and request no tools or file access. The controller supplies observations and applies the returned edits; the Target receives the working Skill when it runs a task.

## Measure

Use `references/evaluation.md`, the same worker protocol and scoreboard format shipped with APE and OPRO. Dispatch the requested Target version, model, case and run index; collect a complete case-by-repeat matrix. The existing Harbor verifier supplies the scores. This Skill does not introduce another grader.

For each comparison, evaluate the current Skill and candidate with the same cases, repeats and runtime. The GDPevo adapter measures the entire frozen reporting set for a comparable learning curve, with the iteration's training batch chosen in advance. Only that batch's results drive the proposal, gate and EIT update. Full reporting-set measurements are an integration choice that costs more than evaluating the batch alone.

Reuse a prior measurement when its state, runtime, cases and repeats match; retain its trial references. Infrastructure failures leave a measurement incomplete and must be resolved before comparison. A completed task with a genuine zero reward remains a scored result. See `references/gdpevo.md` for collecting trace feedback and publishing results to the Evaluation Center.

## Optimize

Repeat the following for the configured number of proposal iterations. Start each iteration from the last accepted Skill, its EIT and the current edit budget.

### 1. Observe the current Skill

Select the training batch using the frozen sampling rule. Measure or reuse the current Skill's results and collect the batch's task context, trajectories and scores. Save the ordered case ids so the candidate is compared on exactly these cases.

### 2. Propose an edit

Give a fresh proposer the current working Skill, the batch feedback, the EIT and the allowed hunk count. A suitable prompt is:

```text
Improve the working Skill using the training observations below.
Use the issue tracker to account for previous attempts. Explain which
observed problem your change addresses and how it should help across tasks.
Write reusable procedures rather than answers to the training cases.

Return one JSON object with string fields "reasoning" and "patch".
The patch must be a unified diff from a/SKILL.md to b/SKILL.md, edit only
the Markdown body, and contain at most <next_budget> hunks.
An empty patch is allowed when you have no supported change to propose.

Current Skill: <complete working Skill>
Training feedback: <batch tasks, traces and scores>
Issue tracker: <current EIT>
```

Save the reply and validate it with `scripts/skilladam.py prepare`; the command is documented in `references/gdpevo.md`. An invalid or unchanged proposal consumes one proposal iteration without changing the Skill, EIT or variance. Otherwise install the prepared candidate and snapshot its new version.

### 3. Evaluate and decide

Evaluate the candidate and pair its scores with the current Skill's scores. The paper allows each benchmark to define improvement thresholds and protected metrics. For GDPevo, `scripts/skilladam.py assess` averages repeats per case and converts percentage scores to rewards in `0..1`. Its gate accepts an edit only when:

- the batch's mean reward gain is strictly greater than `min_gain` (default `0`); and
- no case's reward drops by more than `max_case_drop` (default `0.1`).

Keep an accepted candidate. Restore the previous accepted Skill when the gate rejects it. Save both measured versions and the decision, including rejected candidates.

### 4. Update the tracker and next edit budget

Ask a fresh tracker call to update the EIT using the prior tracker, the attempted edit, paired batch feedback and gate decision. Preserve issue ids and attempted fixes. Record whether each problem remains open, is resolved on the retained Skill, or has returned. A rejected attempt still teaches the tracker what was tried.

For each case, let `delta` be candidate reward minus current reward. The helper computes:

```text
V = beta2 * previous_V + (1 - beta2) * sample_variance(deltas)
scale = 1 - clip(V / variance_cap, 0, 1)
next_budget = max(min_budget, round(base_budget * scale))
```

Sample variance uses `n - 1` in the denominator, or zero for one case. Both accepted and rejected evaluated candidates update `V`, the next budget and the EIT. Save them with the retained Skill as the starting point for the next iteration. The checkpoint and tracker format are in `references/initialization.md`.

## Freeze and report

The final Skill is the **last accepted Skill**. Measure it on the same training reporting set as S0. If held-out evaluation was included in the experiment, freeze optimization first, then evaluate S0 and the final Skill on the same Test cases. Test feedback does not enter proposals or tracker updates, and does not select the final Skill.

Report the initial Hraw batch result, S0 and final comparable scores, accepted and rejected changes, invalid or unchanged proposals, and the variance/edit-budget history. Include case coverage, versions, trial references and known costs, with missing cost information identified. Publish complete reporting matrices through the shared evaluation protocol. Describe the GDPevo sampling, gate and reporting adaptations so readers can distinguish this experiment from the paper's benchmarks.
