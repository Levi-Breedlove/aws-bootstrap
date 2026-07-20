# AWS Core Dependency Policy

Fastlane follows AWS Core from the official AWS Agent Toolkit marketplace.
It does not redistribute a pinned copy of the plugin.

## Policy record

```text
dependency_policy: OFFICIAL_CURRENT
marketplace_repository: aws/agent-toolkit-for-aws
marketplace: agent-toolkit-for-aws
plugin: aws-core
plugin_identity: aws-core@agent-toolkit-for-aws
last_tested_version: 1.1.0
```

`last_tested_version` is compatibility information for the Fastlane v1.1.0
development line. It is not an installation pin, minimum version, security
guarantee, or reason to reject a newer official plugin by itself.

## Why official-current is the default

The official marketplace path:

- follows the installation model AWS documents and supports;
- reuses an official AWS Core already present in a user's Codex profile;
- avoids a second Fastlane-specific AWS Core identity;
- receives current AWS skills, MCP configuration, and upstream fixes; and
- reduces repository-specific plugin installation steps.

Register the official marketplace only when absent:

```text
codex plugin marketplace add aws/agent-toolkit-for-aws
```

Then install or reuse AWS Core through `/plugins` and start a new session.

## What this policy does not guarantee

Official provenance does not prove that:

- every AWS Core update is compatible with the current Codex host;
- its MCP service is available;
- its hook behaves correctly on every platform;
- a plugin is enabled, trusted, or actually used in the current session;
- credentials or IAM permissions are safe; or
- AWS activity is authorized.

The moving official dependency trades byte-for-byte reproducibility for simpler
onboarding and current upstream behavior. Fastlane addresses that tradeoff with
runtime verification and release smoke testing, not with a prompt-only claim.

## Required verification after install or update

An official version that differs from `last_tested_version` triggers review; it
does not fail solely because the version changed.

Before guided intake, require:

1. exactly one enabled `aws-core@agent-toolkit-for-aws` source;
2. a new Codex session after plugin-state changes;
3. owner inspection and trust of the current AWS Core hook in `/hooks`;
4. inventory of other hooks matching shell or AWS MCP tools;
5. a blocked inert deny probe;
6. a successful harmless allow probe; and
7. live, explicit AWS Core calls to both `retrieve_skill` and
   `search_documentation`.

Installation metadata, model memory, generic documentation tools, and prose
claims are not usage proof. BOOT-00 does not call `call_aws`, `run_script`, AWS
account APIs, or credential tools.

## Evidence throughout the workflow

AWS Core is required at three boundaries:

| Phase | Evidence purpose |
|---|---|
| BOOT-00 | Prove official source, hook behavior, skill retrieval, and documentation search |
| DESIGN-10 | Validate consequential service, IAM, Region, security, reliability, cost, and quota decisions |
| AWS-10 | Refresh deployment, operational, IAM, and service guidance before proposing AWS execution |

Non-sensitive design and operational evidence belongs in
`docs/project/VERIFY.md`. It records the phase, capability, retrieved skill,
documentation topic, source references, decision influenced, official source
and invoked identity, observation time, current revision or artifact binding,
and observed status. It must not contain plugin cache paths, usernames, trust databases,
Codex credentials, AWS credentials, or secret values.

Missing DESIGN-10 evidence blocks Gate B readiness. Missing AWS-10 evidence
blocks AWS execution planning.

## Existing and duplicate installations

An existing official AWS Core is reused. An older pinned or unknown AWS Core is
not an automatic fallback. If more than one source is enabled, Fastlane returns
`AWS_CORE_DUPLICATE_BLOCKED` until the owner keeps only the official source and
starts a new session.

This matters because enabled sources can contribute overlapping skills, MCP
servers, and matching hooks. Codex may run matching command hooks concurrently.
See [Existing AWS Core](EXISTING-AWS-CORE.md).

## Release maintenance

Before publishing a Fastlane release, maintainers should record the official AWS
Core version observed in a supported authenticated session and smoke-test:

- Windows native, including the literal `python3` limitation;
- WSL2;
- macOS;
- Linux;
- a clean Codex profile;
- an existing official AWS Core profile;
- old and duplicate AWS Core source handling;
- hook deny and allow behavior; and
- both required live AWS Core capabilities.

Unit tests can validate state transitions and response rendering, but they
cannot prove authenticated marketplace state, hook trust, MCP startup, or live
AWS Core calls. Release notes must distinguish deterministic tests from observed
manual smoke tests.

## If strict reproducibility is required

An organization may maintain a separately governed pin, but that is outside the
default Fastlane contract. It must use a distinct policy, source-bound
verification, update review, security-fix process, duplicate-source handling,
and release evidence. Fastlane must not silently fall back from official-current
to that private mode.
