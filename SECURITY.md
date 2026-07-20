# Security Policy

## Supported state

Security corrections are maintained on `main`. Each published release identifies
the exact template version it contains; an unreleased `main` revision must not be
treated as equivalent to an older release artifact.

## Report a concern

Use GitHub private vulnerability reporting when it is available. Otherwise,
contact the repository owner privately before publishing details that would make
exploitation easier. Never include credentials, customer data, production
identifiers, secret values, or active access tokens in a report.

Include the affected version or commit, observable behavior, a minimal
reproduction using synthetic data, and the safeguard that should have held.

## Trust boundaries

Fastlane's gates are workflow-governance controls. They constrain what the agent
is instructed and authorized to do, but they are not IAM, account, network, or
runtime security boundaries. Codex sandbox permissions, plugin availability,
hook success, cached credentials, or prior access never authorize AWS activity.

AWS Core is consumed from the official AWS Agent Toolkit marketplace as an
`OFFICIAL_CURRENT` dependency. Official provenance is not proof that every
update is compatible or risk-free. A new or changed version requires current
hook review, synthetic probes, and live capability verification before use.

The AWS Core secret-safety hook is defense-in-depth. It is not a security
boundary and does not replace least-privilege IAM, permission boundaries,
service control policies, short-lived credentials, network controls, logging,
or human review. AWS Core can expose authenticated operations such as `call_aws`
and `run_script`; their presence grants no authority to invoke them.

## Setup controls

This template and generated projects must ensure that:

- Codex installation and login, marketplace registration, plugin changes,
  session launch, and hook trust remain owner-run actions;
- only `aws-core@agent-toolkit-for-aws` is accepted, and duplicate or unknown
  AWS Core sources stop setup until the owner resolves them;
- enabled hooks matching shell or AWS MCP tools are inventoried because Codex
  can run matching hooks from multiple sources;
- executable plugin hooks remain skipped until the owner reviews and trusts the
  current definition through Codex; trust is never bypassed;
- an inert deny probe and harmless allow probe pass before the AWS Core
  handshake, without credentials, network access, or an AWS account call;
- both `retrieve_skill` and `search_documentation` run live through the
  explicitly invoked official AWS Core plugin; prose, memory, and installation
  metadata are not accepted as usage proof;
- setup never invokes `call_aws`, `run_script`, AWS account APIs, or credential
  tools, and never inspects or configures AWS credentials;
- the setup assistant prints owner-run guidance only and never launches an
  installer, package manager, login, plugin action, hook action, or AWS action;
- Codex login, plugin state, hook trust, client paths, usernames, credentials,
  and session history are never written into tracked files or release archives.

Do not enable two AWS Core sources. Duplicate plugin sources can expose
overlapping skills, MCP servers, and hooks; matching command hooks may run
concurrently rather than replacing one another.

## Project and AWS controls

Generated projects should prove that:

- approved access succeeds and unapproved access is denied;
- secrets stay out of code and logs, as well as fixtures, evidence, and release artifacts;
- invalid or oversized input is rejected at the boundary, including malformed input;
- IAM permits only required actions through the least-privileged identity;
- sensitive data uses approved encryption and retention controls;
- DESIGN-10 records current AWS Core evidence for consequential architecture,
  IAM, Region, security, reliability, cost, and quota decisions;
- AWS-10 records fresh operational and deployment evidence before proposing an
  AWS execution; and
- deployment and teardown stay inside the named account, Region, environment,
  resources, operations, cost ceiling, rollback plan, and expiration boundary.

Use a read-only or no-access identity by default. When mutation is approved,
prefer a separate, short-lived elevated role scoped to the exact authorization,
and preserve CloudTrail and relevant service evidence. A Gate A or Gate B
approval does not substitute for this AWS authorization.

Do not hide a discovered defect to keep a review green. Record product defects
in `docs/project/BUGFIX.md` or an authorized private issue while keeping
sensitive evidence private.
