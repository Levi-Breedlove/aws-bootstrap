# AWS Codex Fastlane Prompt Pack

**Pack version:** 1.0.0

This pack turns a rough idea or an existing repository into a reviewed,
executable AWS delivery plan, then lets Codex run the approved work for long
periods without turning delivery into a document factory.

The default is the **native fast lane**:

~~~text
BOOT-00
  -> INTAKE-10
  -> REQ-10
  -> INTAKE-20  [human Gate A]
  -> DESIGN-10
  -> DESIGN-20  [human Gate B]
  -> TASK-10
  -> BUILD-10 or BUILD-20
  -> RELEASE-10
  -> AWS-10/20/30 when deployment is in scope
~~~

There are exactly two routine lifecycle gates:

1. **Gate A** accepts a versioned requirements set.
2. **Gate B** accepts the complete PRD and a bounded construction envelope.

AWS mutations, production changes, destructive actions, merges, and other
external side effects may still need action-specific authorization when they
were not explicitly included in the approved construction envelope. Those are
safety authorizations, not extra lifecycle gates.

### Owner quick guide

A Quick MVP is one small, reversible development release. Use `high-risk` when
work involves production, sensitive or regulated data, payments, customer
isolation, shared infrastructure, irreversible data changes, or a potentially
large outage or cost increase. The profile changes scope and review depth; it
never reduces required testing or approval.

An AWS lane describes planned access; it does not authorize a change. AWS
changes require an approved record naming the account, Region, environment,
resources, operations, cost limit, rollback plan, and expiration.

## Start here

For a GitHub-template or extracted-release installation, send `init template`.
BOOT-00 expands that shorthand to **START AWS CODEX FASTLANE**, `Setup:
THIS_REPOSITORY`, and the safely detected local-Git choice. For brownfield
adoption, use
`Setup: ADOPT_EXISTING_REPOSITORY` and an exact absolute target. BOOT-00 safely
initializes or resumes the project, explains the workflow, and returns a
prefilled **START GUIDED INTAKE** command. Paste that command to begin.

For an initialized repository, use the prompt matching the current state. Do
not skip a missing Gate A or Gate B.

## Agent reference — exact authority and operating model

The repository is authoritative:

| Concern | Authoritative source |
|---|---|
| Scope, engineering rules, and safety | AGENTS.md and applicable nested AGENTS.md files |
| Requirements, analysis, design, gates, and construction envelope | PRD.md |
| Active defect contract | BUGFIX.md |
| Tasks, dependencies, waves, status, and execution log | TASKS.md |
| Evidence actually observed | VERIFY.md |
| Deployment, rollback, recovery, operations, and teardown | RUNBOOK.md |
| Machine-readable lifecycle and resume mirror | bootstrap.yaml (derived only; never authorization) |
| Durable review and collaboration | GitHub issues and pull requests |
| Runtime behavior | Code, tests, schemas, configuration, and infrastructure |

Notion may launch the prompts and present status, but it is not a second source
of truth. When sources conflict, stop and report the conflict. Do not silently
choose one or create another planning document. A `bootstrap.yaml` mismatch is
a stop condition; never use the mirror to infer approval or widen authority.

Every run declares two independent axes:

- **Project mode:** greenfield or brownfield.
- **Delivery profile:** quick-mvp, standard, or high-risk.

Quick-mvp is the default when the project can be delivered as one small,
reversible development release. Brownfield mode begins with repository
discovery and preserves existing conventions unless an approved requirement
justifies changing them.

Apply the selected delivery profile as an overlay, never as a substitute for
the common safety contract:

| Profile | Planning and construction overlay |
|---|---|
| `quick-mvp` | One thin outcome, one development environment and Region where feasible, the fewest independently verifiable tasks, one worker by default, and release as soon as the approved outcome is safe and observable. |
| `standard` | Complete operational design for the intended environments, explicit integration and migration coverage, and bounded parallelism only where task isolation is proven. |
| `high-risk` | Deeper review of identity, data access, customer separation, migration, recovery, rollback, shared-resource impact, audit needs, and failure handling; stronger evidence and smaller mutation batches; production or destructive actions remain separately authorized when not already exact. |

Select `high-risk` for production, sensitive or regulated data, payments,
customer isolation, shared infrastructure, irreversible data changes, or a
potentially large outage or cost increase, even if a faster profile was
requested. All profiles still use only Gate A and Gate B as routine lifecycle
gates.

## Common prompt contract

Apply this contract to every prompt below.

### Authorization

- Tool availability, credentials, a task state, a GitHub label, prior access,
  silence, or continued conversation never equals authorization.
- Codex cannot approve its own proposal or fill in an approver identity.
- Reject `Codex`, `agent`, `automation`, `system`, `AI`, and every other model
  or service identity as a gate approver, case-insensitively.
- Local read-only inspection is allowed unless the user restricts it.
- Local writes must be within the prompt's declared write set.
- GitHub reads and writes are separate modes. A write requires the current
  user request or the active construction authorization to name the repository
  and permit that operation.
- AWS documentation lookup, authenticated read-only discovery, and AWS mutation
  are separate modes. Each requires the mode declared by the prompt.
- Never expose credentials or secret values. Never weaken IAM, networking,
  encryption, validation, or logging to make a command pass.
- A material requirements change invalidates Gate A and dependent Gate B.
  A material design or construction-envelope change invalidates Gate B.
  Mark each affected gate `STALE`, increment the affected revision, and return
  to the corresponding gate.

### Exactly accepted gate receipts

Gate A is accepted only when the human sends a receipt equal to this complete
block after trimming surrounding whitespace, with IDs that exactly match the
current proposed requirements card:

~~~text
APPROVE REQUIREMENTS GATE A
Requirements revision: REQ-0001
Accepted assumptions: ASM-... or NONE
Approver: <name/handle>
~~~

Gate B is accepted only when the human sends a receipt equal to this complete
block after trimming surrounding whitespace, with IDs that exactly match the
current proposed design card:

~~~text
APPROVE PRD AND CONSTRUCTION GATE B
Requirements revision: REQ-0001
Design revision: DES-0001
Construction authorization: AUTH-0001
Construction envelope SHA-256: sha256:<64-lowercase-hex>
Use the proposed construction envelope above.
Approver: <name/handle>
~~~

The values shown are examples. The generated card must use the current proposed
IDs, and the human must replace the approver placeholder. Do not accept a
paraphrase, mismatched revision, placeholder approver, partial receipt, silence,
continued conversation, task state, or tool access. Reject extra non-blank
lines, comments, duplicate fields, missing fields, reordered fields, and code
fences around the receipt.

Only the owner can approve either gate. A valid Gate A receipt sets the current
requirements gate to `APPROVED_FOR_DESIGN`. A valid Gate B receipt sets the
current PRD and construction gate to `APPROVED_FOR_CONSTRUCTION`. Codex may
record those receipts but may never create or self-accept them.

When recording a valid receipt, also record its observed ISO 8601 time and the
exact source locator available in the current interaction (for example, a
message, issue, or meeting-record link). Those provenance fields are metadata,
not extra receipt lines. Do not invent a source link or approver identity; if
the source cannot be durably identified, stop and ask the owner how it should
be cited.

For Gate B, compute the digest from the canonical complete construction-envelope
table defined in PRD.md: header, separator, and every boundary row in stored
order; trailing whitespace removed per line; LF separators and one final LF;
UTF-8 bytes; SHA-256 lowercase hex. The agent review, owner record, proposed
receipt, and returned receipt must all contain the same digest. Any envelope
change increments AUTH, makes Gate B stale, and requires a new digest and owner
receipt.

### Exact conditional AWS action receipts

These receipts authorize one bounded external action; they are not additional
routine lifecycle gates. A deployment receipt is required for an
`explicit-gate` mutation. A fast-dev mutation instead must fit the current Gate
B envelope exactly; a mismatch makes Gate B stale and cannot be repaired by an
action receipt. Teardown always requires its own receipt. After trimming
surrounding whitespace, accept only the complete block with actual values,
exact current IDs, no placeholders, and no extra, missing, duplicate,
reordered, commented, or fenced lines.

~~~text
AUTHORIZE AWS DEPLOYMENT
AWS authorization: AWS-AUTH-0001
Construction authorization: AUTH-0001
Profile or role: <allowlisted profile or role>
Account: <12-digit account ID or approved alias>
Region: <AWS Region>
Environment: <non-production or production>
Artifact digest: <immutable digest>
Stack, application, and resources: <exact boundary>
Allowed operations: <exact create/update/delete operations>
Cost ceiling: <currency and amount>
Rollback boundary: <exact allowed rollback or NONE>
Valid until: <ISO 8601 time or exact one-operation condition>
Approver: <name/handle>
~~~

~~~text
AUTHORIZE AWS TEARDOWN
Teardown authorization: TEARDOWN-AUTH-0001
Construction authorization: AUTH-0001
Profile or role: <allowlisted profile or role>
Account: <12-digit account ID or approved alias>
Region: <AWS Region>
Environment: <environment>
Stack, application, and resources to remove: <exact boundary>
Resources and data to retain: <exact list or NONE>
Allowed deletion operations: <exact operations>
Shared dependencies: <exact list or NONE>
Cost effect: <expected continuing and removed billing dimensions>
Post-teardown verification: <read-only checks>
Valid until: <ISO 8601 time or exact one-operation condition>
Approver: <name/handle>
~~~

Record a supplied receipt verbatim in the action journal or durable evidence
location named by the active envelope, plus its observed time and source. It
activates only the exact AWS mutation contemplated by the current
`explicit-gate` envelope; it never widens construction scope, local or GitHub
writes, resource boundaries, or platform authority. A deployment receipt never
authorizes teardown.

### Construction envelope

Gate B approves only the versioned envelope recorded in PRD.md. It must state:

- project mode and delivery profile;
- repository, base branch, branch strategy, and allowed local write boundary;
- task scope, non-goals, and maximum autonomous run boundary;
- allowed GitHub write operations, or NONE;
- AWS mode: NONE, DOCS_ONLY, READ_ONLY, or MUTATION;
- stop conditions, validation commands, and evidence requirements;
- cost, security, data, environment, and destructive-action limits;
- whether merge and branch cleanup are allowed;
- authorization ID and expiry or completion condition.

