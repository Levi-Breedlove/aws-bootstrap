# My AWS Project

A lightweight, Codex-native AWS project bootstrap aligned to the AWS Well-Architected Framework.

It keeps the project rigorous without creating a document factory.

## Core model

| Source | Owns |
|---|---|
| `PRD.md` | Requirements, user stories, acceptance criteria, architecture, component design, data flow, error handling, and testing strategy |
| `BUGFIX.md` | Current, expected, and intentionally unchanged behavior for an active defect |
| `TASKS.md` | Executable task graph, dependencies, waves, and live implementation status |
| `AGENTS.md` | How Codex must analyze, plan, implement, validate, and synchronize work |
| `VERIFY.md` | Evidence that requirements and Well-Architected controls are satisfied |
| `RUNBOOK.md` | Repeatable build, deployment, monitoring, rollback, recovery, and teardown procedures |
| `docs/adr/` | Only consequential, difficult-to-reverse architectural decisions |
| GitHub Issues | Durable project-tracking mirror of non-trivial `TASKS.md` items |
| GitHub Projects | Status, priority, wave, release, risk, and evidence views |
| Pull requests | Change review and task-specific implementation evidence |
| Code, tests, schemas, and IaC | Actual system behavior |

## Repository shape

```text
.
├── README.md
├── AGENTS.md
├── PRD.md
├── BUGFIX.md
├── TASKS.md
├── VERIFY.md
├── RUNBOOK.md
├── bootstrap.py
├── app/
│   └── AGENTS.md
├── infrastructure/
│   └── AGENTS.md
├── tests/
│   └── AGENTS.md
├── scripts/
│   └── task_waves.py
├── prompts/
│   └── CODEX-PROMPTS.md
├── docs/
│   └── adr/
│       └── 0000-template.md
└── .github/
    ├── ISSUE_TEMPLATE/
    │   ├── aws-vertical-slice.yml
    │   ├── bugfix.yml
    │   └── waf-risk.yml
    └── PULL_REQUEST_TEMPLATE.md
```

Add nested `AGENTS.md` files only where a directory genuinely needs different rules.

## Project flow

```text
Idea or problem
  -> PRD requirements
  -> requirements analysis gate
  -> PRD technical design
  -> TASKS checklist sorted into dependency-aware waves
  -> execute one task or one safe wave
  -> pull requests and verification evidence
  -> end-of-day GitHub Issue synchronization
  -> deployment and operations through RUNBOOK.md
```

For a defect:

```text
Bug report
  -> BUGFIX.md analysis
  -> regression properties and expected behavior
  -> TASKS.md
  -> implementation and verification
```

## Why design lives in `PRD.md`

For solo builders and small AWS projects, a separate design document often creates another synchronization surface. This template keeps requirements and technical design in one file, but separates them into explicit sections.

Codex must analyze the full requirement set before it may mark the design as ready. The requirements-analysis gate checks for:

- logical inconsistencies;
- ambiguities;
- conflicting constraints;
- unstated assumptions;
- missing edge cases;
- concurrency and failure gaps;
- requirements that cannot be objectively verified.

A separate `DESIGN.md` is appropriate later only if the design has a distinct owner, approval process, audience, or release lifecycle.

## Property-based testing model

The PRD does not contain test code. It defines properties and invariants that implementation tests must prove across generated inputs.

Examples:

- unauthorized actors can never access another tenant's resource;
- duplicate delivery produces one effective result;
- any accepted payload round-trips without data loss;
- retries never exceed the configured bound;
- invalid state transitions never produce a committed state;
- no generated secret or sensitive value appears in telemetry.

Example-based tests still cover known scenarios. Property-based tests explore broader input and state spaces.

## `TASKS.md` and GitHub Issues

`TASKS.md` is the **live execution source** during a Codex work session.

Each non-trivial task receives a stable ID such as `TASK-004`. That ID is copied into its GitHub Issue title or body. By the end of the workday, Codex synchronizes:

- title and outcome;
- acceptance criteria;
- dependencies;
- current status;
- linked pull request;
- validation and evidence summary;
- blockers.

GitHub Issues are the durable collaboration and project-tracking mirror. They do not independently redefine the task.

Tiny implementation steps may remain checkboxes inside a task or issue. Do not create issue spam for every command or variable rename.

## Waves and concurrency

`TASKS.md` declares dependencies. `scripts/task_waves.py` validates them and sorts tasks into waves:

- Wave 1: tasks with no dependencies.
- Wave 2: tasks whose dependencies are all in earlier waves.
- Wave N: continues until every task is assigned.
- A cycle or missing dependency fails validation.

Tasks in one wave are *eligible* for concurrency, not automatically safe to run concurrently. Codex must serialize tasks that:

- edit overlapping files;
- mutate the same AWS resources;
- share mutable state;
- depend on one another semantically;
- require the same irreversible approval gate.

AWS-changing tasks remain approval-gated and should normally run sequentially.

## Task wave commands

Windows Command Prompt (`cmd.exe`):

```cmd
REM Show the computed wave plan
py -3 scripts\task_waves.py TASKS.md

REM Show tasks whose dependencies are complete
py -3 scripts\task_waves.py TASKS.md --ready

REM Show one task
py -3 scripts\task_waves.py TASKS.md --task TASK-001

REM Mark a task in progress
py -3 scripts\task_waves.py TASKS.md --set-status TASK-001 IN_PROGRESS

REM Link the corresponding GitHub Issue
py -3 scripts\task_waves.py TASKS.md --set-issue TASK-001 https://github.com/OWNER/REPO/issues/12
```

macOS, Linux, or a POSIX shell:

```bash
# Show the computed wave plan
python3 scripts/task_waves.py TASKS.md

# Show tasks whose dependencies are complete
python3 scripts/task_waves.py TASKS.md --ready

# Show one task
python3 scripts/task_waves.py TASKS.md --task TASK-001

# Mark a task in progress
python3 scripts/task_waves.py TASKS.md --set-status TASK-001 IN_PROGRESS

# Link the corresponding GitHub Issue
python3 scripts/task_waves.py TASKS.md --set-issue TASK-001 https://github.com/OWNER/REPO/issues/12
```

The script validates and updates task metadata. Codex performs the actual implementation.

## Set up in another IDE

This repository is a project template, not a deployable application. Its bootstrap uses only the Python standard library; application, infrastructure, and AWS dependencies are chosen later from the approved `PRD.md` design.

The setup is IDE-independent. Use the official Codex IDE extension when it is available for your editor. Otherwise, run Codex CLI in the editor's integrated terminal. Both approaches use the same repository files and instructions.

The `My AWS Project`, `{{AWS_REGION}}`, and `{{MONTHLY_BUDGET}}` values are template placeholders. Do not replace every occurrence manually. Running `bootstrap.py` writes a generated project in which those placeholders are replaced with the command-line values you provide.

### 1. Install the local prerequisites

Required:

