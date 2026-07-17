# My AWS Project — Deployment and Operations Runbook

> `RUNBOOK.md` owns repeatable operational procedures. Project work and live status belong in `TASKS.md` and mirrored GitHub Issues.

This document is procedural, not authorization. Gate A and Gate B are the only
routine human gates. Local validation, AWS preflight, deployment checks, smoke
tests, rollback checks, and release checks are readiness controls inside the
current construction authorization (`AUTH`), not additional human gates.

Repository, GitHub, and AWS actions occur only when the current AUTH or a
current action-specific authorization names the target and operation. Tool or
credential availability never grants authority.

Construction starts from the Gate B-authorized local Git baseline. Every
validated wave is committed locally before pause, its commit becomes the
TASKS.md Last known-green/checkpoint commit, and doctor runs against that
checkpoint. Never commit protected dirty paths or infer remote/push authority
from local Git authorization.

## Active operational boundary

Complete this card before authenticated AWS work. It mirrors the authoritative
boundary; it does not create one.

| Field | Current value |
|---|---|
| Requirements / design / construction IDs | `REQ-0001` / `DES-0001` / `AUTH-0001` |
| Project AWS lane | `documentation-only` / `read-only` / `fast-dev` / `explicit-gate` |
| AWS action authorization ID | TODO / `NONE` |
| AWS action authorization source, observed at, and receipt SHA-256 | TODO / `NONE` |
| Profile or role | TODO / `NONE` |
| Account ID or approved alias | TODO / `NONE` |
| Region and environment | {{AWS_REGION}} / TODO |
| Stack, application, and exact resources | TODO / `NONE` |
| Approved operation and artifact/change set | TODO / `NONE` |
| Billable impact or cost ceiling | {{MONTHLY_BUDGET}} / `NONE` |
| Rollback boundary | TODO / `NONE` |
| Teardown authorization ID | TODO / `NONE` |
| Teardown authorization source, observed at, and receipt SHA-256 | TODO / `NONE` |
| Approver and validity window | TODO / `NONE` |
| Prohibited actions | TODO |

Missing, stale, conflicting, placeholder, or mismatched values grant no mutation
authority.

## Canonical AWS lanes

| Project lane | Permitted operation | Required readiness and authorization |
|---|---|---|
| `documentation-only` | AWS documentation and repository-only planning; no authenticated AWS access | Current AUTH boundary `DOCS_ONLY` |
| `read-only` | Authenticated observation inside the named account, Region, environment, and resource scope | Current AUTH boundary `READ_ONLY`; no mutation |
| `fast-dev` | Listed mutations in a non-production development target | Current Gate B `MUTATE_LISTED_RESOURCES` envelope plus successful AWS-10 read-only preflight and an exact final match |
| `explicit-gate` | Documentation or read-only work by default; one separately authorized mutation | Current action-specific AWS-20 authorization containing every mutation-boundary field |

`NONE`, `DOCS_ONLY`, `READ_ONLY`, and `MUTATION` are prompt access modes; they
are not interchangeable with project lane names. Every AWS mutation is
serialized, even when local task paths are disjoint. Exactly one named operator
may mutate a stack, state backend, database, or account target at a time.

For `fast-dev`, stop and route the proposed action to `explicit-gate` when the
target is production, the change deletes or replaces a resource, broadens IAM
or trust, exposes sensitive data publicly, affects a shared or unowned resource,
mutates or migrates retained data, exceeds cost, or differs from the approved
identity, Region, environment, artifact, change set, or resource list.

Deployment or rollback authority never implies teardown authority. Teardown
always requires its own exact deletion and retention authorization.

## Conditional AWS action receipts

These are action-specific safety authorizations, not routine lifecycle gates.
An `explicit-gate` deployment needs the exact first receipt. A `fast-dev`
deployment may instead use the current Gate B envelope only when AWS-10 proves
the final operation is fully contained in it. Every teardown needs the exact
second receipt, including under `fast-dev`.

