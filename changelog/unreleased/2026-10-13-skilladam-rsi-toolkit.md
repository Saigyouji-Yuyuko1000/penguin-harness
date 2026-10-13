# SkillAdam skill evolution toolkit

- **Date:** 2026-10-13
- **Type:** feature
- **Scope:** `skills`, `docs`

[中文版](2026-10-13-skilladam-rsi-toolkit.zh.md)

Added a local `skilladam-rsi-toolkit` plugin package with one controller Skill for evolving a Target's working Skill from execution feedback.

## Evolution and evaluation

The Skill combined an evolving issue tracker, bounded patches, paired evaluation, acceptance or rollback, and a variance-controlled edit budget. It included deterministic patch and score validation helpers and a GDPevo workflow with separate training and held-out evaluation.

The package was made available for local import. Registration in the default npm plugin library was left outside this change.
