# AWS Codex Fastlane

AWS Codex Fastlane is a reusable project template that turns an AWS idea into
approved requirements, an AWS-informed technical PRD, an organized task plan,
and a safely bounded build.

Requires the Codex CLI, Git, and Python 3.11 or newer. AWS credentials are
needed only for an explicitly authorized deployment or other approved AWS
operation.

## Start

1. Select [Use this template](https://github.com/Levi-Breedlove/aws-bootstrap/generate)
   and clone the new repository.
2. Open it in a signed-in interactive Codex CLI and send:

   ```text
   init template
   ```

3. Fastlane checks Codex login, Git, Python, platform sandbox tools, `uvx`, and
   official AWS Core. If anything is missing, complete its one copyable
   checklist and send `init template` again.
4. When prerequisites pass, answer three short setup questions:
   - project name;
   - preferred AWS Region; and
   - development budget or "minimize cost; no hard cap."

Codex then configures the template and begins guided intake.
Setup does not inspect AWS credentials or access an AWS account. Detailed
platform commands are in [SETUP.md](docs/SETUP.md).

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
AWS guidance. Fresh initialization verifies the current official
`aws-core@agent-toolkit-for-aws`. It does not pin a plugin version or commit. Initialized projects do not rerun setup, while material AWS phases
still require current attributable evidence.
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
