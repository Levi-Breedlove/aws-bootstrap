# AWS Repository Operating Guide

## Mission

Build and operate **My AWS Project** according to the approved requirements and design in `PRD.md`.

## Sources of truth

| Subject | Authoritative source |
|---|---|
| Feature requirements, user stories, acceptance criteria, architecture, and implementation approach | `PRD.md` |
| Active defect analysis and regression expectations | `BUGFIX.md` |
| Executable task checklist, dependencies, waves, and live work status | `TASKS.md` |
| Verification and release evidence | `VERIFY.md` |
| Build, deployment, rollback, recovery, and operations | `RUNBOOK.md` |
| Machine-readable lifecycle and resume mirror | `bootstrap.yaml` (derived only; never authorization) |
| Consequential architectural decisions | `docs/adr/` |
| Durable project tracking and collaboration | GitHub Issues, Projects, and pull requests |
| Actual system behavior | Code, tests, schemas, configuration, and infrastructure |

When sources disagree, stop and identify the conflict. Do not silently invent a reconciliation.
`bootstrap.yaml` must agree with the authoritative Markdown records. A mismatch
is a stop condition; never use the mirror to infer or widen approval.

## Specification mode

Determine the work type before planning implementation:

- **Feature or planned change:** use `PRD.md`.
- **Defect or regression:** use `BUGFIX.md`, while referencing unchanged requirements in `PRD.md`.
- **Mixed work:** separate the defect correction from new behavior unless one cannot be completed safely without the other.

## Operating mode and delivery profile

Record these independent choices in `PRD.md` before requirements approval:

- Project mode: `greenfield` or `brownfield`.
- Delivery profile: `quick-mvp`, `standard`, or `high-risk`.
- AWS lane: `documentation-only`, `read-only`, `fast-dev`, or `explicit-gate`.

Default a new small project to `quick-mvp` and `explicit-gate`. Brownfield is a
project mode, not a risk profile. A quick MVP is a smaller approved scope; it is
not weaker engineering or weaker security.

Treat the effective profile as `high-risk` when work involves production,
regulated or highly sensitive data, payments, tenant isolation, consequential
identity or trust changes, irreversible migration or deletion, public exposure,
shared infrastructure, multi-account or multi-Region coordination, strict
recovery targets, or material unbounded spend. Record the trigger. A faster
selected profile never overrides an objective risk trigger.

Apply these overlays without adding lifecycle gates:

- `quick-mvp`: one thin observable outcome, minimal independently verifiable
  tasks, one development environment and Region where feasible, and one worker
  by default;
- `standard`: full intended-environment operational coverage and only proven,
  bounded task parallelism;
- `high-risk`: deeper threat, data, tenancy, migration, recovery, rollback, and
  audit analysis, smaller mutation batches, and stronger evidence.

Every overlay retains the same security baseline, objective acceptance rules,
AWS identity checks, and Gate A/Gate B authority model.

Gate A and Gate B each use one compact readiness card in PRD.md. Fill every
listed field with explicit current facts and stable IDs. Use `NOT_APPLICABLE —
<reason>` only when genuinely inapplicable; never use it to avoid discovery.

## Two-gate lifecycle

This bootstrap has exactly two routine human decision points.

### Gate A — Requirements approval

Before technical design, Codex interviews the owner, drafts Part I of `PRD.md`,
and analyzes the complete requirement set together.

Check for:

- logical inconsistencies;
- ambiguous terms or unmeasurable outcomes;
- conflicting functional and non-functional constraints;
- undefined concepts and unstated assumptions;
- missing boundary, failure, security, concurrency, and recovery cases;
- requirements that cannot be verified objectively;
- incompatible cost, availability, performance, privacy, or regional constraints.

Record findings in the `PRD.md` requirements-analysis section.

The agent recommendation must be one of:

- `BLOCKED`
- `READY_WITH_PROPOSED_ASSUMPTIONS`
- `READY_FOR_OWNER_APPROVAL`

When a ready recommendation is recorded, update the detailed Gate A owner
state and Document status to `PENDING_OWNER_APPROVAL` in the same checkpoint,
then mirror both gate states in `bootstrap.yaml` and copy the current REQ plus
Gate B state into TASKS.md's Active execution snapshot. Keep Gate B `BLOCKED`
for a new design or `STALE` after a material requirements revision. Do not leave
an agent-ready gate marked `BLOCKED`.

