# Prepare the selected Benchmark

Read `benchmark_config.toml`, the Case `statement/README.md` files and their
linked task manifest and runtime README. These determine the Train/Test mapping,
source revision, native task path, installation, feedback route, answer paths,
Skill export and scoring. A combined Train Case may contain several questions;
it is one learning trial, not one trial per question. Resolve aliases such as
`024` from documented IDs and descriptions; if ambiguous, report the candidates.
Do not infer a source directory from the number or hardcode a GDPevo-only path.

Follow the installed package's source links. A built-in package can contain run
descriptions while its data and environments live in the linked repository.
Fetch the documented resources once at the requested revision, or resolve the
documented branch/tag once and record its commit. Reuse that checkout throughout
the experiment. Do not introduce an additional benchmark checkout; if the actual
package still requires an intermediate repository, report that dependency rather
than silently substituting different tasks or graders. Preserve native task
conversion, split and scoring behavior.

Use the current CLI, model connection and documented adapter. Keep credentials
inside its supported private transport. Check Docker/runner availability,
source checkout, output paths and feedback capability before training. Evo needs
the complete authorized grade delivered to the original Solver before its
Session ends, or through `input_subagent` continuing that same Session. A
post-exit-only verifier cannot replace this capability. Never self-score a
failed grader or create a new Reflector to reconstruct the conversation.

Record the experiment version, Harness/runner/toolkit versions, actual source
commit and package hashes, model/thinking level, training roster/order, topic,
negative-feedback predicate, limits, budget, repetition count and output paths.
Keep a job index with phase, benchmark, State digest, case, repetition, native
job/Session ID and completion status. Do not overwrite earlier experiment data.

## Common base and training State

Use the requested base Agent or create a separate one through the native CLI:

```bash
penguin agent create --agent-id <unused-id> --project-id <project-id> --json
```

Freeze the common base before installing learning instructions. Disable memory,
schedules and state-mutating hooks; record the effective runtime and limits.
Make an isolated training copy. Install `training.md` as its training Skill,
`roles.md` beside it and `scripts/evo.py` in that Skill's scripts directory.
Add `training-request.json` and `benchmark-training.md` at the training State
root. The brief contains only public training inputs, business tools, allowed
feedback route, scale/predicate and output paths. Private grader files, held-out
tasks and credentials do not belong in the brief. The request records the
frozen setup above, starting with an empty library unless a base was requested.

The training State's `AGENTS.md` tells its main Target to read those two files
and its training Skill, then coordinate exactly one batch. Delegated Solvers
follow only their task and reflection roles; they do not start another learning
controller. Use inline `prompt` with full role text, explicit provider, model_id
and thinking_level on `run_subagent`. Do not use nonstandard prompt-file,
working-directory or permission arguments. Children share the parent workspace;
give each its own output paths and serialize access to shared business state.

## Export and frozen test States

The helper's `export` command writes a fresh package directory and returns its
file hashes, byte count, exact topic `context` and `context_sha256`. Copy only
that package into the final test State's `skills/`. Insert the returned context
verbatim in a delimited `AGENTS.md` block before taking the State snapshot.
Use the same rendering for every task of that topic; do not retrieve or clip
entries per task. Keep automatic extra Skill discovery disabled in these
experiment States (`skills.enabled: false`); the complete learned context is
already in the initial system prompt. Verify the actual prompt against its
hash in native records. Baseline uses the same reader with an empty library.

Build both test States from the same common base. They receive no training
Skill, private library, candidates, grader material, answers, conversations or
memory. Keep all independent exported methods plus Reader/manifest within the
16,000-byte limit; the helper rejects overflow without dropping methods. Keep
private general bodies only in learning artifacts. Record State versions and
archive hashes; reuse the exact frozen archive for each case/repetition.

For a Harbor State handoff, pack the State contents at the archive root, omitting
vault, memory and schedules. Supply its existing adapter arguments as the
benchmark README specifies; install bundles are needed only when that runtime
requires one. Do not put an enclosing `agent_state/` directory inside the tar.
Test States are immutable throughout measurement.
