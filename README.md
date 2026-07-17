# AWS Codex Fastlane Bootstrap

Turn a rough AWS idea—or an existing repository—into a reviewed product plan,
then let Codex implement the approved work for long stretches without creating
a document factory.

**Current release:** `2.0.0`
**Runtime:** Python 3.11+ with no third-party Python dependencies

## What the fast lane does

- starts with a short, plain-language intake instead of asking you to write a
  complete PRD;
- supports new projects and brownfield repositories;
- keeps requirements, design, tasks, evidence, and operations in one small set
  of authoritative files;
- asks for exactly two routine human decisions;
- turns the approved PRD into dependency-aware tasks;
- lets Codex run those tasks autonomously inside a bounded construction
  envelope;
- pauses on stale approval, unsafe state, exhausted boundaries, or an external
  action that was not authorized;
- separates local evidence from GitHub and deployed AWS evidence.

## The two gates

| Gate | You approve | What Codex can do next |
|---|---|---|
| Gate A | A versioned, analyzed requirements set | Complete the technical design |
| Gate B | The complete PRD and an exact construction envelope | Generate tasks and run the authorized implementation |

Gate B is the handoff into autonomous construction. GitHub writes, AWS
mutations, production changes, destructive actions, and other side effects
remain limited to the exact authority recorded in that envelope or a later
action-specific receipt.

## Start a project

1. Download and verify [`aws-codex-fastlane-bootstrap.zip`](aws-codex-fastlane-bootstrap.zip),
   or clone this repository and open `my-project/`.
2. Extract the archive and open the extracted folder—the one containing
   `AGENTS.md`, `bootstrap.py`, and `prompts/CODEX-PROMPTS.md`—in Codex.
3. Choose an explicit target path outside the extracted template.
4. Paste this launch command, using an absolute target path:

```text
START AWS CODEX BOOTSTRAP
Target path: /absolute/path/to/project
Local Git setup: INIT_AND_BASELINE_COMMIT
```

`INIT_AND_BASELINE_COMMIT` creates a local repository and reviewed baseline
when Git author identity is already configured. Use `USE_EXISTING` for an
existing local repository or `DO_NOT_INITIALIZE` when you do not authorize a
Git write yet.

Codex runs `BOOT-00`, validates the install, explains the current state, and
returns a prefilled `START GUIDED INTAKE` command. The detailed startup and
fallback CLI instructions are in [`my-project/README.md`](my-project/README.md).

## Delivery choices

Project mode and delivery profile are independent:

| Choice | Use it for |
|---|---|
| `greenfield` | A new workload or repository |
| `brownfield` | An existing codebase or deployed system whose behavior and user changes must be preserved |
| `quick-mvp` | The smallest useful, observable, reversible outcome; the default when risk allows |
| `standard` | Broader integration and operational coverage |
| `high-risk` | Production, sensitive data, payments, tenancy, migrations, or other high-blast-radius work |

Faster delivery changes scope and ceremony, not identity, security, testing,
cost, rollback, or evidence standards.

## Operating model

The repository is authoritative. Notion can launch prompts and show status, but
it is not a second PRD.

| File | Authority |
|---|---|
| `AGENTS.md` | Workflow, scope, safety, and completion rules |
| `PRD.md` | Requirements, design, Gate A, Gate B, and the construction envelope |
| `TASKS.md` | Executable graph, task state, runs, claims, and checkpoints |
| `VERIFY.md` | Observed evidence and release proof |
| `RUNBOOK.md` | Build, deploy, rollback, recovery, operations, and teardown |
| `bootstrap.yaml` | Derived lifecycle mirror; never authorization |
| `prompts/CODEX-PROMPTS.md` | The versioned launch, intake, build, release, and AWS prompts |

The runtime controls are:

- `bootstrap.py` for collision-safe greenfield and brownfield installation;
- `scripts/bootstrap_doctor.py` for read-only integrity and lifecycle checks;
- `scripts/task_waves.py` for dependency planning, claims, checkpoints, pause,
  and resume.

Their SHA-256 digests are sealed in `bootstrap.manifest.json`.

## Verify the download

The checksum sidecar uses the standard `<digest>  <filename>` format:

```bash
sha256sum --check aws-codex-fastlane-bootstrap.zip.sha256
unzip -t aws-codex-fastlane-bootstrap.zip
```

On PowerShell, compare the output of:

```powershell
Get-FileHash .\aws-codex-fastlane-bootstrap.zip -Algorithm SHA256
Get-Content .\aws-codex-fastlane-bootstrap.zip.sha256
```

## Maintainer checks

The committed archive is generated only from the exact file list in
`my-project/bootstrap.manifest.json`. Paths are validated, symlinks are
rejected, member order and metadata are fixed, and the archive contains the
source bytes unchanged.

```bash
python -m unittest discover -s tests -v
python scripts/package_release.py --check
```

To rebuild the release artifact and checksum:

```bash
python scripts/package_release.py
```

See [`CHANGELOG.md`](CHANGELOG.md) for release notes.
