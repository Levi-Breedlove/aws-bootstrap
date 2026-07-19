# AWS Repository Operating Guide

## Mission

Build and operate **My AWS Project** according to the approved requirements and design in `docs/project/PRD.md`.

## Immediate template entrypoint

When the owner says `init template`, `initialize template`, or `start Fastlane`,
route immediately through the repo-scoped `launch-fastlane` skill and `BOOT-00`.
Welcome the owner and explain that Fastlane turns an idea into owner-approved
requirements and a technical PRD, then builds only inside Gate B. Setup does not
access AWS. The short form means `THIS_REPOSITORY`; brownfield adoption requires
an explicit target. Before project questions or writes, run:

```
python scripts/bootstrap_dependencies.py --root . --json
```

It validates repo skills, read-only advisors, the immutable AWS Core pin, and
hook contract. `DECLARED_AND_PINNED` is not live plugin proof. Discover repo
assets in place; never copy them into a personal Codex directory.

The IDE extension cannot manage plugins. Give instructions only: never install
a Codex client, register a marketplace, change plugin state, or launch another
session for the owner. Tell the owner to open ChatGPT desktop Codex or an
interactive Codex CLI, open a terminal at this repository root, and run
`codex plugin marketplace add .` themselves. Then tell them to launch or reopen
this repository, enter `/plugins`, select **AWS Codex Fastlane Dependencies →
AWS Core**, and restart Codex. Do not run those Codex commands.

Ask the owner to run `uvx --version` visibly; do not execute a PATH-discovered
`uvx` as a setup probe. If missing, `scripts/uv_setup_assistant.py` may print one
precise official owner-run package-manager command. Never execute that command,
a package manager, an installer, or a runtime probe for the owner. Never read
Codex credentials or persist local client, plugin, trust, identity, or setup
state in the repository. After owner-managed runtime and plugin setup and
restart, check `python3`, inventory all
matching hooks, compare the exact pin, and stop on unknown or conflicting code.
Only the owner may trust the current definition; never bypass hook trust. Run
BOOT-00's inert deny and harmless allow probes before confirmation.

The hook only blocks direct Secrets Manager value retrieval; it grants no
authority. AWS Core is `AVAILABLE`, not automatic. After doctor and marketplace
checks, instruct the owner to select it through `/plugins`, restart, review and
trust the hook, and send:

```text
@AWS Core
VERIFY AWS CORE AND CONTINUE FASTLANE
```

Require live `retrieve_skill` and `search_documentation`; generic tools or
memory are not proof. Setup never calls `call_aws`/`run_script`, configures
credentials, or accesses AWS. Do not substitute the user-global AWS CLI wizard
for the reviewed pin. BOOT-00 uses Python 3.11+ standard-library scripts; do not
probe for `pytest` or run maintainer tests during initialization.

## How to use this guide

Ask the owner for project mode (`greenfield`/`brownfield`), delivery profile
(`quick-mvp`/`standard`/`high-risk`), and planned AWS lane
(`documentation-only`/`read-only`/`fast-dev`/`explicit-gate`). Record them in
docs/project/PRD.md, complete Gate A and Gate B, then continue inside the
approved boundary unless scope, risk, cost, authority, or observed state changes.

Codex loads this file automatically. The four repo skills hold task-specific
procedures; `operate-fastlane-aws` requires explicit invocation. The read-only
requirements, AWS, and evidence advisors may review facts but never approve a
gate or authorize AWS. The coordinator alone writes project ledgers, lifecycle
state, and GitHub state.

## Sources of truth

| Subject | Authoritative source |
|---|---|
| Feature requirements, user stories, acceptance criteria, architecture, and implementation approach | `docs/project/PRD.md` |
| Active defect analysis and regression expectations | `docs/project/BUGFIX.md` |
| Executable task checklist, dependencies, waves, and live work status | `docs/project/TASKS.md` |
| Verification and release evidence | `docs/project/VERIFY.md` |
| Build, deployment, rollback, recovery, and operations | `docs/project/RUNBOOK.md` |
| Machine-readable lifecycle and resume mirror | `bootstrap.yaml` (derived only; never authorization) |
| Consequential architectural decisions | `docs/adr/` |
| Durable project tracking and collaboration | GitHub Issues, Projects, and pull requests |
| Actual system behavior | Code, tests, schemas, configuration, and infrastructure |

When sources disagree, stop and identify the conflict. Do not silently invent a reconciliation.
`bootstrap.yaml` must agree with the authoritative Markdown records. A mismatch
is a stop condition; never use the mirror to infer or widen approval.

