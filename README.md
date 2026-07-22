# AWS Codex Fastlane

AWS Codex Fastlane is a reusable project template that turns an AWS idea into
approved requirements, an AWS-informed technical PRD, an organized task plan,
and a safely bounded build.

Requires Codex and Python 3.11 or newer. AWS credentials are needed only for
an explicitly authorized deployment or other approved AWS operation.

## Start

1. Select [Use this template](https://github.com/Levi-Breedlove/aws-bootstrap/generate),
   clone the new repository, and open it in Codex.
2. Send:

   ```text
   init template
   ```

3. Answer three short setup questions:
   - project name;
   - preferred AWS Region; and
   - development budget or "minimize cost; no hard cap."

Codex validates and configures the template, then begins guided intake. It
does not require AWS credentials or access an AWS account during setup.

## What to expect

Gate A — approve requirements → Gate B — approve the PRD and construction boundary → Codex builds autonomously inside that boundary.

Codex asks short, plain-language questions, prefers secure pay-per-use
serverless options when they fit, seeks the lowest practical total cost without
weakening required safeguards, and records evidence.
You can always answer, "I'm not sure—recommend one."

When an approved requirement expresses a testable invariant, Codex records a
`PROP-*` specification, generates framework-appropriate property tests, runs
them during construction, and records reproducible seeds and counterexamples.

AWS changes require a separate exact authorization naming the account, Region,
environment, resources, operations, cost ceiling, rollback plan, and expiry.

## AWS Core

Fastlane is built to use official AWS Core from the
[AWS Agent Toolkit](https://github.com/aws/agent-toolkit-for-aws) for current
AWS design guidance. AWS Core is not required for project intake or Gate A.

When AWS-specific design needs AWS Core and it is unavailable, Codex gives one
setup step. Fastlane uses the current official
`aws-core@agent-toolkit-for-aws`; it does not pin a plugin version or commit.
Codex's own `/plugins` and `/hooks` screens manage installation and trust.
AWS Core advises; it cannot approve either gate or authorize an AWS change.

## Project files

```text
.
├── AGENTS.md                  Always-on Codex rules
├── docs/project/PRD.md        Requirements, design, Gate A, and Gate B
├── docs/project/TASKS.md      Dependency graph and execution state
├── docs/project/VERIFY.md     Observed evidence
├── docs/project/RUNBOOK.md    Deploy, rollback, recovery, and teardown
├── bootstrap.yaml             Derived lifecycle state
├── .agents/skills/            Fastlane workflows
├── .codex/agents/             Optional read-only challengers
├── prompts/CODEX-PROMPTS.md   Exact lifecycle contracts
└── scripts/                   Doctor, task runtime, and packaging tools
```

## Safety

Setup, login, plugin, hook-trust, credential, and machine state stay outside
the repository. Tool availability never authorizes AWS access.

## Agent reference

Detailed references: [setup](docs/SETUP.md) ·
[workflow](docs/WORKFLOW.md) · [security](SECURITY.md) ·
[agent rules](AGENTS.md).
