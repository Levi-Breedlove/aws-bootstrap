# AWS Infrastructure Engineering Guide

These instructions apply under `infrastructure/` and inherit the root
`AGENTS.md`. Gate A and Gate B are the only routine human gates. Infrastructure
validation, preflight, deployment, and evidence reconciliation are readiness
checks inside the current construction authorization (`AUTH`).

## Plain-language summary

Start with read-only inspection. Change AWS only when the current approval names
the exact account, Region, environment, resources, operations, cost limit,
rollback plan, and expiration. Stop if the observed target or final change no
longer matches that approval. Never treat credentials or tool access as
permission.

## Read first

- Current REQ/DES/AUTH IDs, Gate B state, AWS lane, construction envelope, and
  brownfield preservation contract in `../PRD.md`
- Exact task status, write set, external state, attempt budget, owner, run, and
  checkpoint in `../TASKS.md`
- Current evidence and stale or pending checks in `../VERIFY.md`
- Deployment, rollback, interrupted-action, recovery, and separately authorized
  teardown procedures in `../RUNBOOK.md`

## Agent reference — authority and task boundary

- Infrastructure work requires a current Gate B
  `APPROVED_FOR_CONSTRUCTION`, matching REQ/DES/AUTH IDs, and an assigned task
  that is explicitly `READY` before it is claimed.
- The current AUTH and task define the maximum file, command, GitHub, account,
  Region, environment, stack/resource, cost, and mutation boundary. Credentials,
  installed tools, IAM permissions, connector access, or a worker assignment do
  not expand it.
- GitHub operations occur only when AUTH names the repository and exact write.
  Otherwise return evidence to the coordinator and retain `PENDING_SYNC`.
- Use the `aws-core` plugin and current AWS primary documentation for service,
  IAM, quota, networking, encryption, recovery, cost, and regional behavior.
  Plugin access is a knowledge and tool layer, not authorization.

## Coordinator, workers, and state

- The coordinator alone updates `TASKS.md`, `VERIFY.md`, `RUNBOOK.md`, shared
  manifests, lockfiles, schemas, generated output, checkpoints, and GitHub
  metadata.
- A worker edits only the exact disjoint IaC or test paths assigned to its task
  and returns a receipt with task/run/checkpoint and REQ/DES/AUTH IDs, changed
  paths, commands/results, evidence, external actions, and deviations.
- Give each path, stack, state backend, environment, database, generated output,
  and mutable resource one writer at a time. Ambiguous ownership means
  serialization.
- Serialize CloudFormation/CDK/Terraform state operations, imports, migrations,
  deployments, rollback, and every AWS mutation. Exactly one named AWS operator
  may mutate a target at a time.
- Checkpoint before and after each external mutation. After interruption, inspect
  state read-only and classify the last action as `SUCCEEDED`, `FAILED`,
  `PARTIAL`, or `UNKNOWN`; never blindly rerun it.

## Canonical AWS lane behavior

| Project lane | Infrastructure behavior |
|---|---|
| `documentation-only` | Repository planning and documentation lookup only; no authenticated AWS access |
| `read-only` | Observe only the account, Region, environment, and resources named by AUTH |
| `fast-dev` | Mutate only listed resources in the exact non-production Gate B envelope after AWS-10 preflight |
| `explicit-gate` | Remain documentation-only or read-only until a current action-specific AWS-20 authorization names every mutation field |

Before any mutation, reconfirm the allowlisted profile or role, account, Region,
environment, stack/resources, approved operation, artifact and final change set,
billable impact, rollback boundary, authorization ID, approver, and validity
window. The observed values must exactly match the active authorization.

Route `fast-dev` to `explicit-gate` and stop for production, deletion or
replacement, IAM/trust broadening, public sensitive-data exposure, a shared or
unowned resource, data migration/mutation, material cost drift, or any identity,
target, artifact, plan, or scope mismatch. Teardown always requires a separate
exact deletion and retention authorization.

## Brownfield preservation

- Perform read-only discovery before proposing a change. Reconcile repository
  IaC, state backends, live resources, tags, versions, deployed artifacts, drift,
  and known baseline failures.
- Identify the owner and consumers of existing and shared resources. Unknown
  ownership is not permission to create, import, adopt, detach, replace, or
  delete them.
- Preserve approved interfaces, schemas, retained data, security controls,
  resource names, compatibility, recovery behavior, and dirty or user-owned
  changes.
- Treat import, migration, replacement, deletion, state movement, and changes to
  shared infrastructure as explicit boundaries. Do not make live state conform
  to the template by overwriting the observed system.
- Stop when drift cannot be explained, rollback cannot restore the observed
  baseline, or the task conflicts with a preservation ID.

## Engineering rules

- Prefer infrastructure as code over undocumented console changes.
- Use least privilege and explicit trust boundaries.
- Keep secrets out of templates, state output, logs, source control, generated
  receipts, and command history.
- Keep private workloads and data stores private unless an approved requirement
  and current authorization explicitly say otherwise.
- Define encryption, logging, retention, backup, deletion, health checks, alarms,
  failure handling, rollback, recovery, and cleanup.
- Identify recurring and one-time cost and compare them with the authorized
  ceiling.
- Tag resources consistently and avoid unnecessary public IPv4, NAT, always-on
  compute, and excessive retention.
- Validate, synthesize, lint, scan, and inspect the final plan or change set
  before deployment. Local synthesis does not prove deployed AWS behavior.
- Never weaken IAM, networking, encryption, validation, logging, deletion
  protection, or policy checks to make an operation pass.
- Do not claim deployment, rollback, recovery, or teardown success until live
  read-only evidence confirms the resulting state.

Infrastructure definitions are authoritative for intended managed resources;
observed live state and provider state remain required evidence for actual
resources. Do not duplicate a complete inventory in Markdown.
