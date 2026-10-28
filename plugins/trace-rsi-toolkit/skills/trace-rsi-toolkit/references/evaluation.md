# Launch, collect and report

The outside Organizer owns scheduling and collection. Read the published Case instructions, linked README and adapter contract for exact commands. Use existing Penguin CLI, execution tools or evaluation workers; a worker handles one continuous training trial or one independent test cell, without creating another experiment controller.

## Launch contract

Record benchmark/case, experiment and State version/digest, condition, repetition, runtime, native job/trial paths and process handle. For repository-backed experiments, organizer records live in the experiment's `jobs/` directory; Harbor-managed trials retain their native locations, normally the published Benchmark's `.jobs/`.

Launch training once per unit with the Curator State. After collecting its exports, launch the selected-bank and no-Skill test matrices with the corresponding frozen solver archives. All role launches explicitly bind provider/model/thinking and identity; confirm actual recorded settings. The two test conditions use the same task revision, capabilities, limits and repetition count.

Give repetitions stable indices before execution. A repetition contains one run of every test case; different repetitions may execute concurrently. Each test cell starts in its own fresh environment/session. Respect shared trial concurrency and total container capacity, including sidecars.

Record completion from native results and exported artifacts, not merely process launch or a successful shell exit. Workers return trial identity, result/artifact locations, native status, score, cost and timing evidence. Missing grading is missing, not an invented zero. Follow the benchmark's treatment of task failures and retries, retaining original attempts and linking any authorized replacement.

## Training handoff

Collect H1 and B0…BR task × A matrices, immutable submitted candidates, judge responses, action/selection trajectories, Curator analyses/proposals, stage bank snapshots and publication decisions. Check bank hashes and recompute selection using [training.md](training.md). Keep actual stage scores, including regressions; a running maximum is not a training curve.

Training uses one continuous run by default. Its within-batch task/attempt scores do not provide a standard deviation across independent training runs. Report stage mean, coverage and selected stage separately from the native training verifier score. The latter grades exported answers and does not prove all training phases ran.

Freeze `best_train` selection before reading held-out results. Test the exact exported snapshot. Keep training evidence outside the deployed bank and preserve all stages even when they are not tested.

## Test scores and uncertainty

Follow the benchmark's score scale. For GDPevo convert native rewards in [0, 1] to percentages. Retain unrounded per-case, per-repetition scores; round only displayed results.

For N cases and K complete repetitions, let x(i,r) be case i's score in repetition r:

```text
m(r) = sum_i x(i,r) / N
mean = sum_r m(r) / K
sample SD = sqrt(sum_r (m(r) - mean)^2 / (K - 1))
```

Report `mean ± sample SD` over complete repetition means, as required by the benchmark. For five cases and three repetitions, first obtain three five-case means, then compute their mean and sample SD with ddof=1. Do not average per-case SDs, substitute propagated per-case variances or label SE as SD. For K=1, SD is unavailable.

A per-case row may show that case's mean and sample SD across its K trials. When reporting an equal-weight macro-average across benchmarks, first average benchmark means within each repetition, then compute SD across those aggregate repetition means. Label any alternative weighting. Preserve raw matrices so both levels are reproducible.

Show no-Skill and selected-bank results side by side, their mean difference, selected stage/hash and coverage. An incomplete matrix is preliminary and shows missing cells; do not turn different subsets into a complete comparison. H1 training results do not replace the held-out baseline. Pass@K or all-repetitions success may be supplementary when requested; neither is the mean score.

## Costs, tokens and time

Report training, no-Skill testing and selected-bank testing separately, plus experiment totals and failure/retry overhead. Report Organizer cost separately when available. Sum distinct model calls; parent totals that already include children must not be added to the same child totals again. Unknown cost is unavailable, not zero.

Preserve native cost and token fields with their semantics. Separate uncached input, cached input and output; total input is cached plus uncached input, and total tokens are total input plus output. Harbor input counts may already include cache reads, so do not add them again. Include reasoning tokens only according to the provider's output-token accounting. Explain any normalized pricing separately from recorded provider cost.

Use native start/end timestamps for wall-clock duration; separate Agent execution time when available. Summed trial durations measure consumed trial time, not elapsed experiment time under parallelism. Report actual completed phases, outstanding work and failed attempts rather than estimating completion from a process being absent.

## Evaluation Center

Resolve the Project App Data Dir from the Environment:

```text
STATE      = <app_data_dir>/agents/<agent_id>/agent_state
BENCHMARK  = <app_data_dir>/benchmarks/<benchmark_id>
SCOREBOARD = BENCHMARK/scoreboard.yaml
```

Append one evaluation per complete State/case/repetition matrix using the existing schema. Preserve existing entries; serialize writes when workers finish concurrently. Use the published Case ids, actual runtime and frozen State version. Do not label a case subset as a whole-Benchmark evaluation.

```yaml
evaluations:
  - time: <UTC ISO timestamp>
    agent_id: <solver id>
    version: <frozen State version>
    provider: <actual provider>
    model_id: <actual model>
    thinking_level: <actual thinking>
    summary_title: <experiment version and condition>
    summary: <coverage and native result references>
    score: <mean case score, 2 decimals>
    cost: <mean of known case costs, 6 decimals, or null>
    duration_ms: <mean case duration, integer>
    cases:
      - case: <published case id>
        score: <mean run score, 2 decimals>
        cost: <mean of known run costs, 6 decimals, or null>
        duration_ms: <mean run duration, integer>
        runs:
          - score: <normalized native score>
            cost: <native run cost or null>
            duration_ms: <native duration in milliseconds>
            session_id: "harbor:<native trial directory>"
```

These scoreboard cost/duration fields are averages; keep experiment totals, SD calculations, tokens, selection evidence and detailed resource accounting in the report. A continuous Train Case has one native run; internal Actor batches remain in training records, not fabricated scoreboard repetitions.