- [Git](https://git-scm.com/downloads);
- Python 3.9 or newer;
- Codex through either the [IDE extension](https://learn.chatgpt.com/docs/codex/ide) or [Codex CLI](https://learn.chatgpt.com/docs/codex/cli).

Optional until the project design requires them:

- AWS CLI v2 for authenticated AWS discovery and deployments;
- GitHub CLI for creating and synchronizing issues and pull requests;
- an application runtime such as Node.js, Java, .NET, or Docker.

### 2. Identify the active terminal shell and Python command

The IDE does not determine the shell. A Windows IDE can open Git Bash, Command Prompt, or PowerShell, and each shell has different command syntax.

| What the terminal looks like | Active shell | Try this Python command first |
|---|---|---|
| `$`, `MINGW64`, or an error beginning with `bash:` | Bash or Git Bash | `python3` |
| `C:\path\to\project>` | Windows Command Prompt (`cmd.exe`) | `py -3` |
| `PS C:\path\to\project>` | Windows PowerShell | `py -3` |
| macOS or Linux terminal | Bash, Zsh, or another POSIX shell | `python3` |

If the terminal reports `bash: py: command not found`, you are in Bash—not Command Prompt. Try `python3`; the missing `py` command does not by itself mean Python is missing.

Bash or Git Bash:

```bash
python3 --version
git --version
```

Command Prompt or PowerShell:

```text
py -3 --version
git --version
```

Python 3.9 or newer is required. If the first Python command fails, try `python --version`. Use whichever command successfully reports Python 3.9+ in every later step; do not mix Bash, CMD, and PowerShell continuation syntax.

### 3. Extract and open the template

Extract the ZIP to a normal development directory. In the IDE, open the inner `aws-codex-well-architected-bootstrap` folder—the folder that directly contains `AGENTS.md`, `README.md`, and `bootstrap.py`.

Do not use the extracted template directory as the target. Keep it clean and generate the real project as a sibling directory so the template remains reusable.

### 4. Generate the project

From the template root in the IDE terminal, first confirm that the script is present. Use `ls bootstrap.py` in Bash or `dir bootstrap.py` in Command Prompt. Then run the example for the shell identified in Step 2. Replace the example name, Region, budget, and target directory with the values for the workload.

Bash or Git Bash when `python3 --version` succeeds:

```bash
python3 bootstrap.py --target ../my-project --project-name "My AWS Project" --region {{AWS_REGION}} --budget '{{MONTHLY_BUDGET}}'
```

Windows Command Prompt (`cmd.exe`)—recommended as one line:

```cmd
py -3 bootstrap.py --target ..\my-project --project-name "My AWS Project" --region {{AWS_REGION}} --budget "{{MONTHLY_BUDGET}}"
```

Command Prompt does not use Bash backslashes or PowerShell backticks for continuation. If `py` is unavailable but `python --version` works, replace `py -3` with `python`.

Windows PowerShell:

```powershell
py -3 bootstrap.py --target ..\my-project --project-name "My AWS Project" --region {{AWS_REGION}} --budget '{{MONTHLY_BUDGET}}'
```

The arguments mean:

| Argument | Purpose |
|---|---|
| `--target` | Destination for the generated project. Prefer a new sibling directory. |
| `--project-name` | Human-readable workload name written into the templates. |
| `--region` | Primary AWS Region used in planning and preflight checks. It does not deploy anything. |
| `--budget` | Monthly cost ceiling recorded in the project documents. It does not create an AWS Budget. |
| `--force` | Overwrites matching bootstrap files in an existing target. Omit it for normal setup. |

The script skips files that already exist unless `--force` is supplied. Treat `--force` carefully because it can replace planning files that already contain project decisions.

### 5. Open the generated project root

Close the template workspace and open the generated `my-project` folder as the IDE workspace or project. Codex discovers the root `AGENTS.md` and applies the more specific files under `app/`, `infrastructure/`, and `tests/` when work enters those directories.

Do not open only a nested source folder. Opening the generated project root ensures Codex can see the complete requirements, task, verification, and runbook context.

### 6. Connect Codex

#### Option A: Codex IDE extension

Install the official Codex extension from the IDE's extension marketplace, open its panel, and select **Sign in with ChatGPT**. If the extension is not offered for that IDE, use Option B.

#### Option B: Codex CLI in any IDE terminal

Install the CLI with the official installer.

macOS or Linux:

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | sh
codex login
```

Windows with Git Bash can invoke the official Windows installer through PowerShell:

```bash
powershell.exe -NoProfile -Command "irm https://chatgpt.com/codex/install.ps1 | iex"
codex login
```

Windows PowerShell:

```powershell
irm https://chatgpt.com/codex/install.ps1 | iex
codex login
```

Windows Command Prompt (`cmd.exe`) can invoke the same official installer through PowerShell:

```cmd
powershell -NoProfile -Command "irm https://chatgpt.com/codex/install.ps1 | iex"
codex login
```

Restart the IDE terminal if `codex` is not found immediately. Then, from the generated project root, verify the session and start Codex:

```bash
codex login status
codex
```

The normal login flow opens a browser. For a remote or headless environment, use `codex login --device-auth`. Do not place an API key, access token, or AWS credential in this repository.

### 7. Initialize Git and validate the bootstrap

Bash or Git Bash when `python3` passed Step 2:

```bash
cd ../my-project
git init
git add .
git commit -m "chore: initialize AWS Codex project"
python3 scripts/task_waves.py TASKS.md
python3 scripts/task_waves.py TASKS.md --ready
```

Windows Command Prompt (`cmd.exe`):

```cmd
cd /d ..\my-project
git init
git add .
git commit -m "chore: initialize AWS Codex project"
py -3 scripts\task_waves.py TASKS.md
py -3 scripts\task_waves.py TASKS.md --ready
```

Windows PowerShell:

```powershell
Set-Location ..\my-project
git init
git add .
git commit -m "chore: initialize AWS Codex project"
py -3 scripts\task_waves.py TASKS.md
py -3 scripts\task_waves.py TASKS.md --ready
```

If Step 2 selected `python` instead, replace `python3` or `py -3` with `python` in the validation commands.

Expected initial validation includes `TASK-001` in Wave 1. This confirms the task file parses; it does not mean the placeholder task is approved for implementation.

### 8. Start the requirements gate

Use Prompt 1 in [`prompts/CODEX-PROMPTS.md`](prompts/CODEX-PROMPTS.md), or begin with:

```text
Read AGENTS.md, PRD.md, TASKS.md, VERIFY.md, and RUNBOOK.md. Do not change code or AWS. Help me complete the workload profile and requirements-analysis gate for this project. Identify conflicts, missing boundaries, security and recovery gaps, and assumptions that would materially change the design.
```

Do not install an application framework or deploy AWS resources just to complete setup. First make the requirements gate ready, complete the technical design, generate real tasks, and replace the placeholder commands in `RUNBOOK.md`.

### Common setup problems

| Symptom | Likely cause | Fix |
|---|---|---|
| `bootstrap.py` is not found | The terminal is not in the extracted template root | Open the folder containing `bootstrap.py`, or change to it in the terminal |
| `bash: py: command not found` | The terminal is Bash or Git Bash, not Command Prompt | Run `python3 --version`; if it succeeds, use `python3` for all Python commands |
| `python`, `python3`, or `py` is not found | Python is missing or the IDE has not reloaded `PATH` | Install Python 3.9+ and restart the IDE |
| `codex` is not found after installation | The current terminal has stale `PATH` state | Open a new terminal or restart the IDE |
| Codex ignores repository guidance | The IDE opened a nested directory instead of the project root | Reopen the generated folder that contains the root `AGENTS.md` |
| Existing files show `SKIP` | The target directory already contains those paths | Use a new target, or inspect every conflict before considering `--force` |
| AWS commands use the wrong account or Region | The shell has the wrong profile or inherited environment variables | Stop; run the read-only identity and Region checks in `RUNBOOK.md` before any mutation |

## First project actions

0. Confirm the currently available Codex models with `/model`; use the prompt pack's model guide as the workflow default.

1. Complete the workload profile and initial feature requirements in `PRD.md`.
2. Run the requirements-analysis prompt.
3. Resolve or explicitly accept the findings.
4. Complete the architecture and implementation sections in `PRD.md`.
5. Define the MVP or first release outcome.
6. Generate `TASKS.md` as a checklist sorted into dependency-aware waves.
7. Remove irrelevant rows from `VERIFY.md`.
8. Add actual build and deployment procedures to `RUNBOOK.md`.
9. Create a GitHub parent issue for the release.
10. Mirror non-trivial tasks as native GitHub sub-issues.
11. Execute one task or one safe wave at a time.
12. Synchronize task status to GitHub by the end of the workday.

## Suggested GitHub Project fields

| Field | Values |
|---|---|
| Status | Backlog, Ready, In progress, In review, Blocked, Done |
| Priority | Critical, High, Medium, Low |
| Wave | 1, 2, 3, N |
| Primary pillar | Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization, Sustainability |
| Risk | High, Medium, Low |
| Release | MVP, v1.0, Hardening, Production |
| Evidence | Not started, Local pass, Pending AWS, Verified |
| Effort | XS, S, M, L |

## Suggested labels

```text
pillar:operational-excellence
pillar:security
pillar:reliability
pillar:performance
pillar:cost
pillar:sustainability

type:feature
type:bug
type:risk
type:operations

status:ready
status:blocked

priority:critical
priority:high
priority:medium
priority:low

evidence:local
evidence:pending-aws
evidence:verified
```

## Prompt pack

[`prompts/CODEX-PROMPTS.md`](prompts/CODEX-PROMPTS.md) begins with a current Codex model-selection guide, then provides reusable prompts for:

1. requirements analysis;
2. completing PRD architecture and design;
3. bugfix analysis;
4. generating the task checklist, waves, and GitHub plan;
5. executing one task;
6. executing a safe wave;
7. end-of-day GitHub synchronization;
8. release-readiness review;
9. post-deployment evidence reconciliation;
10. educational implementation and mentoring mode.


## Educational mode

Use Prompt 10 when you want Codex to implement a real task while explaining:

- the current architecture and affected components;
- relevant AWS services and patterns;
- risks and Well-Architected tradeoffs;
- alternatives considered;
- validation and evidence;
- reusable engineering lessons.

It provides concise milestone updates and a final learning recap without
creating extra tutorial or planning documents.

## Minimality rules

- One fact has one authoritative home.
- Requirements and design live in `PRD.md`.
- Active defect behavior lives in `BUGFIX.md`.
- Executable work and live status live in `TASKS.md`.
- Durable task tracking mirrors to GitHub Issues.
- Proof lives in `VERIFY.md`.
- Operational procedures live in `RUNBOOK.md`.
- Runtime truth lives in code, tests, schemas, IaC, metrics, and logs.
- New Markdown files require a distinct owner and lifecycle.
