# My AWS Project — Deployment and Operations Runbook

> `RUNBOOK.md` owns repeatable operational procedures. Project work and live status belong in `TASKS.md` and mirrored GitHub Issues.

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

Before any mutation:

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
- explicit approval.

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

Do not continue when required local gates fail.

## 5. Cost preflight

Confirm:

- monthly ceiling: `{{MONTHLY_BUDGET}}`;
- budget and alert recipients;
- expensive resources;
- NAT Gateway, public IPv4, EKS, RDS, ALB, OpenSearch, provisioned capacity, and log-retention implications where applicable;
- teardown command or procedure;
- intended retention of data, logs, images, backups, and source repositories.

## 6. Deployment

Record the exact reviewed artifact:

- commit:
- image digest:
- IaC version:
- parameter source:
- environment:
- operator or workflow identity:
- approval:

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

Default to a dry run where possible.

```bash
# Dry run or inventory
TODO

# Approved execution
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
