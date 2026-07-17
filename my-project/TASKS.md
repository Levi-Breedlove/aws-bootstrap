# My AWS Project — Executable Tasks

`TASKS.md` is the live construction ledger after Gate B. Task blocks are the
only authoritative task records. GitHub Issues are conditional mirrors when the
current construction authorization (`AUTH`) permits the named GitHub writes.

Gate A and Gate B are the only routine human gates. Task readiness, wave
selection, checkpoints, verification, deployment preflight, and release checks
are execution controls inside an approved envelope; they are not additional
human gates.

## Active execution snapshot

This is a resumable snapshot, not a new authorization. It must match the
authoritative values in `PRD.md`. A mismatch or stale Gate B stops construction.

| Field | Value |
|---|---|
| Task-plan revision | `UNINITIALIZED` |
| Task-plan state | `UNINITIALIZED` |
| Requirements revision | `REQ-0001` |
| Design revision | `DES-0001` |
| Construction authorization | `AUTH-0001` |
| Gate B state | `BLOCKED` |
| Run state | `NOT_STARTED` |
| Active run ID | `NONE` |
| Baseline commit | `TODO` |
| Protected dirty paths | `NONE` |
| Coordinator | `UNASSIGNED` |
| Maximum workers | `1` |
| Current wave | `NONE` |
| Last checkpoint | `NONE` |
| Last known-green commit | `TODO` |
| Next safe action | Complete Gate B; when current, run `TASK-10` |

Run state is one of `NOT_STARTED`, `RUNNING`, `PAUSED`, `BLOCKED`, or
`COMPLETE`. Task-plan state is exactly `UNINITIALIZED`, `CURRENT`, or `STALE`.
Use monotonic IDs such as `PLAN-0001`, `RUN-0001`, and `CP-0001`. Update this
snapshot only at a coordinator checkpoint.

Lifecycle prompts update this snapshot before task generation. REQ-10 copies a
new requirements identity and makes construction non-runnable; an agent-ready
Gate A is `PENDING_OWNER_APPROVAL`. DESIGN-10 copies the current REQ/DES/AUTH,
authorized worker limit, baseline, and protected dirty paths and sets an
agent-ready Gate B to `PENDING_OWNER_APPROVAL`. DESIGN-20 acceptance changes the
snapshot to `APPROVED_FOR_CONSTRUCTION` in the same checkpoint as PRD.md and
bootstrap.yaml. A stale gate or identity mismatch sets the run to `BLOCKED` and
never silently retargets existing tasks. Before marking a plan `STALE`,
reconcile every `IN_PROGRESS` task to `DONE` with evidence or `BLOCKED` with the
observed revision blocker, checkpoint and commit the stale ledger, then stop all
claims. After a new Gate B, TASK-10 archives the stale plan by commit, replaces
its graph with tasks for the current IDs, and sets the new plan `CURRENT`.

## Coordinator and worker contract

- One coordinator owns task selection, worker assignment, checkpoints, and all
  writes to `TASKS.md`, `VERIFY.md`, `RUNBOOK.md`, shared manifests, lockfiles,
  schemas, generated output, and GitHub metadata.
- A worker edits only the exact disjoint code, test, or infrastructure paths
  assigned from one `READY` task. A worker never changes a shared control file
  or expands its write or external-state boundary.
- Each path and mutable external target has exactly one writer at a time. Treat
  ambiguous globs, shared generated output, the same branch, the same stack or
  state backend, and the same database as overlapping.
- Workers return a receipt containing task ID, base checkpoint, current
  REQ/DES/AUTH IDs, changed paths, commands and observed results, evidence IDs,
  GitHub or AWS actions, deviations, and recommended next status.
- The coordinator reconciles every worker receipt before recording evidence or
  selecting another wave. Workers do not mark their own tasks `DONE`.
- GitHub writes occur only when the current AUTH names the repository and
  operation. Otherwise retain `PENDING_SYNC`.
- AWS mutations occur only within a complete current AUTH or action-specific AWS
  authorization. Exactly one named AWS operator may mutate AWS at a time.

