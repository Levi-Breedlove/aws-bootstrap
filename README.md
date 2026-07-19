# AWS Codex Fastlane Bootstrap

Turn a rough AWS idea—or a change to an existing system—into an approved product
plan, then let Codex build for long stretches inside a clear boundary.

**Current release:** `1.0.0`
**Runtime:** Python 3.11+ with no third-party Python dependencies

## Start here

The primary path is [Use this template](https://github.com/Levi-Breedlove/aws-bootstrap/generate).
It creates a new repository whose root is ready to open in Codex. The
[v1.0.0 ZIP](https://github.com/Levi-Breedlove/aws-bootstrap/releases/download/v1.0.0/aws-codex-fastlane-bootstrap.zip)
and its
[checksum](https://github.com/Levi-Breedlove/aws-bootstrap/releases/download/v1.0.0/aws-codex-fastlane-bootstrap.zip.sha256)
provide the same working bootstrap as a downloadable recovery artifact.

Open the repository root in the Codex desktop app or Codex CLI, trust the
repository when prompted, and send:

```text
init template
```

That short message is the normal entrypoint. Fastlane welcomes you, checks its
repo-scoped skills and project agents, confirms that the pinned official AWS
Core plugin is loaded, inspects the repository, and then asks only for project
name, preferred AWS Region, and development budget.

For a repository created with **Use this template**, the equivalent explicit
form is:

```text
START AWS CODEX FASTLANE
Setup: THIS_REPOSITORY
Local Git setup: USE_EXISTING
```

For an extracted release ZIP, `init template` safely creates a local Git
baseline when Git is absent and author identity is already configured. The
equivalent explicit form is:

```text
START AWS CODEX FASTLANE
Setup: THIS_REPOSITORY
Local Git setup: INIT_AND_BASELINE_COMMIT
```

Setup changes only untouched template placeholders and runs read-only checks.
It may download the exact pinned `aws-core` plugin from the official AWS Agent
Toolkit repository. It does not configure AWS credentials, inspect an AWS
account, or authorize an AWS change.

### First-session AWS Core setup

The repo marketplace at `.agents/plugins/marketplace.json` declares AWS Core as
`INSTALLED_BY_DEFAULT` from an immutable official AWS commit. The four Fastlane
skills and three read-only project agents are already stored in the repository
and are discovered by Codex; they are not copied into a personal Codex folder.
The current dependency is AWS Core `1.1.0` at Agent Toolkit commit
[`36f16570`](https://github.com/aws/agent-toolkit-for-aws/commit/36f16570de2015c0f0ce94ba9e391bd703c9ffb7).
See the official [Agent Toolkit product page](https://aws.amazon.com/products/developer-tools/agent-toolkit-for-aws/),
[plugin guide](https://docs.aws.amazon.com/agent-toolkit/latest/userguide/plugins.html),
and [Codex plugin documentation](https://learn.chatgpt.com/docs/plugins).

New plugin capabilities load only when a Codex session starts. If the first
`init template` request cannot see AWS Core yet, Fastlane returns `TOOLKIT SETUP
REQUIRED` with one next action: approve or confirm AWS Core in `/plugins` if
prompted, start a new Codex session in the same repository, and send `init
template` again. Fastlane does not continue to intake or claim AWS assistance
until the current session can actually observe the plugin.

## The complete path

Gate A — approve requirements → Gate B — approve the PRD and construction boundary → Codex builds autonomously inside that boundary.

```text
Template setup
  → guided intake
  → Gate A: requirements approval
  → technical PRD and AWS design
  → Gate B: PRD and construction approval
  → dependency-aware tasks
  → autonomous local construction
  → read-only AWS preflight
  → exactly authorized deployment, when applicable
  → observed verification evidence
```

There are exactly two routine human decisions. Deployment, production,
destructive work, or a material change in scope pauses only when the current
Gate B boundary does not already contain that exact action.

## What Codex returns after setup

The explanation may adapt to the project, but these fields and their values are
derived from repository state:

```text
AWS CODEX FASTLANE — READY

Classification: ACTIVE_GREENFIELD
Lifecycle: INTAKE_REQUIRED
Doctor: PASS
Next prompt: INTAKE-10
Git baseline: <commit>
Fastlane skills: READY
Project agents: READY
AWS Toolkit marketplace: READY
aws-core plugin: AVAILABLE
AWS MCP documentation: READY
AWS credentials: NOT CHECKED
AWS access: NOT USED
Gate A: BLOCKED
Gate B: BLOCKED
Evidence: NOT_READY
AWS authorization: NONE
```

When setup is ready, the response ends with a prefilled `START GUIDED INTAKE`
command. `RESUME` means the project is coherent and has a later next prompt.
`BLOCKED` means the doctor found a concrete inconsistency and no construction
or AWS action may continue until it is reconciled.

## What users should expect

- Intake asks no more than three related questions at a time and accepts
  “I’m not sure—recommend one.”
- Gate A confirms scope, non-goals, assumptions, data, access, and measurable
  success before technical design begins.
- Gate B confirms the full PRD plus the exact files, commands, task limits,
  GitHub boundary, and AWS boundary Codex may use.
- After Gate B, Codex creates the task graph and continues through normal local
  work without task-by-task approval.
- AWS credentials are not needed for setup, intake, design, or local work.
- AWS Core supports requirements feasibility and design decisions with current
  AWS documentation. It advises Codex; it cannot approve Gate A or Gate B.
- AWS changes require an approved record naming the account, Region,
  environment, resources, operations, cost limit, rollback plan, and
  expiration. A credential or connected tool is never that approval.
- Observed local results and observed deployed AWS results are recorded
  separately. A plan, mock, or generated command is not deployed evidence.

## Repository map

```text
.
├── AGENTS.md                 # Always-on Codex operating rules
├── PRD.md                    # Requirements, design, Gate A, and Gate B
├── TASKS.md                  # Dependency graph and execution state
├── VERIFY.md                 # Observed evidence
├── RUNBOOK.md                # Deploy, rollback, recovery, and teardown
├── bootstrap.yaml            # Derived lifecycle state
├── bootstrap.manifest.json   # Exact template inventory and control hashes
├── bootstrap.py              # Initialization and brownfield adoption
├── .agents/skills/           # Repo-scoped Fastlane workflows
├── .agents/plugins/          # Pinned official AWS Core marketplace entry
├── .codex/agents/            # Read-only planning and evidence advisors
├── app/AGENTS.md             # Application-specific rules
├── infrastructure/AGENTS.md  # Infrastructure-specific rules
├── tests/AGENTS.md           # Verification rules
├── prompts/CODEX-PROMPTS.md  # Exact prompt and receipt contracts
├── scripts/                  # Doctor, task runtime, and packaging
└── .github/                  # CI, issue forms, and PR template
```

`bootstrap.manifest.json` is the exhaustive release inventory. The tree above
shows the files most users need to understand.

## What is deterministic and what uses agent judgment

| Machine-enforced | Context-dependent agent work |
|---|---|
| Template inventory, dependency pin, skills, agents, hashes, and release bytes | Which understandable follow-up question is most useful |
| Setup classification and lifecycle route | Recommended architecture and explained tradeoffs |
| Gate revision and approval validity | Implementation choices inside the approved design |
| Task dependency, claim, checkpoint, and ready-state rules | How independent approved tasks are divided |
| AWS authorization fields, expiry, identity, and target matching | Service-specific recommendations supported by current AWS documentation |
| Evidence status and release route | Plain-language summaries and learning explanations |

The model’s prose is intentionally human. Decisions, permissions, transitions,
and evidence are checked by the runtime rather than inferred from prose.

AWS Core adds current AWS knowledge and tools to the session; it does not make
the gates automatic. The requirements reviewer and AWS advisor may challenge a
proposal, but only the owner approves Gate A and Gate B. The evidence reviewer
may identify a mismatch, but the coordinator remains the only ledger writer.

## Delivery choices

| Choice | Use it for |
|---|---|
| `greenfield` | A new workload or repository |
| `brownfield` | An existing system whose behavior and user-owned changes must be preserved |
| `quick-mvp` | One small, useful, observable, reversible development release |
| `standard` | Broader integration and operational coverage |
| `high-risk` | Production, sensitive or regulated data, payments, customer isolation, shared infrastructure, irreversible data changes, or potentially large outage or cost impact |

A Quick MVP is one small, reversible development release. Use High Risk when
work involves production, sensitive or regulated data, payments, customer
isolation, shared infrastructure, irreversible data changes, or a potentially
large outage or cost increase. The profile changes scope and review depth; it
never reduces required testing or approval. An AWS lane describes planned access; it does not authorize a
change. AWS changes require an approved record
naming the account, Region, environment, resources, operations, cost limit,
rollback plan, and expiration.

## Brownfield adoption

From an untouched template checkout or ZIP, send:

```text
START AWS CODEX FASTLANE
Setup: ADOPT_EXISTING_REPOSITORY
Target path: <absolute existing repository path>
Local Git setup: USE_EXISTING
```

Codex performs read-only discovery and previews every collision. Existing
files remain unchanged unless the owner confirms a complete hash-bound decision
map. Blanket overwrite remains disabled.

## Verify or resume locally

```bash
python scripts/bootstrap_dependencies.py --root .
python scripts/bootstrap_doctor.py --root .
python scripts/bootstrap_doctor.py --root . --json
python scripts/task_waves.py TASKS.md --ready
```

The doctor is read-only. Treat an error as a stop condition; never edit
`bootstrap.yaml` to bypass an authoritative PRD, task, or evidence record.

## Release verification

The ZIP is only a delivery container; no ZIP is nested inside the project.

```bash
sha256sum --check aws-codex-fastlane-bootstrap.zip.sha256
unzip -t aws-codex-fastlane-bootstrap.zip
```

PowerShell:

```powershell
Get-FileHash .\aws-codex-fastlane-bootstrap.zip -Algorithm SHA256
Get-Content .\aws-codex-fastlane-bootstrap.zip.sha256
```

Before changing or repackaging this template, run:

```bash
python -m unittest discover -s tests -v
python scripts/package_release.py --check
```

Release assets are generated under ignored `dist/`; binary archives are never
committed to `main`. Security expectations remain in
[`SECURITY.md`](SECURITY.md).

## Agent reference — exact contracts

`AGENTS.md` contains the always-on authority, gate, stop, and single-writer
rules. `prompts/CODEX-PROMPTS.md` contains every exact prompt and receipt.
`bootstrap.manifest.json` is the complete source allowlist, and the doctor plus
task runtime enforce lifecycle, task, evidence, and AWS authorization state.
Those files are exhaustive; this README is the human onboarding guide.