Accept a receipt only when the owner's message equals the applicable complete
block after trimming surrounding whitespace. Replace every placeholder; reject
extra, missing, duplicate, reordered, commented, or fenced lines and any value
that differs from the current PRD, artifact, AWS-10/AWS-40 observation, or
caller identity.

```text
AUTHORIZE AWS DEPLOYMENT
AWS authorization: AWS-AUTH-0001
Construction authorization: AUTH-0001
Profile or role: <allowlisted profile or role>
Account: <12-digit account ID or approved alias>
Region: <AWS Region>
Environment: <non-production or production>
Artifact digest: <immutable digest>
Stack, application, and resources: <exact boundary>
Allowed operations: <exact create/update/delete operations>
Cost ceiling: <currency and amount>
Rollback boundary: <exact allowed rollback or NONE>
Valid until: <ISO 8601 time or exact one-operation condition>
Approver: <name/handle>
```

```text
AUTHORIZE AWS TEARDOWN
Teardown authorization: TEARDOWN-AUTH-0001
Construction authorization: AUTH-0001
Profile or role: <allowlisted profile or role>
Account: <12-digit account ID or approved alias>
Region: <AWS Region>
Environment: <environment>
Stack, application, and resources to remove: <exact boundary>
Resources and data to retain: <exact list or NONE>
Allowed deletion operations: <exact operations>
Shared dependencies: <exact list or NONE>
Cost effect: <expected continuing and removed billing dimensions>
Post-teardown verification: <read-only checks>
Valid until: <ISO 8601 time or exact one-operation condition>
Approver: <name/handle>
```

The owner's exact message remains the authorization source. Before mutation,
copy it verbatim into the protected external-operation journal named by the
construction envelope and record its stable source, observed ISO 8601 time, and
SHA-256 in VERIFY.md's action-authorization evidence table. The copy and mirror
do not create or widen authority. A missing durable source blocks mutation.

## 1. Environments

| Environment | Purpose | AWS account | Region | Deployment method | Owner |
|---|---|---|---|---|---|
| Local | Development | N/A | N/A | TODO | TODO |
| Development | Integration and AWS validation | TODO | {{AWS_REGION}} | TODO | TODO |
| Production | User-facing workload | TODO | {{AWS_REGION}} | TODO | TODO |

## 2. Prerequisites

- Required tools and versions: TODO
- Required AWS profile or role: TODO
- Required permissions: TODO
- Required environment variables: TODO
- Required secret locations: TODO
- Required external services: TODO
- Expected recurring cost: TODO
- Expected one-time deployment cost: TODO

Never place secret values in this document.

## 3. Read-only AWS preflight

AWS-10 runs only when VERIFY.md release state is `READY_TO_DEPLOY`. Before any
mutation:

```bash
aws sts get-caller-identity
aws configure get region
```

Confirm:

- intended profile or role;
- account identity;
- Region `{{AWS_REGION}}`;
- intended stack, application, cluster, or environment name;
- current resource collisions;
- service quota headroom;
- current budget and cost exposure;
- change reversibility;
- current matching REQ/DES/AUTH IDs and Gate B state;
- current lane and complete action authorization when required;
- no protected brownfield ownership, drift, or preservation conflict.

Perform this stage through AWS-10. Execute deployment or corrective mutation
only through AWS-20, reconcile it through AWS-30, review residual resources
through AWS-40, and execute teardown only through AWS-50. BUILD-10, BUILD-20,
and RELEASE-10 never run AWS-changing commands directly.

AWS-30 records deployed evidence and returns to RELEASE-10. Only RELEASE-10 may
advance `READY_TO_DEPLOY` to `RELEASE_VERIFIED`; failed, partial, stale, or
pending evidence returns the release to `NOT_READY`.

Add workload-specific read-only checks:

```bash
# TODO
```

## 4. Local validation

