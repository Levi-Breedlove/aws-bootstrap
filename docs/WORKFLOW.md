# AWS Codex Fastlane Workflow

Fastlane turns an idea into owner-approved requirements, an AWS-informed
technical design, and a build constrained by an explicit construction boundary.

## Start

Send:

```text
init template
```

Codex welcomes the owner and asks once for:

1. project name;
2. preferred AWS Region; and
3. development budget posture.

Use a finite cap with currency when one exists, or answer
`minimize cost; no hard cap`. Codex initializes or resumes the project, runs
the doctor, and immediately begins the next lifecycle prompt. A configured
project never returns to BOOT-00 merely because AWS Core is unavailable.

## Lifecycle

| Phase | Outcome | Owner decision |
|---|---|---|
| BOOT-00 | Repository initialized or safely resumed | None |
| INTAKE-10 / REQ-10 | Requirements, assumptions, cost posture, safeguards, and success criteria | Answer questions |
| Gate A / INTAKE-20 | Exact requirements revision reviewed | Approve requirements for design |
| DESIGN-10 | Technical PRD, current AWS evidence, and construction envelope | None until ready |
| Gate B / DESIGN-20 | Exact design and construction boundary reviewed | Approve construction |
| TASK-10 / BUILD | Dependency-aware tasks run inside the approved boundary | No task-by-task approval |
| RELEASE-10 | Release evidence evaluated | Only when the release contract requires it |
| AWS-10 | Read-only deployment preflight | No mutation authority |
| AWS-20 / AWS-50 | Exact authorized deployment or teardown | Separate expiring AWS authorization |
| AWS-30 / AWS-40 | Deployed evidence and residual review | Governed by the authorization and runbook |

Gate A — approve requirements → Gate B — approve the PRD and construction boundary → Codex builds autonomously inside that boundary.

## AWS Core throughout Fastlane

Fastlane prefers the current official
`aws-core@agent-toolkit-for-aws` from `aws/agent-toolkit-for-aws` whenever
current AWS facts materially affect:

- feasibility and requirements;
- service and Region fit;
- architecture, IAM, networking, encryption, and data protection;
- reliability, quotas, observability, and cost drivers;
- release readiness, deployment, rollback, operations, and teardown.

AWS Core is not a BOOT-00 or intake prerequisite. If it is absent at an
AWS-specific design or operating step, Codex pauses only that step and gives one
concise setup action. It never repeats completed intake.

DESIGN-10 and AWS-10 record fresh attributable `retrieve_skill` and
`search_documentation` results in `docs/project/VERIFY.md`. A generic
connector, cached prose, or model memory does not satisfy required evidence.
AWS Core advises; it cannot approve Gate A, Gate B, or an AWS change.

## Gate A

Gate A approves one exact requirements revision. It includes users, outcomes,
scope, data, failure behavior, access, security, recovery, cost posture, and
measurable success. It does not approve design, construction, GitHub mutation,
AWS access, or spending.

## Gate B

Gate B approves the exact current PRD and a construction envelope naming the
outcome, scope, write boundaries, prohibited work, task and retry limits,
checkpoints, GitHub permission, and planned AWS lane.

After Gate B, Codex can build normally without repeated approvals. A material
change in requirements, design, scope, risk, cost, or authority makes the
applicable gate stale and stops affected work.

## AWS authorization

An AWS lane describes intended access; it never grants access. Every AWS
mutation requires a separate current record naming:

- account, Region, and environment;
- allowed resources and operations;
- finite cost ceiling and billing dimensions;
- rollback or teardown plan; and
- expiration.

Tools, credentials, sandbox permission, prior access, or AWS Core availability
never replace this authorization.

## Resume behavior

The doctor selects the next prompt. Correct only the reported blocker, then
resume that prompt. BOOT-00 is rerun only for a real local initialization
problem, not for missing AWS research tooling or a repeated `init template`.