Only the owner can accept named assumptions and approve the current
requirements revision. Codex must not infer approval from silence, continued
conversation, a task status, or tool access. Design may start only when Gate A
is `APPROVED_FOR_DESIGN`, the approved revision matches the current revision,
and no blocking finding remains open.

The recorded approver must be the named human decision owner. Reject `Codex`,
`agent`, `automation`, `system`, `AI`, and other model or service identities,
case-insensitively, at both gates.

### Gate B — PRD and construction authorization

After technical design, Codex proposes one bounded construction envelope in
`PRD.md`. It names the approved outcome and scope, exact write boundaries,
prohibited work, task and concurrency limits, investigation or attempt budget,
checkpoint policy, GitHub permission, and AWS lane and boundaries.

Only the owner can approve the current design revision and proposed envelope.
Task generation and implementation may start only when Gate B is
`APPROVED_FOR_CONSTRUCTION` and its approved requirements and design revisions
match the current revisions.

Before Gate B can become pending, the project must be a local Git repository
with a resolvable authorized baseline commit, protected dirty paths recorded,
and the complete construction-envelope table hashed under PRD.md's canonical
SHA-256 rule. The agent review, owner record, and exact receipt all bind that
same digest.

Once Gate B is current, Codex should generate tasks and continue through safe
implementation waves without routine task-by-task approval. It pauses only for
a declared stop condition, stale approval, exhausted boundary, unavailable
authority, or an action that the approved envelope does not cover.

When the complete PRD and envelope earn
`READY_FOR_CONSTRUCTION_APPROVAL`, update the detailed Gate B owner state and
Document status to `PENDING_OWNER_APPROVAL`, and atomically mirror the exact
REQ/DES/AUTH IDs, Gate B state, authorized worker limit, baseline, and protected
dirty paths into TASKS.md and `bootstrap.yaml`. A valid Gate B owner receipt
then changes all of those mirrors to `APPROVED_FOR_CONSTRUCTION` in one
coordinator checkpoint. Record the observed authorization time and exact source
for both gate receipts; provenance is metadata and does not add receipt lines.

Business approval does not widen the Codex sandbox or bypass platform approval
controls. Conversely, filesystem, network, GitHub, or AWS capability never
grants business authorization.

### Approval invalidation

- Any change to requirements-revision-controlled content makes Gate A and Gate
  B `STALE`. This includes workflow/profile/risk/AWS-lane fields, workload and
  intake facts, the brownfield preservation contract, Part I, findings,
  proposed assumptions, and open decisions, as defined precisely in `PRD.md`.
- Any change to the approved technical design or construction envelope makes
  Gate B `STALE`.
- A material implementation discovery that changes requirements, architecture,
  scope, risk, budget, or authorization boundaries must stop affected work and
  route back to the applicable gate.
- Revision IDs are monotonic. Never reuse an approved revision ID for changed
  content.

A stale Gate A routes to `INTAKE-10` when owner facts are missing and otherwise
to `REQ-10`. A stale Gate B with a current Gate A routes to `DESIGN-10`.
Construction remains stopped until the applicable gate is current again; stale
state is recoverable workflow state, not a reason to dead-end at STOP.

Do not silently design around an unresolved contradiction.

## Required Codex workflow

1. Read this file and every applicable nested `AGENTS.md`.
2. Run or resume `BOOT-00` and determine greenfield or brownfield mode.
3. Run `python scripts/bootstrap_doctor.py --root .` and stop on an unsafe or
   inconsistent result.
4. Determine feature-spec, bugfix-spec, or mixed mode.
5. Use `INTAKE-10` and `REQ-10` to draft and analyze requirements.
6. Stop for explicit owner approval at Gate A.
7. Use `DESIGN-10` to complete architecture, data flow, error handling, and testing design.
8. Stop for explicit owner approval at Gate B.
9. Generate discrete tasks with `TASK-10` inside the approved envelope.
10. Validate dependencies and structural waves with `scripts/task_waves.py`.
11. Acquire one durable run coordinator before `BUILD-20`; treat an
    interrupted `RUNNING` state as recovery-required, not automatically resumable.
12. Execute one task with `BUILD-10` or long-run safe groups with `BUILD-20`.
13. Claim a task atomically before implementation; the claim increments its
    persistent attempt count. Mark it `DONE` only after acceptance evidence.
