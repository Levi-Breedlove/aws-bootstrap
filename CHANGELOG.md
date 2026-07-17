# Changelog

All notable changes to AWS Codex Fastlane are recorded here.

## [2.0.0] - 2026-07-17

### Added

- `BOOT-00` collision-safe launch and a plain-language guided intake.
- Exactly two versioned owner gates: requirements Gate A and PRD/construction
  Gate B.
- Greenfield, brownfield, quick-MVP, standard, and high-risk operating paths.
- A hash-bound construction envelope for bounded autonomous implementation.
- Durable task claims, attempt budgets, checkpoints, pause/resume, and release
  state in `task_waves.py`.
- Read-only lifecycle, manifest, receipt, evidence, and runtime-integrity checks
  in `bootstrap_doctor.py`.
- A machine-readable lifecycle mirror and sealed runtime-control hashes.
- A deterministic, manifest-driven release archive and SHA-256 sidecar.

### Changed

- Replaced the document-heavy AWS AIDLC flow with a Codex-native fast lane.
- Made the repository authoritative while keeping Notion suitable as a prompt
  launcher and status view.
- Restricted brownfield adoption to explicit per-path preserve, adopt, or stage
  decisions bound to the exact source, target, and content digests.
- Required objective AWS identity, scope, cost, artifact, rollback, and expiry
  boundaries before mutation.

### Security

- Gate approvals require exact receipts from a named human and become stale
  when their versioned basis changes.
- Bootstrap, task execution, GitHub operations, and AWS mutations fail closed
  when integrity, authority, or recovery state is ambiguous.