```bash
# Formatting
TODO

# Linting and type checking
TODO

# Unit and integration tests
TODO

# Infrastructure validation
TODO

# Security and dependency checks
TODO
```

Do not continue when required local readiness checks fail.

## 5. Cost preflight

Confirm:

- monthly ceiling: `{{MONTHLY_BUDGET}}`;
- budget and alert recipients;
- expensive resources;
- NAT Gateway, public IPv4, EKS, RDS, ALB, OpenSearch, provisioned capacity, and log-retention implications where applicable;
- teardown command or procedure;
- intended retention of data, logs, images, backups, and source repositories.

## Brownfield deployment readiness

Before changing an existing environment:

1. Record the repository and deployed baselines, including known failing checks.
2. Reconcile IaC, state backends, tags, live inventory, versions, and drift using
   read-only operations.
3. Identify owners and consumers of every existing or shared resource in the
   proposed change set.
4. Confirm protected interfaces, schemas, data, retention, imports, migrations,
   dirty paths, and rollback constraints from the approved preservation contract.
5. Prove that the proposed plan preserves owner or user changes and does not
   create, adopt, import, replace, detach, or delete an existing resource merely
   to make IaC converge.

Unknown ownership, unexplained drift, an unapproved import/replacement, or an
inability to restore the observed baseline stops the affected operation.

## Interrupted or uncertain external action

Never resume by blindly rerunning a deployment, migration, rollback, or cleanup
command. At the next checkpoint:

1. Reconfirm the exact identity, account, Region, environment, authorization,
   artifact, and expected resource boundary.
2. Inspect live state read-only and correlate operation, stack, deployment, or
   request identifiers.
3. Classify the prior action as `SUCCEEDED`, `FAILED`, `PARTIAL`, or `UNKNOWN`.
4. Compare observed resources, data, telemetry, billing dimensions, and locks to
   the last safe checkpoint.
5. Continue only when the documented next operation is idempotent, inside the
   current authorization, and safe for the observed state.

`PARTIAL` or `UNKNOWN` state is a mandatory stop unless the current authorization
explicitly covers the reconciled corrective or rollback action.

## 6. Deployment

Record the exact reviewed artifact:

- commit:
- image digest:
- IaC version:
- parameter source:
- environment:
- operator or workflow identity:
- construction and AWS action authorization IDs:
- final read-only plan or change-set identifier:

Deployment commands:

```bash
TODO
```

Record:

- start time;
- completion time;
- deployment result;
- stack or release identifiers;
- warnings or deviations.

Immediately before mutation, recheck caller identity and prove that the final
plan is fully contained in the active boundary. Stop on any mismatch, unexpected
replacement, deletion, IAM/network exposure, shared-resource effect, retained
data impact, cost increase, alarm, or rollback trigger. Do not improvise broader
permissions or resources.

Checkpoint before the first mutation and after each bounded external action.
Record actual identifiers and results in `VERIFY.md`; a submitted request is not
evidence of completion.

## 7. Smoke tests

```bash
# Health
TODO

# Primary flow
TODO

# Authentication and authorization
TODO

# Data persistence
TODO

# External integrations
TODO
```

Verify:

- expected response and user outcome;
- safe negative authorization behavior;
- logs contain no prohibited values;
- metrics are emitted;
- alarms are configured;
- health and readiness checks reflect actual dependency health.

Record evidence in `VERIFY.md`.

## 8. Monitoring and alarms

| Signal | Source | Expected behavior | Threshold | Response |
|---|---|---|---|---|
| Availability | TODO | TODO | TODO | TODO |
| Errors | TODO | TODO | TODO | TODO |
| Latency | TODO | TODO | TODO | TODO |
| Queue or event backlog | TODO | TODO | TODO | TODO |
| Database health | TODO | TODO | TODO | TODO |
| Resource utilization | TODO | TODO | TODO | TODO |
| Cost | AWS Budgets / Cost Explorer | Remain within approved ceiling | TODO | TODO |
| Security events | TODO | TODO | TODO | TODO |