## Status and transition contract

| Status | Meaning | Allowed next status |
|---|---|---|
| `BACKLOG` | Defined but not executable | `READY`, `BLOCKED`, `SKIPPED` |
| `READY` | All execution preconditions are currently satisfied | `IN_PROGRESS`, `BACKLOG`, `BLOCKED`, `SKIPPED` |
| `IN_PROGRESS` | Claimed inside the current run and attempt budget | `DONE`, `BLOCKED` |
| `BLOCKED` | Cannot proceed; blocker and next action are recorded | `READY`, `BACKLOG`, `SKIPPED` |
| `DONE` | Acceptance criteria and required local evidence passed | Terminal |
| `SKIPPED` | Intentionally omitted under an explicit skip record | Terminal |

- `BACKLOG` is never runnable. Only an explicitly `READY` task may be claimed.
- Only a `CURRENT` task plan may be validated for execution or claimed;
  `UNINITIALIZED` and `STALE` route to TASK-10.
- An interrupted task remains `IN_PROGRESS` until the coordinator reconciles
  its paths and external state. Do not hide partial work by returning it to
  `READY`.
- `DONE` and `SKIPPED` are audit-terminal. Represent later work with a new task.
- `READY` requires current matching REQ/DES/AUTH IDs, resolved inputs, a concrete
  write set and external-state set, available attempt budget, objective
  validation, and satisfied dependencies.
- `IN_PROGRESS` requires an assigned owner, incremented attempt count, and base
  checkpoint; its `Run ID` must equal the snapshot's active run. `DONE` requires
  recorded evidence. `BLOCKED` requires a blocker and smallest useful next
  action. `SKIPPED` requires an explicit skip record.

Use the coordinator-owned tool for validation and atomic task updates:

```bash
python scripts/task_waves.py TASKS.md
python scripts/task_waves.py TASKS.md --ready --json
```

The ready result is a candidate list, not a parallel-safe batch.

Use the next unused monotonic IDs and these command shapes; do not hand-edit
claim or run fields:

```bash
# Start exactly one task or an autonomous run.
python scripts/task_waves.py TASKS.md --start-run RUN-0001 --coordinator codex-coordinator --run-mode SINGLE_TASK
python scripts/task_waves.py TASKS.md --start-run RUN-0001 --coordinator codex-coordinator --run-mode AUTONOMOUS

# Claim one serialized task only after the run is RUNNING.
python scripts/task_waves.py TASKS.md --claim TASK-0001 --owner codex-worker-1 --run-id RUN-0001 --coordinator codex-coordinator --checkpoint CP-0000

# For a proven-disjoint concurrent group, every claim includes this flag.
python scripts/task_waves.py TASKS.md --claim TASK-0002 --owner codex-worker-2 --run-id RUN-0001 --coordinator codex-coordinator --checkpoint CP-0000 --isolated-worktrees

# Reconcile every IN_PROGRESS task, then pause or complete.
python scripts/task_waves.py TASKS.md --set-status TASK-0001 DONE --evidence EV-0001 --run-id RUN-0001 --coordinator codex-coordinator --checkpoint CP-0001
python scripts/task_waves.py TASKS.md --pause-run RUN-0001 --coordinator codex-coordinator --checkpoint CP-0002

# Resume only the same safely checkpointed run and coordinator.
python scripts/task_waves.py TASKS.md --resume-run RUN-0001 --coordinator codex-coordinator
```

Use `--complete-run RUN-0001 --coordinator codex-coordinator --checkpoint
CP-0002` only when all tasks are terminal. Every mutation names the exact active
coordinator. Claims cite the current base checkpoint and concurrent claims may
share it. Each `IN_PROGRESS` reconciliation advances to the next unique
checkpoint. Pause or completion then consumes a later unique checkpoint and
requires its newest complete row and VERIFY.md reference; do not reuse CP-0001.
Run start and issue synchronization do not create fictional checkpoints. A
persisted `RUNNING` state is recovery-required, not automatically resumable.