14. Record meaningful progress, blockers, deviations, and validation in the task log.
15. Record produced evidence in `VERIFY.md` and update `RUNBOOK.md` only when repeatable procedures change.
16. Synchronize GitHub only when the current Gate B envelope permits it; otherwise preserve `PENDING_SYNC`.
17. Use read-only AWS preflight before any deployment and require a fully matching AWS authorization envelope for mutation.
18. Create an ADR only for a consequential, difficult-to-reverse decision.

Release state is exactly `NOT_READY`, `READY_TO_DEPLOY`, or
`RELEASE_VERIFIED`. RELEASE-10 alone changes it. AWS-10 accepts only
READY_TO_DEPLOY; AWS-30 records deployed evidence and returns to RELEASE-10 for
the RELEASE_VERIFIED decision.

Task-plan state is `UNINITIALIZED`, `CURRENT`, or `STALE`. Only CURRENT is
runnable. On REQ/DES/AUTH change, reconcile every IN_PROGRESS task, commit the
non-runnable stale ledger, and stop claims. After a new Gate B, TASK-10 records
the old plan's archive commit and replaces the graph with a new monotonic plan
and never-reused task IDs.

Start, claim, checkpoint, pause, and resume runs through
`scripts/task_waves.py`; do not hand-edit coordinator state. The canonical
command shapes are:

```bash
python scripts/task_waves.py TASKS.md --start-run RUN-0001 --coordinator codex-coordinator --run-mode SINGLE_TASK
python scripts/task_waves.py TASKS.md --start-run RUN-0001 --coordinator codex-coordinator --run-mode AUTONOMOUS
python scripts/task_waves.py TASKS.md --claim TASK-0001 --owner codex-worker-1 --run-id RUN-0001 --coordinator codex-coordinator --checkpoint CP-0000
python scripts/task_waves.py TASKS.md --claim TASK-0002 --owner codex-worker-2 --run-id RUN-0001 --coordinator codex-coordinator --checkpoint CP-0000 --isolated-worktrees
python scripts/task_waves.py TASKS.md --set-status TASK-0001 DONE --evidence EV-0001 --run-id RUN-0001 --coordinator codex-coordinator --checkpoint CP-0001
python scripts/task_waves.py TASKS.md --pause-run RUN-0001 --coordinator codex-coordinator --checkpoint CP-0002
python scripts/task_waves.py TASKS.md --complete-run RUN-0001 --coordinator codex-coordinator --checkpoint CP-0002
python scripts/task_waves.py TASKS.md --resume-run RUN-0001 --coordinator codex-coordinator
```

Every mutation names the exact active coordinator. Use the next unused monotonic
IDs. Reconcile every `IN_PROGRESS` task before
pausing. Resume only the same safely checkpointed run and coordinator; a
persisted `RUNNING` run requires recovery inspection.

Claims cite the current base checkpoint; proven-disjoint concurrent claims may
share it. Reconciling an `IN_PROGRESS` task to `DONE` or `BLOCKED` consumes the
next unique checkpoint and advances the snapshot. A later pause or completion
consumes another unique checkpoint and requires the newest complete checkpoint
row plus VERIFY.md reference. Starting a run or synchronizing issue metadata
does not invent a checkpoint. Never reuse a reconciliation checkpoint for the
following pause or completion.

After each validated task or wave, inspect the integrated diff, record EV-nnnn
evidence in the exact VERIFY.md `Task completion evidence` table, including the
task, observed command/result, actor/time, tested commit/worktree/artifact,
durable source, and `LOCAL_PASS` or `VERIFIED` status. Commit only authorized
changes, update Last known-green and the checkpoint row to that commit, and run
doctor. Do this before pausing or starting another wave. Never commit protected
dirty paths or use a Git remote without separate authorization.

## Task checklist and execution contract

`TASKS.md` is the live execution checklist.

Do not generate or execute tasks unless the current Gate B is
`APPROVED_FOR_CONSTRUCTION`. Every task must trace to the approved requirements
and design revisions and remain inside the approved construction envelope.

Every task must have:

- stable task ID;
- clear outcome;
- status;
- dependencies;
- affected components or write set;
- acceptance criteria;
- validation commands or evidence;
- GitHub Issue link or `PENDING_SYNC`;
- execution log.

Allowed statuses:

- `BACKLOG`
- `READY`
- `IN_PROGRESS`
- `BLOCKED`
- `DONE`
- `SKIPPED`

Never renumber an existing task ID.

### Individual execution

