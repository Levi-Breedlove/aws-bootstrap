---
name: operate-fastlane-aws
description: Perform the Fastlane AWS read-only preflight, exactly authorized deployment, deployed-evidence reconciliation, residual-resource review, or teardown. Use only when the user explicitly invokes this skill for AWS-10, AWS-20, AWS-30, AWS-40, or AWS-50.
---

# Operate Fastlane AWS

1. Read the root and `infrastructure/AGENTS.md`, current REQ/DES/AUTH records,
   `docs/project/TASKS.md`, `docs/project/VERIFY.md`, `docs/project/RUNBOOK.md`, and the requested AWS prompt section.
2. Run `python scripts/bootstrap_dependencies.py --root . --json` and require
   the current task's explicit `@AWS Core` verification receipt with successful
   `retrieve_skill` and `search_documentation` checks. A generic AWS
   documentation connector is insufficient. Then run
   `python scripts/bootstrap_doctor.py --root . --json`. Stop unless the
   lifecycle and release state permit the requested AWS prompt.
3. Use `aws-core`, the read-only `fastlane-aws-advisor` where useful, and
   current primary AWS documentation for service behavior,
   Region availability, IAM, quotas, encryption, recovery, and cost. If the
   required capability is unavailable, stop and identify the missing check.
4. Treat documentation access, credentials, connector access, and IAM
   permissions as capabilities only. They never authorize an AWS change.
5. Run `AWS-10` read-only first. Reconfirm the caller, account, role or profile,
   Region, environment, stack, resources, operations, cost, artifact, rollback,
   and expiration against the exact active record.
6. Confirm expected low-usage cost, billing dimensions, scaling breakpoints,
   alerts, and the exact mutation ceiling. Treat the ceiling as a maximum, not
   a spending goal, and never weaken an approved security or recovery control
   for savings.
7. Before `AWS-20`, prove the final infrastructure diff is completely contained
   in that record. Serialize every mutation and checkpoint before and after it.
8. Route deployed observation through `AWS-30`. Record only evidence actually
   observed from the named environment.
9. Require the separate exact teardown receipt for `AWS-50`; preserve retained
   data and verify residual resources read-only afterward.

Stop on any identity, target, artifact, resource, operation, cost, validity, or
state mismatch. Never broaden IAM, make sensitive data public, bypass a failed
control, or claim deployment evidence without observing it.
