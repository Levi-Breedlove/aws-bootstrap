# My AWS Project — Fastlane Start Guide

This repository uses AWS Codex Fastlane `1.0.0`: a two-gate path from a rough
idea to safe, bounded autonomous construction.

The bootstrap does not deploy AWS resources. It first helps you define what to
build, records two explicit owner decisions, and then lets Codex implement only
inside the approved construction envelope.

## Choose the smallest responsible path

A Quick MVP is one small, reversible development release.

- Use `quick-mvp` for that narrow development outcome.
- Use `standard` when the release needs broader integration and operating
  coverage.
- Use `high-risk` for production, sensitive or regulated data, payments,
  customer isolation, shared infrastructure, irreversible data changes, or a
  potentially large outage or cost increase.

The profile changes scope and review depth; it never reduces required testing
or approval. An AWS lane describes planned access; it does not authorize a
change. AWS changes require an approved record naming the account, Region,
environment, resources, operations, cost limit, rollback plan, and expiration.

## Before you start

You need:

- Python 3.11 or newer;
- Git;
- Codex in the IDE or terminal;
- an absolute target path that is not this template directory or inside it.

AWS credentials and the AWS CLI are not needed for intake, requirements,
design, or local construction. Add them only when the approved work reaches an
AWS preflight.

## Preferred launch: BOOT-00

Open the extracted template root—the folder containing this file,
`AGENTS.md`, and `bootstrap.py`—in Codex. Then paste:

```text
START AWS CODEX BOOTSTRAP
Target path: /absolute/path/to/project
Local Git setup: INIT_AND_BASELINE_COMMIT
```

Replace the target with a real absolute path. On Windows, use a complete path
such as `C:\Users\you\source\project`.

Choose exactly one local Git setup:

| Choice | Meaning |
|---|---|
| `INIT_AND_BASELINE_COMMIT` | Initialize a new local repository and commit the validated bootstrap using an already configured Git identity |
| `USE_EXISTING` | Preserve and inspect an existing local repository and its current baseline |
| `DO_NOT_INITIALIZE` | Make no Git write; Gate B remains blocked until a trustworthy baseline is authorized later |

Codex uses `BOOT-00` from `prompts/CODEX-PROMPTS.md` to inspect before writing,
classify the target, run the installer safely, validate the result, and explain
the workflow. It never adds a remote, writes GitHub, or accesses AWS during
this launch.

For a brownfield target, BOOT-00 previews every collision. Existing files are
preserved unless you explicitly approve a complete, hash-bound per-file
adoption plan. Blanket overwrite is disabled.

## Begin the guided intake

When launch succeeds, Codex ends with a prefilled command like this:

```text
START GUIDED INTAKE
Project path: /absolute/path/to/project
Project mode: greenfield
Delivery profile: quick-mvp
Idea or requested change: A plain-language description of the outcome
```

Paste the returned command. Codex asks short, understandable questions in
small rounds, reflects what it heard, and writes the agreed facts into
`PRD.md`. You do not need to arrive with a finished PRD.

Choose `brownfield` for an existing repository or deployed system. If you are
unsure about mode or profile, use `I'm not sure—recommend one` and let Codex
explain its recommendation.

## The delivery path

```text
BOOT-00 -> guided intake -> requirements analysis -> Gate A
        -> technical design and construction envelope -> Gate B
        -> task plan -> bounded autonomous construction -> release review
```

There are exactly two routine human gates:

1. **Gate A** approves the current analyzed requirements. Codex can then design
   the solution, but cannot start implementation.
2. **Gate B** approves the complete PRD and exact construction envelope. Codex
   can then generate tasks and run them without task-by-task approval while it
   stays inside that envelope.

Codex generates the exact approval receipt for each current revision. Return
that receipt unchanged with a real human approver name or handle. Do not use an
example receipt from the prompt pack because its IDs and digest will not match
your project.

After Gate B, `TASK-10` creates the executable task graph. `BUILD-20` can run
multiple safe waves over a long session, using claims, attempt budgets, Git
checkpoints, verification evidence, and explicit pause/resume state. It stops
when approval becomes stale, a boundary is exhausted, state is unsafe, or a
needed action was not authorized.

## Agent reference — exact bootstrap operation

## Check the project at any time

From the generated project root:

```bash
python scripts/bootstrap_doctor.py --root .
python scripts/task_waves.py TASKS.md
python scripts/task_waves.py TASKS.md --ready
```

The doctor is read-only. It verifies the manifest and runtime-control hashes,
checks lifecycle consistency, and tells you the correct next prompt. Treat an
error as a stop condition; do not edit the machine-readable mirror to bypass
it.

## Manual installation fallback

If you cannot launch Codex from the extracted template, generate a target with
the standard-library installer:

```bash
python bootstrap.py \
  --target /absolute/path/to/project \
  --project-name "My AWS Project" \
  --region us-west-2 \
  --budget '$50/month'
```

Then open the generated target in Codex, initialize or connect it to the
intended local Git repository, run the doctor, and send the BOOT-00 launch
command with `USE_EXISTING`. Never use `--force`; brownfield conflicts require
the reviewable adoption-map flow.

## Where information lives

| File | Purpose |
|---|---|
| `AGENTS.md` | Workflow and safety rules Codex must follow |
| `PRD.md` | Requirements, design, gates, and approved construction envelope |
| `TASKS.md` | Task graph, live execution state, claims, and checkpoints |
| `VERIFY.md` | Evidence actually observed |
| `RUNBOOK.md` | Build, deploy, rollback, recovery, operations, and teardown |
| `bootstrap.yaml` | Derived resume mirror; never approval or authority |
| `prompts/CODEX-PROMPTS.md` | Canonical prompt pack and exact receipts |

The repository is the source of truth. Notion may be used as a convenient
launcher and view, but decisions must be reconciled into these versioned files.

## AWS safety boundary

Intake, design, tasks, and local implementation do not imply permission to
change AWS. Before any AWS mutation, Codex must identify the account, role,
Region, environment, resources, operations, cost, artifact, rollback, and
expiry; run a read-only preflight; and prove the action fits the current
authorization. Production, destructive, shared-resource, or out-of-envelope
work stops for explicit authority.
