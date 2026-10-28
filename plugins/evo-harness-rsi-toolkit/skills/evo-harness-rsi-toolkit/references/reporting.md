# Fixed-Skill repeated testing

Train each domain once and compile once. Freeze its Skill and configuration, then
run three complete test repetitions for Base and Skill. Repetitions use fresh
Sessions and environments but the same frozen State. Do not repeat learning or
change the Skill between tests. An explicit different test count must be frozen
before execution; it does not change Evo's learning algorithm.

For domain d and repetition r, compute score s[d,r] using the benchmark's declared
aggregation. For GDPevo this is the mean of all five task scores. On a common
score scale, compute each complete round's overall score first:

    A[r] = mean(s[d,r] for every domain d in the frozen roster)
    mean = sum(A) / R
    sample_variance = sum((A[r] - mean)^2) / (R - 1)
    sample_stddev = sqrt(sample_variance)

For the six-domain, three-test experiment, the three observations are A[1], A[2]
and A[3], each averaging all six domains. Calculate Base and Skill separately;
also report their paired per-round differences. Preserve each domain's individual
round scores, mean, sample variance and sample standard deviation. Do not pool
all tasks or all domain-round scores as independent observations of the overall
score. One repetition has undefined sample variance/stddev (null, not zero).

This measures test execution variation for fixed learned Skills, not variation
across independent training runs. Domain averaging can reduce observed variation;
it does not guarantee a smaller variance or establish improvement. Retain all low
scores and original validation verdicts. An incomplete domain/round is missing,
never zero; do not report a full-roster summary until every planned cell exists.
Do not select best rounds or combine different frozen Skills.

For native arithmetic-mean, 0–100 matrices, use
`python3 -B "$SKILL_DIR/scripts/runtime/statistics_report.py" REQUEST.json`.
The request contains `common_scale: "0-100"`, `runs: 3`, and `domains`, one object
per frozen domain: `benchmark`, `base`, `skill`. The latter two are paths to the
existing native `matrix` request JSONs (case roster, identity and cells). The
helper preserves identities, input hashes, case scores and pending costs; it
does not replace original Harbor/State acceptance or launch any work. Benchmarks
with another aggregation use that declared rule to produce s[d,r] before the
same round-first statistics; do not silently average their tasks.

## Versions and resource records

Freeze an experiment/report ID and the resolved Harness, runner, benchmark package
and source commit, Evo method, provider/model and actual thinking parameters.
Record each frozen Skill and State digest. Missing provider model revision is
unknown, not an invented revision. Keep these in the report request's `versions`.

Keep Train and Test separate. For Train, record the single continuous trial that
produced the Skill and its actual per-task feedback; Evo has no repeated candidate
training curve. For Test, retain every case, repetition and Base/final identity,
including failed attempts. No additional training is required for reporting.

Add `measurements` to the statistics request: one entry per actual native trial,
with `phase` (`train` or `test`), `benchmark`, `state`, `run`, `case_id` and
`trial_result` (the original Harbor result.json). The helper reads cost, timestamps,
elapsed time and usage from that artifact, preserves its hash and rejects duplicate
trial identities. Its Train/Test totals keep unknowns as null plus known subtotals.
Retain native per-session usage artifacts alongside those records. Harbor
`n_input_tokens` includes `n_cache_tokens`; uncached input is their difference
only when both exist. `n_output_tokens` already includes reasoning. Penguin
`cacheRead`, `cacheWrite`, `output` (or token-record snake_case names) provide the
corresponding cached, uncached and output breakdown when available; never add the
session breakdown again to trial totals. Do not invent missing costs or token counts.

Record host controller and worker overhead separately from container trial costs;
count each underlying Session once, and exclude children already included in a
parent/trial total. Keep pending budget reservations until costs settle. Report
actual experiment start/end/wall time separately from summed parallel durations.
The reporting helper collects evidence; it does not rescore or turn a diagnostic
run into a valid experiment.
