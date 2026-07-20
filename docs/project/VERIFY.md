# My AWS Project — Verification and Release Evidence

`docs/project/VERIFY.md` records observed proof, not plans or authorization. Gate A and Gate B
remain the only routine human gates. The checks below determine construction and
release readiness inside the current approved envelope; they are not additional
human gates.

## Active evidence scope

| Field | Value |
|---|---|
| Workload | My AWS Project |
| Release | TODO |
| Release state | `NOT_READY` |
| Requirements revision | `REQ-0001` |
| Design revision | `DES-0001` |
| Construction authorization | `AUTH-0001` |
| Run ID | `NONE` |
| Checkpoint | `NONE` |
| Commit, tag, or image digest | TODO |
| Evidence cutoff | TODO (ISO 8601 with timezone) |
| Environment | TODO |
| AWS account alias or non-secret ID | TODO / `NOT_APPLICABLE` |
| Region | {{AWS_REGION}} / `NOT_APPLICABLE` |
| Last reviewed | TODO |
| Reviewer | TODO |

These values identify the evidence set; they do not grant repository, GitHub,
or AWS authority. All external actions remain conditional on the current AUTH.

## Evidence status vocabulary

| Status | Meaning |
|---|---|
| `NOT_STARTED` | No implementation or evidence exists |
| `IMPLEMENTED` | Code exists; verification is incomplete |
| `LOCAL_PASS` | Required local checks passed for the identified revision |
| `PENDING_AWS` | Required live AWS or external evidence has not been observed |
| `VERIFIED` | Required evidence passed for the identified artifact and environment |
| `FAILED` | Verification ran and failed |
| `BLOCKED` | A known dependency prevents verification |
| `STALE` | Earlier evidence no longer matches the current revision, artifact, environment, or target state |
| `NOT_APPLICABLE` | Excluded with an explicit rationale |

`STALE` never satisfies a readiness check. A task may be `DONE` when its
authorized task-level local criteria pass while a required live check remains
`PENDING_AWS`; the release remains not ready until that evidence is observed.

## Evidence rules

- Documentation is not implementation evidence, and implementation is not test
  evidence.
- Mocks do not prove live integrations. Local success does not prove AWS
  behavior.
- Every evidence item identifies its requirement/task, command or observation,
  actor, timestamp, commit or digest, environment, result, and durable source.
- Worker receipts are evidence candidates. The coordinator reconciles them
  against changed paths and observed outputs before recording them here.
- Manual evidence says who observed what, when, where, and by which identity,
  without exposing secrets.
- Mark evidence `STALE` when REQ/DES/AUTH, the tested code or artifact, relevant
  configuration, environment, or target state changes.
- Property-based tests prove invariants only within their generated domain and
  do not replace deployed evidence, security review, or recovery rehearsal.
- Preserve failing output, reproduction seeds, and partial external results.
  Never rewrite a failure as not run.
- GitHub and AWS evidence may be read or written only within current AUTH. Use
  `PENDING_SYNC` or `PENDING_AWS` when authority or access is unavailable.

Assign every recorded evidence item one monotonic `EV-nnnn` ID, beginning with
`EV-0001`. Task Evidence fields cite these exact IDs. Requirement, property,
baseline, authorization, and task IDs remain traceability fields, not alternate
evidence-ID formats.

## AWS Core evidence

This ledger proves observed use of the official
`aws-core@agent-toolkit-for-aws` plugin; installation metadata, generic AWS
connectors, cached content, prior conversation, and prose claims are not proof.
BOOT-00, DESIGN-10, and AWS-10 each require fresh successful observations of
both `retrieve_skill` and `search_documentation`, with one independently
attributed result row for each capability. A failed, missing, stale,
wrong-source, or unattributed BOOT-00 row blocks intake; the same condition at
DESIGN-10 blocks Gate B readiness and at AWS-10 blocks AWS execution planning.

Every completed row must come from observed live calls through
`aws-core@agent-toolkit-for-aws` and source `aws/agent-toolkit-for-aws`. Every
passing row uses observation actor `CODEX_LIVE_TOOL_CALL`, records the observed
current semantic plugin version without pinning it to the last-tested version,
and records `Credentials inspected` and `AWS account accessed` as exactly
`NO`. Both rows for a phase use the same observed version.

BOOT-00 requests skill `aws-serverless` and records the nonempty canonical
identifier returned by `retrieve_skill`. Its `search_documentation` query is
exactly `AWS Lambda security best practices for serverless applications,
including least-privilege IAM and input validation` and its source references
include returned official AWS documentation. Other phases also record the
requested and returned skill identifiers or documentation query and returned
official AWS references, as applicable.