## Specification mode

Use docs/project/PRD.md for planned change and docs/project/BUGFIX.md for a
defect or regression. Separate mixed work unless safe correction requires both.

## Project choices — plain-language guide

Record these independent choices in `docs/project/PRD.md` before requirements approval:

- Project mode: `greenfield` or `brownfield`.
- Delivery profile: `quick-mvp`, `standard`, or `high-risk`.
- AWS lane: `documentation-only`, `read-only`, `fast-dev`, or `explicit-gate`.

Default a new small project to `quick-mvp` and `explicit-gate`.

Default planning to `MINIMIZE_TOTAL_COST; HARD_CAP_NOT_STATED` unless the owner
supplies a real limit. Preserve the exact owner-supplied ISO currency and amount
as `MINIMIZE_TOTAL_COST; HARD_CAP: <ISO_CURRENCY> <OWNER_AMOUNT>`; `USD 20.00`
is only an example and never a default or substituted value.
A budget is a ceiling, never a spending target. Gate A needs a cost posture,
not an invented number. AWS mutation still requires a finite positive ceiling
such as `USD: 20.00`, billing dimensions, alerts, rollback or teardown, and
expiry. The mutation ceiling covers the authorization-validity period and may
not exceed or change the currency of an owner hard cap.

A Quick MVP is one small, reversible development release. Use `high-risk` when
work involves production, sensitive or regulated data, payments, customer
isolation, shared infrastructure, irreversible data changes, or a potentially
large outage or cost increase. Also use it for consequential identity changes,
public exposure, multi-account or multi-Region coordination, or strict recovery
targets. Record the reason in `docs/project/PRD.md`.

The profile changes scope and review depth; it never reduces required testing
or approval. An AWS lane describes planned access; it does not authorize a
change. AWS changes require an approved record naming the account, Region,
environment, resources, operations, cost limit, rollback plan, and expiration.

Apply profiles without adding lifecycle gates. `quick-mvp` favors one observable
development outcome and minimal tasks; `standard` covers the intended
environment; `high-risk` uses smaller change batches and stronger review and
evidence for identity, data access, isolation, migration, recovery, shared
resources, and audit. All retain the same controls and authority model.

For a new application, evaluate a secure managed serverless baseline first.
Prefer the smallest pay-per-use design that meets the outcome and keeps idle
cost low. Require least-privilege access, encryption, protected secrets,
validated inputs, safe failures, and useful telemetry. Never weaken required
security, recovery, or evidence controls to save money.

Serverless-first is a starting hypothesis, not a forced architecture. Record a
different choice when verified workload fit is better. Keep boundaries and IaC
clear, record measurable expansion triggers, and do not provision early.

Gate A and Gate B each use one compact readiness card in docs/project/PRD.md. Fill every
listed field with explicit current facts and stable IDs. Use `NOT_APPLICABLE —
<reason>` only when genuinely inapplicable; never use it to avoid discovery.

## Agent reference — exact lifecycle and execution rules

## Two-gate lifecycle

This bootstrap has exactly two routine human decision points.

### Gate A — Requirements approval

Before design, interview the owner, draft PRD Part I, and record contradictions,
ambiguity, assumptions, missing boundary/failure/security/recovery behavior,
unmeasurable outcomes, and incompatible cost or operational constraints. The
recommendation is `BLOCKED`, `READY_WITH_PROPOSED_ASSUMPTIONS`, or
`READY_FOR_OWNER_APPROVAL`.

For a ready recommendation, set Gate A to `PENDING_OWNER_APPROVAL` and mirror
the same current REQ and gate states into `bootstrap.yaml` and
docs/project/TASKS.md. Do not leave an agent-ready gate marked `BLOCKED`.
Only the named human owner may accept assumptions and approve the exact current
revision. The Gate A receipt must also repeat the exact current cost posture;
the receipt, owner record, readiness card, and `bootstrap.yaml` must match.
Never infer approval from silence, continued work, status, or tools.
Design requires `APPROVED_FOR_DESIGN` with no blocking finding.

At either gate, reject `Codex`, `agent`, `automation`, `system`, `AI`, or any
other model or service as the recorded approver.

### Gate B — PRD and construction authorization

After design, propose one construction envelope naming outcome, scope, write
boundaries, prohibited work, task/concurrency/attempt limits, checkpoints,
GitHub permission, and AWS lane/boundaries. Before Gate B is pending, require a
local Git baseline, protected dirty-path record, and the PRD's canonical digest
of the complete envelope.

