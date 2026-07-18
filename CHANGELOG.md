# Changelog

All notable changes to AWS Codex Fastlane are recorded here.

## [1.0.0] - 2026-07-17

Initial public release.

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
- Release-only packaging that keeps generated ZIP files out of `main`.
- A ready-to-use repository-root layout for GitHub Template adoption.
- Four repo-scoped Fastlane skills that route directly into launch, planning,
  construction, and explicitly authorized AWS operations.
- Additive, machine-stable doctor fields for setup, gates, evidence, and
  authorization state.

### Changed

- Replaced the document-heavy AWS AIDLC flow with a Codex-native fast lane.
- Made the repository authoritative while keeping Notion suitable as a prompt
  launcher and status view.
- Put Gate A and Gate B on one plain-language lifecycle line in both start
  guides.
- Restricted brownfield adoption to explicit per-path preserve, adopt, or stage
  decisions bound to the exact source, target, and content digests.
- Required objective AWS identity, scope, cost, artifact, rollback, and expiry
  boundaries before mutation.
- Made GitHub **Use this template** the primary adoption path, with an equivalent
  release ZIP as the secondary recovery path.

### Security

- Gate approvals require exact receipts from a named human and become stale
  when their versioned basis changes.
- Bootstrap, task execution, GitHub operations, and AWS mutations fail closed
  when integrity, authority, or recovery state is ambiguous.
