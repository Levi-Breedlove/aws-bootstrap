# Verification and Release Evidence

## Scope

| Field | Value |
|---|---|
| Workload | My AWS Project |
| Release | TODO |
| Commit, tag, or image digest | TODO |
| Environment | TODO |
| AWS account alias or non-secret ID | TODO |
| Region | {{AWS_REGION}} |
| Last reviewed | TODO |
| Reviewer | TODO |

## Status vocabulary

| Status | Meaning |
|---|---|
| `NOT_STARTED` | No implementation or evidence exists |
| `IMPLEMENTED` | Code exists; verification is incomplete |
| `LOCAL_PASS` | Required local checks passed |
| `PENDING_AWS` | Requires deployed AWS or external evidence |
| `VERIFIED` | Required evidence passed in the correct environment |
| `FAILED` | Verification ran and failed |
| `BLOCKED` | A known dependency prevents verification |
| `NOT_APPLICABLE` | Excluded with rationale |

## Evidence rules

- Documentation is not implementation evidence.
- Implementation is not test evidence.
- Mocks do not prove live integrations.
- Local success does not prove AWS behavior.
- Evidence identifies version and environment.
- Stale evidence cannot remain verified.
- Manual evidence records who, when, where, and what was observed.
- Property-based tests prove general invariants within their generated domain; they do not replace deployed AWS evidence.

## Verification matrix

| ID | PRD / property IDs | Task IDs | GitHub Issues | Requirement or invariant | Automated evidence | AWS/manual evidence | Status |
|---|---|---|---|---|---|---|---|
| FUNC-001 | FR-001 | TASK-001 | TODO | Primary outcome succeeds | TODO | TODO | `NOT_STARTED` |
| SEC-001 | SEC-001, SEC-002, PROP-001 | TODO | TODO | Protected operations enforce authentication and authorization | TODO | TODO | `NOT_STARTED` |
| REL-001 | REL-001, REL-002, PROP-002, PROP-004 | TODO | TODO | Retry and duplicate behavior is safe | TODO | TODO | `NOT_STARTED` |
| OPS-001 | TODO | TODO | TODO | Deployment is repeatable and observable | TODO | TODO | `NOT_STARTED` |
| PERF-001 | TODO | TODO | TODO | Performance target is met | TODO | TODO | `NOT_STARTED` |
| COST-001 | TODO | TODO | TODO | Budget and cleanup controls are effective | TODO | TODO | `NOT_STARTED` |

Add rows for material workload risks, not every individual test.

## Property-based test evidence

| Property ID | Framework or suite | Generated cases or runs | Seed or reproduction info | Result | Evidence |
|---|---|---|---|---|---|
| PROP-001 | TODO | TODO | TODO | `NOT_STARTED` | TODO |

Record failing seeds or minimal counterexamples in the relevant task, issue, or test output.

## Release gates

| Gate | Required condition | Status |
|---|---|---|
| Requirements | Analysis gate allows design and implementation | `NOT_STARTED` |
| Design | Architecture and testing strategy are approved | `NOT_STARTED` |
| Tasks | Task dependencies validate, waves are ordered, and required tasks are complete | `NOT_STARTED` |
| Build | Formatting, linting, typing, tests, and packaging pass | `NOT_STARTED` |
| Infrastructure | IaC and policy checks pass | `NOT_STARTED` |
| Security | No unresolved release-blocking security findings | `NOT_STARTED` |
| Reliability | Failure, recovery, and rollback paths pass | `NOT_STARTED` |
| Performance | Required targets pass | `NOT_STARTED` |
| Deployment | AWS deployment and smoke tests pass | `NOT_STARTED` |
| Operations | Monitoring, restore, rollback, and teardown are usable | `NOT_STARTED` |
| Cost | Budget controls and cost review pass | `NOT_STARTED` |

## Known gaps and accepted risks

| ID | Risk or gap | Severity | Owner | Review date | Rationale |
|---|---|---|---|---|---|
| TODO | TODO | TODO | TODO | TODO | TODO |

## Current release decision

- Decision: `NOT_READY`
- Blocking IDs: TODO
- Accepted risks: None
- Next evidence required: TODO
