# AWS Infrastructure Engineering Guide

These instructions apply under `infrastructure/` and inherit the root `AGENTS.md`.

## Read first

- Relevant architecture, security, reliability, performance, cost, and sustainability sections in `../PRD.md`
- Executable infrastructure work and dependencies in `../TASKS.md`
- Current evidence gaps in `../VERIFY.md`
- Deployment, rollback, recovery, and teardown procedures in `../RUNBOOK.md`

## Rules

- Prefer infrastructure as code over undocumented console changes.
- Use AWS MCP and current AWS primary documentation.
- Perform read-only discovery before proposing mutations.
- Validate the target account, Region, environment, and naming convention.
- Use least privilege and explicit trust boundaries.
- Keep secrets out of templates, state output, logs, source control, and command history.
- Keep private workloads and data stores private unless an approved requirement says otherwise.
- Define encryption, logging, retention, backup, and deletion behavior.
- Define health checks, alarms, failure handling, rollback, and cleanup.
- Identify recurring and one-time cost.
- Tag resources consistently.
- Avoid unnecessary public IPv4, NAT, always-on compute, and excessive retention.
- Validate and lint IaC before deployment.
- Do not mutate or destroy AWS resources without explicit authorization.

Infrastructure definitions are authoritative for actual resources. Do not duplicate complete resource inventories in Markdown.