## Required task record schema

`TASK-10` creates task headings and these exact singleton metadata keys. There
is intentionally no placeholder task: `UNINITIALIZED` plus a current Gate B
routes to `TASK-10`, not construction.

| Metadata key | Required content |
|---|---|
| `Status` | One status from the transition contract |
| `Requirements` | Current REQ ID and requirement IDs |
| `Design` | Current DES ID and applicable design sections or decisions |
| `Authorization` | Current AUTH ID |
| `Depends on` | Stable task IDs or `NONE` |
| `Dependency waivers` | `TASK-nnn=WAIVER-nnn` entries or `NONE` |
| `Owner` | Assigned worker/coordinator or `UNASSIGNED` |
| `Run ID` | Active run ID while `IN_PROGRESS`, otherwise `NONE` |
| `Risk` | Objective task risk classification |
| `Write set` | Exact paths or narrow globs |
| `External state` | Exact mutable targets or `NONE` |
| `AWS mode` | `NONE`, `DOCS_ONLY`, `READ_ONLY`, or `MUTATION` |
| `Attempt budget` | Positive integer from AUTH |
| `Attempts used` | Non-negative integer not exceeding the budget |
| `Evidence` | Evidence IDs or `NONE` before evidence exists |
| `Blocker` | Current blocker and next action, or `NONE` |
| `Skip record` | Explicit record ID or `NONE` |
| `GitHub issue` | Authorized issue URL or `PENDING_SYNC` |
| `Last checkpoint` | Coordinator checkpoint ID or `NONE` |
| `Last updated` | ISO 8601 timestamp or `TODO` before initialization |

`TASK-10` emits every real record in this exact structural shape. Replace every
angle-bracket value; do not leave unresolved values on a `READY`, `IN_PROGRESS`,
or `DONE` task.

~~~text
### <TASK-ID> — <short title>

- Status: BACKLOG
- Requirements: <current REQ ID and requirement IDs>
- Design: <current DES ID and sections or decisions>
- Authorization: <current AUTH ID>
- Depends on: NONE
- Dependency waivers: NONE
- Owner: UNASSIGNED
- Run ID: NONE
- Risk: <objective risk>
- Write set: <exact paths or narrow globs>
- External state: NONE
- AWS mode: NONE
- Attempt budget: <positive integer from AUTH>
- Attempts used: 0
- Evidence: NONE
- Blocker: NONE
- Skip record: NONE
- GitHub issue: PENDING_SYNC
- Last checkpoint: NONE
- Last updated: <ISO 8601 timestamp>

#### Outcome

<one observable outcome>

#### Acceptance criteria

- [ ] <objective criterion>

#### Validation

```bash
<exact validation command>
```

#### Execution log

- <timestamped coordinator entry or NOT_STARTED>
~~~

A READY task cannot contain `TODO` in its outcome, acceptance, validation,
boundaries, or traceability. A DONE task has every acceptance checkbox checked,
non-`NONE` Evidence using `EV-nnnn` IDs (for example `EV-0001`), and an observed
execution-log entry. Each cited local ID must have exactly one explicit,
passing row under VERIFY.md `Task completion evidence`; the task tool rejects
placeholder, duplicate, wrong-task, unfenced URL-only, and non-passing rows.

## Dependencies, waivers, and waves

- `Depends on: NONE` places a task in structural Wave 1. Other wave numbers are
  derived from the dependency graph and are not manually stored.
- Missing dependencies, duplicate IDs, self-dependencies, and cycles are
  invalid.
- A `DONE` dependency is satisfied. A `SKIPPED` dependency is not satisfied by
  status alone.
- To proceed past a skipped dependency, the downstream task must declare
  `TASK-nnn=WAIVER-nnn` under `Dependency waivers`, and the waiver registry must
  name the downstream task, skipped task, rationale, evidence, and current AUTH
  clause or separate owner decision that permits the omission.
