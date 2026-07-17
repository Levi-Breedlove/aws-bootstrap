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

For a repository created with **Use this template**, open the repository root
in Codex and send:

```text
START AWS CODEX FASTLANE
Setup: THIS_REPOSITORY
Local Git setup: USE_EXISTING
```

For an extracted release ZIP, send:

```text
START AWS CODEX FASTLANE
Setup: THIS_REPOSITORY
Local Git setup: INIT_AND_BASELINE_COMMIT
```

Codex asks for the project name, preferred AWS Region, and development budget
in one short round. Setup changes only the untouched template placeholders,
runs the read-only doctor, and does not contact AWS.

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
├── app/AGENTS.md             # Application-specific rules
├── infrastructure/AGENTS.md  # Infrastructure-specific rules
├── tests/AGENTS.md           # Verification rules
├── prompts/CODEX-PROMPTS.md  # Exact prompt and receipt contracts
├── scripts/                  # Doctor, task runtime, demo, and packaging
├── docs/demo/                # Tested quick-MVP walkthrough
└── .github/                  # CI, issue forms, and PR template
```

`bootstrap.manifest.json` is the exhaustive release inventory. The tree above
shows the files most users need to understand.

## What is deterministic and what uses agent judgment

| Machine-enforced | Context-dependent agent work |
|---|---|
| Template inventory, hashes, and release bytes | Which understandable follow-up question is most useful |
| Setup classification and lifecycle route | Recommended architecture and explained tradeoffs |
| Gate revision and approval validity | Implementation choices inside the approved design |
| Task dependency, claim, checkpoint, and ready-state rules | How independent approved tasks are divided |
| AWS authorization fields, expiry, identity, and target matching | Service-specific recommendations supported by current AWS documentation |
| Evidence status and release route | Plain-language summaries and learning explanations |

The model’s prose is intentionally human. Decisions, permissions, transitions,
and evidence are checked by the runtime rather than inferred from prose.

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
python scripts/bootstrap_doctor.py --root .
python scripts/bootstrap_doctor.py --root . --json
python scripts/task_waves.py TASKS.md --ready
```

The doctor is read-only. Treat an error as a stop condition; never edit
`bootstrap.yaml` to bypass an authoritative PRD, task, or evidence record.

## Tested example

Run the no-credential Internal Change Request API demonstration:

```bash
python scripts/run_demo.py
python scripts/run_demo.py --json
```

The demonstration creates a temporary project, verifies setup and routing,
shows the two approvals and three-task construction plan, runs local tests, and
proves that AWS mutation remains blocked without an exact authorization. See
[`docs/demo/internal-change-request-api.md`](docs/demo/internal-change-request-api.md).

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

Maintainers run:

```bash
python -m unittest discover -s tests -v
python scripts/package_release.py --check
```

Release assets are generated under ignored `dist/`; binary archives are never
committed to `main`. See [`CONTRIBUTING.md`](CONTRIBUTING.md),
[`SECURITY.md`](SECURITY.md), and [`CHANGELOG.md`](CHANGELOG.md).

## Agent reference — exact contracts

`AGENTS.md` contains the always-on authority, gate, stop, and single-writer
rules. `prompts/CODEX-PROMPTS.md` contains every exact prompt and receipt.
`bootstrap.manifest.json` is the complete source allowlist, and the doctor plus
task runtime enforce lifecycle, task, evidence, and AWS authorization state.
Those files are exhaustive; this README is the human onboarding guide.
