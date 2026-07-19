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

Open the repository root in the ChatGPT desktop app's Codex experience or in
Codex CLI, trust the repository when prompted, and send:

```text
init template
```

AWS Core plugins are not available in the Codex IDE extension. You may edit the
repository from VS Code, Cursor, or a Codespace, but first-run AWS Core setup
and verification must run in the ChatGPT desktop app or Codex CLI. Fastlane
detects the unsupported IDE surface, completes only safe local setup, and gives
you an exact handoff instead of downloading another Codex client.

That short message is the normal entrypoint. Fastlane welcomes you, validates
its repo-scoped skills, project agents, and pinned AWS Core marketplace entry,
then asks only for project name, preferred AWS Region, and development budget.
It configures the local template and runs the doctor before walking you through
the separate AWS Core plugin verification step.

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
It does not configure AWS credentials, inspect an AWS account, or authorize an
AWS change. It also does not install `pytest` or any other Python package;
Fastlane setup uses Python 3.11+ standard-library scripts.

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

AWS Core launches its MCP server with `uvx`, which is supplied by Astral
`uv`. This is a separate prerequisite from Python and `pytest`. BOOT-00 checks
`uvx --version` only after local setup passes and a supported Codex surface is
confirmed. It never installs `uv` automatically. If `uvx` is missing, follow
the official [AWS Agent Toolkit quick start](https://docs.aws.amazon.com/agent-toolkit/latest/userguide/quick-start.html)
and [Astral uv installation guide](https://docs.astral.sh/uv/getting-started/installation/),
then start a new Codex task. If `pipx` is already installed, `pipx install uv`
is one official isolated installation method, but it remains an explicit user
action rather than a template initialization step.

The marketplace file proves that Fastlane requests one approved AWS Core
revision; it does not prove that the plugin is installed, current, loaded, or
callable. Plugin management uses `/plugins`. Typing `@` invokes a selected
plugin; there is no separate `@plugin management` command.

On a supported surface, Fastlane uses the already-installed desktop app or CLI.
It never downloads or launches Codex CLI from the IDE extension as a workaround.
It also never registers a marketplace, installs AWS Core, or installs `uv`
from the unsupported IDE surface.

After local initialization, Fastlane shows this walkthrough when AWS Core still
needs installation, update, or verification:

1. Enter `/plugins` in Codex.
2. Open `AWS Codex Fastlane Dependencies`.
3. Install or update `AWS Core` to the template-approved `1.1.0` revision.
4. Restart Codex if prompted and reopen this repository in a new task.
5. Send `init template` again so Fastlane can review the installed hook before
   invoking the plugin.

### AWS Core hook approval

AWS Core includes one `PreToolUse` secret-safety hook. It checks Bash and AWS
MCP calls and blocks direct Secrets Manager value retrieval. That behavior is
compatible with Fastlane: it adds a restriction and cannot approve Gate A or
Gate B, authorize AWS, widen IAM, or override the construction boundary. The
stock template declares no project-local hooks.

Codex loads all matching user, project, and plugin hooks together, however, so
the template cannot assume that a user's other hooks are compatible. BOOT-00
therefore performs a runtime review:

1. Confirm the pinned AWS Core hook definition and expected file hashes.
2. Confirm the exact `python3` command used by the hook is available.
3. Open the Hooks page in Codex Settings, or `/hooks` in Codex CLI, and
   inventory every active hook that can match Bash or AWS MCP tools.
4. Stop if a hook is unreadable, changed, disabled, unknown, or conflicting.
5. Ask the owner to review and trust the exact current AWS Core hook definition.
6. Run an inert deny probe and harmless allow probe through Codex's normal Bash
   hook path; neither command accesses AWS.
7. Require the generated `APPROVE AWS CORE HOOKS` confirmation before continuing.

Codex records hook trust against the current definition hash. Updating the
plugin or changing the hook requires review again. Fastlane never automatically
trusts a hook and never uses `--dangerously-bypass-hook-trust`.

After the hook approval receipt, send:

```text
@AWS Core
VERIFY AWS CORE AND CONTINUE FASTLANE
```

The verification uses AWS Core's unauthenticated skill retrieval and
documentation search only. It must observe successful `retrieve_skill` and
`search_documentation` calls from AWS Core; a generic AWS documentation tool is
not enough. It never calls `call_aws` or `run_script`, configures credentials,
or accesses an AWS account during setup.

If the repository marketplace is not visible after trusting and reopening the
repository, stop setup. Confirm this repository is trusted, verify
`.agents/plugins/marketplace.json` is unchanged, and reopen it in ChatGPT
desktop Codex or Codex CLI. Do not register the moving upstream repository or
another marketplace as a fallback: only the immutable source revision declared
by this template is approved. If it remains unavailable, report
`PINNED_MARKETPLACE_UNAVAILABLE` and stop before plugin installation or intake.

## The complete path

Gate A — approve requirements → Gate B — approve the PRD and construction boundary → Codex builds autonomously inside that boundary.

```text
Template setup
  → AWS Core runtime and plugin setup
  → owner review of the current AWS Core hook definition
  → unauthenticated AWS Core capability verification
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

There are exactly two routine product decisions. AWS Core hook trust is a
one-time tool-setup confirmation, not a product lifecycle gate, and repeats
only when the trusted hook definition changes. Deployment, production,
destructive work, or a material change in scope pauses only when the current
Gate B boundary does not already contain that exact action.

## What Codex returns after setup

If setup was started in the Codex IDE extension, local setup may finish, but
Fastlane stops before AWS Core verification and intake with this stable handoff:

```text
AWS CODEX FASTLANE — SUPPORTED CODEX SURFACE REQUIRED

Local setup: COMPLETE
Doctor: PASS
Current Codex surface: IDE_EXTENSION
AWS Core plugin management: UNAVAILABLE_ON_THIS_SURFACE
AWS Toolkit marketplace: DECLARED_AND_PINNED
aws-core plugin: NOT_VERIFIED
AWS credentials: NOT CHECKED
AWS access: NOT USED
AWS authorization: NONE
Next action: OPEN THIS REPOSITORY IN THE CHATGPT DESKTOP APP (CODEX) OR CODEX CLI
```

Do not approve an automatic `npx` or other client download in response to this
receipt. Open the same repository on one of the named supported surfaces, send
`init template` again, and continue with the walkthrough below.

On a supported surface, Fastlane next checks whether the `uvx` launcher is
available. If it is missing, it stops with this stable prerequisite receipt:

```text
AWS CODEX FASTLANE — AWS CORE RUNTIME REQUIRED

Local setup: COMPLETE
Doctor: PASS
Current Codex surface: <CHATGPT_DESKTOP_CODEX|CODEX_CLI>
AWS Toolkit marketplace: DECLARED_AND_PINNED
aws-core plugin: NOT_VERIFIED
AWS Core runtime: UVX_MISSING
Automatic runtime installation: NOT AUTHORIZED
AWS credentials: NOT CHECKED
AWS access: NOT USED
AWS authorization: NONE
Next action: INSTALL UV FROM THE OFFICIAL ASTRAL GUIDE, THEN START A NEW CODEX SESSION
```

This is a tool prerequisite, not AWS authentication and not a lifecycle gate.
Install `uv` only when you intend to use AWS Core on that supported surface,
then reopen the repository and send `init template` again.

For a normal first run on a supported surface, local setup finishes before
plugin verification and `uvx` is already available. The explanation may adapt,
but the walkthrough begins
with stable fields like these:

```text
AWS CODEX FASTLANE — AWS CORE SETUP REQUIRED

Local setup: COMPLETE
Doctor: PASS
Fastlane skills: READY
Project agents: READY
AWS Toolkit marketplace: DECLARED_AND_PINNED
aws-core plugin: MANAGEMENT_CHECK_REQUIRED
AWS MCP: NOT CONNECTED
AWS credentials: NOT CHECKED
AWS access: NOT USED
AWS authorization: NONE
Next action: OPEN `/plugins`
```

After AWS Core is installed and the new session confirms its hook runtime and
active hook inventory, Fastlane pauses with:

```text
AWS CODEX FASTLANE — AWS CORE HOOK REVIEW REQUIRED

Local setup: COMPLETE
Doctor: PASS
AWS Core: INSTALLED_AND_CURRENT
Expected hook: PRETOOLUSE_SECRET_SAFETY
Hook purpose: BLOCK_DIRECT_SECRETS_MANAGER_VALUE_FETCH
Hook runtime: PASS
Repository hook sources: NONE_DECLARED
Active hook conflict review: PASS
AWS Core hook trust: PENDING_OWNER_APPROVAL
Synthetic hook probes: PENDING
Automatic hook trust: NOT AUTHORIZED
AWS credentials: NOT CHECKED
AWS access: NOT USED
AWS authorization: NONE
Next action: OPEN CODEX SETTINGS > HOOKS (OR `/hooks` IN CLI) AND REVIEW THE CURRENT AWS CORE HOOK
```

The owner reviews and trusts the hook in Codex Settings or `/hooks`. Fastlane then verifies that
an unreachable synthetic secret-fetch shape is denied while a fixed print
command is allowed. Only after both probes pass does it generate this exact
confirmation:

```text
APPROVE AWS CORE HOOKS
Plugin: AWS Core
Version: 1.1.0
Commit: 36f16570de2015c0f0ce94ba9e391bd703c9ffb7
Hook purpose: BLOCK_DIRECT_SECRETS_MANAGER_VALUE_FETCH
Repository hook sources: NONE_DECLARED
Active hook conflicts: NONE
Trust: CURRENT_DEFINITION_HASH
Hook probes: PASS
```

For an adopted repository with project hooks, Fastlane replaces
`NONE_DECLARED` with the exact reviewed source list. It does not produce the
confirmation card while any source is unknown or conflicting.

After the explicit `@AWS Core` command and live handshake, Codex reports:

```text
AWS CODEX FASTLANE — AWS CORE VERIFIED

Approved marketplace pin: AWS Core 1.1.0
Plugin invocation: PASS
retrieve_skill: PASS
search_documentation: PASS
AWS credentials: NOT CHECKED
AWS access: NOT USED
Next action: CONTINUE BOOT-00
```

It then returns the normal state-derived launch receipt:

```text
AWS CODEX FASTLANE — READY

Classification: ACTIVE_GREENFIELD
Lifecycle: INTAKE_REQUIRED
Doctor: PASS
Next prompt: INTAKE-10
Git baseline: <commit>
Fastlane skills: READY
Project agents: READY
AWS Toolkit marketplace: DECLARED_AND_PINNED
aws-core plugin: AVAILABLE
AWS Core hooks: APPROVED_AND_VERIFIED
AWS Core hook conflict review: PASS
AWS MCP: CONNECTED_FOR_SKILLS_AND_DOCUMENTATION
AWS credentials: NOT CHECKED
AWS access: NOT USED
Gate A: BLOCKED
Gate B: BLOCKED
Evidence: NOT_READY
AWS authorization: NONE
```

When setup and AWS Core verification are ready, the response ends with a
prefilled `START GUIDED INTAKE` command. `RESUME` means the project is coherent
and has a later next prompt. `BLOCKED` means the doctor found a concrete
inconsistency and no construction or AWS action may continue until it is
reconciled.

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
- First-run AWS Core setup is a tool-availability pause, not a third human gate:
  `/plugins` manages the install and `@AWS Core` performs the live check.
- The Codex IDE extension can edit and test the repository, but it cannot browse,
  install, or invoke plugins. Use the ChatGPT desktop app or Codex CLI for the
  AWS Core handshake and Fastlane planning sessions that require it.
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
├── docs/
│   ├── adr/                  # Durable architecture decisions
│   └── project/              # Active Fastlane project workspace
│       ├── PRD.md            # Requirements, design, Gate A, and Gate B
│       ├── BUGFIX.md         # Active defect and regression contract
│       ├── TASKS.md          # Dependency graph and execution state
│       ├── VERIFY.md         # Observed evidence
│       └── RUNBOOK.md        # Deploy, rollback, recovery, and teardown
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
├── SECURITY.md               # Repository security policy
└── .github/                  # CI, issue forms, and PR template
```

`bootstrap.manifest.json` is the exhaustive release inventory. The tree above
shows the files most users need to understand. The five files in
`docs/project/` are the complete active project workspace; `docs/adr/` is only
for consequential architecture decisions that should remain durable.

| Project workspace file | What it owns |
|---|---|
| [`docs/project/PRD.md`](docs/project/PRD.md) | Requirements, technical design, Gate A, Gate B, and the approved construction boundary |
| [`docs/project/BUGFIX.md`](docs/project/BUGFIX.md) | One active defect or regression contract |
| [`docs/project/TASKS.md`](docs/project/TASKS.md) | Dependency-aware execution state and checkpoints |
| [`docs/project/VERIFY.md`](docs/project/VERIFY.md) | Observed local, release, and AWS evidence |
| [`docs/project/RUNBOOK.md`](docs/project/RUNBOOK.md) | Repeatable deployment, rollback, recovery, and teardown procedures |

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
python scripts/task_waves.py docs/project/TASKS.md --ready
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
python scripts/update_manifest.py --check
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