Only the owner may approve the exact design and envelope.
`READY_FOR_CONSTRUCTION_APPROVAL` becomes `PENDING_OWNER_APPROVAL` and mirrors
the exact REQ/DES/AUTH IDs, Gate B state, worker limit, baseline, and protected
paths into docs/project/TASKS.md and `bootstrap.yaml`. A valid owner receipt
changes all mirrors to `APPROVED_FOR_CONSTRUCTION` in one coordinator
checkpoint; record its observed time and source.

Then Codex may generate tasks and run safe waves without task-by-task approval.
Pause on a stop condition, stale state, exhausted boundary, missing authority,
or uncovered action.

Business approval does not widen the Codex sandbox or bypass platform approval
controls. Conversely, filesystem, network, GitHub, or AWS capability never
grants business authorization.

### Approval invalidation

- Requirements-controlled changes make both gates `STALE`.
- Design or construction-envelope changes make Gate B `STALE`.
- Material discoveries that change requirements, architecture, scope, risk,
  budget, or authority stop affected work and return to the applicable gate.
- Revision IDs are monotonic and never reused for changed content.

A stale Gate A routes to `INTAKE-10` when owner facts are missing and otherwise
to `REQ-10`. A stale Gate B with a current Gate A routes to `DESIGN-10`.
Construction remains stopped until the applicable gate is current again; stale
state is recoverable workflow state, not a reason to dead-end at STOP.

Do not silently design around an unresolved contradiction.

## Required Codex workflow

1. Read applicable `AGENTS.md` files and run/resume `BOOT-00`.
2. Run the dependency checker, configure/resume the template, and run the
   doctor. Static pins do not prove a live plugin or hook.
3. When the current surface cannot manage plugins, give the owner the exact
   supported-surface, marketplace, plugin-selection, restart, and hook-review
   instructions. Never install or launch Codex, register the marketplace, or
   change plugin state. The uv helper prints instructions only and may not
   execute a command. On the supported surface, finish the owner-approved hook
   review and explicit `@AWS Core`
   `retrieve_skill`/`search_documentation` handshake.
4. Use INTAKE-10 and REQ-10; stop for Gate A.
5. Use DESIGN-10; stop for Gate B.
6. Use TASK-10 and `task_waves.py` to create a current dependency graph.
7. Acquire one coordinator; use BUILD-10 or BUILD-20, atomic claims, bounded
   attempts, and evidence-backed completion.
8. Reconcile docs/project/TASKS.md, docs/project/VERIFY.md,
   docs/project/RUNBOOK.md, and `bootstrap.yaml` at checkpoints.
9. Sync GitHub only if Gate B permits; otherwise keep `PENDING_SYNC`.
10. Run AWS-10 read-only preflight before any AWS mutation; require an exact
    current authorization for AWS-20 or AWS-50.
11. Use ADRs only for consequential, hard-to-reverse decisions.

Release state is exactly `NOT_READY`, `READY_TO_DEPLOY`, or
`RELEASE_VERIFIED`. RELEASE-10 alone changes it. AWS-10 accepts only
READY_TO_DEPLOY; AWS-30 records deployed evidence and returns to RELEASE-10 for
the RELEASE_VERIFIED decision.

Task-plan state is `UNINITIALIZED`, `CURRENT`, or `STALE`; only `CURRENT` is
runnable. Use `scripts/task_waves.py` for all run, claim, status, checkpoint,
pause, completion, and resume transitions. Never hand-edit coordinator state.
Use monotonic run, task, checkpoint, and evidence IDs. Reconcile every
`IN_PROGRESS` task before pausing, and inspect a persisted `RUNNING` state before
resuming.

After each validated task or wave, inspect the integrated diff and record the
observed command/result, actor/time, tested commit/worktree/artifact, durable
source, and `LOCAL_PASS` or `VERIFIED` status in docs/project/VERIFY.md's
`Task completion evidence` table. Run the doctor before the next wave. The exact
commands and transition rules live in the `build-fastlane` skill, TASK-10,
BUILD-10, BUILD-20, and docs/project/TASKS.md.

## Task execution boundary

docs/project/TASKS.md is the live checklist. Generate and run tasks only while
Gate B is `APPROVED_FOR_CONSTRUCTION` and current. Each task must trace to the
approved REQ/DES/AUTH IDs, stay inside its write and external-state boundaries,
and use one legal status: `BACKLOG`, `READY`, `IN_PROGRESS`, `BLOCKED`, `DONE`,
or `SKIPPED`. Never renumber an existing task.

