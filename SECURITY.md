# Security Policy

## Supported state

Security corrections are maintained on `main`. A release identifies the exact
template revision it contains.

## Report a concern

Use GitHub private vulnerability reporting when available. Otherwise contact
the repository owner privately. Never include credentials, customer data,
production identifiers, secret values, or active tokens.

Include the affected version or commit, observable behavior, a minimal
synthetic reproduction, and the safeguard that should have held.

## Trust boundaries

Fastlane gates govern workflow; they are not IAM, account, network, or runtime
security boundaries. Codex permissions, AWS Core availability, credentials,
prior access, or a passing check never authorize AWS activity.

Fastlane uses current official `aws-core@agent-toolkit-for-aws` as an AWS
research advisor. The template does not pin the plugin, redistribute it, read
its private local state, or manage its hooks. Codex's native plugin and hook
controls remain owner-managed. Fastlane requires attributable current evidence
for material AWS design and execution planning, but does not add a separate
owner trust gate.

AWS Core may expose authenticated operations. Their presence grants no
authority to invoke them.

## Setup controls

- BOOT-00 asks only for project name, preferred Region, and budget posture.
- Missing AWS Core never blocks initialization, intake, or ordinary Gate A.
- Installation commands are owner-run; Fastlane never installs software,
  changes plugin state, signs in, or trusts hooks.
- Only the official Agent Toolkit source is accepted for required AWS evidence.
- The retired local marketplace is never registered or used as a fallback.
- Setup never inspects credentials, accesses an AWS account, or calls AWS
  account tools.
- Login, plugin, hook, machine, username, credential, and session state are
  never written into tracked files or release archives.

## Project and AWS controls

Generated projects should prove:

- approved access succeeds and unapproved access is denied;
- secrets stay out of code, logs, fixtures, evidence, and release artifacts;
- invalid or oversized input is rejected at the boundary;
- IAM permits only required actions on required resources;
- sensitive data uses approved encryption and retention;
- failures are safe and telemetry is observable;
- DESIGN-10 records current AWS Core evidence for consequential architecture,
  IAM, Region, security, reliability, cost, and quota decisions;
- AWS-10 records fresh operational and deployment evidence before AWS execution
  planning; and
- deployment and teardown stay inside the named account, Region, environment,
  resources, operations, finite cost ceiling, rollback plan, and expiration.

Use no AWS identity or a read-only identity by default. When mutation is
approved, prefer a separate short-lived role scoped to the exact authorization.
Gate A and Gate B do not substitute for AWS authorization.

Do not hide a discovered defect. Record it in `docs/project/BUGFIX.md` or an
authorized private issue while keeping sensitive evidence private.
