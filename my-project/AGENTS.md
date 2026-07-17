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
| Consequential architectural decisions | `docs/adr/` |
| Durable project tracking and collaboration | GitHub Issues, Projects, and pull requests |
| Actual system behavior | Code, tests, schemas, configuration, and infrastructure |

When sources disagree, stop and identify the conflict. Do not silently invent a reconciliation.

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

Only the owner can accept named assumptions and approve the current
requirements revision. Codex must not infer approval from silence, continued
conversation, a task status, or tool access. Design may start only when Gate A
is `APPROVED_FOR_DESIGN`, the approved revision matches the current revision,
and no blocking finding remains open.

### Gate B — PRD and construction authorization

After technical design, Codex proposes one bounded construction envelope in
`PRD.md`. It names the approved outcome and scope, exact write boundaries,
prohibited work, task and concurrency limits, investigation or attempt budget,
checkpoint policy, GitHub permission, and AWS lane and boundaries.

Only the owner can approve the current design revision and proposed envelope.
Task generation and implementation may start only when Gate B is
`APPROVED_FOR_CONSTRUCTION` and its approved requirements and design revisions
match the current revisions.

Once Gate B is current, Codex should generate tasks and continue through safe
implementation waves without routine task-by-task approval. It pauses only for
a declared stop condition, stale approval, exhausted boundary, unavailable
authority, or an action that the approved envelope does not cover.

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

Do not silently design around an unresolved contradiction.

## Required Codex workflow

1. Read this file and every applicable nested `AGENTS.md`.
2. Run or resume `BOOT-00` and determine greenfield or brownfield mode.
3. Determine feature-spec, bugfix-spec, or mixed mode.
4. Use `INTAKE-10` and `REQ-10` to draft and analyze requirements.
5. Stop for explicit owner approval at Gate A.
6. Use `DESIGN-10` to complete architecture, data flow, error handling, and testing design.
7. Stop for explicit owner approval at Gate B.
8. Generate discrete tasks with `TASK-10` inside the approved envelope.
9. Validate dependencies and waves with `scripts/task_waves.py`.
10. Execute one task with `BUILD-10` or long-run safe waves with `BUILD-20`.
11. Mark a task `IN_PROGRESS` before implementation and `DONE` only after its acceptance criteria and required local evidence pass.
12. Record meaningful progress, blockers, deviations, and validation in the task log.
13. Record produced evidence in `VERIFY.md` and update `RUNBOOK.md` only when repeatable procedures change.
14. Synchronize GitHub only when the current Gate B envelope permits it; otherwise preserve `PENDING_SYNC`.
15. Use read-only AWS preflight before any deployment and require a fully matching AWS authorization envelope for mutation.
16. Create an ADR only for a consequential, difficult-to-reverse decision.

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

Tasks in the same wave may execute concurrently only when they have disjoint write sets and no shared mutable AWS or application state.

Serialize tasks that:

- edit overlapping files;
- modify the same infrastructure stack or resource;
- run migrations against the same data store;
- depend on shared generated output;
- require irreversible or billable actions;
- have unresolved assumptions.

AWS mutations require explicit authorization regardless of wave eligibility.

## Brownfield preservation contract

Before changing an existing repository, record in `PRD.md`:

- the baseline commit or working-tree state and pre-existing test results;
- current architecture, infrastructure ownership, and known failures;
- dirty or user-owned changes that must be preserved;
- in-scope components and exact write boundaries;
- protected behavior, files, resources, interfaces, and compatibility limits;
- migration, import, shared-resource, and rollback constraints;
- unresolved bootstrap overlay collisions.

Bootstrap overlay is preview-only until every collision is understood. Do not
overwrite existing planning files, code, infrastructure, configuration, or user
changes to make the template fit. Brownfield mode does not add a routine third
gate; stop only when preservation, ownership, migration, destructive-change,
or scope boundaries require a decision.

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

Run read-only discovery first.

A current Gate B `fast-dev` envelope is prospective AWS authorization only when
it names the exact development account or alias, profile or role, Region,
environment, stack, allowed operations and resources, cost ceiling, rollback,
and prohibited actions. Immediately before mutation, re-identify the caller and
prove the final IaC diff is fully contained in that envelope. Any mismatch,
production target, destructive or replacement action, IAM broadening, public
sensitive-data exposure, shared or unowned resource, or scope or cost drift
routes to `explicit-gate` and stops.

Teardown always requires its own exact deletion and retention authorization.

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