Run only `READY` tasks with satisfied dependencies. Parallelize only proven
disjoint work in isolated worktrees; serialize shared files, resources,
migrations, generated output, irreversible work, billable work, and all AWS
mutations. The coordinator is the sole writer of project ledgers, lifecycle
state, shared manifests, lockfiles, schemas, generated output, and GitHub state.
Workers edit only their assigned paths and return receipts.

## Brownfield preservation contract

Before changing an existing repository, record in `docs/project/PRD.md`:

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

## GitHub synchronization

Credentials and connector availability are not authorization. Sync GitHub only
when the current Gate B envelope permits it. Keep stable task IDs, dependencies,
status, blockers, pull-request links, and concise evidence aligned with
docs/project/TASKS.md. Otherwise leave `PENDING_SYNC` and make no GitHub changes.
Report drift instead of silently reconciling it.

## Testing and teaching

Use example, integration, end-to-end, property-based, security, recovery, and
deployed checks when the approved requirements make them relevant. Teaching
mode may explain decisions and evidence, but never weakens scope, testing,
security, gate, or AWS authorization rules and does not create extra documents.

## AWS evidence and research

- Setup-ready requires explicit `@AWS Core` invocation and successful
  `retrieve_skill` and `search_documentation` checks from the pinned plugin.
- Use current primary AWS documentation through AWS Core for material service,
  Region, IAM, quota, networking, encryption, recovery, observability, and cost
  facts. Never substitute memory.
- Gate A cannot be ready with a material feasibility fact unverified; Gate B
  requires checks for its design boundary.
- If AWS Core or a required capability fails, stop the affected gate/operation,
  record the gap, and route through BOOT-00 recovery.
- Separate recommendations from repository facts and local from deployed
  evidence. Advisors advise; only the owner approves gates and only an exact
  current AWS record authorizes mutation.

## AWS mutation safety

Before an AWS-changing command, verify profile/role, account, Region
`{{AWS_REGION}}`, environment, stack/resources, billable impact, reversibility,
rollback/teardown, and explicit authorization.

Run read-only discovery through `AWS-10` first. BUILD-10, BUILD-20, and
RELEASE-10 never execute AWS mutations directly; every deployment or corrective
mutation routes through `AWS-20`, and deployed evidence routes through `AWS-30`.

A `fast-dev` envelope is prospective authorization only when it names the exact
non-production identity, Region, environment, resources/operations, cost,
rollback, prohibitions, artifact digest or SHA-256 derivation from the approved
commit, and expiration. Re-identify the caller and prove the final IaC diff is
contained. Mismatch, production, destructive/replacement work, IAM broadening,
public sensitive-data exposure, shared/unowned resources, or scope/cost drift
routes to `explicit-gate` and stops.

For `explicit-gate`, accept deployment authorization only as the exact complete
`AUTHORIZE AWS DEPLOYMENT` receipt defined in the canonical prompt pack, with
current IDs and values matching AWS-10. Record the receipt verbatim with its
observed ISO 8601 time and exact source. Teardown always requires the separate
exact `AUTHORIZE AWS TEARDOWN` receipt and routes through AWS-40/AWS-50. These
are conditional action authorizations, not routine lifecycle gates.

Never:

- use AWS root credentials;
- store secrets in source, logs, receipts, or command history;
- weaken IAM, networking, encryption, validation, or logging;
- expose private data without an approved requirement;
- mutate without exact approval; or
- claim unobserved AWS evidence.

## Well-Architected impact

For meaningful requirements, designs, and tasks, record applicable Operational
Excellence, Security, Reliability, Performance Efficiency, Cost Optimization,
and Sustainability effects in the existing PRD, task, evidence, or runbook
record.

## Documentation policy

Do not create new planning, status, design, security, traceability, audit, lifecycle, or pillar documents unless explicitly requested.

Before creating a document, determine whether the content belongs in:

- `docs/project/PRD.md`;
- `docs/project/BUGFIX.md`;
- `docs/project/TASKS.md`;
- `docs/project/VERIFY.md`;
- `docs/project/RUNBOOK.md`;
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
- `docs/project/VERIFY.md` reflects actual evidence;
- operational changes are reflected in `docs/project/RUNBOOK.md`;
- task and GitHub status are synchronized when authorized, or clearly `PENDING_SYNC`;
- remaining AWS-only checks are clearly pending rather than passed.
