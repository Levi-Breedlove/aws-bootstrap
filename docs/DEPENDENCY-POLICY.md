# Dependency Policy

Fastlane uses the current official AWS Core plugin from the AWS Agent Toolkit:

```text
Marketplace: aws/agent-toolkit-for-aws
Plugin: aws-core@agent-toolkit-for-aws
Policy: OFFICIAL_CURRENT_NO_TEMPLATE_PIN
```

The template does not redistribute AWS Core and does not pin its version or
commit. Plugin installation, updates, and native hook trust stay in each
adopter's local Codex profile and are never written to the repository.

## When AWS Core is required

Fresh templates require current official AWS Core before initialization.
Initialized projects skip the prerequisite gate during ordinary resume. During
Define, query AWS Core only when a current AWS fact materially affects
feasibility; current attributable evidence is required for the evidence-bound
AWS work at DESIGN-10 and AWS-10.

Use it for current service behavior, Region support, IAM, networking,
encryption, quotas, reliability, observability, pricing drivers, deployment,
rollback, operations, and teardown. When unavailable, pause only the affected
AWS-specific step and provide one concise owner action.

## Evidence

Installation metadata is not design evidence. DESIGN-10 and AWS-10 require
fresh attributable `retrieve_skill` and `search_documentation` results from
the official identity. Record the observed current version as metadata, not a
pin. Generic connectors, cached prose, and model memory do not satisfy required
evidence.

## Authority and privacy

AWS Core is an advisor. It cannot approve Gate A, Gate B, or an AWS mutation.
Tool availability never grants AWS authority. Fastlane never stores plugin
state, trust state, usernames, client paths, credentials, account identifiers,
or local setup history.
