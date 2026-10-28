---
name: evo-training
description: "Coordinate one Evo training batch with original-Solver reflection and one independent compilation."
---

# One Evo training batch

You are the training coordinator inside this Benchmark environment. Read the
frozen `training-request.json`, train-only `benchmark-training.md` and complete
role instructions. You orchestrate; Solvers answer tasks and one Evolver curates.
Use only the selected training roster and fixed pre-batch library. Keep the same
model, tools and thinking level throughout, including every delegated role.

1. Export the pre-batch library for the declared topic. Install its exact context
   before Solver creation. Every Solver gets identical pre-batch guidance; no
   earlier candidate or edited library reaches a later Solver. Complete public
   input reads before scoring. Hash input grants before dispatch and pass those
   hashes with the candidate schema. Keep input and output paths per task.
2. Launch one native Solver per task, in roster order when business state is
   shared. Its inline `prompt` contains the full Solver and reflection roles,
   public task and allowed material locations, input hashes, answer path,
   one-grade interface and output contracts. Use `run_in_background: true` and
   retain its child/Session ID. The Solver makes one answer and one actual
   external scoring call, observes all feedback, and reflects there when negative.
   If the coordinator supplies feedback instead, continue that same child with
   `input_subagent` and the full raw feedback. Never spawn another Reflector.
   Empty follow-up polls collect output; a nonempty follow-up continues the same
   original Session. Do not resend an already completed reflection.
3. Preserve each answer, full raw authorized feedback, complete native trajectory,
   Session ID and negative reflection (including an explicit empty array).
   Successful tasks have no candidates. A grader/transport failure stops the
   batch as incomplete. The coordinator never rewrites role-authored candidates.
   Verify no post-grade answer edits, rescoring, new business retrieval, hidden
   grading material or test access. Reflection may reason over data already
   observed; it may not acquire new evidence from business services.
4. After all tasks finish, invoke one independent native Evolver with its full
   role, all authorized training contexts (successes included as counterevidence),
   all negative candidates and the entire private pre-batch library. Supply
   five-entry ceilings and the 16,000-byte export budget. Empty candidates still
   require that real Evolver invocation and an explicit empty decision array.
5. Validate its decisions with `evo.py compile`. Structural or size errors may
   be repaired in that same Evolver conversation before compilation. Do not
   add new lessons yourself, retest a proposed method, rerun learning, ask a
   second reviewer or use a score acceptance gate. Freeze the validated library
   and export once. Follow the Benchmark's answer/Skill export paths; collect
   the complete learning artifacts before the container exits.

The compile request is an object with `task_ids`, `topic`, `contexts`, `library`,
`candidates`, `decisions` and optional `max_bytes` (at most 16000). Every context
identifies `task_id`, `attempt_id`, the original `session_id`, `status: "ok"`,
the benchmark-derived boolean `negative`, `input_sha256` and `tool_call_ids`.
Those reference lists come from the actual native record, never invented IDs.
The helper checks references and coverage; the coordinator checks the real trace
and complete roster. Follow the role's candidate and decision schemas.

```bash
python3 scripts/evo.py compile --request batch.json
python3 scripts/evo.py export --request frozen-library.json --output exported-skills
```

Save compile stdout privately. The export request has `library` from that output,
the frozen `topic` and optional `max_bytes`. Export refuses an existing output
directory. Keep the private library, input/answer/feedback records, candidate
arrays, decisions and role identities beside the native learning record. They
do not enter the learned Skill package or frozen test State. Report actual
grades and usage, including incomplete/failed work. Do not invent a training
curve or claim semantic correctness from passing structural validation.
