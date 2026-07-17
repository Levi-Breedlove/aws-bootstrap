# AWS Codex Fastlane Prompt Pack

**Pack version:** 2.0.0

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

## Start here

For a new installation, paste **BOOT-00** with an explicit
**START AWS CODEX BOOTSTRAP** target. It safely initializes a new target or
resumes an initialized one, explains the workflow, and returns a prefilled
**START GUIDED INTAKE** command. Paste that command to begin.

For an initialized repository, use the prompt matching the current state. Do
not skip a missing Gate A or Gate B.

## Authority and operating model

The repository is authoritative:

| Concern | Authoritative source |
|---|---|
| Scope, engineering rules, and safety | AGENTS.md and applicable nested AGENTS.md files |
| Requirements, analysis, design, gates, and construction envelope | PRD.md |
| Active defect contract | BUGFIX.md |
| Tasks, dependencies, waves, status, and execution log | TASKS.md |
| Evidence actually observed | VERIFY.md |
| Deployment, rollback, recovery, operations, and teardown | RUNBOOK.md |
| Durable review and collaboration | GitHub issues and pull requests |
| Runtime behavior | Code, tests, schemas, configuration, and infrastructure |

Notion may launch the prompts and present status, but it is not a second source
of truth. When sources conflict, stop and report the conflict. Do not silently
choose one or create another planning document.

Every run declares two independent axes:

- **Project mode:** greenfield or brownfield.
- **Delivery profile:** quick-mvp, standard, or high-risk.

Quick-mvp is the default when risk and requirements allow it. It means the
smallest useful, observable, reversible release—not weaker security, tests, or
AWS controls. Brownfield mode begins with repository discovery and preserves
existing conventions unless an approved requirement justifies changing them.

## Common prompt contract

Apply this contract to every prompt below.

### Authorization

- Tool availability, credentials, a task state, a GitHub label, prior access,
  silence, or continued conversation never equals authorization.
- Codex cannot approve its own proposal or fill in an approver identity.
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

**Official grounding reviewed July 17, 2026.** For AWS work, prefer the
aws-core plugin from Agent Toolkit for AWS:

- [Agent Toolkit for AWS](https://aws.amazon.com/products/developer-tools/agent-toolkit-for-aws/)
- [Agent Toolkit plugins](https://docs.aws.amazon.com/agent-toolkit/latest/userguide/plugins.html)
- [AWS MCP Server tools](https://docs.aws.amazon.com/agent-toolkit/latest/userguide/understanding-mcp-server-tools.html)
- [Multi-profile support](https://docs.aws.amazon.com/agent-toolkit/latest/userguide/multi-account-access.html)

Use aws-core skills, current AWS primary documentation, regional-availability
checks, and its AWS API tools before relying on model memory. The plugin is a
knowledge and tool layer; it does not replace PRD.md, IAM, or authorization.
If aws-core is unavailable, repository-only work may continue, but authenticated
AWS mutation is blocked and unverified AWS claims must be identified.

Before any AWS mutation, the active authorization must state all of:

~~~text
profile or role
account ID or approved alias
Region
environment
stack, application, and resource boundary
approved operation
approved resource summary
billable impact or budget ceiling
rollback or teardown path
authorization ID, approver, and validity window
~~~

Missing, stale, or conflicting values make the mutation BLOCKED. Read-only
discovery must precede mutation. Prefer a read-only profile by default and the
least-privileged write profile only for an authorized operation.

To install aws-core for Codex, follow the current Agent Toolkit documentation.
The currently reviewed flow is:

~~~bash
codex plugin marketplace add aws/agent-toolkit-for-aws
codex
~~~

Then open /plugins, install aws-core, and restart the session if requested. For
multiple profiles, allowlist only intended profiles; the first is the default:

~~~bash
export AWS_MCP_PROXY_PROFILES="mvp-readonly mvp-deploy"
~~~

### Evidence states

Use evidence states that do not overclaim:

~~~text
NOT_STARTED -> IMPLEMENTED -> LOCAL_PASS -> PENDING_AWS -> VERIFIED
~~~

Local tests cannot produce deployed AWS evidence. A task can be DONE when its
approved task-level criteria pass while AWS-only evidence remains PENDING_AWS.

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
| RELEASE-10 | Review and, if authorized, finalize the release | AWS-10 or STOP |
| AWS-10 | Read-only deployment preflight | AWS-20 or STOP |
| AWS-20 | Execute an authorized deployment | AWS-30 |
| AWS-30 | Reconcile deployed evidence | AWS-40 or STOP |
| AWS-40 | Read-only residual and teardown review | AWS-50 or STOP |
| AWS-50 | Execute an authorized teardown | STOP |
| LEARN-10 | Add concise teaching to another prompt | Same as wrapped prompt |

---

## BOOT-00 — Bootstrap Launchpad

**Preconditions:** The user sent START AWS CODEX BOOTSTRAP with an explicit,
non-root target path. The bootstrap template source is available.

**Authoritative inputs:** Resolved template and target paths; bootstrap.py dry-run;
template manifest; target tree; AGENTS.md files; existing PRD.md, BUGFIX.md,
TASKS.md, VERIFY.md, and RUNBOOK.md; local Git, Python, prompt-pack, placeholder,
and aws-core availability checks.

**Permitted writes:** Collision-free bootstrap files inside the explicitly named
NEW_TARGET or resolved brownfield overlay target. Never overwrite. ACTIVE
targets are inspected and resumed without regeneration.

**GitHub mode:** NONE. Local Git availability and repository-state inspection
are allowed; no init, commit, push, branch, issue, pull request, or other write.

**AWS mode:** NONE.

**Required authorization:** The exact START AWS CODEX BOOTSTRAP command
authorizes only safe local initialization at its explicit target. It does not
authorize requirements, tasks, implementation, GitHub writes, or AWS access.

**Stop conditions:** Missing/ambiguous target; filesystem root or home target;
template/target equality or containment; symlink escape; dry-run failure;
collision or overwrite risk; unresolved source-of-truth conflict; partial write;
expected-file or placeholder verification failure.

**Receipt:** Standard work receipt plus classification, lifecycle state, and
READY, RESUME, or BLOCKED bootstrap status.

**Next:** State-derived: INTAKE-10, REQ-10, INTAKE-20, DESIGN-10, DESIGN-20,
TASK-10, BUILD-10, BUILD-20, RELEASE-10, or STOP.

~~~text
[BOOT-00]
Process this initiation command:

START AWS CODEX BOOTSTRAP
Target path: <explicit target path>

Act as the AWS Codex Fastlane installer and launchpad. Resolve the template and
target without relying on an unresolved variable, glob, home shortcut, or
command substitution. Refuse a root/home target, equality, either-direction
containment, or symlink escape.

Inspect before writing and classify exactly one:
- TEMPLATE_SOURCE: this is the reusable source, not an initialized target;
- NEW_TARGET: explicit absent or empty target safe to initialize;
- ACTIVE_GREENFIELD: initialized target without an existing production system;
- ACTIVE_BROWNFIELD: existing project or system being overlaid or resumed;
- BLOCKED: target safety, collision, integrity, or authority is unresolved.

For NEW_TARGET, run bootstrap.py dry-run/collision checks first. If clean,
initialize only the missing expected files at the explicit target using the
bootstrap's safe path. Never overwrite. For an uninitialized brownfield target,
produce an overlay preview first; write only when every planned path is absent
and collision checks are clean. On a collision, make no changes. Preserve every
existing path and return a per-path adoption map. Offer only these safe choices:
1. keep the existing path and adapt the Fastlane contract around it; or
2. generate the template at a separate, explicit, collision-free staging path,
   compare it, and propose an exact per-path merge for later authorization.
Never silently merge or overwrite. For ACTIVE_GREENFIELD or ACTIVE_BROWNFIELD
with a coherent bootstrap, resume it without regeneration.

After initialization or resume, verify:
- expected bootstrap files and applicable nested AGENTS.md files;
- no unresolved project placeholders outside documented examples;
- prompt-pack title/version and all canonical prompt IDs;
- Git and Python availability and whether the target is already a Git repo;
- aws-core availability, without authenticated AWS access;
- source-of-truth file coherence.

Determine lifecycle state from the current PRD revisions and derived gates,
TASKS.md, and release evidence. Route to exactly one next prompt:
- no material requirements: INTAKE-10;
- intake exists but requirements need analysis: REQ-10;
- Gate A awaits a current owner receipt: INTAKE-20;
- Gate A approved and design incomplete: DESIGN-10;
- Gate B awaits a current owner receipt: DESIGN-20;
- Gate B approved and tasks absent: TASK-10;
- one named task requested or only one task is READY: BUILD-10;
- multiple eligible tasks and autonomous execution is authorized: BUILD-20;
- authorized tasks are terminal: RELEASE-10;
- stale/conflicting state or no authorized action: STOP.

Do not write requirements, design, tasks, application code, or infrastructure.
Do not initialize or change Git, create GitHub objects, or access/mutate AWS.

Print classification, lifecycle state, target, files added or NONE, collisions
or NONE, checks, and exactly one status: READY, RESUME, or BLOCKED. Explain the
two routine human gates, that autonomous work begins only inside Gate B's
envelope, and the next three steps in plain language. Return the standard work
receipt. Only when the state-derived next prompt is INTAKE-10, end with this
prefilled command exactly:

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
writes.

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
current primary documentation needed to validate external constraints.

**Permitted writes:** PRD.md requirements-revision-controlled content plus the
Document status requirements revision and derived Gate A/Gate B states. Update
the summary and detailed analysis atomically.

**GitHub mode:** READ_ONLY only if authorized and needed for brownfield facts.

**AWS mode:** DOCS_ONLY; authenticated AWS access is not required.

**Required authorization:** Requirements analysis and declared PRD.md writes only.

**Stop conditions:** Unresolved contradiction; missing critical security/data
boundary; unverifiable outcome; requested requirement is infeasible or unsafe.

**Receipt:** Standard work receipt with proposed REQ revision.

**Next:** INTAKE-10 when blocked; otherwise INTAKE-20.

~~~text
[REQ-10]
Analyze the entire intake as one requirement set before technical design.

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

Set readiness to exactly one:
- BLOCKED;
- READY_WITH_PROPOSED_ASSUMPTIONS;
- READY_FOR_OWNER_APPROVAL.

Do not silently resolve contradictions, choose architecture, approve
assumptions, or mark Gate A accepted. If blocked, ask at most three plain
questions using the INTAKE-10 style. Otherwise prepare a concise Gate A decision
brief for INTAKE-20. Return the standard work receipt.
~~~

## INTAKE-20 — Requirements Gate A

**Preconditions:** REQ-10 produced a current requirements revision that is not
BLOCKED.

**Authoritative inputs:** Current PRD.md requirements, analysis, assumptions, and revision.

**Permitted writes:** PRD.md Gate A owner record and the matching Document
status Gate A state only after receiving an exact valid receipt. Update both
atomically.

**GitHub mode:** NONE.

**AWS mode:** NONE.

**Required authorization:** Presentation only until the human sends the exact receipt.

**Stop conditions:** BLOCKED readiness; stale or mismatched ID; placeholder
approver; altered or partial receipt; requirements change during review.

**Receipt:** Standard work receipt with WAITING_FOR_GATE_A, followed by the
copyable Gate A receipt as the final block.

**Next:** DESIGN-10 only after exact acceptance; otherwise REQ-10 or INTAKE-10.

~~~text
[INTAKE-20]
Present the current requirements for human Gate A.

Show a concise decision brief:
- requirements revision and delivery profile;
- user outcome and measurable success;
- in scope and non-goals;
- accepted-fact candidates versus proposed assumptions;
- security, data, cost, deployment, and brownfield constraints;
- unresolved risks that do not block the gate;
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
a valid receipt, record it and atomically update the detailed owner record and
Document status to APPROVED_FOR_DESIGN. Return a standard work receipt whose
Next is DESIGN-10. Before acceptance, return WAITING_FOR_GATE_A and put the
exact proposed approval receipt last.
~~~

## DESIGN-10 — Technical PRD and Construction Envelope

**Preconditions:** PRD.md contains a valid Gate A receipt for the current
requirements revision.

**Authoritative inputs:** All applicable AGENTS.md; complete PRD.md; brownfield code, tests,
IaC, config, schemas, and relevant history; current AWS primary documentation.

**Permitted writes:** PRD.md Parts III and IV, proposed construction envelope,
and matching Document status DES/AUTH/design/Gate B fields; narrowly scoped ADR
only for a consequential, hard-to-reverse decision. Update summary and detailed
records atomically.

**GitHub mode:** READ_ONLY only when authorized and needed for design facts.

**AWS mode:** DOCS_ONLY by default; authenticated READ_ONLY only when explicitly
authorized and necessary to validate an existing brownfield environment.

**Required authorization:** Design writes only. No implementation, GitHub writes, or AWS
mutation.

**Stop conditions:** Missing/invalid Gate A; requirements/design conflict;
unresolved high-impact decision; unverified AWS claim material to safety.

**Receipt:** Standard work receipt with REQ, DES, and proposed AUTH IDs.

**Next:** REQ-10 for material scope changes; otherwise DESIGN-20.

~~~text
[DESIGN-10]
Complete a build-ready technical PRD for the accepted requirements.

Create or increment a design revision such as DES-0001 and a proposed
construction authorization such as AUTH-0001. Use aws-core and current AWS
primary documentation for material AWS claims.

Complete only the design needed to build safely:
- context, boundaries, components, interfaces, and data flow;
- identity, authorization, secrets, encryption, validation, and audit behavior;
- schemas, state transitions, idempotency, concurrency, retries, and failures;
- observability, SLO-relevant signals, recovery, rollback, and teardown;
- deployment approach, environments, regional constraints, and cost drivers;
- test strategy, system properties/invariants, and acceptance traceability;
- brownfield compatibility, rollout, migration, and rollback when applicable;
- explicit decisions, alternatives, assumptions, and Well-Architected effects.

Prefer the simplest architecture satisfying the accepted requirements. In
quick-mvp, avoid VPCs, NAT Gateways, public IPv4, container platforms,
always-on compute, and provisioned databases unless a requirement demands one.

Propose a complete construction envelope with the fields defined in this pack.
GitHub writes default to branch/commit/push/pull-request only when explicitly
listed. Merge and branch deletion default to not authorized. AWS defaults to
DOCS_ONLY. A fast-dev AWS mutation envelope may be proposed only when every AWS
mutation-boundary field is complete, the environment is non-production, the
cost ceiling is explicit, and rollback/teardown is proven feasible.

Do not implement, generate tasks, approve the design, or perform GitHub/AWS
writes. Return the standard work receipt.
~~~

## DESIGN-20 — PRD and Construction Gate B

**Preconditions:** Complete, internally consistent PRD; current Gate A;
proposed DES revision and AUTH envelope.

**Authoritative inputs:** PRD.md in full, including traceability and proposed envelope.

**Permitted writes:** PRD.md Gate B owner record and the matching Document
status Gate B state only after an exact valid human receipt. Update both
atomically.

**GitHub mode:** NONE.

**AWS mode:** NONE.

**Required authorization:** Presentation only until the exact receipt is received.

**Stop conditions:** Stale Gate A; incomplete design/envelope; mismatch between
requirements, design, or IDs; placeholder approver; altered/partial receipt.

**Receipt:** Standard work receipt with WAITING_FOR_GATE_B, followed by the
copyable Gate B receipt as the final block.

**Next:** TASK-10 only after exact acceptance; otherwise DESIGN-10 or REQ-10.

~~~text
[DESIGN-20]
Review the complete PRD and proposed construction envelope for human Gate B.

Show a concise decision brief:
- REQ, DES, and AUTH IDs;
- architecture and key tradeoffs;
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
Use the proposed construction envelope above.
Approver: <name/handle>

All IDs must exactly match the proposed card. Reject extra or duplicate fields,
comments, reordered lines, partial blocks, and code fences. Silence, continued
conversation, task state, or tool access never counts. After a valid receipt,
record it and atomically update the detailed owner record and Document status to
APPROVED_FOR_CONSTRUCTION. Activate only that envelope. Return a standard work
receipt whose Next is TASK-10. Before acceptance, return WAITING_FOR_GATE_B and
put the exact proposed approval receipt last.
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
TASKS.md; VERIFY.md; RUNBOOK.md.

**Permitted writes:** TASKS.md only; no implementation.

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

For every task include:
- stable ID and outcome;
- status: BACKLOG, READY, IN_PROGRESS, BLOCKED, DONE, or SKIPPED;
- requirement/bug and design traceability;
- dependencies and safe wave;
- exact write set and external-state set;
- acceptance criteria;
- validation commands and required evidence;
- risk class and model/reasoning recommendation when useful;
- GitHub link or PENDING_SYNC;
- concise execution log.

Keep tasks thin enough to validate independently. Mark READY only when all
dependencies, inputs, and authorization are satisfied. Compute waves so tasks
share neither files nor mutable application/AWS state. Anything sharing a
manifest, lockfile, schema, stack, database, generated output, or deployment
target must be serialized unless isolation is proven.

Plan a single coordinator as the writer for shared control files such as
TASKS.md and VERIFY.md. Do not let parallel workers update them. Do not create
GitHub objects, implement code, or access AWS. Validate task graph consistency
with scripts/task_waves.py when available. Return the standard work receipt.
~~~

## BUILD-10 — Execute One Task

**Preconditions:** Named READY task; valid current AUTH; dependencies complete;
write and external-state sets are available.

**Authoritative inputs:** Applicable AGENTS.md; task-linked PRD/BUGFIX sections; task entry;
relevant code, tests, IaC, VERIFY.md, and RUNBOOK.md.

**Permitted writes:** Named task write set; serialized updates to TASKS.md and VERIFY.md;
RUNBOOK.md only when repeatable operations change.

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

Before editing, verify its READY state, dependencies, exact write set, active
REQ/DES/AUTH IDs, and external authorization. Mark it IN_PROGRESS. Inspect
before changing code and make the smallest coherent implementation.

Run the task's validation plus relevant regression, security, IaC, and failure
checks. Record observed evidence in VERIFY.md. Update RUNBOOK.md only if a
repeatable procedure changed. Mark DONE only when every acceptance criterion
and required local check passes; otherwise mark BLOCKED with the next useful
action. Leave AWS-only evidence PENDING_AWS until observed.

Perform only GitHub/AWS actions listed in the active authorization. A connected
tool does not grant permission. Stop on any common-contract condition. Return
the standard work receipt.
~~~

## BUILD-20 — Autonomous Construction Run

**Preconditions:** Valid Gate B; active AUTH explicitly permits autonomous
execution; TASKS.md graph is valid; at least one READY task.

**Authoritative inputs:** All sources required by eligible tasks.

**Permitted writes:** Eligible task write sets; coordinator-only serialized writes to
TASKS.md, VERIFY.md, RUNBOOK.md, shared manifests, lockfiles, schemas,
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

Use this loop:
1. reconcile REQ/DES/AUTH IDs and task states;
2. select only READY tasks whose dependencies are DONE;
3. form a wave only from disjoint file and external-state sets;
4. assign one owner per path and one coordinator for shared control files;
5. if isolation cannot be guaranteed, serialize;
6. mark selected tasks IN_PROGRESS before implementation;
7. implement, validate, and collect evidence;
8. have the coordinator alone update TASKS.md and VERIFY.md between waves;
9. mark tasks DONE only on observed acceptance evidence;
10. run the relevant aggregate suite before the next wave.

Workers must not edit shared control files, the same manifest/lockfile/schema,
or overlapping generated output concurrently. Do not have multiple agents push
the same branch. Keep GitHub synchronization serialized and within
authorization. Serialize every AWS mutation, even when tasks are otherwise
eligible for parallel work.

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

**Receipt:** Standard work receipt with READY or BLOCKED.

**Next:** AWS-10 when deployment is in scope; otherwise STOP.

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

Record observed evidence and return READY or BLOCKED with specific reasons.
If authorization explicitly permits finalization, perform only the named
GitHub operations after required checks pass. Never infer permission to merge,
publish a release, delete a branch, or deploy. Return the standard work receipt.
~~~

## AWS-10 — Read-Only Deployment Preflight

**Preconditions:** RELEASE-10 is READY for the intended artifact; target account,
Region, environment, and stack are named; authenticated read access is
explicitly authorized.

**Authoritative inputs:** PRD.md; VERIFY.md; RUNBOOK.md; IaC; deployment artifact; aws-core
skills/docs; read-only AWS identity, configuration, quotas, and target state.

**Permitted writes:** VERIFY.md preflight evidence only.

**GitHub mode:** NONE or authorized READ_ONLY for artifact/check identity.

**AWS mode:** DOCS_ONLY plus explicitly authorized READ_ONLY. No mutation.

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
authorization naming all mutation-boundary fields. Tool access is insufficient.

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

**Receipt:** Standard work receipt with VERIFIED, PENDING_AWS, or BLOCKED facts.

**Next:** AWS-40, an authorized AWS-20 correction, or STOP.

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
checks PENDING_AWS. Do not mutate to repair a failed check. Return the standard
work receipt.
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
authorization does not imply teardown permission.

**Stop conditions:** Resource/identity mismatch; shared or retained dependency;
unexpected data; scope expansion; protection requiring an unauthorized change;
partial failure that changes the safe order.

**Receipt:** Standard work receipt with removed, retained, failed, and
post-teardown observed resources.

**Next:** STOP, or AWS-40 for residual read-only review.

~~~text
[AWS-50]
Execute only teardown operation <TEARDOWN-AUTH-ID>.

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