Do not record credentials, local plugin/cache paths, usernames, session
identifiers, hook-trust state or trust-database data, secrets, or private
machine information. Every passing row also records an ISO 8601 observation
time and a current binding: `bootstrap:<Fastlane version>` for BOOT-00, the
current DES revision for DESIGN-10, or the Active evidence scope artifact for
AWS-10.

| Phase | Plugin source | Invoked plugin identity | Observed plugin version | Capability | Observation actor | Requested skill | Returned skill identifier | Documentation query | Source references | Design decision influenced | Credentials inspected | AWS account accessed | Observed at | Evidence binding | Observed status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `BOOT-00` | TODO | TODO | TODO | `retrieve_skill` | TODO | `aws-serverless` | TODO | — | — | Setup capability handshake | `NO` | `NO` | TODO | TODO | `NOT_STARTED` |
| `BOOT-00` | TODO | TODO | TODO | `search_documentation` | TODO | — | — | `AWS Lambda security best practices for serverless applications, including least-privilege IAM and input validation` | TODO | Setup capability handshake | `NO` | `NO` | TODO | TODO | `NOT_STARTED` |
| `DESIGN-10` | TODO | TODO | TODO | `retrieve_skill` | TODO | TODO | TODO | — | — | TODO | `NO` | `NO` | TODO | TODO | `NOT_STARTED` |
| `DESIGN-10` | TODO | TODO | TODO | `search_documentation` | TODO | — | — | TODO | TODO | TODO | `NO` | `NO` | TODO | TODO | `NOT_STARTED` |
| `AWS-10` | TODO | TODO | TODO | `retrieve_skill` | TODO | TODO | TODO | — | — | TODO | `NO` | `NO` | TODO | TODO | `NOT_STARTED` |
| `AWS-10` | TODO | TODO | TODO | `search_documentation` | TODO | — | — | TODO | TODO | TODO | `NO` | `NO` | TODO | TODO | `NOT_STARTED` |

## Task completion evidence

This is the machine-checked local evidence ledger for `DONE` transitions. One
unfenced row must exist for every local `EV-nnnn` reference. It names exactly
one task, observed work rather than a plan, the observing actor and time, the
tested commit/worktree/artifact, and a durable local source. Only `LOCAL_PASS`
or `VERIFIED` satisfies task completion; a stock, duplicate, wrong-task,
`NOT_STARTED`, URL-only, or placeholder row does not.

| Evidence ID | Task | Command or observation | Result | Actor | Observed at | Commit / worktree / artifact | Durable source | Status |
|---|---|---|---|---|---|---|---|---|
| EV-0001 | TODO | TODO | TODO | TODO | TODO | TODO | TODO | `NOT_STARTED` |

## Brownfield baseline and regression evidence

Complete this section for brownfield work. For greenfield work, set rows to
`NOT_APPLICABLE`.

| Evidence ID | Baseline commit/environment | Command or observation | Pre-existing result | Post-change result | Attribution and protected behavior | Status |
|---|---|---|---|---|---|---|
| EV-0201 | TODO | TODO | TODO | TODO | TODO | `NOT_STARTED` |

Do not treat a known baseline failure as a new regression, or a newly introduced
failure as accepted debt. If attribution is uncertain, stop affected work and
preserve both states.

## Verification matrix

| Evidence ID | PRD / property IDs | Task IDs | Requirement or invariant | Automated evidence | AWS/manual evidence | Artifact/environment | Status |
|---|---|---|---|---|---|---|---|
| EV-0101 | FR-001 | TODO | Primary outcome succeeds | TODO | TODO | TODO | `NOT_STARTED` |
| EV-0102 | SEC-001, SEC-002, PROP-001 | TODO | Protected operations enforce authentication and authorization | TODO | TODO | TODO | `NOT_STARTED` |
| EV-0103 | REL-001, REL-002, PROP-002, PROP-004 | TODO | Retry and duplicate behavior is safe | TODO | TODO | TODO | `NOT_STARTED` |
| EV-0104 | TODO | TODO | Deployment is repeatable and observable | TODO | TODO | TODO | `NOT_STARTED` |
| EV-0105 | TODO | TODO | Performance target is met | TODO | TODO | TODO | `NOT_STARTED` |
| EV-0106 | TODO | TODO | Budget and cleanup controls are effective | TODO | TODO | TODO | `NOT_STARTED` |

Add rows for material workload risks, not every individual test.

## Property-based test evidence

| Property ID | Framework or suite | Generated cases or runs | Seed or reproduction info | Result | Evidence source |
|---|---|---|---|---|---|
| PROP-001 | TODO | TODO | TODO | `NOT_STARTED` | TODO |

## Construction and release readiness checks

Only Gate A and Gate B are owner approval gates. Everything below is an
evidence-based readiness check performed within the active authorization.