- A waiver cannot broaden scope, weaken an acceptance criterion, or conceal a
  missing security, data, migration, recovery, or release obligation. If it
  would, stop and revise Gate A or Gate B as applicable.
- Tasks in one structural wave may run concurrently only when their write sets,
  external state, dependencies, generated outputs, and tool operations are
  demonstrably disjoint. Otherwise serialize them.
- Every AWS mutation is serialized even when local task paths are disjoint.
- BUILD-10 and BUILD-20 stop at an AWS mutation boundary. Preflight through
  AWS-10, mutate only through AWS-20, and reconcile live evidence through AWS-30.

### Dependency waiver registry

| Waiver ID | Skipped task | Applies to task | Authority | Rationale and preserved acceptance evidence | Recorded at |
|---|---|---|---|---|---|
| `NONE` | `NONE` | `NONE` | `NONE` | No waivers recorded | TODO |

## Attempt budget and stop conditions

An attempt is one coherent implementation-and-validation cycle for a task.
Claiming a task atomically increments `Attempts used`. A materially new
hypothesis may use the next available attempt; repeating the same failed action
does not reset the budget.

Stop affected work and checkpoint when any of the following occurs:

- Gate A or Gate B is stale, expired, revoked, or inconsistent with the active
  REQ/DES/AUTH IDs;
- the requested outcome, task, path, command, GitHub operation, AWS target, or
  external-state mutation is outside AUTH;
- an attempt budget is exhausted without a materially new authorized approach;
- a worker discovers overlapping ownership, protected dirty work, unexpected
  generated changes, or a failing baseline it cannot safely attribute;
- a new requirement, design decision, migration, destructive action, public
  exposure, IAM broadening, production/shared-resource impact, sensitive-data
  concern, or material cost change is required;
- caller identity, account, Region, environment, artifact, change set, or live
  state does not match the authorized AWS boundary;
- an external operation is partial or its result is unknown; or
- the next action cannot be validated objectively.

Record the smallest decision or boundary change needed. Do not ask routine
questions while safe tasks remain inside the current envelope.

## Checkpoints and resume

The coordinator checkpoints after every task or safe wave, before and after an
external mutation, before handing work to another session, and whenever work
pauses or stops. Gate B requires a local Git repository and resolvable baseline
commit. After each validated wave, the coordinator inspects the integrated
diff, records EV evidence, commits only authorized wave changes, updates Last
known-green commit and the checkpoint row to that commit, and then runs doctor.
Only after those steps may the run pause or start another wave. Never absorb a
protected dirty path into the checkpoint commit.

| Checkpoint | Run | Time | REQ / DES / AUTH | Commit and protected dirty paths | Task outcomes and attempts | Evidence and external actions | Blockers and next safe action |
|---|---|---|---|---|---|---|---|
| `NONE` | `NONE` | TODO | `REQ-0001` / `DES-0001` / `AUTH-0001` | TODO | No work started | `NONE` | Complete Gate B; when current, run `TASK-10` |

To resume, reconcile the active revisions and authorization expiry, baseline and
current worktree, protected paths, task states and owners, remaining attempt
budgets, last-known GitHub state, and last-known AWS state. Inspect an interrupted
external operation read-only and classify it as succeeded, failed, partial, or
unknown before deciding what is safe. Stop on any mismatch; never blindly rerun
a mutation.

### Archived task-plan registry

| Plan revision | Plan state | REQ / DES / AUTH | Archive commit | Reason replaced |
|---|---|---|---|---|
| `NONE` | `UNINITIALIZED` | `REQ-0001` / `DES-0001` / `AUTH-0001` | `NONE` | No prior plan |

## Task definitions

No tasks have been generated. After Gate B is current, run `TASK-10` when the
plan state is `UNINITIALIZED` or `STALE` to create or replace the current
`TASK-nnn` graph from the approved REQ/DES/AUTH envelope. Preserve the stale
graph in its archive commit and registry row; never reuse its task IDs. Each task
must include an observable outcome, bounded scope, objective acceptance criteria,
exact validation commands, evidence references, blockers, and an execution log.