When asked to execute one task, do not implement unrelated tasks. You may perform prerequisite inspection and validation, but scope changes must be recorded.

### Wave execution

Structural dependency waves are not automatically concurrency-safe. Use the
validator's conservative execution groups. Tasks may execute concurrently only
when they have disjoint write and external-state sets and run in isolated
worktrees. Otherwise serialize them.

Serialize tasks that:

- edit overlapping files;
- modify the same infrastructure stack or resource;
- run migrations against the same data store;
- depend on shared generated output;
- require irreversible or billable actions;
- have unresolved assumptions.

AWS mutations require explicit authorization regardless of wave eligibility.
Every AWS mutation is serialized. A `SKIPPED` prerequisite unlocks a dependent
only through an explicit current waiver naming both tasks, its authority,
rationale, and replacement evidence.

The coordinator is the sole writer of `TASKS.md`, `VERIFY.md`, `RUNBOOK.md`,
`bootstrap.yaml`, shared manifests, lockfiles, schemas, generated outputs, and
GitHub metadata. Workers edit only assigned task paths and return receipts. The
coordinator verifies the actual diff before accepting a worker result.

## Brownfield preservation contract

Before changing an existing repository, record in `PRD.md`:

- the baseline commit or working-tree state and pre-existing test results;
- current architecture, infrastructure ownership, and known failures;
- dirty or user-owned changes that must be preserved;
- in-scope components and exact write boundaries;
- protected behavior, files, resources, interfaces, and compatibility limits;
- migration, import, shared-resource, and rollback constraints;
- unresolved bootstrap overlay collisions.

In brownfield mode, repository/baseline, deployments, architecture/ownership,
interfaces/consumers, data/migration, security controls, baseline commands and
evidence, and protected components are mandatory facts and cannot be `NONE` or
unknown. Use `NOT_APPLICABLE — <reason>` only after proving a concern genuinely
cannot apply. Only drift, dirty changes, known debt/defects, and overlay
collisions may use their PRD-defined NONE forms.

Bootstrap overlay is preview-only until every collision is understood. Blanket
`--force` is disabled. Resolve each collision with a hash-bound adoption map:
preserve it, adopt the exact reviewed template bytes, or stage the candidate in
a separate non-overlapping target for merge. The launch command alone does not
authorize `ADOPT_TEMPLATE`: Codex may propose the map, but the user must confirm
the exact plan digest, canonical target root, named human owner, and complete ordered decision map
before any adoption write. Reject drift or partial confirmation. This is a
one-time collision authorization, not a third lifecycle gate. Do not overwrite existing planning
files, code, infrastructure, configuration, or user changes merely to make the
template fit. Brownfield mode does not add a routine third gate; stop only when
preservation, ownership, migration, destructive-change, or scope boundaries
require a decision.

Nested `AGENTS.md` files may narrow a task but may never widen the current AUTH,
write set, command boundary, GitHub mode, AWS boundary, or stop conditions.

## GitHub synchronization contract

`.github/ISSUE_TEMPLATE/` contains issue forms, not task records.

Actual task tracking lives in GitHub Issues.

When the current Gate B construction envelope authorizes GitHub mutation, for
each non-trivial task:

- include the stable task ID in the issue;
- attach the issue as a native sub-issue of the release parent where supported;
- preserve dependencies and wave information;
- link the implementation pull request;
- mirror status and blockers at the next authorized checkpoint;
- summarize validation and evidence without copying entire logs.

`TASKS.md` remains the live execution source during a session. GitHub is the durable mirror for project visibility and collaboration.

When GitHub mutation is not authorized, leave links as `PENDING_SYNC` and
report the pending synchronization without creating or changing Issues,
branches, pull requests, labels, Projects, or comments.
Credentials and connector availability are not authorization.

If the two drift, reconcile using the stable task ID and report the conflict.

## Property-based testing contract

`PRD.md` defines system properties and invariants. Test code implements them using the language-appropriate property-based testing framework where valuable.

For each material property, define:

- property ID;
- invariant;
- generated input or state space;
- preconditions;
- expected oracle;
- boundary and shrinking considerations;
- applicable test layer.

Property-based testing supplements rather than replaces:

- example-based unit tests;
- integration tests;
- end-to-end tests;
- deployed AWS verification;
- security and recovery exercises.

Prioritize properties for:

