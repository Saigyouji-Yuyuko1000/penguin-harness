# Target state and recovery

Resolve `PROJECT_DIR` from the Environment's App Data Dir, `TARGET = PROJECT_DIR/agents/<test_agent_id>` and `STATE = TARGET/agent_state`. The learned document is `STATE/skills/skilladam-working-skill/SKILL.md`. Store optimizer records in the controller's scratchpad:

```text
OUT = PROJECT_DIR/agents/<controller_id>/scratchpad/<session_id>/skilladam-rsi-toolkit/<UTC timestamp>-<target_id>/
  experiment.json        # frozen parameters, cases, runtime and source identities
  state.json             # accepted snapshot, completed iteration, variance and next budget
  stage0/                # Hraw observations, initialization prompt and generated S0
  iterations/<number>/   # batch, measurements, feedback, proposal, decision and EIT
  reports/               # comparable Train/Test results and final report
```

The optimizer's OUT is outside the Target, so its issue tracker, scores and candidate history never become Target instructions. Resolve identifiers within the current Project. Record the installed controller Skill version/hash, helper hash, Target state hashes, benchmark statement hashes, case/group lists, source bundle hash and source commit. Keep the full tracker history; prompts may use a condensed copy with stable issue ids and evidence references.

## Prepare the Target

For `create: <id>`, require that `PROJECT_DIR/agents/<id>` does not exist. An Agent id starts with a lowercase letter, followed by 1 to 63 lowercase letters, digits or underscores. Create it through the CLI so the server registers it:

```bash
PROJECT_DIR="<app_data_dir>"
PROJECT_ID="$(basename "$PROJECT_DIR")"
PENGUIN_HOME="$(dirname "$PROJECT_DIR")"
export PENGUIN_HOME
penguin agent create --agent-id "<id>" --project-id "$PROJECT_ID" --json
```

Use an empty plugin set for a fresh Target, and set `memory.enabled: false` and `hooks.enabled: false` in its `agent_state/system_config.yaml`, updating existing keys rather than adding duplicates. Fix `model.thinking_level` to the declared level. Ensure `memory/user/MEMORY.md` exists before hashing, since the harness would otherwise create it at Session start. These settings are part of Hraw and every later measured state.

For an existing Target, snapshot its original state before preparation. Do not overwrite a working Skill slot from another experiment. Resume a slot only with matching experiment, runtime and hashes; otherwise use a fresh Target. If freezing it requires changes to unrelated user behavior that the request does not authorize, explain those changes and resolve them before measuring. Record any authorized preparation as part of the baseline rather than attributing it to SkillAdam.

## Versions and snapshots

Read `version` as a positive integer from `system_config.yaml`. Before each new state, allocate one more than the largest current version, snapshot version, scoreboard version and previously allocated experiment version, including abandoned candidates. Never reuse a number. Candidate versions may increase even when the accepted version is older after rollback.

Snapshot every state before measurement to `TARGET/snapshots/v<N>.tar.gz`, containing `agent_state/` but excluding `.vault.toml`. Refuse an existing archive unless its contents match the recorded state. Build a new archive at a temporary path and rename it only after success. Record its SHA-256 and a deterministic digest over relative file paths and contents, excluding the vault. Hash the state before and after each matrix; any change invalidates the matrix and stops the run after restoring the accepted snapshot.

Hraw has no generated working Skill or new reader line. After Stage 0, wrap the seed body in this frontmatter (use the actual date):

```markdown
---
name: skilladam-working-skill
description: The working procedures this agent applies to its tasks.
version: YYYY.MM.DD.1
---

<generated skill body>
```

Require UTF-8 with LF line endings and a final newline. Append this fixed line to the Target's `AGENTS.md` once:

```text
Before substantive task actions, read skills/skilladam-working-skill/SKILL.md in your Agent State in full and apply its procedures within the current task's access and output requirements.
```

During evolution, only the working Skill body, its date version and the State version change. Its name/description and the reader line stay fixed. The helper enforces unchanged frontmatter during patch application; the controller advances only the version metadata after that check. Record both the prepared-document hash and the installed version's actual hash. The controller Skill, tools, other skills, runtime configuration and AGENTS.md remain frozen.

## Commit and resume

The EIT starts as `{"issues": []}`. Each issue has a stable `id`, `description`, `status`, `evidence` references and an append-only `attempts` list. Each attempt records `iteration`, `approach`, `gate_accepted` and `outcome_refs`. Accept only `open`, `resolved` or `reopened` as issue statuses, unique ids, references to this experiment's training artifacts and an actual Boolean gate decision matching the saved assessment. Prior issues and attempts cannot disappear from an update. A resolution needs evidence on the state retained by the gate. An unsupported update stays pending; retain the previous committed tracker and decision artifacts for repair.

`OUT/experiment.json` fixes parameters, identities, train/test case lists and statement hashes, Stage 0/reporting panels, runtime, source bundle and controller/helper hashes. `OUT/state.json` references the accepted snapshot and the last completed iteration's decision/tracker. A completed iteration has an integer index, accepted state version/hash, nonnegative variance, next integer hunk budget and tracker path/hash. Initial state is iteration 0, S0, variance 0 and the base budget.

Before publishing a candidate, save a pending record with the previous accepted snapshot, batch, candidate version and phase. Save measurements and helper decisions before any update to `state.json`. Write the new checkpoint to a sibling temporary file, flush it, then use `os.replace` to commit. Store the new EIT as a separate immutable iteration file, so an interrupted update cannot overwrite the previous committed tracker.

On resume, check the experiment/controller/helper hashes, runtime, source bundle, benchmark material, snapshots and measurement coverage. A changed input requires a new experiment, not a silent reset. If the active Target is a pending candidate, finish only steps supported by saved evidence, or restore the last committed accepted snapshot. Do not guess whether a paid trial completed; bind its saved result before considering any rerun. Do not apply an already committed variance/tracker update twice.

Restore snapshots through a staging directory: validate archive paths, unpack `agent_state/`, preserve the live vault without reading or logging it, and replace the live state only after validation. Verify the restored version and digest. Keep the replaced state until verification succeeds, and retain all measured snapshots and experiment records. Never overwrite an unrelated Target change discovered during resume.
