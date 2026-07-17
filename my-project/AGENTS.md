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

## Requirements-analysis gate

Before writing or approving technical design, analyze the full requirement set together.

Check for:

- logical inconsistencies;
- ambiguous terms or unmeasurable outcomes;
- conflicting functional and non-functional constraints;
- undefined concepts and unstated assumptions;
- missing boundary, failure, security, concurrency, and recovery cases;
- requirements that cannot be verified objectively;
- incompatible cost, availability, performance, privacy, or regional constraints.

Record findings in the `PRD.md` requirements-analysis section.

Design readiness must be one of:

- `BLOCKED`
- `READY_WITH_ACCEPTED_ASSUMPTIONS`
- `READY_FOR_DESIGN`

Do not silently design around an unresolved contradiction.

## Required Codex workflow

1. Read this file and every applicable nested `AGENTS.md`.
2. Determine feature-spec or bugfix-spec mode.
3. Read the relevant `PRD.md` or `BUGFIX.md` sections.
4. Inspect existing code, tests, IaC, configuration, and Git history.
5. Analyze requirements before completing or changing design.
6. Complete the relevant architecture, data-flow, error-handling, and testing sections in `PRD.md`.
7. Generate or update discrete tasks in `TASKS.md`.
8. Validate dependencies and sort tasks into waves with `scripts/task_waves.py`.
9. Execute one task or one safe wave.
10. Mark a task `IN_PROGRESS` before implementation.
11. Update its execution log with meaningful progress, blockers, and validation.
12. Mark it `DONE` only when acceptance criteria and required local evidence pass.
13. Record produced evidence in `VERIFY.md`.
14. Update `RUNBOOK.md` only when repeatable operating procedures change.
15. Synchronize non-trivial tasks to GitHub Issues by the end of the workday.
16. Create an ADR only for a consequential, difficult-to-reverse decision.

## Task checklist and execution contract

`TASKS.md` is the live execution checklist.

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

## GitHub synchronization contract

`.github/ISSUE_TEMPLATE/` contains issue forms, not task records.

Actual task tracking lives in GitHub Issues.

For each non-trivial task:

- include the stable task ID in the issue;
- attach the issue as a native sub-issue of the release parent where supported;
- preserve dependencies and wave information;
- link the implementation pull request;
- mirror status and blockers by the end of the workday;
- summarize validation and evidence without copying entire logs.

`TASKS.md` remains the live execution source during a session. GitHub is the durable mirror for project visibility and collaboration.

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

- Use configured AWS MCP tools and current AWS primary documentation for AWS decisions.
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
- task and GitHub status are synchronized;
- remaining AWS-only checks are clearly pending rather than passed.
