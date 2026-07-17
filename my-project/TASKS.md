# My AWS Project — Executable Tasks

`TASKS.md` is the live task checklist and execution source for Codex.

GitHub Issues mirror non-trivial tasks for durable tracking and collaboration. Stable task IDs reconcile the two systems.

## Execution dashboard

| Field | Value |
|---|---|
| Target release | TODO |
| Parent GitHub Issue | `PENDING_SYNC` |
| Current wave | Not started |
| Current task | None |
| Last updated | TODO |
| Blockers | None |
| Completed | 0 |
| Total | 1 |

## Status vocabulary

| Status | Meaning |
|---|---|
| `BACKLOG` | Defined but not ready |
| `READY` | Dependencies are complete and work may begin |
| `IN_PROGRESS` | Codex or a human is actively implementing it |
| `BLOCKED` | Cannot proceed; blocker is recorded |
| `DONE` | Acceptance criteria and required local evidence pass |
| `SKIPPED` | Intentionally omitted with rationale |

## Source-of-truth and GitHub sync rules

- Never renumber a task ID.
- `TASKS.md` owns live execution status during a work session.
- Every non-trivial task should have a GitHub Issue by the end of the workday.
- Include the stable task ID in the GitHub Issue title or body.
- Attach task issues as native sub-issues of the release parent where supported.
- Mirror acceptance criteria, dependencies, status, blockers, linked PR, and evidence summary.
- Do not copy full execution logs into GitHub.
- If GitHub and this file drift, reconcile using the stable task ID and report the conflict.

## Dependency-aware wave rules

- `Depends on: NONE` means the task belongs to structural Wave 1.
- A task is placed in the earliest wave allowed by its dependencies.
- Missing dependencies and cycles are invalid.
- Tasks in one wave are eligible for concurrency only when their write sets and mutable resources do not overlap.
- AWS mutations remain approval-gated and normally execute sequentially.
- A task is ready at runtime only when all dependencies are `DONE` or `SKIPPED`.

Validate dependencies and print the wave order with:

```bash
python scripts/task_waves.py TASKS.md
```


## Wave checklist

This is the human-readable execution order. Keep tasks grouped by wave after dependencies are validated.

### Wave 1 — No incomplete dependencies

- [ ] `TASK-001` — Replace with first executable task

### Wave 2 — Unlocked after Wave 1

- No tasks yet

### Later waves

- Add additional wave sections only when needed.

Tasks inside one wave may run concurrently only when their write sets and mutable resources do not overlap.

## Task registry

| ID | Title | Status | Depends on | GitHub Issue | Outcome |
|---|---|---|---|---|---|
| TASK-001 | Replace with first executable task | `BACKLOG` | `NONE` | `PENDING_SYNC` | TODO |

Keep this registry concise. Detailed execution data belongs in the task block below.

## Task definitions

### TASK-001 — Replace with first executable task

- Status: `BACKLOG`
- Depends on: `NONE`
- Wave: `AUTO`
- GitHub issue: `PENDING_SYNC`
- Parent issue: `PENDING_SYNC`
- Owner: `UNASSIGNED`
- Affected pillars: `TODO`
- Write set: `TODO`
- AWS mutation: `NO`
- Last updated: `TODO`

#### Outcome

State one observable implementation outcome.

#### Scope

- In scope: TODO
- Out of scope: TODO

#### Acceptance criteria

- [ ] TODO
- [ ] Relevant PRD or BUGFIX requirements are satisfied
- [ ] Required example tests pass
- [ ] Required property-based tests pass
- [ ] Security and failure paths pass
- [ ] Validation evidence is recorded

#### Implementation notes

- TODO

#### Validation

```bash
# Replace with exact commands
TODO
```

#### Evidence

- Local: TODO
- AWS: `PENDING_AWS`
- Pull request: TODO

#### Blockers

- None

#### Execution log

- TODO — Task created
