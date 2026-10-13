---
name: skilladam-rsi-toolkit
description: "Optimize an agent's working Skill with SkillAdam (Stable and Efficient Skill Evolution for Agents, 2026): use execution feedback, an evolving issue tracker and a variance-controlled patch budget. Includes GDPevo training and held-out evaluation."
version: 2026.10.13.2
---

# SkillAdam

Implement the skill-evolution loop from [SkillAdam: Stable and Efficient Skill Evolution for Agents](https://arxiv.org/abs/2609.08944), v1, with reference code at [ruc-datalab/SkillAdam](https://github.com/ruc-datalab/SkillAdam), revision `b6c9640f7a9e0d5e3a500c25bc4e6369eeca78f1` (`skilladam/core/edit_budget.py`, `acceptance_gate.py`, `momentum.py`, `feedback_loop.py`). Model weights, tools and runtime stay fixed. Optimize one Target-owned Skill document. This controller Skill never rewrites itself.

The evolving issue tracker (EIT) preserves problems, evidence and attempted corrections across iterations. A moving average of the variance of per-case reward changes controls the next patch's hunk budget. This is a functional analogy to Adam; do not add numerical gradients, a first-moment coefficient or bias correction. GDPevo is an adaptation; the paper does not report results on it.

## Before you start

This controller needs `run_subagent`. If unavailable, report that a top-level Session must run the Skill. Resolve the Target and authorized execution budget before starting model calls. Ask only for required inputs the request and Environment do not supply:

- `test_agent_id`: an existing Agent or `create: <id>`, distinct from the controller. The quick start creates `gdpevo_skilladam`; an existing directory requires another id or a verified resume.
- `benchmark_id`: the training Benchmark selected in the Evaluation Center, default `penguinharness-benchmark-gdpevo-train` only when omitted. Accept `train_benchmark_id` as an alias; if both are supplied they must agree. Record and dispatch the resolved value as `benchmark_id`. Never replace a supplied Benchmark with the default. Reject a Test split as optimization input.
- `case_ids`: the fixed reporting/training pool. Honor an explicit subset after validating membership and sampling coverage. Otherwise smoke selects six training cases, one per environment; full uses every training case. Freeze the list before any scores exist.
- `test_benchmark_id`: default `penguinharness-benchmark-gdpevo-test`, used only in the full profile, after optimization ends.
- `provider` and `model_id`: the explicit pair, else this Session's Environment pair. Fix the Target's `thinking_level` as described in `references/evaluation.md`. Record the proposer and tracker model too; do not silently switch models.
- `profile`: `smoke` by default, or `full` when requested. Smoke uses two iterations and one run per case unless supplied. Both profiles measure each published candidate on the same fixed `case_ids`; full uses a sampled subset of those measurements for its optimization gate and measures S0 and the final Skill on held-out Test after evolution. An explicit subset remains a subset even in full mode.
- `install_bundle`: a local, source-built Penguin bundle for Harbor; see `references/gdpevo.md`. Resolve this prerequisite before any paid evaluation.

Freeze these parameters in `OUT/experiment.json` before Stage 0:

| Parameter | Default | Meaning |
| --- | --- | --- |
| `iterations` | 2 | Maximum proposal iterations, including invalid or empty proposals |
| `batch_size` | 6 | One training case per GDPevo environment |
| `runs` | 1 | Repeats of each case; fixed across both sides of a comparison |
| `seed` | 42 | Reproducible sampling, independent of outcomes |
| `base_budget`, `min_budget` | 4, 1 | Maximum and minimum diff hunk counts |
| `beta2`, `variance_cap` | 0.9, 0.1 | Variance EMA and budget saturation point |
| `min_gain` | 0.0 | Strict improvement in mean reward on the `0..1` scale |
| `max_case_drop` | 0.1 | Largest allowed drop in any paired case mean, on `0..1` |
| Harbor concurrency | 4 | Respect a lower user limit; never exceed 8 |

The sampling, profiles and gate above are explicit GDPevo choices, not published GDPevo hyperparameters. User-specified values replace them before measurement, never in response to Test results. A custom batch size must be a positive multiple of the six environment groups, within the available cases. A non-GDPevo Benchmark needs an explicit sampling map and score adapter; do not infer them from private answers.

Read `references/initialization.md` for Target preparation, snapshots and recovery. Read `references/gdpevo.md` for the benchmark split, source bundle, feedback and reporting. Like OPRO and APE, this Skill dispatches workers using its own byte-identical `references/evaluation.md` and appends complete fixed-case matrices through that protocol; it does not require the `agent-evaluation` plugin. The native Harbor verifier remains the scorer.

## State and budget

Resolve `PROJECT_DIR` from the Environment's App Data Dir, `TARGET = PROJECT_DIR/agents/<test_agent_id>` and `STATE = TARGET/agent_state`. The learned document is `STATE/skills/skilladam-working-skill/SKILL.md`. Put all optimizer data outside the Target:

```text
OUT = PROJECT_DIR/agents/<controller_id>/scratchpad/<session_id>/skilladam-rsi-toolkit/<UTC timestamp>-<target_id>/
  experiment.json        # immutable inputs, runtime, split, hashes, source revisions, adaptations
  state.json             # last completed iteration, accepted snapshot, variance, next budget
  stage0/                # raw baseline, seed prompt and generated S0
  iterations/<number>/   # batch, baseline/candidate cells, feedback, prompts, patch, decision, EIT
  reports/               # fixed-panel or full Train/Test measurements and final report
```

Record the installed controller Skill's version/hash, helper hash, target state hashes, benchmark statement hashes, case/group lists, source bundle hash and source commit. Save every proposal, tracker update and failure. Keep the complete records; the prompt may use a condensed tracker with stable issue ids and evidence references.

State the maximum number of Target executions before running: `R * (I + (2*T + 2)*C_train + 2*C_test)`, where I is the Stage 0 panel size, T the iteration count and C the frozen reporting sets. Smoke has I=C_train=6, C_test=0: at most 42 executions with defaults. Full with 30 Train and 30 Test has at most 246. Full-case candidate reporting is a declared evaluation-cost adaptation; only the sampled batch drives its gate. This excludes proposer/tracker calls and setup; report their costs separately. Reuse a complete measurement only when the State version/hash, case set, runs, runtime and source bundle all match; keep the original trial references and do not append it again. Skipped proposals also reduce the total. Respect any user ceiling; do not silently broaden smoke into full evaluation or run OPRO/APE comparisons.

## Stage 0: initialize from execution

1. Snapshot the unmodified Target as Hraw. Evaluate the fixed Stage 0 training panel with the frozen runtime and collect its public task context, Target trajectories and scalar rewards. No generated working Skill is installed yet. If this panel equals the reporting set, publish its complete matrix; otherwise keep it as a seed diagnostic in OUT, clearly distinct from a reporting evaluation.
2. Make one fresh proposer call (no `agent_id`, no tools or file access) with those observations: ask for a concise Markdown skill body of reusable task-solving procedures, grounded in repeated successes and failures. Exclude task-specific answers, private grading logic and test information. Save the exact prompt and reply. A missing or unusable reply stops initialization; do not substitute a seed invented by the controller.
3. Wrap the body in the fixed working-Skill frontmatter from `references/initialization.md`, install the fixed reader, allocate a new State version and snapshot S0. Initialize an empty EIT, `variance = 0` and `next_budget = base_budget`. Measure S0 on the fixed reporting Train set. Hraw and S0 are separate baselines; Stage 0 gains are not iterative gains.

## Iterate

For each iteration, start from the last accepted snapshot and its committed EIT/variance. Nothing else writes the Target while a matrix is running.

1. **Baseline.** Select the training batch deterministically using `references/gdpevo.md`. Save its exact ordered case ids. Measure or reuse the current Skill's complete reporting `case_ids` × runs matrix, publish a new complete measurement, and save `before.json`. Bind feedback only for the sampled batch. Incomplete or mismatched measurements have no score; stop and retain the last accepted state.
2. **Propose.** In a fresh tool-free proposer call, provide the exact current working Skill, current training tasks/trajectory feedback, the previous EIT and `next_budget`. Ask for a JSON object with exactly `reasoning` and `patch` strings. The patch is a unified diff of `a/SKILL.md` to `b/SKILL.md`, at most the allowed hunks, editing only the body. An empty patch is permitted. Ask for reusable corrections and evidence links; prohibit inserting answers or optimizer records. Do not show previous candidates outside the recorded tracker, private rubrics or Test data. Save the raw reply; do not repair its patch yourself.
3. **Validate.** Parse the reply as one JSON object, then run `scripts/skilladam.py prepare` as documented below. Invalid JSON, an invalid patch, changed frontmatter or an exceeded budget spends this iteration but changes neither the Skill nor EIT, variance or next budget. An empty/no-change patch is a recorded no-op with the same behavior, a declared evaluation-cost adaptation.
4. **Candidate.** Publish the prepared document, advance its date version and allocate a new State version. Snapshot before measuring. Evaluate it on exactly the same reporting cases and run indices as the baseline, with the same runtime and source bundle. Save `after.json` and publish the complete matrix, including a candidate later rejected by the gate. Record the candidate's hashes after version metadata is advanced. A launch failure is not a zero reward and cannot enter the gate.
5. **Gate and budget.** Run the helper's `assess` command with `--case-ids` naming the frozen iteration batch. It validates both full reporting matrices, then uses only that batch: averages repeats within each case, divides percentage scores by 100, calculates per-case candidate-minus-baseline deltas and their sample variance, then updates `V = beta2*V + (1-beta2)*variance(deltas)`. Next budget is `max(min_budget, round(base_budget*(1-clip(V/variance_cap, 0, 1))))`. Accept only if mean reward gain is strictly greater than `min_gain` and every case drop is within `max_case_drop`. A tie is rejected. Save the complete decision. Do not use the remaining reporting cases to change the gate, proposal, tracker or next batch.
6. **Tracker.** Make a fresh tool-free tracker call with the prior EIT, the two measured versions' training feedback, proposed approach and actual gate decision. Preserve stable issue ids; record evidence, status (`open`, `resolved`, `reopened`) and attempts (`iteration`, `approach`, `gate_accepted`, outcome references). Retain rejected attempts. Resolve a problem only with evidence on the accepted state; a rejected candidate's success does not resolve the live Target's problem. Validate the structured update and save it before committing the iteration.
7. **Commit.** If accepted, retain the candidate snapshot; otherwise restore the previous accepted snapshot exactly. In either case, commit the new tracker and computed variance/budget for the next iteration. Update `state.json` atomically with the completed iteration and evidence hashes. Invalid proposals and incomplete measurements never perform this step. If the tracker update fails, retain the pending decision and stop; resume that step rather than rerunning paid evaluations.

The final Skill is the last accepted state. Scores from different minibatches cannot rank candidates; do not pick a global winner by minibatch score. Do not import another optimizer's selection or early-stopping rule.

## Deterministic helper

Python 3 standard library only. Resolve `SKILL_DIR` to the installed directory containing this `SKILL.md`; all output paths below are new files under OUT. The helper does not edit the Target, its snapshots, the tracker or the scoreboard.

```bash
python3 "$SKILL_DIR/scripts/skilladam.py" prepare \
  --skill "$STATE/skills/skilladam-working-skill/SKILL.md" \
  --proposal "$ITER/proposal.json" --budget "$NEXT_BUDGET" \
  --output "$ITER/prepared.md"

python3 "$SKILL_DIR/scripts/skilladam.py" assess \
  --before "$ITER/before.json" --after "$ITER/after.json" \
  --case-ids <the frozen batch's full CASE-directory names> \
  --previous-variance "$PREVIOUS_VARIANCE" --beta2 0.9 \
  --base-budget 4 --min-budget 1 --variance-cap 0.1 \
  --min-gain 0 --max-case-drop 0.1
```

Replace numeric flags with the frozen experiment parameters. Save stdout as the result only on exit 0; exit 2 means invalid input, never a scored rejection. `prepare` reports `ready` or `noop`; a no-op creates no output. `assess` emits both the acceptance decision and the next budget, including for valid rejected candidates. `report` validates a matrix against the frozen reporting specification and formats the existing worker scores for the scoreboard; it never grades answers or writes the scoreboard. Matrix and reporting schemas are in `references/gdpevo.md`.

## Freeze and report

Measure the final accepted state on the same reporting Train set as S0. In full mode only, with evolution finished, measure S0 and the final state on the frozen Test set, then finish with the final accepted snapshot restored. Neither Test scores nor Test traces go to the proposer or EIT; Test results never select a winner.

Report Hraw's panel score, S0 and final fixed-set scores, accepted/rejected/invalid/no-op iterations, per-case changes, variance/budget history, exact versions/hashes, trial references, total known costs and unknown cost components. Publish complete frozen reporting matrices, including smoke, to the Evaluation Center using `references/evaluation.md`. Give all records the same experiment/coverage label; partial matrices and sampled gate diagnostics remain in OUT. State the adaptations and coverage, and say when there is no improvement. Do not claim a reproduced paper result or a full GDPevo result from a six-case smoke run.