| Check | Required condition | Status |
|---|---|---|
| Requirements identity | Gate A remains current for the active REQ revision | `NOT_STARTED` |
| Construction identity | Gate B remains current for matching REQ/DES/AUTH IDs | `NOT_STARTED` |
| AWS design grounding | Current DESIGN-10 has fresh successful official AWS Core `retrieve_skill` and `search_documentation` evidence | `NOT_STARTED` |
| Task graph | Dependencies validate, waivers are explicit, and required tasks are complete | `NOT_STARTED` |
| Build | Formatting, linting, typing, tests, and packaging pass | `NOT_STARTED` |
| Infrastructure | IaC, policy, and brownfield drift checks pass | `NOT_STARTED` |
| Security | No unresolved release-blocking security finding remains | `NOT_STARTED` |
| Reliability | Failure, recovery, idempotency, and rollback evidence passes | `NOT_STARTED` |
| Performance | Required targets pass for the identified artifact and environment | `NOT_STARTED` |
| Deployment | Required live deployment and smoke evidence is `VERIFIED` or explicitly not applicable | `NOT_STARTED` |
| Operations | Monitoring, restore, rollback, and authorized cleanup procedures are usable | `NOT_STARTED` |
| Cost | Observed and forecast cost remains inside the approved ceiling | `NOT_STARTED` |
| AWS execution grounding | Current AWS-10 has fresh successful official AWS Core operational and deployment evidence before any AWS execution plan | `NOT_STARTED` |

## Autonomous run receipts

The coordinator records one receipt after every safe wave and a final receipt
when the run completes or stops.

| Field | Receipt value |
|---|---|
| Run and checkpoint | TODO |
| REQ / DES / AUTH | `REQ-0001` / `DES-0001` / `AUTH-0001` |
| Tasks completed, blocked, or skipped | TODO |
| Attempts used and remaining | TODO |
| Changed paths and resulting commit/worktree | TODO |
| Commands and observed results | TODO |
| Evidence IDs | TODO |
| GitHub actions | `NONE` / exact authorized actions |
| AWS actions and identifiers | `NONE` / exact authorized actions without secrets |
| Boundary or preservation deviations | `NONE` / TODO |
| Completion or stop reason | TODO |
| Next safe action | TODO |

An AWS submission is not proof of completion. After a deployment, rollback, or
teardown attempt, use read-only evidence to record succeeded, failed, partial,
or unknown state before continuing.

## Action authorization provenance

This table proves which exact owner message was checked before an external
mutation; it does not itself authorize an action or widen Gate B. The stable
source must resolve to the complete verbatim receipt defined in docs/project/RUNBOOK.md and
the prompt pack.

| Action | Authorization ID | Construction AUTH | Stable owner-message source | Observed at | Verbatim receipt SHA-256 | Preflight evidence | Identity and boundary match | Result |
|---|---|---|---|---|---|---|---|---|
| Deployment | TODO | `AUTH-0001` | TODO | TODO (ISO 8601 with timezone) | TODO | TODO / `NONE` | TODO | `NOT_STARTED` |
| Teardown | TODO | `AUTH-0001` | TODO | TODO (ISO 8601 with timezone) | TODO | TODO / `NONE` | TODO | `NOT_STARTED` |

For an AWS mutation, record the authorization source and receipt digest before
execution, then link the AWS-10 or AWS-40 identity/boundary evidence. Record
`FAILED` or `BLOCKED` on any mismatch. Deployment evidence is reconciled by
AWS-30; residual and teardown evidence is reconciled read-only after AWS-50.

## Known gaps and accepted risks

| ID | Risk or gap | Severity | Owner | Review date | Rationale and authority |
|---|---|---|---|---|---|
| TODO | TODO | TODO | TODO | TODO | TODO |

An accepted risk cannot contradict a requirement or exceed AUTH. A material
scope, security, data, cost, or preservation decision routes back to the
applicable Gate A or Gate B owner decision.

## Current release decision

- Release state: `NOT_READY`
- Active evidence cutoff: TODO
- Blocking or stale evidence IDs: TODO
- Pending AWS evidence IDs: TODO / `NONE`
- Accepted risks: `NONE`
- Last safe checkpoint: `NONE`
- Next evidence required: TODO

Release state is exactly one of:

- `NOT_READY`: a required task, check, risk disposition, rollback, or evidence
  item is incomplete, failed, blocked, or stale;
- `READY_TO_DEPLOY`: all required pre-deployment evidence is current for the
  immutable artifact and AWS deployment is the remaining required step;
- `RELEASE_VERIFIED`: every required local and deployed acceptance item is
  VERIFIED for the identified artifact/environment, or deployed evidence is
  explicitly not applicable.

Only RELEASE-10 changes release state. AWS-10 requires `READY_TO_DEPLOY`.
AWS-30 records observed deployment evidence and returns to RELEASE-10, which
sets `RELEASE_VERIFIED` only when the complete release matrix supports it.
