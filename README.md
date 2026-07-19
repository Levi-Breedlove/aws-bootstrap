# AWS Codex Fastlane

AWS Codex Fastlane is a reusable Codex template that turns an AWS project idea
into approved requirements, a practical technical PRD, an organized task plan,
and a safely bounded build.

It is built for **AWS Core** from the AWS Agent Toolkit, giving Codex current AWS
guidance for service choices, IAM, Regions, reliability, security, and cost.
AWS Core advises; the project owner approves.

## Start

1. Select [Use this template](https://github.com/Levi-Breedlove/aws-bootstrap/generate),
   or download the [v1.0.0 ZIP](https://github.com/Levi-Breedlove/aws-bootstrap/releases/download/v1.0.0/aws-codex-fastlane-bootstrap.zip)
   and [checksum](https://github.com/Levi-Breedlove/aws-bootstrap/releases/download/v1.0.0/aws-codex-fastlane-bootstrap.zip.sha256).
2. Open the repository root in Codex.
3. Send:

```text
init template
```

Codex welcomes you, checks the template, and guides you to the next step. If
AWS Core needs attention, Codex gives you the exact owner-run instructions.
Template setup does not access or change an AWS account.

## What to expect

Gate A — approve requirements → Gate B — approve the PRD and construction boundary → Codex builds autonomously inside that boundary.

1. Codex asks short, plain-language questions about the users, outcome, scope,
   data, constraints, and success criteria.
2. You approve the requirements at Gate A.
3. Codex completes the AWS design and technical PRD.
4. You approve the design and build boundary at Gate B.
5. Codex creates dependency-aware tasks, builds within the approved boundary,
   and records verification evidence.
6. AWS changes occur only with a separate exact authorization naming the target,
   allowed operations, cost ceiling, rollback plan, and expiration.

You can always answer, “I’m not sure—recommend one.” Fastlane starts with secure,
managed, pay-per-use serverless options and looks for the lowest practical total
cost without weakening required safeguards.

## Project files

```text
.
├── AGENTS.md                   # Always-on Codex rules
├── docs/project/
│   ├── PRD.md                  # Requirements, design, Gate A, and Gate B
│   ├── TASKS.md                # Work plan and execution state
│   ├── VERIFY.md               # Observed evidence
│   ├── RUNBOOK.md              # Deploy, rollback, and recovery
│   └── BUGFIX.md               # Active defect contract
├── bootstrap.py                # Safe initialization and adoption
├── bootstrap.yaml              # Derived lifecycle state
├── .agents/skills/             # Fastlane workflows
├── .codex/agents/              # Focused planning advisors
├── prompts/CODEX-PROMPTS.md    # Exact prompts and receipts
└── scripts/                    # Doctor, task, and release tools
```

## Safety

- AWS Core cannot approve Gate A, Gate B, or an AWS change.
- No Codex login, plugin state, hook trust, AWS credential, or machine-specific
  setup history is stored in the repository or release ZIP.
- Tool availability never grants AWS authority.
- Fastlane stops when requirements, evidence, or authorization are incomplete.

## Agent reference

See [AGENTS.md](AGENTS.md) for operating rules,
[prompts/CODEX-PROMPTS.md](prompts/CODEX-PROMPTS.md) for exact workflow contracts,
and [SECURITY.md](SECURITY.md) for safeguard and reporting guidance.
