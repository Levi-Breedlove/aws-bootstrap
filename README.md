# AWS Codex Fastlane Bootstrap

Turn a rough AWS idea—or a safe change to an existing system—into approved requirements, a technical PRD, and an autonomous Codex construction run.

**Release:** `1.0.0` · **Runtime:** Python 3.11+ using only the standard library during setup

## What Fastlane does

Fastlane welcomes the owner, configures this template, checks its own files,
and guides the owner through connecting the reviewed AWS Core plugin for current
AWS planning guidance. It then asks short intake questions and records decisions
in one project workspace.

Gate A — approve requirements → Gate B — approve the PRD and construction boundary → Codex builds autonomously inside that boundary.

AWS Core advises on service fit, IAM, Region support, reliability, security,
and cost. It cannot approve either gate or authorize an AWS change.

## Start in three steps

1. Create a repository with [Use this template](https://github.com/Levi-Breedlove/aws-bootstrap/generate),
   or download the [v1.0.0 ZIP](https://github.com/Levi-Breedlove/aws-bootstrap/releases/download/v1.0.0/aws-codex-fastlane-bootstrap.zip)
   and [checksum](https://github.com/Levi-Breedlove/aws-bootstrap/releases/download/v1.0.0/aws-codex-fastlane-bootstrap.zip.sha256).
2. Open the repository root in Codex.
3. Send:

```text
init template
```

Fastlane asks only for the project name and preferred AWS Region when they are
missing. A budget is optional during intake; the default is
`MINIMIZE_TOTAL_COST; HARD_CAP_NOT_STATED`, not an invented dollar limit.
When the owner supplies one, preserve its exact ISO currency and amount as
`MINIMIZE_TOTAL_COST; HARD_CAP: <ISO_CURRENCY> <OWNER_AMOUNT>`; for example,
`MINIMIZE_TOTAL_COST; HARD_CAP: USD 20.00`.

For a GitHub template, use `Setup: THIS_REPOSITORY` with `Local Git setup: USE_EXISTING`.
For an extracted ZIP, use `Local Git setup: INIT_AND_BASELINE_COMMIT`. For an existing project,
use `Setup: ADOPT_EXISTING_REPOSITORY`; Fastlane previews collisions and never
blanket-overwrites the project.

## Set up AWS Core

The Fastlane skills and read-only advisors are already inside this repository.
AWS Core `1.1.0` is declared from the official Agent Toolkit commit
`36f16570de2015c0f0ce94ba9e391bd703c9ffb7` and remains `AVAILABLE` until the owner
selects it. Its immutable AWS Core marketplace declaration is [`.agents/plugins/marketplace.json`](.agents/plugins/marketplace.json).

Fastlane is instruction-only for Codex and AWS Core. It never installs a Codex
client, registers a marketplace, changes plugin state, or launches another
session. BOOT-00 tells the owner exactly what to do:

1. Plugins are unavailable in the Codex IDE extension. Open this repository in
   ChatGPT desktop Codex or an interactive Codex CLI. Install or update the CLI
   yourself from the [official Codex instructions](https://learn.chatgpt.com/docs/developer-commands?surface=cli)
   if needed; Fastlane never runs that installation.
2. Run `uvx --version` in the terminal you opened. If it is missing, Fastlane
   prints one precise option from the official [uv guide](https://docs.astral.sh/uv/getting-started/installation/):

```text
python scripts/uv_setup_assistant.py plan --root . --json
```

   Fastlane never runs the printed command, a package manager, an installer, or
   a PATH-discovered `uvx` binary. Run the command yourself in a visible
   terminal, restart that terminal, and run `uvx --version` yourself.
3. In a terminal that **you opened** at this repository root, run:

```text
codex plugin marketplace add .
codex -C . --sandbox workspace-write --ask-for-approval on-request
```

4. Following the [AWS plugin guide](https://docs.aws.amazon.com/agent-toolkit/latest/userguide/plugins.html),
   enter `/plugins`, open **AWS Codex Fastlane Dependencies**, and select the
   `AVAILABLE` AWS Core `1.1.0` pin. Restart Codex and reopen this repository.
5. Open `/hooks`, compare every matching hook, and stop on a changed, disabled,
   unknown, or conflicting definition.
6. The owner trusts the exact current definition. Fastlane never uses
   `--dangerously-bypass-hook-trust`.
7. Run the inert deny and harmless allow probes, then send:

```text
@AWS Core
VERIFY AWS CORE AND CONTINUE FASTLANE
```

Setup proves `retrieve_skill` and `search_documentation` are callable. Fastlane
never runs the two Codex commands above, calls `call_aws` or `run_script`,
configures credentials, or accesses AWS.

## How the workflow runs

```text
BOOT-00 setup and AWS Core verification
  → INTAKE-10 guided intake
  → REQ-10 requirements review
  → Gate A owner approval
  → DESIGN-10 technical PRD
  → Gate B owner approval
  → TASK-10 dependency graph
  → BUILD-20 autonomous local construction
  → RELEASE-10 evidence review
  → AWS-10 read-only preflight
  → exact authorized deployment, or stop
```

Intake asks no more than three related questions at a time and accepts “I’m not
sure—recommend one.” A Quick MVP is one small, reversible development release.
An AWS lane describes planned access; it does not authorize a change. Security
controls are requirements, not cost tradeoffs. Fastlane evaluates a secure,
managed, pay-per-use serverless baseline first, then records a different
architecture when requirements justify it.

A successful first setup ends with stable machine-derived fields:

```text
AWS CODEX FASTLANE — READY

Classification: ACTIVE_GREENFIELD
Lifecycle: INTAKE_REQUIRED
Doctor: PASS
Next prompt: INTAKE-10
Fastlane skills: READY
Project agents: READY
AWS Toolkit marketplace: DECLARED_AND_PINNED
aws-core plugin: AVAILABLE
AWS Core hooks: APPROVED_AND_VERIFIED
AWS Core hook conflict review: PASS
AWS access: NOT USED
Gate A: BLOCKED
Gate B: BLOCKED
Evidence: NOT_READY
AWS authorization: NONE
```

`RESUME` routes to the next valid prompt. `BLOCKED` names the exact inconsistency
and stops affected work. An AWS change always requires a current record naming
the account, Region, environment, resources, operations, cost limit, rollback
plan, and expiration.

## Repository map

```text
.
├── AGENTS.md                 # Always-on authority and lifecycle rules
├── README.md                 # Human onboarding
├── bootstrap.py              # Initialization and brownfield adoption
├── bootstrap.yaml            # Derived lifecycle mirror; never authorization
├── bootstrap.manifest.json   # Exact release inventory and hashes
├── docs/
│   ├── adr/                  # Consequential architecture decisions
│   └── project/
│       ├── PRD.md            # Requirements, design, Gate A, and Gate B
│       ├── BUGFIX.md         # Active defect and regression contract
│       ├── TASKS.md          # Dependency graph and execution state
│       ├── VERIFY.md         # Observed evidence
│       └── RUNBOOK.md        # Deploy, rollback, recovery, and teardown
├── .agents/skills/           # Repo-scoped Fastlane procedures
├── .agents/plugins/          # Immutable AWS Core marketplace declaration
├── .codex/agents/            # Read-only planning and evidence advisors
├── prompts/CODEX-PROMPTS.md  # Exact prompts, receipts, and stop conditions
├── scripts/                  # Doctor, optional uv setup, runtime, and packaging
├── {app,infrastructure,tests}/AGENTS.md  # Scope-specific rules
└── .github/                  # CI, issue forms, and PR template
```

The five files in [`docs/project/`](docs/project/) are the active workspace; `bootstrap.manifest.json` is the exhaustive inventory.

## Privacy and AWS safety

- The repository stores no Codex login, client path, plugin installation state,
  hook trust, AWS credentials, account identifier, username, or setup history.
- Setup receipts may display a local path to that user, but never commit it.
- The uv assistant emits instructions only. It never starts a child process,
  forwards environment variables, reads credentials, or writes user state.
- Codex keeps its normal login, plugin, trust, and session data in that user's
  local Codex profile. Those files are outside this repository and release ZIP.
- Hook trust is separate because executable hook code must be reviewed by the
  owner. Tool availability never grants AWS authority.

## Verify or troubleshoot

```text
python scripts/bootstrap_dependencies.py --root . --json
python scripts/bootstrap_doctor.py --root . --json
python scripts/uv_setup_assistant.py plan --root . --json
python scripts/task_waves.py docs/project/TASKS.md --ready
```

Maintainers also run `python -m unittest discover -s tests -v`,
`python scripts/update_manifest.py --check`, and
`python scripts/package_release.py --check`. Release ZIPs are generated under
ignored `dist/` and are never committed.

## Agent reference — exact contracts

[`AGENTS.md`](AGENTS.md), [`prompts/CODEX-PROMPTS.md`](prompts/CODEX-PROMPTS.md), and
[`SECURITY.md`](SECURITY.md) own exact contracts. Runtime state comes from repository evidence, not chat.