- authorization isolation;
- serialization and round trips;
- idempotency;
- ordering and concurrency;
- state machines;
- parsers and validators;
- retry bounds;
- resource naming;
- encryption or redaction invariants;
- financial or compliance-sensitive calculations.


## Educational mode

When the user invokes educational, mentor, teaching, or learning mode:

- provide concise milestone updates rather than narrating every operation;
- explain relevant AWS and software-engineering concepts;
- summarize decision rationale and tradeoffs;
- distinguish repository facts from recommendations;
- distinguish local evidence from AWS environment evidence;
- conclude with a practical learning recap;
- do not create extra tutorial documents unless requested.

Educational mode does not weaken task scope, validation, evidence, security,
or AWS authorization requirements.

## AWS evidence and research

- Use the installed `aws-core` plugin from Agent Toolkit for AWS and current AWS primary documentation for AWS decisions.
- Retrieve applicable `aws-core` skills and verify service behavior and regional availability when they affect the design.
- Do not rely on memory for IAM, quotas, networking, service behavior, encryption, recovery, cost, or deployment guidance.
- Distinguish recommendations from verified repository facts.
- Distinguish local evidence from deployed AWS evidence.

## AWS mutation safety

Before any AWS-changing command, verify:

- profile or role;
- account identity;
- Region `{{AWS_REGION}}`;
- environment and stack;
- exact resources in scope;
- billable impact;
- reversibility;
- rollback and teardown;
- explicit authorization.

Run read-only discovery through `AWS-10` first. BUILD-10, BUILD-20, and
RELEASE-10 never execute AWS mutations directly; every deployment or corrective
mutation routes through `AWS-20`, and deployed evidence routes through `AWS-30`.

A current Gate B `fast-dev` envelope is prospective AWS authorization only when
it names the exact development account or alias, profile or role, Region,
environment, stack, allowed operations and resources, cost ceiling, rollback,
prohibited actions, immutable artifact digest or deterministic derivation rule,
and finite future validity. Its environment classification must be
`NON_PRODUCTION`. A derivation rule names SHA-256 and the full authorized
baseline commit. Immediately before mutation, re-identify the caller and
prove the final IaC diff is fully contained in that envelope. Any mismatch,
production target, destructive or replacement action, IAM broadening, public
sensitive-data exposure, shared or unowned resource, or scope or cost drift
routes to `explicit-gate` and stops.

For `explicit-gate`, accept deployment authorization only as the exact complete
`AUTHORIZE AWS DEPLOYMENT` receipt defined in the canonical prompt pack, with
current IDs and values matching AWS-10. Record the receipt verbatim with its
observed ISO 8601 time and exact source. Teardown always requires the separate
exact `AUTHORIZE AWS TEARDOWN` receipt and routes through AWS-40/AWS-50. These
are conditional action authorizations, not routine lifecycle gates.

Never:

- use AWS root credentials;
- commit credentials, secrets, tokens, keys, kubeconfig, or secret-bearing parameters;
- weaken IAM, networking, encryption, validation, or logging to bypass failures;
- expose private data stores without an approved requirement;
- deploy, destroy, rotate secrets, or mutate data without explicit approval;
- claim AWS evidence without observing it.

## Well-Architected impact rule

For each meaningful requirement, design decision, and task, identify relevant effects on:

- Operational Excellence;
- Security;
- Reliability;
- Performance Efficiency;
- Cost Optimization;
- Sustainability.

Record requirements and design in `PRD.md`, executable work in `TASKS.md`, proof in `VERIFY.md`, and procedures in `RUNBOOK.md`.

## Documentation policy

Do not create new planning, status, design, security, traceability, audit, lifecycle, or pillar documents unless explicitly requested.

Before creating a document, determine whether the content belongs in:

- `PRD.md`;
- `BUGFIX.md`;
- `TASKS.md`;
- `VERIFY.md`;
- `RUNBOOK.md`;
- a GitHub Issue or pull request;
- code, tests, schemas, or IaC;
- a narrowly scoped ADR.

One fact must have one authoritative home.

## Completion standard

Work is complete only when:

- the requested outcome is implemented;
- the task acceptance criteria pass;
- relevant example and property-based tests pass;
- security and failure paths are handled;
- affected IaC validates;
- `VERIFY.md` reflects actual evidence;
- operational changes are reflected in `RUNBOOK.md`;
- task and GitHub status are synchronized when authorized, or clearly `PENDING_SYNC`;
- remaining AWS-only checks are clearly pending rather than passed.
