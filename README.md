# AWS Codex Fastlane

AWS Codex Fastlane is a reusable Codex template that turns an AWS project idea
into approved requirements, an AWS-reviewed technical PRD, an organized task
plan, and a safely bounded build. AWS Core advises; the project owner approves.

## Requirements

- Git and Python 3.11 or newer
- `uv` with the `uvx` command
- Codex CLI, ChatGPT web Work mode, or ChatGPT desktop Work/Codex
- AWS Core from the official AWS Agent Toolkit marketplace

See the [complete setup guide](docs/SETUP.md) for every platform and the official [Codex install/login guide](https://learn.chatgpt.com/docs/codex/cli).

## Start

1. Select [Use this template](https://github.com/Levi-Breedlove/aws-bootstrap/generate),
   clone your new repository, and open a terminal at its root.
2. Verify Codex and sign in:

```text
codex --version
codex login
codex login status
```

3. If the official AWS marketplace is not already registered, run:

```text
codex plugin marketplace add aws/agent-toolkit-for-aws
```

4. Launch Codex in the repository:

```text
codex -C . --sandbox workspace-write --ask-for-approval on-request
```

5. Open `/plugins`. Install or reuse **AWS Core** from **AWS Agent Toolkit**,
   ensure no second AWS Core source is enabled, and start a new session.
6. Send:

```text
init template
```

Codex responds with one setup action at a time. After an interruption, send
`continue setup`; completed checks are not repeated unnecessarily.

## What setup verifies

- The template, Python runtime, `uvx`, and repository doctor are ready.
- Exactly one AWS Core is enabled from the official marketplace.
- The current AWS Core hook is owner-reviewed and passes deny/allow probes.
- Live `retrieve_skill` and `search_documentation` calls prove AWS Core use.

Setup does not configure AWS credentials, access an AWS account, or create
cloud resources.

## What to expect

Gate A — approve requirements → Gate B — approve the PRD and construction boundary → Codex builds autonomously inside that boundary.

Codex asks short, plain-language questions, prefers pay-per-use serverless options
at the lowest practical total
cost without weakening required safeguards, and records current AWS evidence.
It creates dependency-aware tasks and stops when evidence or authority is incomplete.
You can always answer, “I’m not sure—recommend one.”

AWS changes require a separate exact authorization naming the account, Region,
environment, resources, operations, cost ceiling, rollback plan, and expiry.

## Safety

- AWS Core cannot approve Gate A, Gate B, or an AWS change.
- Hook checks are defense-in-depth, not an IAM security boundary.
- Tool or credential availability never grants AWS authority.
- Login, plugin, hook-trust, credential, and machine state stay outside the repo.

## Project files

Project truth lives in `docs/project/` (`PRD.md`, `TASKS.md`, `VERIFY.md`); agent assets live in `.agents/skills/`, `.codex/agents/`, and
`prompts/CODEX-PROMPTS.md`. [Setup](docs/SETUP.md) · [Existing AWS Core](docs/EXISTING-AWS-CORE.md) ·
[Troubleshooting](docs/TROUBLESHOOTING.md) · [Dependency policy](docs/DEPENDENCY-POLICY.md) ·
[Workflow](docs/WORKFLOW.md) · [Security](SECURITY.md)

## Agent reference

See [AGENTS.md](AGENTS.md) for operating rules and [prompts/CODEX-PROMPTS.md](prompts/CODEX-PROMPTS.md) for lifecycle contracts.
