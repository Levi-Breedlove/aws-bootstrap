# AWS Codex Fastlane Operating Guide

## Mission and routing

Fastlane turns ideas into approved requirements, AWS designs, tasks, and
evidence. Use `fastlane` as the single coordinator and sole writer.
It follows the doctor-selected route; initialized projects never repeat setup.
Use `maintain-fastlane` only for engine work; it never starts adopter intake.
`launch-fastlane`, `plan-fastlane`, and `build-fastlane` are
compatibility aliases that delegate to `fastlane`. `explain-fastlane` and
`operate-fastlane-aws` are explicit-only. `LEARN-10` is only a compatibility
alias for `explain-fastlane`, never an automatic route.

## Sources of truth

| Subject | Authority |
|---|---|
| Requirements, design, gates, construction envelope | `docs/project/PRD.md` |
| Active defect contract | `docs/project/BUGFIX.md` |
| Tasks, dependencies, waves, execution state | `docs/project/TASKS.md` |
| Observed evidence | `docs/project/VERIFY.md` |
| Deploy, rollback, recovery, operations, teardown | `docs/project/RUNBOOK.md` |
| Consequential architecture decisions | `docs/adr/` |
| Derived lifecycle mirror | `bootstrap.yaml` (never authorization) |
| Engine and package inventory | `bootstrap.manifest.json` |
| Actual behavior | Code, tests, schemas, configuration, and IaC |

Stop on disagreement; never create duplicate authority. Nested `AGENTS.md`
files may narrow but never widen root authority.

## Invariants

- Fastlane has exactly two routine owner gates: Gate A for requirements and
  Gate B for the PRD plus construction boundary.
- Only the owner may accept assumptions, approve gates, or authorize external
  actions. Reject `Codex`, `agent`, `automation`, `system`, `AI`, or a service
  as approver.
- Credentials and connector availability are not authorization. Tool access
  never widens the approved filesystem, GitHub, Codex, or AWS boundary.
- Requirements-controlled changes make both gates stale. Design or envelope
  changes make Gate B stale.
- A stale Gate B with a current Gate A routes to `DESIGN-10`.
- The coordinator is the only writer. Challengers are read-only and cannot
  choose scope or architecture, edit files, approve gates, satisfy AWS
  evidence, or authorize actions.
- Deterministic scripts decide lifecycle state, receipt validity, task
  readiness, stale approvals, evidence completeness, and package integrity.
- Never claim a test, AWS fact, deployment, or recovery result not observed.
- Do not leave an agent-ready gate marked `BLOCKED`; transition it to the
  matching pending-owner state and synchronize its derived snapshots.

## Project choices and safeguards

Record project mode (`greenfield` or `brownfield`), delivery profile
(`quick-mvp`, `standard`, or `high-risk`), and planned AWS lane
(`documentation-only`, `read-only`, `fast-dev`, or `explicit-gate`) before
Gate A. A Quick MVP is one small, reversible development release. Use
`high-risk` for production, sensitive or regulated data, payments, identity,
customer isolation, shared infrastructure, irreversible changes, or large
outage or cost impact. Profiles adjust depth without adding lifecycle gates
or reducing approval, tests, safeguards, or evidence.

Default cost posture to `MINIMIZE_TOTAL_COST; HARD_CAP_NOT_STATED`. Preserve an
owner cap as `MINIMIZE_TOTAL_COST; HARD_CAP: <ISO> <AMOUNT>`. A cap is a
ceiling, not a spending target or guaranteed billing stop. Evaluate a secure
managed serverless baseline for greenfield work, then select verified workload
fit. Never weaken an invariant, identity, least privilege, encryption, secrets,
validation, isolation, recovery, logging, or evidence to reduce cost.

An AWS lane describes planned access; it does not authorize a change. AWS
mutation requires an exact current record naming account, Region, environment,
resources, operations, finite positive cost ceiling, rollback, and expiration.

## Lifecycle

Run `python scripts/bootstrap_doctor.py --root . --json` before routing and
after each checkpoint. Load exactly one phase reference from
`.agents/skills/fastlane/references/` and its canonical prompt section.

1. BOOT-00 initializes or resumes without repeating setup.
2. INTAKE-10 and REQ-10 create measurable requirements and analysis; ask at
   most three related decisions per response.
3. Gate A requires the exact current owner receipt and no blocking finding.
4. DESIGN-10 completes whole-system design and current material AWS evidence.
5. Gate B requires the exact current receipt and construction-envelope digest.
6. TASK-10 and BUILD-10/BUILD-20 execute only current approved local work.
   Route AWS mutation through AWS-10/AWS-20; BUILD never deploys.
7. RELEASE-10, AWS-10 through AWS-50, and teardown retain exact evidence and
   authorization contracts.

After valid Gate A, record approval and continue to design. After valid Gate B,
record approval, generate tasks, and continue permitted local construction.
Stop only for owner decisions, stale scope, failed validation, unavailable
material evidence, exhausted boundaries, or missing external authority.

## Challengers and explanation

Quick MVP uses no subagent by default. Use
`fastlane-requirements-challenger` only for ambiguity, contradictions,
sensitive data, identity, payments, migrations, shared interfaces, high risk,
or explicit owner request. Use `fastlane-architecture-challenger` only after a
completed proposal and only for high-risk, hard-to-reverse, shared
infrastructure, isolation, recovery, or explicit owner request. The
coordinator evaluates findings and remains the only writer.

Use `explain-fastlane` only when explicitly invoked or when the owner asks to
teach. It changes no state and restores the pending owner action.

## Tasks, tests, and evidence

Run only `READY` tasks with satisfied dependencies. Preserve task IDs, write
boundaries, attempts, checkpoints, and legal transitions. Use
`scripts/task_waves.py`. Update `Task completion evidence` after passing work.

Trace approved requirements through acceptance criteria, `PROP-*`, design,
tasks, tests, minimized counterexamples, and evidence. Preserve seeds and
classify a property failure before correcting implementation, property, or
requirement. Never weaken an invariant or generator, discard a seed, or hide a
failure.

## AWS Core and external actions

Use current official AWS Core (`aws-core@agent-toolkit-for-aws`) from
`aws/agent-toolkit-for-aws` for material current AWS facts. Do not pin its
version or commit. AWS Core is not required for BOOT-00, ordinary intake, or
Gate A. Generic connectors, memory, challengers, and installation metadata
cannot satisfy required live AWS evidence. Missing capability pauses only the
affected material AWS step.

Plugin installation and native trust are owner-managed. Do not install
software, change plugin state, inspect private trust storage, compare hook
hashes, inspect credentials, or access an AWS account during planning.

GitHub synchronization requires current Gate B authority or the owner's
explicit request; otherwise keep `PENDING_SYNC`. AWS mutation uses AWS-10 and
the exact AWS-20 receipt; teardown uses AWS-40/AWS-50 and its exact receipt.

## Brownfield and completion

Before brownfield writes, record baseline behavior, tests, interfaces, data,
security, user changes, migration constraints, and rollback. Preview collisions.
Adoption requires the owner's complete ordered decision map. Preserve user work.

Complete only when the approved outcome is implemented, applicable checks
pass, VERIFY and RUNBOOK hold observed evidence, and authorized external
tracking is reconciled or explicitly pending.

## Agent reference

- Application code: `app/AGENTS.md`
- Infrastructure and AWS operations: `infrastructure/AGENTS.md`
- Engine scripts: `scripts/AGENTS.md`
- Tests: `tests/AGENTS.md`
- Phase procedures: `.agents/skills/fastlane/references/`
- Exact receipts and compatibility IDs: `prompts/CODEX-PROMPTS.md`
