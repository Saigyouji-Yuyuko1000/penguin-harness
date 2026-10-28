# Historical Evo Skill compatibility

- **Date:** 2026-10-28
- **Type:** fix
- **Scope:** `skills`

[中文版](2026-10-28-backward-compatibility.zh.md)

Preserved exact historical .6 Reader bytes, absolute and relative read-plan paths, State identity and the original 16,000-byte limit. Verification reads original files without re-exporting them or replacing scores, costs and verdicts.

## Compatibility

Keep this dual-format support until the owner explicitly approves removing historical readers and archived experiments no longer need them. The Evo plugin maintainer owns removal; no automatic migration or expiry was introduced.