It also requires a resolvable local Git baseline, explicit protected dirty
paths, exact external-state targets, literal allowed command prefixes, and the
canonical complete-envelope SHA-256. Use PRD.md's exact row grammars; do not
replace them with prose or synonyms.

If a fast development deployment is proposed, the envelope must also include
the complete AWS mutation boundary listed below. Otherwise Gate B does not
authorize AWS mutation.

### Canonical AWS mode mapping

The project lane, one prompt's access mode, and Gate B's AWS boundary are
different fields. Use this mapping and no synonyms:

| Project AWS lane | Prompt AWS mode | Gate B AWS boundary |
|---|---|---|
| `documentation-only` | `DOCS_ONLY` | `DOCS_ONLY` |
| `read-only` | `READ_ONLY` | `READ_ONLY` |
| `fast-dev` | `MUTATION` only after AWS-10 preflight | `MUTATE_LISTED_RESOURCES` |
| `explicit-gate` | `DOCS_ONLY` or `READ_ONLY` | `DOCS_ONLY` or `READ_ONLY`; AWS-20 also requires a separate action-specific mutation receipt |

`NONE` means no AWS access in the current prompt. An IaC synth or local plan
does not itself require authenticated AWS mutation.

### AWS grounding and mutation boundary

**Official grounding reviewed July 18, 2026.** Fastlane uses the official
aws-core plugin from Agent Toolkit for AWS:

- [Agent Toolkit for AWS](https://aws.amazon.com/products/developer-tools/agent-toolkit-for-aws/)
- [Agent Toolkit plugins](https://docs.aws.amazon.com/agent-toolkit/latest/userguide/plugins.html)
- [Agent Toolkit AWS CLI setup](https://docs.aws.amazon.com/agent-toolkit/latest/userguide/aws-cli.html)
- [AWS MCP Server tools](https://docs.aws.amazon.com/agent-toolkit/latest/userguide/understanding-mcp-server-tools.html)
- [Multi-profile support](https://docs.aws.amazon.com/agent-toolkit/latest/userguide/multi-account-access.html)

The repo marketplace pins `aws-core` version `1.1.0` at Agent Toolkit commit
`36f16570de2015c0f0ce94ba9e391bd703c9ffb7`. Use AWS Core skills, current AWS
primary documentation, regional-availability checks, and its AWS API tools
before relying on model memory. The plugin is a knowledge and tool layer; it
does not replace PRD.md, the human gates, IAM, or an AWS authorization record.
If AWS Core is unavailable in the current session, BOOT-00 dependency recovery
is required before Fastlane claims setup readiness or makes a gate-ready AWS
recommendation. AWS operations remain blocked.

Before any AWS mutation, the active authorization must state all of:

~~~text
profile or role
account ID or approved alias
Region
environment
stack, application, and resource boundary
approved operation
approved resource summary
artifact authorization and provenance
billable impact or budget ceiling
prohibited operations
rollback or teardown path
authorization ID, approver, and validity window
~~~

Missing, stale, or conflicting values make the mutation BLOCKED. Read-only
discovery must precede mutation. Prefer a read-only profile by default and the
least-privileged write profile only for an authorized operation.

Fastlane ships `.agents/plugins/marketplace.json` with an
`INSTALLED_BY_DEFAULT` request for that exact official revision. Repository
trust and managed platform policy still apply. A newly installed plugin is not
available to an already-running conversation: confirm AWS Core in `/plugins`
if prompted, start a new session in the same repository, and send `init
template` again. Never infer plugin availability from files; verify a surfaced
AWS Core skill or AWS MCP tool in the current session.

BOOT-00 does not configure AWS credentials. When an explicitly invoked AWS
operating prompt later needs account access, follow the current Agent Toolkit
flow (`aws configure agent-toolkit`) and allowlist only the intended profiles.
For multiple profiles, the first is the default:

~~~bash
export AWS_MCP_PROXY_PROFILES="mvp-readonly mvp-deploy"
~~~

### Evidence states

Use evidence states that do not overclaim:

~~~text
NOT_STARTED -> IMPLEMENTED -> LOCAL_PASS -> PENDING_AWS -> VERIFIED
                    \-> FAILED | BLOCKED
Any formerly passing state -> STALE when its revision, artifact, environment,
or target identity no longer matches.
~~~

Local tests cannot produce deployed AWS evidence. A task can be DONE when its
approved task-level criteria pass while AWS-only evidence remains PENDING_AWS.
Before any DONE mutation, record each cited local `EV-nnnn` exactly once in
VERIFY.md under `Task completion evidence`, with the exact task, observed
command/result, actor, timezone-qualified time, tested commit/worktree/artifact,
durable source, and `LOCAL_PASS` or `VERIFIED`. Placeholder, duplicate,
wrong-task, fenced, URL-only, and non-passing rows grant no completion evidence.

### Standard work receipt

Every prompt returns this exact field set, populated with concise facts:

~~~text
WORK RECEIPT
Prompt: <canonical prompt ID>
Status: COMPLETE | BLOCKED | NEEDS_INPUT | WAITING_FOR_GATE_A | WAITING_FOR_GATE_B | READY
Revisions: <requirements/design/authorization IDs or NONE>
Authorization used: <ID and scope or NONE>
Files changed: <paths or NONE>
GitHub actions: <observed actions or NONE>
AWS actions: <DOCS_ONLY, READ_ONLY, MUTATION with observed actions, or NONE>
Validation: <commands and results or NOT_RUN>
Open risks: <concise list or NONE>
Next: <one canonical prompt ID, exact human receipt, or STOP>
~~~

Do not claim an action, test, merge, deployment, or observation without evidence.

## Prompt index

| ID | Purpose | Normal next |
|---|---|---|
| BOOT-00 | Initialize and explain the fast lane | INTAKE-10 |
| INTAKE-10 | Guided plain-language discovery | REQ-10 or another INTAKE-10 round |
| REQ-10 | Analyze and version requirements | INTAKE-20 |
| INTAKE-20 | Present Gate A | DESIGN-10 |
| DESIGN-10 | Complete the PRD and construction envelope | DESIGN-20 |
| DESIGN-20 | Present Gate B | TASK-10 |
| BUG-10 | Define an evidence-based defect contract | TASK-10 |
| TASK-10 | Produce executable tasks and safe waves | BUILD-10 or BUILD-20 |
| BUILD-10 | Execute one approved task | BUILD-10, RELEASE-10, or STOP |
| BUILD-20 | Run approved tasks autonomously | RELEASE-10 or STOP |
| SYNC-10 | Reconcile authorized GitHub tracking | BUILD-20, RELEASE-10, or STOP |
| RELEASE-10 | Review and, if authorized, finalize the release | AWS-10, AWS-40, or STOP |
| AWS-10 | Read-only deployment preflight | AWS-20 or STOP |
| AWS-20 | Execute an authorized deployment | AWS-30 |
| AWS-30 | Reconcile deployed evidence | RELEASE-10 |
| AWS-40 | Read-only residual and teardown review | AWS-50 or STOP |
| AWS-50 | Execute an authorized teardown | STOP |
| LEARN-10 | Add concise teaching to another prompt | Same as wrapped prompt |

---

## BOOT-00 — Bootstrap Launchpad

**Preconditions:** The user sent the plain-language shorthand `init template`,
`initialize template`, or `start Fastlane`; or sent `START AWS CODEX FASTLANE`
with `Setup: THIS_REPOSITORY` or `Setup: ADOPT_EXISTING_REPOSITORY` plus an exact
local-Git setup choice. The short form means `THIS_REPOSITORY`, uses existing
Git when present, and uses safe local baseline behavior when Git is absent.
The legacy `START AWS CODEX BOOTSTRAP` external-target form remains valid for
scripted copies. The template files and manifest are available.

**Authoritative inputs:** Resolved repository and optional adoption-target paths;
bootstrap manifest and source hashes; bootstrap.py dry-run; bootstrap.yaml
mirror; bootstrap doctor JSON; Git state and origin; AGENTS.md files; existing
PRD.md, BUGFIX.md, TASKS.md, VERIFY.md, and RUNBOOK.md; Python, prompt-pack,
placeholder and skill checks; `bootstrap_dependencies.py` JSON; the pinned
Agent Toolkit marketplace; project-agent files; and current-session AWS Core
capability observation.

**Permitted writes:** For `THIS_REPOSITORY`, only allowlisted placeholder
rendering by `bootstrap.py --in-place-template-instance` after the tree matches
the versioned manifest, every source hash matches, no symlink or dirty user file
exists, and the repository is not the official maintainer source. For an
external new target, only manifest-allowlisted files inside the explicit
collision-free target. For brownfield collisions, only a user-confirmed,
complete, hash-bound adoption map may authorize exact `ADOPT_TEMPLATE` paths;
`PRESERVE` does not change the target and `STAGE_FOR_MERGE` writes only to its
separate explicit staging target. Blanket overwrite is prohibited. ACTIVE
targets are inspected and resumed without regeneration. When and only when
local-Git setup is `INIT_AND_BASELINE_COMMIT`, an absent local repository may
be initialized and the reviewed bootstrap state committed as its baseline
using existing Git author identity. No remote may be added.

**GitHub mode:** NONE. Local Git initialization and one baseline commit are not
GitHub actions and are allowed only by the setup choice above. No remote,
fetch, push, hosted repository, issue, pull request, or other GitHub write.

**AWS mode:** NONE. BOOT-00 observes whether AWS Core is surfaced but does not
call AWS documentation or account tools.

**Required authorization:** The exact start command authorizes only safe local
initialization or inspection for its named or safely derived setup method,
repository-local dependency validation, and the marketplace's exact pinned
`INSTALLED_BY_DEFAULT` AWS Core request. It does not authorize requirements,
tasks, implementation, remotes, GitHub writes, AWS credentials, or AWS access.

**Stop conditions:** Missing or ambiguous setup; unsafe repository root; ordinary
external source/target equality or containment; a modified or dirty in-place
template; official maintainer-source detection; source-hash mismatch; symlink
escape; dry-run failure; collision or overwrite risk; unresolved
source-of-truth conflict; partial write; expected-file, skill, placeholder, or
doctor failure; partial core-contract adoption; unconfirmed adoption plan;
adoption-plan digest or target-root drift; dependency-check failure; altered
AWS Toolkit pin; or AWS Core absent from the current session after installation.

**Receipt:** Before initialization, a stable toolkit setup receipt when AWS Core
is not surfaced in the current session. Otherwise, a stable doctor-derived
READY, RESUME, or BLOCKED receipt containing classification, lifecycle, doctor
result, next prompt, Git baseline, Fastlane skills, project agents, AWS Toolkit
marketplace, AWS Core, AWS MCP documentation, AWS credential, AWS access, Gate
A, Gate B, evidence, and AWS authorization state, followed by a standard work
receipt.

**Next:** State-derived: INTAKE-10, REQ-10, INTAKE-20, DESIGN-10, DESIGN-20,
TASK-10, BUILD-10, BUILD-20, RELEASE-10, or STOP.

~~~text
[BOOT-00]
Process this initiation command:

START AWS CODEX FASTLANE
Setup: <THIS_REPOSITORY|ADOPT_EXISTING_REPOSITORY>
Target path: <required only for ADOPT_EXISTING_REPOSITORY>
Local Git setup: <INIT_AND_BASELINE_COMMIT|USE_EXISTING>

The messages `init template`, `initialize template`, and `start Fastlane` are
canonical shorthand for `Setup: THIS_REPOSITORY`. Select `USE_EXISTING` when a
local Git repository exists. Otherwise select `INIT_AND_BASELINE_COMMIT` and
stop without a commit if Git author identity or another baseline precondition
is missing. Shorthand never selects brownfield adoption or a remote action.

Act as the AWS Codex Fastlane installer and launchpad. For THIS_REPOSITORY, use
the repository containing this prompt as both the template instance and project
root. For ADOPT_EXISTING_REPOSITORY, resolve the exact absolute target without
an unresolved variable, glob, home shortcut, or command substitution. Refuse a
filesystem root, home directory, Git metadata path, or symlink escape.

Begin with this welcome, adapting only the project name when it is already
known:

Welcome to AWS Codex Fastlane. This template turns a rough AWS idea into
owner-approved requirements and a technical PRD, then lets Codex build inside
the exact boundary approved at Gate B. Setup checks tools and repository state
only; it does not access or change AWS.

Before asking project questions or writing files, run:

python scripts/bootstrap_dependencies.py --root <repository root> --json

Require `status`, `fastlane_skills.status`, `project_agents.status`, and
`aws_agent_toolkit.marketplace` to equal `READY`. Then inspect only the skills
and tools actually surfaced to this session. AWS Core is `AVAILABLE` only when
the current session exposes an AWS Core-contributed skill or AWS MCP tool. Do
not treat a marketplace file, cached directory, prior conversation, command
output, or model memory as proof that plugin capabilities loaded.

If the static dependency check passes but AWS Core is not surfaced, do not ask
project questions or render placeholders. Print exactly this stable header,
then explain how to confirm AWS Core in `/plugins`, restart Codex in the same
repository, and send `init template` again:

AWS CODEX FASTLANE — TOOLKIT SETUP REQUIRED

Fastlane skills: READY
Project agents: READY
AWS Toolkit marketplace: READY
aws-core plugin: RESTART REQUIRED
AWS MCP documentation: NOT AVAILABLE IN THIS SESSION
AWS credentials: NOT CHECKED
AWS access: NOT USED
AWS authorization: NONE
Next action: START A NEW CODEX SESSION, THEN SEND `init template`

If the dependency checker is BLOCKED, use the same header with the observed
BLOCKED values and stop. Never claim that the plugin installed, activate an AWS
profile, or continue to intake without current-session capability evidence.

Ask no more than these three setup questions, and ask only for values the user
did not already supply:
1. What should the project be called?
2. Which AWS Region should planning prefer?
3. What monthly development budget should the design stay within?

Recommend `us-west-2` and `$20/month` when the owner is unsure. These are
planning inputs, not AWS authorization.

Inspect before writing and classify exactly one:
- TEMPLATE_SOURCE: this is the reusable source, not an initialized target;
- UNCONFIGURED_TEMPLATE: an untouched GitHub-template or release-ZIP instance;
- NEW_TARGET: explicit absent or empty target safe to initialize;
- ACTIVE_GREENFIELD: initialized target without an existing production system;
- ACTIVE_BROWNFIELD: existing project or system being overlaid or resumed;
- BLOCKED: target safety, collision, integrity, or authority is unresolved.

For UNCONFIGURED_TEMPLATE, first run the in-place command with `--dry-run`, then
run it without `--dry-run` only when the manifest, source hashes, Git protection,
symlink checks, and collision checks pass:

python bootstrap.py --target <repository root> --project-name <name> --region <region> --budget <budget> --in-place-template-instance --dry-run
python bootstrap.py --target <repository root> --project-name <name> --region <region> --budget <budget> --in-place-template-instance

Only the allowlisted placeholders may change. The full update is atomic and
must pass the doctor; a failure rolls back every changed file.

For NEW_TARGET, run bootstrap.py dry-run and collision checks first. If clean,
initialize only the manifest-allowlisted files at the explicit target. Never use `--force`.
Ordinary external source/target equality or containment remains
prohibited.

For an uninitialized brownfield target, produce an overlay preview with
rendered-template and target SHA-256 digests. You may propose a decision map,
but START AWS CODEX FASTLANE does not
authorize you to choose `ADOPT_TEMPLATE` for the owner. Make no target change
until every collision has exactly one hash-bound decision: `PRESERVE`,
`ADOPT_TEMPLATE`, or `STAGE_FOR_MERGE` at a separate, explicit, non-overlapping
staging target. Before applying any `ADOPT_TEMPLATE` decision, require the user
to return the exact generated confirmation card containing both canonical
roots, complete ordered decision payload, human owner, time, source, and
`plan_sha256`. Compute `plan_sha256` from canonical JSON containing
`schema_version`, canonical `source_root`, canonical `target_root`, and the
ordered full decisions; each decision contains path, action, expected target
SHA-256, and expected rendered-template SHA-256. It never hashes decisions
alone. Bind application to that receipt and reject a paraphrase, omitted path
or digest, different order, root, schema, or changed hash. Generate the card in
this shape, with one canonical decision line for every collision and no
placeholders:

CONFIRM BOOTSTRAP ADOPTION PLAN
schema_version: 1
source_root: <canonical absolute template source>
target_root: <canonical absolute target>
authorized_by: <human owner>
authorized_at: <RFC 3339 timestamp with timezone>
authorization_source: OWNER_CONFIRMATION
plan_sha256: <64 lowercase hex characters>
Decisions:
<relative path> | <action> | <expected target SHA-256> | <expected rendered-template SHA-256>

Compute the plan digest from the UTF-8 canonical JSON encoding of the complete
plan object—schema version, roots, and ordered decisions—using `sort_keys=true`
and compact separators. Authorization metadata is stored alongside the hash but
is not part of its canonical input. The
observed time and exact owner-message source must agree with the authorization
object. Never invent the authorized identity, time, or source.

Abort the whole preflight on an omitted/unknown/duplicate path, digest
drift, unsafe path, symlink, or root mismatch. Preserving or staging a core
control file is PARTIAL_ADOPTION until doctor validation succeeds. This is a
one-time collision authorization, not Gate A or Gate B. Never silently merge or
overwrite. For
ACTIVE_GREENFIELD or ACTIVE_BROWNFIELD with a coherent bootstrap, resume it
without regeneration.

Apply the local-Git choice exactly. `INIT_AND_BASELINE_COMMIT` may run local
`git init` only when `.git` is absent, validate the configured bootstrap, and
commit that exact reviewed state as the baseline using already configured
author identity. `USE_EXISTING` requires an existing local repository and
records its current commit plus any protected dirty paths. Never add a remote,
create a hosted repository, fetch, or push.

After initialization or resume, verify:
- expected bootstrap files and applicable nested AGENTS.md files;
- no unresolved project placeholders outside documented examples;
- prompt-pack title/version and all canonical prompt IDs;
- Git and Python availability and whether the target is already a Git repo;
- repo-scoped Fastlane skill files and distinct trigger policies;
- the three read-only project-agent files and their no-model/no-MCP override
  contract;
- the exact pinned Agent Toolkit marketplace through
  `bootstrap_dependencies.py`;
- AWS Core and AWS MCP documentation surfaced in this current session, without
  authenticated AWS access;
- source-of-truth file coherence.

Run `python scripts/bootstrap_doctor.py --root <target>` after initialization and on
resume. The doctor is read-only. Unsafe, contradictory, or unreconciled
interrupted state routes to STOP. A coherent `STALE` gate routes to its
requirements or design repair prompt below while construction remains stopped.

Determine lifecycle state from the current PRD revisions and derived gates,
TASKS.md, and release evidence. Route to exactly one next prompt:
- no material requirements: INTAKE-10;
- intake exists but requirements need analysis: REQ-10;
- Gate A is STALE: INTAKE-10 when owner facts are missing, otherwise REQ-10;
- Gate A awaits a current owner receipt: INTAKE-20;
- Gate A approved and design incomplete: DESIGN-10;
- Gate A is current and Gate B is STALE: DESIGN-10;
- Gate B awaits a current owner receipt: DESIGN-20;
- Gate B approved and Task-plan state is UNINITIALIZED or STALE: TASK-10;
- one named task requested or only one task is READY: BUILD-10;
- multiple eligible tasks and autonomous execution is authorized: BUILD-20;
- authorized tasks are terminal: RELEASE-10;
- conflicting state, an unsafe interrupted run, or no authorized action: STOP.

Do not write requirements, design, tasks, application code, or infrastructure.
Outside the exact local-Git setup choice, do not initialize or change Git.
Never create GitHub objects or access/mutate AWS.

Print this stable machine-derived header before any natural-language
explanation. Use READY, RESUME, or BLOCKED from doctor state; do not infer or
rewrite these values:

AWS CODEX FASTLANE — <READY|RESUME|BLOCKED>

Classification: <doctor classification>
Lifecycle: <doctor lifecycle_state>
Doctor: <PASS|FAIL>
Next prompt: <doctor next_prompt>
Git baseline: <doctor git_baseline>
Fastlane skills: <bootstrap_dependencies fastlane_skills.status>
Project agents: <bootstrap_dependencies project_agents.status>
AWS Toolkit marketplace: <bootstrap_dependencies aws_agent_toolkit.marketplace>
aws-core plugin: AVAILABLE
AWS MCP documentation: READY
AWS credentials: NOT CHECKED
AWS access: <doctor aws_access with underscores rendered as spaces>
Gate A: <derived Gate A state>
Gate B: <derived Gate B state>
Evidence: <derived evidence state>
AWS authorization: <NONE|exact current authorization ID>

Then print target, files changed or NONE, collisions or NONE, and checks.
Explain the two routine human gates, that autonomous work begins only inside
Gate B's boundary, and the next three steps in plain language. Return the
standard work receipt. Only when the state-derived next prompt is INTAKE-10,
end with this prefilled command exactly:

START GUIDED INTAKE
Project path: <resolved target path>
Project mode: <greenfield|brownfield|I'm not sure—recommend one>
Delivery profile: <quick-mvp|standard|high-risk|I'm not sure—recommend one>
Idea or requested change: <one plain-language sentence>
~~~

## INTAKE-10 — Guided Intake

**Preconditions:** START GUIDED INTAKE command or an existing intake round.

**Authoritative inputs:** Applicable AGENTS.md; existing source-of-truth files; for brownfield,
repository code, tests, IaC, configuration, and recent relevant history.

**Permitted writes:** PRD.md Document status mode/profile/risk/lane fields,
workload profile, intake provenance, brownfield contract, and Part I only after
reflecting proposed facts to the user. A material edit to previously approved
requirements must atomically mark both derived gates STALE. No design or task
writes. Update the matching non-authoritative `bootstrap.yaml` project and
lifecycle mirror and the identity/state fields in TASKS.md's Active execution
snapshot in the same coordinator checkpoint; do not generate or rewrite task
blocks. If a CURRENT plan has IN_PROGRESS work, stop and reconcile/archive that
work before applying the requirements change and marking the plan STALE.

**GitHub mode:** NONE by default; READ_ONLY only when needed to understand an
identified brownfield repository.

**AWS mode:** DOCS_ONLY only when a current AWS fact is needed; no authenticated
AWS access.

**Required authorization:** Intake and its declared local write only.

**Stop conditions:** More than three unanswered questions; secrets appear in
input; repository facts contradict the request; a decision would materially
change scope without human input.

**Receipt:** Standard work receipt.

**Next:** Another INTAKE-10 round or REQ-10.

~~~text
[INTAKE-10]
Guide the user from a rough idea to requirements in short, plain-language
rounds. Read the repository first in brownfield mode and distinguish observed
facts from recommendations.

In each response:
1. summarize what you understand in at most five bullets;
2. ask no more than three questions;
3. ask only questions needed to avoid a material scope, user, outcome, data,
   security, deployment, or success-measure mistake;
4. give two or three understandable choices when helpful;
5. always allow the answer “I'm not sure—recommend one”;
6. recommend a default and explain its practical effect in one sentence.

Capture:
- project mode: greenfield or brownfield;
- delivery profile: quick-mvp, standard, or high-risk;
- users, problem, observable outcome, and success measures;
- in-scope behavior and explicit non-goals;
- data sensitivity, identity boundary, integrations, and failure impact;
- environment, Region constraints, budget sensitivity, and release expectation;
- brownfield compatibility, migration, and operational constraints.

For quick-mvp, propose a thin first release: one primary actor, one observable
outcome, one core entity or state transition, one entry point, one Region, one
development environment, measurable requirements, explicit non-goals, and one
rollback/teardown path.

Do not ask the user to choose an AWS service unless that choice is itself a
business constraint. Do not design, generate tasks, or seek approval yet.
When the material intake gaps are closed, state that intake is ready for REQ-10.
Return the standard work receipt.
~~~

## REQ-10 — Requirements Analysis

**Preconditions:** Intake has enough information to define a bounded outcome.

**Authoritative inputs:** AGENTS.md; PRD.md; intake facts; brownfield code/tests/IaC/config;
current AWS Core capability and primary documentation needed to validate
external constraints; read-only requirements-review findings.

**Permitted writes:** PRD.md requirements-revision-controlled content plus the
Document status requirements revision and derived Gate A/Gate B states;
TASKS.md's Active execution snapshot identity, Gate B, run-stop, and next-action
fields only. Update the summary, detailed analysis, task snapshot, and matching
`bootstrap.yaml` lifecycle mirror as one coordinator checkpoint. Do not
generate a replacement graph. When invalidating an existing plan, reconcile
IN_PROGRESS tasks to DONE with evidence or BLOCKED with the revision reason,
commit/archive the stopped ledger, then mark its Task-plan state STALE.

**GitHub mode:** READ_ONLY only if authorized and needed for brownfield facts.

**AWS mode:** DOCS_ONLY; authenticated AWS access is not required.

**Required authorization:** Requirements analysis and declared PRD.md writes only.

**Stop conditions:** Unresolved contradiction; missing critical security/data
boundary; unverifiable outcome; requested requirement is infeasible or unsafe;
AWS Core unavailable; or a material AWS feasibility fact remains unverified.

**Receipt:** Standard work receipt with proposed REQ revision.

**Next:** INTAKE-10 when blocked; otherwise INTAKE-20.

~~~text
[REQ-10]
Analyze the entire intake as one requirement set before technical design.

First run `python scripts/bootstrap_dependencies.py --root . --json` and
confirm AWS Core is surfaced in the current session. Ask the read-only
`fastlane-requirements-reviewer` to challenge the complete requirement set. If
AWS feasibility, Region, identity, data protection, recovery, or cost affects
readiness, ask the read-only `fastlane-aws-advisor` to verify those facts with
AWS Core and current primary AWS documentation. The coordinator evaluates the
findings and remains the only writer. Neither advisor can approve Gate A.

Create or increment a requirements revision such as REQ-0001. Give every
requirement, non-goal, assumption, and material open question a stable ID.
Record in PRD.md:
- problem, actors, outcome, scope, and non-goals;
- measurable functional and non-functional requirements;
- security, privacy, data, failure, concurrency, recovery, observability,
  performance, cost, accessibility, and regional constraints where applicable;
- brownfield compatibility and migration constraints;
- acceptance criteria and objective verification method for each requirement;
- assumptions explicitly proposed for acceptance;
- contradictions, ambiguities, undefined terms, missing cases, and feasibility;
- relevant AWS Well-Architected impacts.

Fill the Gate A readiness card with these exact fields: Outcome; Owner and
users; Scope and non-goals; Measurable requirement/acceptance IDs; Data
boundary; Identity/security boundary; Environment/Region; Failure/recovery;
Cost ceiling; Intake provenance. Every value must be explicit and trace to the
current revision. Use `NOT_APPLICABLE — <reason>` only when genuinely
inapplicable; a blank, TODO, TBD, UNKNOWN, or bare NONE keeps readiness BLOCKED.

For brownfield mode, do not mark ready until repository/baseline,
deployments, architecture/ownership, interfaces/consumers, data/migration,
security controls, baseline commands/evidence, and protected components are
observed and explicit. Only drift, dirty changes, known debt/defects, and
overlay collisions may use the exact nullable forms defined in PRD.md.

Set readiness to exactly one:
- BLOCKED;
- READY_WITH_PROPOSED_ASSUMPTIONS;
- READY_FOR_OWNER_APPROVAL.

Do not silently resolve contradictions, choose architecture, approve
assumptions, or mark Gate A accepted. If blocked, set Gate A to `BLOCKED` and
ask at most three plain questions using the INTAKE-10 style. When either ready
recommendation is recorded, atomically set both the Document status and detailed
Gate A owner state to `PENDING_OWNER_APPROVAL`, keep Gate B `BLOCKED` for a new
project or `STALE` after invalidating an earlier design. Mirror both gate states
in bootstrap.yaml and copy the current REQ plus non-runnable Gate B state into
TASKS.md's Active execution snapshot. Reset the Gate A owner decision to
`PENDING`, clear any prior approver/provenance/authorization fields, and render
the current proposed receipt with an approver placeholder; never carry an old
receipt into a new revision. Existing tasks become non-runnable and an active
run becomes `BLOCKED`; never silently retarget them to the new revision. Set the
reconciled plan STALE, then prepare a concise Gate A decision brief for
INTAKE-20. Return the standard work receipt.
~~~

## INTAKE-20 — Requirements Gate A

**Preconditions:** REQ-10 produced a current requirements revision that is not
BLOCKED.

**Authoritative inputs:** Current PRD.md requirements, analysis, assumptions, and revision.

**Permitted writes:** PRD.md Gate A owner record and the matching Document
status Gate A state only after receiving an exact valid receipt. Update both
and the matching `bootstrap.yaml` lifecycle mirror as one coordinator
checkpoint. TASKS.md remains non-runnable; update only its identity/state
snapshot if needed to repair a mirror mismatch, never task blocks.

**GitHub mode:** NONE.

**AWS mode:** DOCS_ONLY through the current AWS Core session; no AWS account
access.

**Required authorization:** Presentation only until the human sends the exact receipt.

**Stop conditions:** BLOCKED readiness; stale or mismatched ID; placeholder
approver; altered or partial receipt; requirements change during review; AWS
Core unavailable; or a material AWS feasibility fact is stale or unverified.

**Receipt:** Standard work receipt with WAITING_FOR_GATE_A, followed by the
copyable Gate A receipt as the final block.

**Next:** DESIGN-10 only after exact acceptance; otherwise REQ-10 or INTAKE-10.

~~~text
[INTAKE-20]
Present the current requirements for human Gate A.

Show a concise decision brief:
- requirements revision and delivery profile;
- all ten fields from the current Gate A readiness card;
- user outcome and measurable success;
- in scope and non-goals;
- accepted-fact candidates versus proposed assumptions;
- security, data, cost, deployment, and brownfield constraints;
- unresolved risks that do not block the gate;
- material AWS feasibility facts verified through AWS Core, their sources, and
  any advisor finding the coordinator rejected with its reason;
- what Gate A does and does not approve.

Do not approve the gate yourself. Render a copyable receipt using the exact
field names below and the actual current IDs. List every assumption ID or NONE.
The human must replace the approver placeholder.

Accept Gate A only if the human response equals the complete block below after
trimming surrounding whitespace:

APPROVE REQUIREMENTS GATE A
Requirements revision: REQ-0001
Accepted assumptions: ASM-... or NONE
Approver: <name/handle>

The revision and assumptions must exactly match the proposed card. Reject extra
or duplicate fields, comments, reordered lines, partial blocks, and code fences.
Silence, continued conversation, task state, or tool access never counts. After
a valid receipt, preserve the complete normalized receipt inside the uniquely
marked Gate A receipt block, then atomically update the detailed owner record,
Document status, and lifecycle mirror to APPROVED_FOR_DESIGN. Record the
observed ISO 8601 authorization time and exact message/issue/meeting-record
source as structured provenance without adding either value to the receipt.
Do not invent a source. Return a standard work receipt whose Next is DESIGN-10.
Before acceptance, return WAITING_FOR_GATE_A and put the exact proposed
approval receipt last.
~~~

## DESIGN-10 — Technical PRD and Construction Envelope

**Preconditions:** PRD.md contains a valid Gate A receipt for the current
requirements revision.

**Authoritative inputs:** All applicable AGENTS.md; complete PRD.md; brownfield code, tests,
IaC, config, schemas, and relevant history; current AWS Core capability,
primary AWS documentation, and read-only AWS advisor findings.

**Permitted writes:** PRD.md Parts III and IV, proposed construction envelope,
and matching Document status DES/AUTH/design/Gate B fields; narrowly scoped ADR
only for a consequential, hard-to-reverse decision; TASKS.md's Active execution
snapshot identity, Gate B, maximum-worker, baseline, protected-path, run-stop,
and next-action fields only. Update summary and detailed records, task snapshot,
and the matching `bootstrap.yaml` lifecycle mirror as one coordinator
checkpoint. Do not generate a replacement graph. When invalidating a CURRENT
plan, first reconcile active tasks and commit/archive the stopped ledger, then
mark the plan STALE.

**GitHub mode:** READ_ONLY only when authorized and needed for design facts.

**AWS mode:** DOCS_ONLY by default; authenticated READ_ONLY only when explicitly
authorized and necessary to validate an existing brownfield environment.

**Required authorization:** Design writes only. No implementation, GitHub writes, or AWS
mutation.

**Stop conditions:** Missing/invalid Gate A; requirements/design conflict;
unresolved high-impact decision; unavailable AWS Core; or an unverified AWS
claim material to service fit, identity, data protection, recovery, Region,
operations, or cost.

**Receipt:** Standard work receipt with REQ, DES, and proposed AUTH IDs.

**Next:** REQ-10 for material scope changes; otherwise DESIGN-20.

~~~text
[DESIGN-10]
Complete a build-ready technical PRD for the accepted requirements.

Create or increment a design revision such as DES-0001 and a proposed
construction authorization such as AUTH-0001. Run the dependency checker,
confirm AWS Core is surfaced in the current session, and ask the read-only
`fastlane-aws-advisor` to verify material service-fit, Region, IAM, encryption,
reliability, observability, quota, and cost facts through AWS Core and current
AWS primary documentation. Record verified facts and sources in the design.
The coordinator remains the only writer and the advisor cannot approve Gate B.

Complete only the design needed to build safely:
- context, boundaries, components, interfaces, and data flow;
- identity, authorization, secrets, encryption, validation, and audit behavior;
- schemas, state transitions, idempotency, concurrency, retries, and failures;
- observability, SLO-relevant signals, recovery, rollback, and teardown;
- deployment approach, environments, regional constraints, and cost drivers;
- test strategy, system properties/invariants, and acceptance traceability;
- brownfield compatibility, rollout, migration, and rollback when applicable;
- explicit decisions, alternatives, assumptions, and Well-Architected effects.

Fill the Gate B readiness card with these exact fields: Design basis IDs;
Architecture/components; Interfaces/data flow; Identity/secrets;
Failure/retry/concurrency; Deployment/operations; Validation/evidence;
Rollback/recovery/teardown; Brownfield compatibility/migration; Outstanding
gaps. Use explicit values and stable IDs; `NOT_APPLICABLE — <reason>` is allowed
only when genuinely inapplicable. Outstanding gaps is exactly `NONE` or stable
gap IDs, and any gap keeps Gate B BLOCKED.

Prefer the simplest architecture satisfying the accepted requirements. In
quick-mvp, avoid VPCs, NAT Gateways, public IPv4, container platforms,
always-on compute, and provisioned databases unless a requirement demands one.

Propose a complete construction envelope with the fields defined in this pack.
GitHub writes default to branch/commit/push/pull-request only when explicitly
listed. Merge and branch deletion default to not authorized. AWS defaults to
DOCS_ONLY. A fast-dev AWS mutation envelope may be proposed only when every AWS
mutation-boundary field is complete, the environment is non-production, the
cost ceiling is explicit, rollback/teardown is proven feasible, artifact
authority is an exact lowercase SHA-256 digest or deterministic authorized
source rule, and the exact finite expiry remains in the future. Use
`ENVIRONMENT: <exact>; CLASS: NON_PRODUCTION`, `EXACT_DIGEST: sha256:<64
lowercase hex>` or `DERIVED_FROM_AUTHORIZED_SOURCE: SHA-256 from baseline <full
authorized commit>; <deterministic rule>`, and
`Expires at <ISO 8601 with timezone>; earlier completion: <exact condition>`.

Use every exact envelope row and grammar in PRD.md. Require a local Git
repository and resolvable baseline commit before readiness. Compute and record
the canonical complete-envelope SHA-256 after the final table edit; copy the
same digest into the Gate B agent review and proposed owner receipt.

If the PRD or envelope is incomplete, keep Gate B `BLOCKED`. When the design and
envelope review recommendation is `READY_FOR_CONSTRUCTION_APPROVAL`, atomically
set both the Document status and detailed owner Gate B state to
`PENDING_OWNER_APPROVAL`; copy the exact REQ/DES/AUTH IDs, Gate B state, maximum
workers, baseline, and protected dirty paths into TASKS.md's Active execution
snapshot; and mirror lifecycle state in bootstrap.yaml. Keep any old task plan
STALE and non-runnable until the new Gate B is approved and TASK-10 replaces it.
Reset
the Gate B owner decision to `PENDING`, clear any prior approver, provenance,
authorized-ID, and receipt fields, and render the current proposed receipt with
an approver placeholder; never carry an old receipt into a new design or AUTH.
Do not implement, generate tasks, approve the design, or perform GitHub/AWS
writes. Return the standard work receipt.
~~~

## DESIGN-20 — PRD and Construction Gate B

**Preconditions:** Complete, internally consistent PRD; current Gate A;
proposed DES revision and AUTH envelope.

**Authoritative inputs:** PRD.md in full, including traceability and proposed
envelope; current AWS Core capability; recorded primary AWS sources and
read-only advisor findings.

**Permitted writes:** PRD.md Gate B owner record and the matching Document
status Gate B state only after an exact valid human receipt. Update both
plus TASKS.md's Active execution snapshot and the matching `bootstrap.yaml`
lifecycle mirror as one coordinator checkpoint. Do not generate or rewrite
task blocks.

**GitHub mode:** NONE.

**AWS mode:** DOCS_ONLY through the current AWS Core session; no AWS account
access.

**Required authorization:** Presentation only until the exact receipt is received.

**Stop conditions:** Stale Gate A; incomplete design/envelope; mismatch between
requirements, design, or IDs; placeholder approver; altered/partial receipt;
AWS Core unavailable; or material AWS design evidence is stale or unverified.

**Receipt:** Standard work receipt with WAITING_FOR_GATE_B, followed by the
copyable Gate B receipt as the final block.

**Next:** TASK-10 only after exact acceptance; otherwise DESIGN-10 or REQ-10.

~~~text
[DESIGN-20]
Review the complete PRD and proposed construction envelope for human Gate B.

Show a concise decision brief:
- REQ, DES, and AUTH IDs;
- canonical complete construction-envelope SHA-256;
- all ten fields from the current Gate B readiness card;
- architecture and key tradeoffs;
- material AWS facts verified through AWS Core, primary sources, and any AWS
  advisor finding the coordinator rejected with its reason;
- requirement-to-design/test traceability;
- security, data, availability, cost, migration, rollback, and teardown risks;
- project mode and delivery profile;
- exact local, GitHub, AWS, merge, branch-cleanup, and autonomous-run boundaries;
- explicit exclusions and stop conditions.

Set the Gate B agent recommendation to exactly `BLOCKED` or
`READY_FOR_CONSTRUCTION_APPROVAL`. The recommendation is advisory and does not
approve the gate.

Do not approve the gate yourself. Render a copyable receipt with the exact
field names below and actual current IDs. The human must replace the approver
placeholder.

Accept Gate B only if the human response equals the complete block below after
trimming surrounding whitespace:

APPROVE PRD AND CONSTRUCTION GATE B
Requirements revision: REQ-0001
Design revision: DES-0001
Construction authorization: AUTH-0001
Construction envelope SHA-256: sha256:<64-lowercase-hex>
Use the proposed construction envelope above.
Approver: <name/handle>

All IDs and the canonical complete-envelope SHA-256 must exactly match the
proposed card and structured owner record. Reject extra or duplicate fields,
comments, reordered lines, partial blocks, and code fences. Silence, continued
conversation, task state, or tool access never counts. After a valid receipt,
preserve the complete normalized receipt inside the uniquely marked Gate B
receipt block, then atomically update the detailed owner record, Document
status, TASKS.md Active execution snapshot, and lifecycle mirror to
APPROVED_FOR_CONSTRUCTION. Record the observed ISO 8601 authorization time and
exact message/issue/meeting-record source as structured provenance without
adding either value to the receipt. Do not invent a source. Activate only that
envelope, and ensure the task snapshot contains the exact REQ/DES/AUTH IDs,
approved Gate B state, authorized maximum workers, baseline, protected dirty
paths, and `TASK-10` as the next safe action while the plan state is
UNINITIALIZED or STALE.
Return a standard work receipt whose Next is TASK-10. Before acceptance, return
WAITING_FOR_GATE_B and put the exact proposed approval receipt last.
~~~

## BUG-10 — Active Defect Contract

**Preconditions:** Reproducible symptom or bounded investigation request; an
active construction authorization is required before implementation.

**Authoritative inputs:** AGENTS.md; BUGFIX.md; relevant PRD.md requirements; code, tests,
logs supplied by the user, configuration, IaC, and relevant history.

**Permitted writes:** BUGFIX.md defect analysis and regression contract only.

**GitHub mode:** READ_ONLY only when authorized and necessary for evidence.

**AWS mode:** NONE by default; READ_ONLY only with explicit environment scope.

**Required authorization:** Analysis only. This prompt never authorizes a fix or external
write.

**Stop conditions:** Evidence requires secrets; production mutation would be
needed to reproduce; symptom suggests active incident/data loss; scope becomes
a feature or material requirements change.

**Receipt:** Standard work receipt.

**Next:** TASK-10 if covered by active Gate B; otherwise REQ-10.

~~~text
[BUG-10]
Define an evidence-based defect contract without implementing the fix.

Record in BUGFIX.md:
- stable bug ID, observed behavior, expected behavior, and business impact;
- reproducible evidence and confidence;
- affected versions/environments and smallest known boundary;
- root-cause hypotheses clearly separated from facts;
- security, privacy, data-loss, concurrency, migration, and rollback risk;
- regression acceptance criteria and validation commands;
- relationship to accepted PRD requirements and current AUTH envelope.

Inspect before hypothesizing. Do not manufacture logs or claim reproduction you
did not observe. If the correction changes accepted behavior or exceeds the
active envelope, return to REQ-10. Otherwise state readiness for TASK-10 and
return the standard work receipt.
~~~

## TASK-10 — Executable Task Plan

**Preconditions:** Valid current Gate B receipt and active construction
authorization; or a defect fully covered by that authorization.

**Authoritative inputs:** AGENTS.md; PRD.md; BUGFIX.md when applicable; current code/tests/IaC;
TASKS.md; VERIFY.md; RUNBOOK.md; bootstrap.yaml; passing bootstrap doctor output.

**Permitted writes:** TASKS.md and its matching `bootstrap.yaml` task-plan mirror
as one checkpoint; no implementation.

**GitHub mode:** NONE. Planning GitHub objects is allowed, creating them is not.

**AWS mode:** NONE, except DOCS_ONLY for validation-command accuracy.

**Required authorization:** Task planning within active AUTH scope.

**Stop conditions:** Gate/revision mismatch; task would exceed envelope; unsafe
dependency; validation cannot objectively prove acceptance.

**Receipt:** Standard work receipt.

**Next:** BUILD-10 for one task or BUILD-20 for an autonomous run.

~~~text
[TASK-10]
Translate the accepted PRD or BUGFIX contract into executable TASKS.md entries.

Run the read-only bootstrap doctor first. Task-plan state is exactly
UNINITIALIZED, CURRENT, or STALE. Set the next monotonic Task-plan revision such
as PLAN-0001 and change state to CURRENT only after the complete replacement
graph validates. If the old state is STALE, first reconcile every IN_PROGRESS
task, checkpoint and commit the non-runnable graph, add its plan/REQ/DES/AUTH and
archive commit to the registry, then replace the current graph without reusing
task IDs.

For every task include:
- stable ID and outcome;
- status: BACKLOG, READY, IN_PROGRESS, BLOCKED, DONE, or SKIPPED;
- requirement/bug and design traceability;
- current AUTH ID, dependencies, and explicit skipped-dependency waivers or NONE;
- exact write set and external-state set;
- acceptance criteria;
- validation commands and required evidence;
- risk class, AWS mode, attempt budget/used count, owner, run ID, blocker,
  skip record, and checkpoint fields;
- GitHub link or PENDING_SYNC;
- concise execution log.

Emit each record in the validator's exact human-first shape: one
`### <TASK-ID> — <title>` heading; visible Status, Owner, Blocker, and GitHub
issue fields; `#### Outcome`, `#### Acceptance criteria`, `#### Validation`, and
`#### Execution log`; then a collapsed `#### Agent execution details` section
containing every remaining singleton metadata line from TASKS.md's Required
task record schema, spelled exactly once. A READY task cannot contain TODO in its outcome,
acceptance criteria, validation, boundary, or traceability. Acceptance criteria
must be checkboxes, and a DONE task must have every acceptance checkbox checked,
non-NONE Evidence, and an observed execution-log entry.

Keep tasks thin enough to validate independently. Mark READY only when all
dependencies, inputs, and authorization are satisfied. A SKIPPED dependency is
not satisfied without a current waiver naming the dependency, downstream task,
authority, rationale, and replacement evidence. Compute structural waves, then
compute conservative execution groups so concurrent tasks share neither files
nor mutable application/AWS state. Anything sharing a
manifest, lockfile, schema, stack, database, generated output, or deployment
target must be serialized unless isolation and separate worktrees are proven.

Plan a single coordinator as the writer for shared control files such as
TASKS.md, VERIFY.md, RUNBOOK.md, and bootstrap.yaml. Do not let parallel workers
update them. Do not create
GitHub objects, implement code, or access AWS. Validate task graph consistency
with `python scripts/task_waves.py TASKS.md`, inspect candidates with
`python scripts/task_waves.py TASKS.md --ready --json`, commit the validated
current plan locally within the Gate B command/write boundary, update Last
known-green and the checkpoint registry, and rerun the doctor. Never push or
touch a remote unless separately authorized. Return the standard work receipt.
~~~

## BUILD-10 — Execute One Task

**Preconditions:** Named READY task on a CURRENT plan; valid current AUTH;
dependencies complete; write and external-state sets are available; local Git
baseline resolves.

**Authoritative inputs:** Applicable AGENTS.md; task-linked PRD/BUGFIX sections; task entry;
relevant code, tests, IaC, VERIFY.md, RUNBOOK.md, bootstrap.yaml, and doctor output.

**Permitted writes:** Named task write set; coordinator-serialized updates to
TASKS.md, VERIFY.md, and bootstrap.yaml; RUNBOOK.md only when repeatable
operations change.

**GitHub mode:** Only operations explicitly allowed by current AUTH or current
user instruction.

**AWS mode:** As stated by current AUTH. AWS mutation still requires a complete
active mutation boundary.

**Required authorization:** One named task inside AUTH scope.

**Stop conditions:** Scope drift; unexpected shared writer; failed safety check;
new requirement/design decision; missing authorization; destructive/billable
impact outside boundary; repeated failure without a new hypothesis.

**Receipt:** Standard work receipt with validation evidence.

**Next:** BUILD-10, RELEASE-10, or STOP.

~~~text
[BUILD-10]
Execute task <TASK-ID> and no unrelated task.

Before editing, run doctor and verify its READY state, dependencies (DONE or an
explicitly waived SKIPPED prerequisite), exact write set, active REQ/DES/AUTH
IDs, and external authorization. Use the coordinator tool rather than hand
editing run or claim fields. Allocate the next unused monotonic IDs and replace
the illustrative IDs below, then run this exact start-and-claim sequence:

```bash
python scripts/task_waves.py TASKS.md --start-run RUN-0001 --coordinator codex-coordinator --run-mode SINGLE_TASK
python scripts/task_waves.py TASKS.md --claim TASK-0001 --owner codex-worker-1 --run-id RUN-0001 --coordinator codex-coordinator --checkpoint CP-0000
```

If the same run is safely checkpointed instead of new, reconcile the checkpoint
and use this exact resume-and-claim sequence:

```bash
python scripts/task_waves.py TASKS.md --resume-run RUN-0001 --coordinator codex-coordinator
python scripts/task_waves.py TASKS.md --claim TASK-0001 --owner codex-worker-1 --run-id RUN-0001 --coordinator codex-coordinator --checkpoint CP-0002
```

A persisted `RUNNING` run is interrupted/recovery-required and must not be
started over or automatically resumed. Claiming atomically records owner, run
ID, base checkpoint, and the incremented persistent attempt before editing.
Inspect before changing code and make the smallest coherent implementation.

Run the task's validation plus relevant regression, security, IaC, and failure
checks. Record observed evidence in the exact VERIFY.md `Task completion
evidence` table before citing its EV ID. Update RUNBOOK.md only if a
repeatable procedure changed. Mark DONE only when every acceptance criterion
and required local check passes; otherwise mark BLOCKED with the next useful
action. Reconcile the task first, then checkpoint the run; never pause with an
IN_PROGRESS task:

```bash
python scripts/task_waves.py TASKS.md --set-status TASK-0001 DONE --evidence EV-0001 --run-id RUN-0001 --coordinator codex-coordinator --checkpoint CP-0001
python scripts/task_waves.py TASKS.md --pause-run RUN-0001 --coordinator codex-coordinator --checkpoint CP-0002
```

Use `--complete-run RUN-0001 --coordinator codex-coordinator --checkpoint
CP-0002` instead of `--pause-run`
only when every task is terminal. For a blocked attempt, use `--set-status
TASK-0001 BLOCKED --blocker "<observed blocker and next action>" --run-id
RUN-0001 --coordinator codex-coordinator --checkpoint CP-0001`, then pause.
Leave AWS-only evidence PENDING_AWS until observed.

Claims cite the current base checkpoint; concurrent claims may share it only
when their isolation is proven. Each `IN_PROGRESS` reconciliation consumes the
next unique checkpoint. Pause or completion consumes a later unique checkpoint
and requires the newest complete checkpoint row plus VERIFY.md reference. Run
start and issue synchronization do not invent checkpoints. A DONE
reconciliation at CP-0001 is therefore followed by pause or completion at
CP-0002; never reuse CP-0001.

Before pausing, inspect the final diff, record `EV-0001`-style evidence, commit
only the authorized validated task changes, and update Last known-green commit
and the checkpoint row to that commit. Run doctor after those updates. Do not
commit a protected dirty path or use a remote Git operation unless separately
authorized.

Perform only GitHub actions listed in the active authorization. BUILD-10 never
executes an AWS mutation directly: if the task reaches a mutation boundary,
record and checkpoint the local state, route through AWS-10 and AWS-20, and use
AWS-30 to reconcile evidence. A connected tool does not grant permission. Stop
on any common-contract condition. Return the standard work receipt.
~~~

## BUILD-20 — Autonomous Construction Run

**Preconditions:** Valid Gate B; active AUTH explicitly permits autonomous
execution; TASKS.md plan is CURRENT and its graph is valid; at least one READY
task; local Git baseline resolves.

**Authoritative inputs:** All sources required by eligible tasks; bootstrap.yaml;
passing doctor output; last clean coordinator checkpoint.

**Permitted writes:** Eligible task write sets; coordinator-only serialized writes to
TASKS.md, VERIFY.md, RUNBOOK.md, bootstrap.yaml, shared manifests, lockfiles, schemas,
generated output, and other shared paths.

**GitHub mode:** Only operations explicitly listed in AUTH; no merge or branch
deletion unless named.

**AWS mode:** AUTH boundary only. AWS mutations are always serialized.

**Required authorization:** Autonomous work only until the envelope completion/expiry,
task boundary, or stop condition.

**Stop conditions:** No READY task; envelope exhausted/expired; revision drift;
shared-write collision; failing mainline; new material decision; unexpected
cost/security/data impact; AWS identity mismatch; destructive step not explicit;
approved attempt budget exhausted without a materially new hypothesis.

**Receipt:** One standard work receipt per completed wave and a final receipt.

**Next:** Continue BUILD-20, SYNC-10, RELEASE-10, or STOP.

~~~text
[BUILD-20]
Run the approved task graph autonomously inside the active construction
authorization until completion or a stop condition.

Allocate the next unused monotonic run ID and acquire it with this exact command
shape before selecting work:

```bash
python scripts/task_waves.py TASKS.md --start-run RUN-0001 --coordinator codex-coordinator --run-mode AUTONOMOUS
python scripts/task_waves.py TASKS.md --safe-ready --isolated-worktrees --json
```

On a safely PAUSED or BLOCKED run, reconcile state and resume only the same run
and coordinator:

```bash
python scripts/task_waves.py TASKS.md --resume-run RUN-0001 --coordinator codex-coordinator
```

Use this loop:
1. run doctor and reconcile PRD, TASKS.md, bootstrap.yaml, REQ/DES/AUTH, baseline,
   protected dirty paths, task states, and last external-operation journal;
2. atomically acquire one durable coordinator run ID; a pre-existing RUNNING
   state is recovery-required and is never auto-cleared;
3. select only READY tasks whose dependencies are DONE or explicitly waived
   SKIPPED prerequisites;
4. form a concurrency group only from disjoint file and external-state sets;
5. require isolated worktrees for more than one worker; otherwise serialize;
6. atomically claim each selected task with owner, run ID, base checkpoint, and
   incremented persistent attempt count before implementation. Use this serial
   form for one worker:

   ```bash
   python scripts/task_waves.py TASKS.md --claim TASK-0001 --owner codex-worker-1 --run-id RUN-0001 --coordinator codex-coordinator --checkpoint CP-0000
   ```

   Every claim in a concurrent group uses the isolated-worktree form:

   ```bash
   python scripts/task_waves.py TASKS.md --claim TASK-0001 --owner codex-worker-1 --run-id RUN-0001 --coordinator codex-coordinator --checkpoint CP-0000 --isolated-worktrees
   ```

7. implement, validate, inspect actual worker diffs, and collect evidence in
   exact VERIFY.md `Task completion evidence` rows;
8. have the coordinator alone update control files and mirrors between groups;
9. mark tasks DONE only on observed acceptance evidence;
10. checkpoint attempts, changed paths, external operations, evidence, blockers,
    and next safe action; after every task is reconciled out of IN_PROGRESS,
    inspect the integrated diff, record EV evidence, commit only the authorized
    validated wave, and update Last known-green and the checkpoint row to that
    commit. Use `--complete-run RUN-0001 --coordinator codex-coordinator
    --checkpoint CP-0002` only when all tasks are terminal. Otherwise run
    `python scripts/task_waves.py TASKS.md --pause-run RUN-0001 --coordinator
    codex-coordinator --checkpoint CP-0002`, then run doctor and aggregate
    tests. Resume the same run and coordinator before claiming the next group.
    Never run doctor against a persisted RUNNING snapshot or commit protected
    dirty paths.

Workers must not edit shared control files, protected/user-dirty paths, the same
manifest/lockfile/schema, or overlapping generated output. Reject a receipt
whose actual diff exceeds its task boundary. Do not have multiple agents push
the same branch. Journal every external operation before execution; an UNKNOWN
or partial result requires read-only reconciliation and must not be blindly
retried. Keep GitHub synchronization serialized and within authorization.
Route AWS mutation through AWS-10/AWS-20 and serialize every mutation, even when
tasks are otherwise eligible for parallel work.

Continue through safe waves without asking routine questions. Pause only for a
declared stop condition or authority that Gate B did not grant. Return receipts
at wave boundaries and a final standard work receipt.
~~~

## SYNC-10 — GitHub Reconciliation

**Preconditions:** Repository identity is verified; task IDs are stable; current
user instruction or AUTH explicitly permits named GitHub writes.

**Authoritative inputs:** TASKS.md; VERIFY.md; existing GitHub issues, project items, branches,
checks, and pull requests in the named repository.

**Permitted writes:** Authorized GitHub objects; TASKS.md link/status reconciliation.

**GitHub mode:** READ_ONLY when no write authorization; otherwise only listed
WRITE operations.

**AWS mode:** NONE.

**Required authorization:** Repository plus allowed operations must be explicit.

**Stop conditions:** Repository mismatch; issue/task conflict; protected branch
or required check failure; requested merge/close/delete not authorized.

**Receipt:** Standard work receipt listing exact observed GitHub actions.

**Next:** BUILD-20, RELEASE-10, or STOP.

~~~text
[SYNC-10]
Reconcile local task truth with GitHub using stable task IDs.

Read first. For each non-trivial task, update or create only the GitHub objects
allowed by the active authorization. Preserve dependencies, wave, status,
blockers, PR links, and concise validation evidence. Do not copy full logs.
When local and GitHub state conflict, report and reconcile from observed facts;
do not silently overwrite.

Creating branches, issues, project items, commits, pushes, PRs, labels,
comments, merges, releases, or deletions are distinct write operations. Perform
only those explicitly named. Tool availability is never authorization. Return
the standard work receipt.
~~~

## RELEASE-10 — Release Readiness and Finalization

**Preconditions:** Intended release tasks are DONE or explicitly excluded;
aggregate local validation is available; release target is identified.

**Authoritative inputs:** PRD.md; BUGFIX.md; TASKS.md; VERIFY.md; RUNBOOK.md; diff; tests; IaC;
dependency/security results; authorized GitHub checks.

**Permitted writes:** VERIFY.md release assessment; RUNBOOK.md only for corrected
procedures; authorized GitHub PR/release actions.

**GitHub mode:** READ_ONLY by default; WRITE only for operations named by AUTH
or the current user. Merge and branch cleanup require explicit inclusion.

**AWS mode:** NONE or DOCS_ONLY. Deployment belongs to AWS-20.

**Required authorization:** Assessment is local; external finalization follows the active
GitHub scope.

**Stop conditions:** Failed required check; unmitigated critical risk; missing
rollback; evidence gap; scope/revision drift; unauthorized merge/release.

**Receipt:** Standard work receipt with READY or BLOCKED and the exact release
state `NOT_READY`, `READY_TO_DEPLOY`, or `RELEASE_VERIFIED` in Validation.

**Next:** AWS-10 only from READY_TO_DEPLOY; AWS-40 after verified deployment
when residual review is in scope; otherwise STOP.

~~~text
[RELEASE-10]
Assess the release against the accepted REQ/DES/AUTH revisions.

Verify:
- requirement and defect acceptance traceability;
- tests, properties/invariants, failure paths, security, IaC, and packaging;
- migration, rollback, recovery, observability, and cost readiness;
- documentation and version consistency;
- GitHub review and required checks when accessible;
- which evidence is LOCAL_PASS versus PENDING_AWS.

Set exactly one release state in VERIFY.md: NOT_READY when any required evidence
is incomplete/failed/stale; READY_TO_DEPLOY when all pre-deployment evidence is
current for the immutable artifact and AWS deployment is the only remaining
required step; RELEASE_VERIFIED only when every required local and deployed
acceptance item is VERIFIED or explicitly not applicable. Record observed
evidence and return READY or BLOCKED with specific reasons.
If authorization explicitly permits finalization, perform only the named
GitHub operations after required checks pass. Never infer permission to merge,
publish a release, delete a branch, or deploy. Return the standard work receipt.
~~~

## AWS-10 — Read-Only Deployment Preflight

**Preconditions:** RELEASE-10 recorded `READY_TO_DEPLOY` for the intended immutable artifact; target account,
Region, environment, and stack are named; authenticated read access is
explicitly authorized.

**Authoritative inputs:** PRD.md; VERIFY.md; RUNBOOK.md; IaC; deployment artifact; aws-core
skills/docs; read-only AWS identity, configuration, quotas, and target state.

**Permitted writes:** VERIFY.md preflight evidence only.

**GitHub mode:** NONE or authorized READ_ONLY for artifact/check identity.

**AWS mode:** READ_ONLY. Documentation grounding may accompany it; no mutation.

**Required authorization:** Exact read-only account/profile/Region/environment scope.

**Stop conditions:** Identity mismatch; missing plugin/tool; unavailable Region
or quota; drift; unreviewed change set; cost/rollback uncertainty; any mutation.

**Receipt:** Standard work receipt with READY or BLOCKED and observed identity.

**Next:** AWS-20 only with valid mutation authorization; otherwise STOP.

~~~text
[AWS-10]
Perform a read-only AWS deployment preflight. Use aws-core and current AWS
primary documentation.

Confirm without exposing secrets:
- caller identity, allowlisted profile/role, account, Region, and environment;
- artifact digest and IaC validation;
- proposed change set or equivalent read-only plan;
- service availability, quotas, naming, IAM boundary, encryption, networking,
  logging, alarms, backups, and data-retention implications;
- estimated billing dimensions/budget boundary;
- rollback and teardown commands and retained-resource behavior;
- absence of unexpected drift or shared-resource impact.

Do not create, update, delete, deploy, rotate, migrate, or mutate data. Record
only observed facts in VERIFY.md. Return READY only when the complete mutation
boundary can be authorized; otherwise BLOCKED. Return the standard work receipt.
~~~

## AWS-20 — Authorized Deployment

**Preconditions:** AWS-10 READY; active fast-dev envelope or action-specific
authorization contains every AWS mutation-boundary field and matches preflight.

**Authoritative inputs:** Current REQ/DES/AUTH; VERIFY.md; RUNBOOK.md; artifact; preflight;
aws-core docs/tools; live read-only target state.

**Permitted writes:** Authorized AWS target; VERIFY.md evidence; TASKS.md status;
RUNBOOK.md only for observed procedural correction.

**GitHub mode:** Only separately authorized deployment-status/check operations.

**AWS mode:** MUTATION, limited to exact authorization.

**Required authorization:** A valid Gate B fast-dev envelope or a current human
action receipt equal to the complete `AUTHORIZE AWS DEPLOYMENT` block in the
common contract and naming all mutation-boundary fields. Tool access is
insufficient.

**Stop conditions:** Any field mismatch; authorization expired; unexpected
change set/cost/resource; alarm or smoke-test failure; rollback condition;
operation expands scope; destructive replacement not explicitly allowed.

**Receipt:** Standard work receipt listing exact mutations and identifiers,
without secrets.

**Next:** AWS-30, including after rollback or partial failure.

~~~text
[AWS-20]
Execute only the AWS deployment authorized by <AWS-AUTH-ID or active fast-dev
AUTH-ID>.

For `explicit-gate`, first compare the supplied owner message to the exact
`AUTHORIZE AWS DEPLOYMENT` block in this pack. Reject placeholders, extra or
missing lines, field-order changes, a stale AUTH, or any value that differs from
AWS-10. Record the valid receipt verbatim with its observed time and exact
source before mutation. Under `fast-dev`, prove instead that the final action is
fully and exactly contained in the current Gate B mutation envelope; otherwise
mark Gate B stale and route to DESIGN-10. An action-specific receipt cannot
repair a fast-dev envelope mismatch.

Reconfirm caller identity, account, Region, environment, artifact digest, exact
change set, cost ceiling, and rollback path immediately before mutation. Use
the least-privileged approved write profile. Execute the documented deployment
method; do not improvise broader permissions or resources.

Stream concise milestones. Stop on every declared threshold. If a rollback
condition occurs, perform rollback only when the authorization includes it;
otherwise stop and report the safest state. Capture command/result identifiers,
resource identifiers, timestamps, alarms, and smoke-test outcomes without
secrets. Do not mark deployed verification complete in this prompt. Return the
standard work receipt and proceed to AWS-30.
~~~

## AWS-30 — Deployed Evidence Reconciliation

**Preconditions:** AWS-20 attempted a deployment or rollback; read-only target
access remains authorized.

**Authoritative inputs:** Deployment receipt; PRD.md acceptance criteria; VERIFY.md; RUNBOOK.md;
live read-only AWS state, telemetry, logs, and smoke-test endpoints.

**Permitted writes:** VERIFY.md; TASKS.md evidence/status; RUNBOOK.md only for repeatable
procedural correction.

**GitHub mode:** Only authorized status/check/comment updates.

**AWS mode:** READ_ONLY. Any corrective mutation requires a new or still-valid
explicit mutation authorization.

**Required authorization:** Exact read-only target scope.

**Stop conditions:** Identity mismatch; telemetry unavailable; security/data
anomaly; failed acceptance test; correction would mutate AWS.

**Receipt:** Standard work receipt with `COMPLETE` or `BLOCKED`; put
`VERIFIED`, `PENDING_AWS`, or failed evidence states in Validation and Open
risks, not in the work-receipt Status field.

**Next:** RELEASE-10 after recording evidence. RELEASE-10 decides whether the
release is RELEASE_VERIFIED, still NOT_READY, or needs an authorized correction.

~~~text
[AWS-30]
Reconcile deployed AWS evidence against the accepted requirements.

Observe:
- deployed artifact/version and resource state;
- smoke tests and user-visible outcome;
- IAM, encryption, network exposure, logging, alarms, and error signals;
- data integrity, migration, retry/idempotency, and recovery signals as relevant;
- performance and cost indicators available in the observation window;
- rollback status after a failed deployment.

Record what was actually observed, when, where, and by which read-only identity.
Mark VERIFIED only with objective evidence. Keep unavailable or time-dependent
checks PENDING_AWS. Do not mutate to repair a failed check. Do not set the
release state here. Return the standard work receipt whose Next is RELEASE-10.
~~~

## AWS-40 — Residual Resource and Teardown Review

**Preconditions:** Deployment, test, rollback, or environment lifecycle creates
a need to assess residual resources; read-only target access is authorized.

**Authoritative inputs:** PRD.md retention requirements; VERIFY.md; RUNBOOK.md; IaC state;
live read-only inventory, dependencies, backups, retention, and billing signals.

**Permitted writes:** VERIFY.md teardown assessment; RUNBOOK.md only for a corrected
repeatable plan.

**GitHub mode:** NONE or authorized status-only writes.

**AWS mode:** READ_ONLY. No deletion or mutation.

**Required authorization:** Exact read-only account/Region/environment/resource boundary.

**Stop conditions:** Shared ownership unclear; retained/regulated data; unknown
dependency; identity mismatch; teardown would cross the named boundary.

**Receipt:** Standard work receipt with residual inventory and authorization
requirements.

**Next:** AWS-50 only with explicit teardown authorization; otherwise STOP.

~~~text
[AWS-40]
Perform a read-only residual-resource and teardown review.

Identify:
- resources created, changed, retained, shared, or drifted;
- dependencies and deletion order;
- data, backups, snapshots, domains, certificates, logs, and secrets affected;
- deletion protection and retention requirements;
- continuing billing dimensions;
- exact resources that should be retained versus removed;
- reversible checkpoints and post-teardown verification.

Compare live inventory to IaC and RUNBOOK.md. Do not delete, disable, detach,
empty, rotate, or mutate anything. Produce the exact proposed teardown boundary
and required authorization fields. Return the standard work receipt.
~~~

## AWS-50 — Authorized Teardown

**Preconditions:** AWS-40 complete; current human authorization explicitly names
the resources/stack, retained data, destructive operations, account, Region,
profile/role, cost effect, and validity window.

**Authoritative inputs:** AWS-40 inventory; PRD.md retention rules; VERIFY.md; RUNBOOK.md; live
read-only identity and target state.

**Permitted writes:** Authorized AWS deletions/mutations; VERIFY.md; TASKS.md; RUNBOOK.md
only for observed procedural correction.

**GitHub mode:** Only separately authorized status updates.

**AWS mode:** MUTATION limited to exact teardown authorization.

**Required authorization:** Current action-specific teardown authorization. A deployment
authorization does not imply teardown permission. The human message must equal
the complete `AUTHORIZE AWS TEARDOWN` block in the common contract.

**Stop conditions:** Resource/identity mismatch; shared or retained dependency;
unexpected data; scope expansion; protection requiring an unauthorized change;
partial failure that changes the safe order.

**Receipt:** Standard work receipt with removed, retained, failed, and
post-teardown observed resources.

**Next:** STOP, or AWS-40 for residual read-only review.

~~~text
[AWS-50]
Execute only teardown operation <TEARDOWN-AUTH-ID>.

Before mutation, compare the supplied owner message to the exact `AUTHORIZE AWS
TEARDOWN` block in this pack. Reject placeholders, extra or missing lines,
field-order changes, stale IDs, or a value that differs from AWS-40's observed
inventory. Record the valid receipt verbatim with its observed time and exact
source. Gate B fast-dev, a deployment receipt, credentials, and prior cleanup
discussion never substitute for this receipt.

Reconfirm identity and exact resource inventory immediately before mutation.
Preserve every resource/data class marked retained. Use the documented order
and least-privileged approved profile. Do not disable safeguards or force
deletion unless that exact action is authorized.

After each bounded step, inspect results and stop on mismatch. Perform
post-teardown read-only verification and capture remaining resources and
billing-relevant residuals. Never claim deletion from a submitted request
alone. Return the standard work receipt.
~~~

## LEARN-10 — Educational Wrapper

**Preconditions:** A canonical prompt ID and desired learning depth are named.

**Authoritative inputs:** Same as the wrapped prompt.

**Permitted writes:** Same as the wrapped prompt; no extra tutorial documents.

**GitHub mode:** Same as the wrapped prompt.

**AWS mode:** Same as the wrapped prompt.

**Required authorization:** LEARN-10 adds explanation only and grants no new authority.

**Stop conditions:** Same as wrapped prompt; explanation would expose secrets
or distract from an active safety condition.

**Receipt:** Standard work receipt using the wrapped prompt ID and noting
LEARN-10 in Open risks only if teaching affected pace or scope.

**Next:** Same as wrapped prompt.

~~~text
[LEARN-10]
Run <CANONICAL-PROMPT-ID> under its unchanged contract and authorization, with
concise educational guidance.

At meaningful milestones:
- explain the relevant AWS or software-engineering concept in plain language;
- distinguish repository facts, documentation-backed facts, recommendations,
  assumptions, and observed evidence;
- explain important tradeoffs and why the chosen option fits the accepted
  requirements;
- give a short practical recap at completion.

Do not narrate every tool call, create tutorial documents, weaken validation,
or broaden scope. LEARN-10 never changes a gate, write boundary, GitHub mode,
AWS mode, stop condition, or authorization. Return the wrapped prompt's
standard work receipt.
~~~

## Suggested model selection

Model availability changes; verify current options with /model and the official
[Codex model guide](https://developers.openai.com/codex/models). The operating
rule reviewed July 14, 2026 is:

~~~text
Think and review with Sol.
Build with Terra.
Synchronize and maintain with Luna.
~~~

Use the lowest reasoning level that reliably handles the risk. Prefer Sol with
high or extra-high reasoning for requirements, architecture, release review,
security, IAM, migrations, concurrency, destructive work, and difficult
failures. Prefer Terra medium/high for normal implementation and read-only AWS
preflight. Use Luna for bounded mechanical synchronization. Use subagents only
for genuinely independent work with disjoint write and external-state sets;
otherwise serialize.