## 9. Common diagnosis flow

1. Confirm environment and user impact.
2. Check recent deployments, configuration changes, and feature flags.
3. Check health, readiness, error rate, latency, saturation, and dependency signals.
4. Inspect correlation IDs and safe structured logs.
5. Check queues, dead-letter destinations, retries, and failed workflows.
6. Check database connections, capacity, locks, and storage.
7. Check IAM denial events without broadening permissions prematurely.
8. Contain the issue without destroying evidence.
9. Roll back when containment is insufficient.
10. Create follow-up GitHub issues for unresolved causes.

## 10. Rollback

Rollback triggers:

- failed smoke test;
- security-control failure;
- error or latency regression;
- migration failure;
- data corruption risk;
- unhealthy targets or failed readiness;
- cost behavior outside approved expectations.

Rollback commands:

```bash
TODO
```

After rollback:

- rerun smoke tests;
- confirm health and alarms;
- verify data consistency;
- record evidence in `VERIFY.md`;
- create an issue for root-cause remediation.

Rollback is performed only when the active authorization names it. If rollback
would exceed that boundary, stop in the safest observable state and report the
smallest authorization needed. In brownfield environments, preserve pre-existing
resources and data rather than forcing template state.

## 11. Backup and recovery

| Item | Value |
|---|---|
| Backup mechanism | TODO |
| Backup schedule | TODO |
| Retention | TODO |
| RTO | TODO |
| RPO | TODO |
| Restore procedure | TODO |
| Last restore rehearsal | TODO |
| Restore evidence | TODO |

Restore commands or procedure:

```bash
TODO
```

## 12. Incident response

1. Assign incident owner.
2. Record start time, environment, and impact.
3. Preserve relevant logs, metrics, and deployment context.
4. Contain exposure or failure.
5. Roll back or fail over when appropriate.
6. Recover service and validate primary flows.
7. Record follow-up actions as GitHub issues.
8. Update this runbook only when the procedure itself changes.

## 13. Teardown and decommissioning

Default to a read-only inventory. Before any deletion, record an exact current
teardown authorization that names the operator/profile, account, Region,
environment, stack/resources, retained data and backups, deletion operations,
shared dependencies, cost effect, approver, and validity window. A deployment,
rollback, Gate B fast-dev, or tool authorization does not substitute for this
teardown authorization.

```bash
# Dry run or inventory
TODO

# Execution only under the exact teardown authorization
TODO
```

Confirm removal or intentional retention of:

- compute and orchestration;
- load balancers and public IP resources;
- NAT Gateways and endpoints;
- databases, backups, and snapshots;
- object storage and artifacts;
- container images and registries;
- pipelines and build resources;
- logs, alarms, dashboards, and traces;
- secrets, keys, and service accounts;
- DNS, certificates, and edge distributions.

Stop rather than disabling protection, force-deleting data, emptying storage,
breaking a shared dependency, or changing retention unless that exact action is
named. Checkpoint after each bounded step. On partial failure, inspect live state
and recompute the safe deletion order before any further mutation.

## 14. Residual-resource and billing verification

After teardown:

```bash
# Resource inventory checks
TODO

# Billing and cost checks
TODO
```

Record:

- residual resources;
- intentional retention;
- expected delayed billing records;
- follow-up date;
- owner.

## 15. Evidence capture

For every deployment, rollback, restore, or teardown, record:

- version or commit;
- environment and Region;
- start and completion time;
- operator or workflow;
- result;
- relevant test, metric, log, or stack references;
- linked GitHub issue or pull request;
- remaining evidence gaps.

Also record the current REQ/DES/AUTH and action authorization IDs, coordinator
checkpoint, changed resources, billable residuals, and whether the observed
operation state is `SUCCEEDED`, `FAILED`, `PARTIAL`, or `UNKNOWN`. GitHub status
or comment updates are written only when AUTH permits those exact operations;
otherwise record `PENDING_SYNC` locally.
