# Evo-Harness benchmark adapters

- **Date:** 2026-10-28
- **Type:** feature
- **Scope:** `skills`, `core`, `server`, `amsp`
- **PR:** [Saigyouji-Yuyuko1000/penguin-harness#2](https://github.com/Saigyouji-Yuyuko1000/penguin-harness/pull/2)

[中文版](2026-10-28-evo-benchmark-adapters.zh.md)

Added the Evo-Harness plugin on the .6 learning baseline, with native Session feedback, scoped Solver tools and background-work waiting. Kept Evo and SkillAdam as separate plugins.

## Details

- Added automatic official resource acquisition, commit-pinned caches and complete Project package fingerprints.
- Packaged Evo's runtime preparation, State transport and trial acceptance helpers with the plugin.
- Added one training pass and three tests per frozen State by default. Reports aggregate domain scores within each repetition before calculating sample variance and standard deviation.
- Registered the plugin in package dependencies, catalogs and documentation.

## Compatibility

Retained the historical Skill formats through read-only verification; see [backward compatibility](2026-10-28-backward-compatibility.md). Ordinary post-exit Harbor verifiers still require an original-Session feedback adapter for full Evo learning.

The 2026.10.28.4 engineering revision included the plugin README in the exact published bundle inventory, retaining file hashes and private-path restrictions.
