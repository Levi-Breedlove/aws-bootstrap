# Codex Prompt Templates

These prompts support the bootstrap repository's controlled delivery workflow:

```text
requirements
  -> requirements analysis gate
  -> technical design
  -> executable tasks and dependency waves
  -> scoped implementation
  -> local verification
  -> release-readiness review
  -> read-only AWS preflight
  -> explicitly authorized deployment
  -> deployed evidence reconciliation
  -> rollback or teardown verification
```

The repository remains the operating system for the work:

| File | Responsibility |
|---|---|
| `AGENTS.md` and nested `AGENTS.md` files | Scope, engineering rules, AWS safety, and local instructions |
| `PRD.md` | Requirements, analysis gate, architecture, decisions, and acceptance criteria |
| `BUGFIX.md` | Defect behavior, evidence, root-cause boundary, and regression contract |
| `TASKS.md` | Executable work, dependencies, waves, status, write sets, and task logs |
| `VERIFY.md` | Local and deployed evidence actually observed |
| `RUNBOOK.md` | Repeatable deployment, rollback, recovery, operations, and teardown procedures |
| GitHub Issues and pull requests | Durable coordination, review, and implementation history |

Do not replace these files with parallel planning documents unless the user explicitly requests one.

## AWS Agent Toolkit requirement — use `aws-core`

**Verified against the official Agent Toolkit for AWS documentation on July 17, 2026.**

For Codex AWS work, use the `aws-core` plugin from
[Agent Toolkit for AWS](https://aws.amazon.com/products/developer-tools/agent-toolkit-for-aws/)
as the primary AWS grounding and tool layer.

AWS documents `aws-core` as the primary Agent Toolkit plugin and recommends it
for AWS developers. It bundles:

- the AWS MCP Server configuration;
- curated, on-demand AWS skills;
- current AWS documentation access;
- regional-availability checks;
- authenticated AWS API tools;
- common guidance for service selection, CDK and CloudFormation, serverless,
  containers, databases, storage, observability, billing, SDK usage, and deployment.

The AWS MCP Server remains valid and is the tool substrate exposed by the
plugin. Prompts in this repository should name **`aws-core` first**, rather than
asking only for a generic AWS MCP integration. When `aws-core` is installed,
use the MCP tools and curated skills that it provides.

`aws-core` does not replace the bootstrap process. It supplies AWS knowledge,
skills, and controlled AWS access; `PRD.md`, `TASKS.md`, `VERIFY.md`,
`RUNBOOK.md`, Git review, and explicit authorization still govern the work.

For new Codex bootstrap work, prefer Agent Toolkit for AWS over legacy AWS Labs
MCP servers, skills, or plugins when `aws-core` covers the use case. Preserve an
existing integration only when the project intentionally depends on it.

Official references:

- [Agent Toolkit for AWS](https://aws.amazon.com/products/developer-tools/agent-toolkit-for-aws/)
- [Agent Toolkit plugins](https://docs.aws.amazon.com/agent-toolkit/latest/userguide/plugins.html)
- [AWS MCP Server tools](https://docs.aws.amazon.com/agent-toolkit/latest/userguide/understanding-mcp-server-tools.html)
- [Multi-profile support](https://docs.aws.amazon.com/agent-toolkit/latest/userguide/multi-account-access.html)

### Install `aws-core` for Codex

In a terminal:

```bash
codex plugin marketplace add aws/agent-toolkit-for-aws
codex
```

Inside Codex:

```text
/plugins
```

Browse the Agent Toolkit marketplace and install `aws-core`. Start a fresh
Codex session when the client requires a reload.

When multiple AWS profiles are required, explicitly allowlist only the profiles
that the agent may use. The first profile becomes the default:

```bash
export AWS_MCP_PROXY_PROFILES="mvp-readonly mvp-deploy"
```

Use project-specific profile names. Prefer a read-only profile first and require
explicit selection of a narrowly scoped write-capable profile.

Installation syntax and plugin contents can change. Recheck the official
Agent Toolkit documentation before changing bootstrap setup instructions.

### `aws-core` operating contract

Apply these rules to every AWS-related prompt in this file:

1. Use the installed `aws-core` plugin before relying on model memory for AWS.
2. Retrieve relevant AWS skills when a tested workflow or decision guide exists.
3. Use current AWS primary documentation for service behavior, IAM, quotas,
   networking, encryption, recovery, regional availability, pricing dimensions,
   and deployment guidance.
4. Verify the configured account, profile or role, Region, environment, stack,
   resource scope, billable impact, reversibility, and authorization boundary
   before any authenticated AWS mutation.
5. Default to documentation and read-only discovery.
6. Use the least-privileged configured AWS profile. Prefer a read-only profile
   as the default and require explicit selection of a write-capable profile.
7. Never treat a plugin, task status, issue label, or natural-language request as
   a substitute for IAM authorization.
8. Do not silently broaden IAM, weaken networking, disable encryption, reduce
   validation, or bypass logging to make a command succeed.
9. Distinguish:
   - repository facts from recommendations;
   - documentation-backed claims from assumptions;
   - local evidence from deployed AWS evidence;
   - read-only inspection from AWS mutation.
10. If `aws-core` is unavailable:
    - continue repository-only analysis when safe;
    - identify which AWS claims remain unverified;
    - do not make authenticated AWS changes;
    - report the missing plugin or tool as an explicit blocker.

### Session verification prompt

Use this before AWS-specific planning or execution when plugin availability is
uncertain:

```text
Confirm that the aws-core plugin from Agent Toolkit for AWS is installed and
available in this Codex session.

Report:
1. whether aws-core is available;
2. which AWS knowledge, skill, regional-availability, and API capabilities are
   available through it;
3. whether authenticated AWS access is configured;
4. which AWS profiles are explicitly allowlisted, without exposing credentials;
5. which profile is the default;
6. whether the current session is suitable for:
   - documentation-only planning;
   - read-only AWS discovery;
   - authorized AWS mutation.

Do not create, update, or delete AWS resources.
Do not expose credentials or secret values.
```

## Bootstrap execution rules

The prompts below preserve the bootstrap's process controls.

### Required state progression

Use evidence states that do not overclaim completion:

```text
NOT_STARTED
  -> IMPLEMENTED
  -> LOCAL_PASS
  -> PENDING_AWS
  -> VERIFIED
```

A task may be `DONE` when its task-level acceptance criteria and required local
evidence pass. AWS-only evidence remains `PENDING_AWS` until it is observed in
the authorized environment.

### AWS mutation boundary

An AWS-changing prompt must define all of the following:

```text
AWS profile or role
AWS account ID or approved alias
AWS Region
environment
stack, application, or resource boundary
approved operation
approved resource summary
expected billable impact or budget ceiling
rollback or teardown path
explicit authorization
```

Missing or conflicting values make the mutation `BLOCKED`.

### Fast MVP path

For a thin development MVP, use the prompts in this order:

```text
Prompt 1  -> analyze requirements
Prompt 2  -> complete technical design
Prompt 4  -> generate TASKS.md and waves
Prompt 5  -> execute one task at a time
Prompt 6  -> execute safe ready waves when appropriate
Prompt 8  -> run release-readiness review
Prompt 9  -> perform read-only AWS preflight
Prompt 10 -> execute only the explicitly authorized deployment
Prompt 11 -> reconcile deployed evidence
Prompt 12 -> review residual resources and teardown
Prompt 13 -> execute teardown only when explicitly authorized
```

For MVP work, keep the first release deliberately thin unless approved
requirements demand more:

```text
one primary actor
one observable outcome
one core entity or state transition
one entry point
one AWS Region
one development environment
one deployment method
three to seven measurable requirements
explicit non-goals
one rollback and teardown path
```

Avoid a VPC, NAT Gateway, public IPv4 resources, container platform,
always-on compute, or provisioned database unless an approved requirement
demands one.

## Codex model selection guide

**Verified against the official OpenAI Codex model guide on July 14, 2026.**

Model availability can change. Before starting work, use `/model` in an
interactive Codex session and confirm the current options in the official
model guide:

`https://developers.openai.com/codex/models`

### Model families

| Model | CLI name | Best use |
|---|---|---|
| GPT-5.6 Sol | `gpt-5.6-sol` | Complex, open-ended, ambiguous, high-value, security-sensitive, or highly polished work |
| GPT-5.6 Terra | `gpt-5.6-terra` | Everyday implementation requiring strong reasoning and tool use |
| GPT-5.6 Luna | `gpt-5.6-luna` | Clear, repeatable, high-volume, mechanical, extraction, transformation, and synchronization work |

A useful operating rule:

```text
Think and review with Sol.
Build with Terra.
Synchronize and maintain with Luna.
```

### Reasoning levels

| Level | Use |
|---|---|
| Light in the app / Low in the CLI | Quick, narrowly scoped work |
| Medium | Everyday planning and implementation |
| High | Difficult work with multiple steps |
| Extra High | Complex work involving multiple sources, constraints, or tradeoffs |
| Max | The hardest single coherent problem when depth matters more than speed |
| Ultra | Complex work that divides into meaningful independent parts handled by subagents |

Use the lowest reasoning level that reliably produces the required result.
Higher reasoning takes longer and uses more tokens.

**Max and Ultra are not default choices.** Max deepens one coherent task.
Ultra delegates separate parts to subagents. Most tasks do not need either.

### Workflow model matrix

| Workflow activity | Recommended model | Reasoning | Escalate when |
|---|---|---|---|
| Repository inspection | Sol | High | Use Extra High for a large brownfield system |
| Requirements analysis | Sol | Extra High | Use Max for regulated, financial, healthcare, identity, or high-loss-risk systems |
| Technical architecture and PRD design | Sol | Extra High | Use Max for difficult cross-account, networking, migration, or consistency decisions |
| Property and invariant design | Sol | High | Use Extra High for authorization, concurrency, state machines, or regulated calculations |
| Normal bug analysis | Terra | High | Switch to Sol for security, data corruption, race conditions, distributed events, or migration defects |
| Generate `TASKS.md` and waves | Terra | High | Switch to Sol only when the design remains materially ambiguous |
| Execute one normal task | Terra | Medium | Use Terra High for multi-file or non-trivial AWS integration work |
| IAM, authorization, encryption, migration, concurrency, or destructive task | Sol | High | Use Extra High when several high-risk constraints interact |
| Execute a safe implementation wave | Terra | High | Use Ultra only for genuinely independent work with disjoint write sets and no shared AWS state |
| Implement already-defined property tests | Terra | Medium or High | Use Sol if the property or oracle remains unclear |
| Mechanical test expansion or formatting | Luna | Medium | Switch to Terra when judgment is required |
| End-of-day GitHub synchronization | Luna | Low or Medium | Use Terra Medium when task and issue state conflict |
| Release-readiness review | Sol | Extra High | Use Max for a high-stakes production decision |
| Read-only AWS preflight | Terra | High | Use Sol for cross-account, networking, migration, or high-risk security boundaries |
| Authorized development deployment | Terra | High | Use Sol for production, destructive, migration, or security-sensitive deployment |
| Successful post-deployment reconciliation | Terra | High | Switch to Sol when smoke tests, IAM, telemetry, cost, or AWS state are unexpected |
| Residual-resource and teardown review | Sol | High | Use Extra High for retained data, backups, shared resources, or production |
| Authorized teardown | Sol | High | Use Extra High when deletion affects shared, retained, regulated, or production data |
| Failed deployment investigation | Sol | High or Extra High | Use Max for a deeply coupled production failure |

### Prompt-by-prompt recommendations

| Prompt | Recommended selection |
|---|---|
| Prompt 1 — Analyze requirements before design | Sol, Extra High |
| Prompt 2 — Complete PRD technical design | Sol, Extra High |
| Prompt 3 — Analyze an active bugfix | Terra, High; Sol High or Extra High for high-risk defects |
| Prompt 4 — Generate executable tasks and GitHub plan | Terra, High |
| Prompt 5 — Execute one task | Terra, Medium by default |
| Prompt 6 — Execute ready tasks by safe waves | Terra, High |
| Prompt 7 — End-of-day GitHub synchronization | Luna, Low or Medium |
| Prompt 8 — Release-readiness review | Sol, Extra High |
| Prompt 9 — Read-only AWS pre-deployment preflight | Terra, High |
| Prompt 10 — Execute an explicitly authorized AWS deployment | Terra, High; Sol for high-risk deployment |
| Prompt 11 — Post-deployment evidence reconciliation | Terra, High; Sol when investigation is required |
| Prompt 12 — Read-only residual-resource and teardown review | Sol, High |
| Prompt 13 — Execute an explicitly authorized teardown | Sol, High or Extra High |
| Prompt 14 — Educational implementation and mentoring mode | Terra High for normal work; Sol High or Extra High for architecture or high-risk work |

### Ultra mode rules for task waves

Ultra is permitted only when all of these are true:

- the work divides into meaningful independent tasks;
- task dependencies are already satisfied;
- write sets do not overlap;
- tasks do not mutate the same stack, service, database, migration, or state;
- no task requires another task's generated output;
- no concurrent task requires an AWS mutation;
- the lead agent will reconcile all outputs and rerun repository-wide validation.

Do not use Ultra merely because several tasks appear in the same wave.
Dependency eligibility does not prove concurrency safety.

### Interactive and CLI selection

In an interactive Codex session:

```text
/model
```

Launch Codex with a model:

```bash
codex -m gpt-5.6-sol
codex -m gpt-5.6-terra
codex -m gpt-5.6-luna
```

Non-interactive examples:

```bash
codex exec -m gpt-5.6-sol \
  "Analyze the requirements in PRD.md before design."

codex exec -m gpt-5.6-terra \
  "Execute TASK-003 from TASKS.md."

codex exec -m gpt-5.6-luna \
  "Synchronize TASKS.md with GitHub Issues."
```

## Reusable prompt add-ons

### Instructional streaming add-on

Add this block to any prompt when you want to learn from the work:

```text
As you work, provide concise instructional progress updates explaining:

- what you inspected;
- what you discovered;
- why it matters;
- which AWS or engineering tradeoff is involved;
- what you will verify next.

Keep these updates educational.
Do not narrate every command.
Do not expose hidden chain-of-thought.
Do not create additional documentation merely to explain the work.
```

### MVP constraint add-on

Add this block to Prompts 1, 2, or 4 for a thin MVP:

```text
MVP constraints:

- Development environment only.
- Primary actor: [ACTOR].
- Primary observable outcome: [OUTCOME].
- AWS Region: [REGION].
- Monthly budget ceiling: [BUDGET].
- Authentication requirement: [REQUIREMENT].
- Core data entity and access pattern: [DATA].
- Hard security, retention, latency, compliance, or networking constraints:
  [CONSTRAINTS].
- Explicit non-goals: [NON-GOALS].

Keep the release to one deployable vertical slice.
Prefer managed services, low idle cost, minimal operational burden, repeatable
deployment, and complete teardown.
Do not add a VPC, NAT Gateway, public IPv4 resources, container platform, or
always-on database unless an approved requirement demands one.
```

## Prompt 1 — Analyze requirements before design

```text
Analyze the full requirement set in PRD.md before producing or changing
technical design.

Read:
- the root and applicable nested AGENTS.md files;
- all requirements, user stories, acceptance criteria, goals, non-goals,
  security, reliability, performance, cost, sustainability, data, and
  operational constraints in PRD.md;
- relevant existing code, tests, IaC, configuration, ADRs, and Git history.

Use the installed aws-core plugin from Agent Toolkit for AWS.

Through aws-core:
- retrieve relevant AWS skills when available;
- use current AWS primary documentation where AWS behavior affects feasibility,
  security, IAM, quotas, reliability, regional availability, deployment, or cost;
- verify material AWS claims rather than relying on model memory;
- use documentation and read-only capabilities only;
- do not create, update, or delete AWS resources.

Reason across the complete requirement set, not one requirement at a time.

Identify:
1. logical inconsistencies;
2. ambiguities or unmeasurable language;
3. conflicting functional and non-functional constraints;
4. unstated assumptions or undefined concepts;
5. missing edge cases and boundary behavior;
6. missing failure, retry, timeout, idempotency, recovery, and concurrency behavior;
7. missing authentication, authorization, privacy, cost, or operational requirements;
8. missing data ownership, consistency, retention, deletion, or restore behavior;
9. requirements that cannot be verified objectively;
10. proposed properties and invariants suitable for property-based testing;
11. decisions required before design;
12. AWS-specific assumptions that remain unverified.

Update only the PRD.md Requirements Analysis Gate:
- findings;
- assumptions;
- open decisions and owners;
- evidence or AWS references used;
- analysis outcome.

Set the outcome to exactly one:
- BLOCKED
- READY_WITH_ACCEPTED_ASSUMPTIONS
- READY_FOR_DESIGN

Do not create DESIGN.md.
Do not generate TASKS.md yet.
Do not implement code.
Do not mutate AWS.
Do not silently resolve material conflicts.
```

## Prompt 2 — Complete PRD technical design

```text
Complete the technical architecture and implementation approach in PRD.md.

Preconditions:
- requirements analysis is READY_FOR_DESIGN or
  READY_WITH_ACCEPTED_ASSUMPTIONS;
- blocking decisions have owners or resolutions;
- accepted assumptions are explicit and testable.

Read:
- the root and applicable nested AGENTS.md files;
- PRD.md;
- existing code, tests, schemas, IaC, configuration, and relevant Git history;
- applicable ADRs and organizational standards.

Use the installed aws-core plugin from Agent Toolkit for AWS.

Through aws-core:
- retrieve relevant service-selection, IaC, serverless, container, database,
  storage, observability, billing, SDK, security, and deployment skills as needed;
- verify current service and feature behavior;
- verify regional availability for the target Region;
- verify material quotas, integration constraints, IAM boundaries, encryption,
  recovery behavior, and pricing dimensions;
- use current AWS primary documentation;
- use documentation and read-only capabilities only;
- do not mutate AWS.

Complete or update:
1. architecture overview and explicit trust boundaries;
2. component responsibilities and interfaces;
3. primary request, event, and failure flows;
4. Mermaid sequence diagrams for primary and failure flows;
5. data-flow diagrams, sensitive-data paths, and egress;
6. data model, ownership, access patterns, consistency, retention, deletion,
   backup, restore, and lifecycle;
7. authentication, authorization, tenancy, and least-privilege boundaries;
8. validation, error taxonomy, retry ownership, timeouts, idempotency,
   backpressure, safe responses, and recovery;
9. AWS service choices, rejected alternatives, and requirement-backed tradeoffs;
10. infrastructure-as-code approach that respects existing project standards;
11. observability, alarms, auditability, and sensitive-data hygiene;
12. primary cost drivers, idle-cost exposure, and budget controls;
13. implementation boundaries, migration, rollout, rollback, teardown,
    and explicitly deferred work;
14. example-based testing strategy;
15. property-based testing properties, generated domains, preconditions,
    oracles, and boundary or shrinking focus;
16. local, deployed AWS, operational, rollback, restore, and teardown evidence
    required for acceptance.

Optimize for the smallest coherent architecture that satisfies the approved
requirements. Prefer managed services, low idle cost, minimal operational
burden, repeatable deployment, and reversibility.

Do not introduce a VPC, NAT Gateway, public IPv4 resources, container platform,
or always-on database unless an approved requirement demands one.

Preserve the approved requirements.
If design exposes a requirements conflict, return the analysis gate to BLOCKED.
Do not create a separate design document.
Do not generate tasks until design is coherent.
Do not implement code.
Do not mutate AWS.
```

## Prompt 3 — Analyze an active bugfix

```text
Analyze the reported defect using BUGFIX.md.

Read:
- the root and applicable nested AGENTS.md files;
- BUGFIX.md and relevant PRD.md requirements;
- affected code, tests, schemas, configuration, IaC, logs, deployment evidence,
  and Git history.

Use the installed aws-core plugin from Agent Toolkit for AWS when AWS service
behavior, IAM, quotas, logs, metrics, deployment state, or regional behavior is
material to the defect.

Through aws-core:
- retrieve relevant troubleshooting or service skills;
- use current AWS primary documentation;
- use authenticated AWS inspection only when read-only access is configured and
  the requested environment is explicitly in scope;
- distinguish observed AWS evidence from hypotheses;
- do not mutate AWS.

Establish:
1. exact current behavior;
2. exact expected behavior;
3. intentionally unchanged behavior;
4. reproducible steps and environment;
5. impact, severity, blast radius, and data exposure;
6. confirmed evidence versus hypotheses;
7. root cause only when evidence supports it;
8. allowed scope and rollback boundary;
9. example regression tests;
10. property-based regression invariants;
11. observability needed to prove the fix;
12. AWS evidence that remains pending.

Update BUGFIX.md only.
Do not silently turn the bugfix into a new feature.
Do not generate tasks until expected and unchanged behavior are clear.
Do not implement code.
Do not mutate AWS.
```

## Prompt 4 — Generate executable tasks and GitHub plan

```text
Generate or update TASKS.md from the approved PRD.md design or BUGFIX.md.

Read:
- the root and applicable nested AGENTS.md files;
- PRD.md;
- BUGFIX.md when active;
- VERIFY.md and RUNBOOK.md;
- existing TASKS.md;
- code, tests, schemas, IaC, configuration, and Git history.

Use the installed aws-core plugin from Agent Toolkit for AWS when current AWS
service, IaC, deployment, quota, observability, cost, or verification behavior
affects task decomposition.

Use aws-core for skills and current AWS primary documentation only.
Do not mutate AWS.

Create discrete tasks with:
- a stable TASK ID;
- one observable outcome;
- explicit scope and non-scope;
- dependencies;
- exact affected write set;
- affected AWS resources;
- AWS access mode: NONE, DOCUMENTATION_ONLY, READ_ONLY, or MUTATING;
- the authorization boundary required for any MUTATING task;
- objective acceptance criteria;
- example-based and property-based test requirements;
- exact local validation commands;
- deployed evidence requirements;
- evidence state expectations;
- rollback, cleanup, and teardown implications;
- affected Well-Architected pillars;
- GitHub Issue state set to PENDING_SYNC when no issue exists.

For an MVP, create no more than seven non-trivial tasks unless a security,
migration, deployment, or teardown dependency requires additional separation.

Build a dependency graph and compute waves:
- Wave 1 has no dependencies;
- Wave N contains tasks whose dependencies are in earlier waves;
- reject cycles and missing dependencies.

Run or reproduce:

python3 scripts/task_waves.py TASKS.md

Group tasks into the same wave only when they are logically independent.
Flag tasks that must be serialized because of overlapping files, shared state,
generated outputs, migrations, or AWS mutations.
Never schedule concurrent AWS mutations merely because tasks share a wave.

Produce:
1. updated TASKS.md;
2. one proposed GitHub parent issue for the release;
3. one proposed native GitHub sub-issue per non-trivial task;
4. dependency, wave, priority, risk, AWS access mode, and evidence metadata;
5. recommended execution order;
6. an explicit list of tasks that can stop at LOCAL_PASS;
7. an explicit list of tasks that require PENDING_AWS and later verification.

When GitHub write access is available and the user authorizes issue creation,
create the parent and sub-issues and write their URLs back into TASKS.md.

Do not implement tasks.
Do not mutate AWS.
Do not create additional planning documents.
```

## Prompt 5 — Execute one task

```text
Execute only TASK-<ID> from TASKS.md.

Read:
- the root and applicable nested AGENTS.md files;
- the selected task and its dependencies;
- relevant PRD.md or BUGFIX.md sections;
- VERIFY.md and RUNBOOK.md;
- affected code, tests, schemas, IaC, configuration, and Git history.

Use the installed aws-core plugin from Agent Toolkit for AWS for current
AWS-specific implementation guidance.

Through aws-core:
- retrieve relevant skills;
- verify current service, SDK, IaC, IAM, deployment, quota, and regional behavior;
- use current AWS primary documentation;
- default to documentation and read-only discovery;
- do not mutate AWS unless this exact task has an explicit authorization
  envelope covering the requested operation.

Before implementation:
- confirm dependencies are DONE or SKIPPED;
- confirm the task is READY;
- restate the observable outcome, scope, and non-scope;
- identify the exact write set and affected AWS resources;
- identify required example and property-based tests;
- identify security, reliability, performance, cost, rollback, and cleanup effects;
- identify the task's AWS access mode;
- identify the local validation commands;
- identify which evidence can be produced locally and which remains PENDING_AWS.

Update the task to IN_PROGRESS and append a timestamped execution-log entry.

Implement only the selected task.
Provide concise milestone progress updates while working.
Update the task execution log for meaningful findings, blockers, validation,
and deviations.

Run the task-specific local validation.
Review generated IaC diff, plan, synth, or change set where applicable.

Mark the task:
- BLOCKED when a material unresolved dependency prevents completion;
- DONE only when acceptance criteria and required local evidence pass.

When local work passes but AWS evidence is still required:
- record LOCAL_PASS;
- leave AWS-only checks as PENDING_AWS;
- document the exact read-only preflight or mutation authorization still needed;
- do not claim deployed verification.

Update VERIFY.md only with evidence actually produced.
Update RUNBOOK.md only if a repeatable procedure changed.
Link or update the GitHub Issue and pull request when access is available.

Do not execute unrelated tasks.
Do not broaden task scope to fix adjacent issues.
Do not mutate AWS without explicit authorization.
Do not mark AWS-only evidence as passed when pending.
```

## Prompt 6 — Execute all ready tasks by safe waves

```text
Execute all currently ready tasks from TASKS.md using dependency waves.

Read the root and applicable nested AGENTS.md files, PRD.md, BUGFIX.md when
active, TASKS.md, VERIFY.md, RUNBOOK.md, code, tests, IaC, and Git history.

Use the installed aws-core plugin from Agent Toolkit for AWS for current
AWS-specific skills and primary documentation. Default to documentation and
read-only discovery. Do not perform an AWS mutation unless the exact task and
operation have an explicit authorization envelope.

First run or reproduce:

python3 scripts/task_waves.py TASKS.md

Validate:
- no missing dependencies;
- no dependency cycles;
- all runtime dependencies are DONE or SKIPPED;
- tasks proposed for concurrency have disjoint write sets;
- tasks proposed for concurrency share no mutable AWS or application state;
- no concurrent task requires another task's generated output;
- no concurrent task performs an AWS mutation.

Execute waves sequentially.
Within a wave, execute tasks concurrently only when safe.
Serialize tasks that edit overlapping files, modify the same stack or data
store, require migrations, share generated output, or require AWS mutation.

For every task:
- confirm the task is READY;
- mark IN_PROGRESS at start;
- provide concise milestone progress;
- append meaningful execution-log entries;
- run task-specific validation;
- mark DONE, BLOCKED, or SKIPPED accurately;
- record LOCAL_PASS and PENDING_AWS separately where applicable;
- update VERIFY.md only with produced evidence;
- update RUNBOOK.md only when a repeatable procedure changes;
- update the corresponding GitHub Issue when available.

After each wave:
- reconcile task status;
- rerun relevant repository-wide validation;
- report blockers and newly ready tasks;
- stop any dependency branch whose prerequisite became BLOCKED.

Stop before any unauthorized AWS mutation.
Do not create extra planning documents.
```

## Prompt 7 — End-of-day GitHub synchronization

```text
Synchronize TASKS.md with GitHub Issues for end-of-day project tracking.

Read:
- the root AGENTS.md;
- TASKS.md;
- open issues;
- linked pull requests;
- today's task logs and validation results.

For every non-trivial task:
1. ensure a GitHub Issue exists;
2. include the stable TASK ID;
3. attach it as a native sub-issue of the release parent where supported;
4. mirror title, outcome, acceptance criteria, dependencies, wave, and status;
5. mirror AWS access mode and authorization requirement;
6. link the pull request;
7. summarize blockers and produced evidence;
8. distinguish LOCAL_PASS, PENDING_AWS, and VERIFIED;
9. update project fields for status, wave, priority, risk, and evidence;
10. write the Issue URL back into TASKS.md.

Do not copy full execution logs into GitHub.
Do not close an issue unless the task is DONE and its required acceptance
criteria pass.
Do not mark an issue VERIFIED from local evidence alone.
Do not change implementation.
Do not mutate AWS.
Report any drift that could not be reconciled.
```

## Prompt 8 — Release-readiness review

```text
Review the repository for release readiness.

Read:
- the root and applicable nested AGENTS.md files;
- PRD.md;
- BUGFIX.md when active;
- TASKS.md;
- VERIFY.md;
- RUNBOOK.md;
- ADRs;
- GitHub Issues and pull requests;
- code, tests, schemas, IaC, configuration, and CI evidence.

Use the installed aws-core plugin from Agent Toolkit for AWS.

Through aws-core:
- retrieve relevant deployment, security, observability, cost, reliability,
  and IaC skills;
- use current AWS primary documentation;
- use read-only AWS inspection only when a read-only profile and target
  environment are explicitly configured;
- verify current service, Region, quota, IAM, recovery, and deployment assumptions;
- do not mutate AWS.

Return:
1. exact release outcome, environment, and version or commit;
2. requirements-analysis and design status;
3. incomplete, blocked, skipped, or scope-drifted tasks;
4. example and property-based test status;
5. six-pillar Well-Architected readiness;
6. passed local gates;
7. AWS evidence still pending;
8. release-blocking and accepted risks;
9. deployment artifact, diff, plan, synth, or change-set readiness;
10. authorization, rollback, restore, and teardown readiness;
11. cost exposure, primary drivers, and budget controls;
12. aws-core findings or AWS claims that remain unverified;
13. decision: NOT_READY, READY_WITH_ACCEPTED_RISK, or READY.

Cite repository evidence for every claim.
Do not deploy.
Do not mutate AWS.
Do not create a separate readiness document.
```

## Prompt 9 — Read-only AWS pre-deployment preflight

```text
Perform the read-only AWS pre-deployment preflight for TASK-<ID>.

Use the installed aws-core plugin from Agent Toolkit for AWS.

Target:
- AWS profile: [READ_ONLY_PROFILE]
- AWS account ID or approved alias: [ACCOUNT]
- AWS Region: [REGION]
- Environment: [ENVIRONMENT]
- Stack or application boundary: [STACK]
- Reviewed commit or artifact: [COMMIT_OR_ARTIFACT]
- Maximum expected recurring cost: [BUDGET]
- Approved resource summary: [RESOURCE_SUMMARY]

Preconditions:
- the task is LOCAL_PASS or otherwise ready for AWS preflight;
- local validation passes;
- the IaC diff, plan, synth, or change set exists;
- rollback and teardown procedures are documented;
- all placeholders above are resolved.

Before any other AWS call:
1. select the explicitly named read-only profile;
2. retrieve caller identity;
3. verify the account and Region exactly match the target;
4. stop on any mismatch.

Through aws-core, use current AWS skills, primary documentation, regional
availability, and read-only API inspection to verify:
- relevant service and feature availability in the target Region;
- naming and stack collisions;
- existing stack or resource state;
- service quotas and practical headroom;
- required deployment permissions without changing IAM;
- encryption, logging, observability, retention, and backup assumptions;
- current cost exposure and likely recurring cost drivers;
- retained-resource behavior;
- rollback, restore, and teardown readiness;
- every resource the reviewed artifact would create, update, replace, retain,
  or delete.

Return:
1. verified caller identity, account, Region, environment, and stack boundary;
2. current state and detected collisions;
3. quota, permission, security, reliability, and cost findings;
4. reviewed resource-change summary;
5. rollback and teardown readiness;
6. blockers and unresolved assumptions;
7. decision: PREFLIGHT_BLOCKED or READY_FOR_AUTHORIZATION.

Update VERIFY.md only with read-only evidence actually observed.
Update TASKS.md only when the preflight changes task status or blockers.

Do not create, update, replace, delete, deploy, or mutate AWS resources.
Do not broaden IAM.
Do not continue after an identity, Region, environment, stack, artifact, or
resource-scope mismatch.
```

## Prompt 10 — Execute an explicitly authorized AWS deployment

```text
Execute the AWS deployment for TASK-<ID> only within this authorization
envelope.

Use the installed aws-core plugin from Agent Toolkit for AWS.

Authorization envelope:
- Write-capable AWS profile: [DEPLOY_PROFILE]
- AWS account ID or approved alias: [ACCOUNT]
- AWS Region: [REGION]
- Environment: [ENVIRONMENT]
- Stack or application boundary: [STACK]
- Reviewed commit or immutable artifact: [COMMIT_OR_ARTIFACT]
- Approved operation: [DEPLOY_OR_UPDATE]
- Approved resource summary: [RESOURCE_SUMMARY]
- Maximum expected recurring cost: [BUDGET]
- Explicitly prohibited operations: [PROHIBITED]
- Rollback command or procedure: [ROLLBACK]
- Teardown command or procedure: [TEARDOWN]
- Authorization granted by: [AUTHORIZER]
- Authorization reference or timestamp: [REFERENCE]

Preconditions:
- Prompt 9 returned READY_FOR_AUTHORIZATION;
- every placeholder above is resolved;
- the authorization covers this exact account, Region, environment, stack,
  artifact, operation, resource set, and cost boundary;
- the reviewed IaC diff, plan, synth, or change set has not changed.

Before deployment:
1. select the explicitly named write-capable profile;
2. retrieve caller identity;
3. verify the account and Region exactly match the authorization;
4. verify the artifact or commit exactly matches the reviewed version;
5. regenerate or recheck the infrastructure change summary;
6. stop if the proposed changes exceed the authorization envelope.

Deploy only the reviewed artifact and approved resources.
Use the repository's approved IaC and deployment procedure. Do not bypass the
reviewed IaC by creating or changing resources ad hoc through AWS API calls
unless the approved design and authorization envelope explicitly require it.

After deployment:
1. record the exact commit, artifact, deployment ID, and stack identifier;
2. run health and primary-flow smoke tests;
3. run at least one relevant negative validation or authorization test;
4. confirm required logs exist and contain no prohibited sensitive values;
5. confirm required metrics and alarms exist;
6. inspect deployment events and unexpected replacements;
7. report unexpected resources, retained resources, or cost exposure;
8. execute rollback only when the authorization envelope or runbook permits it;
9. update VERIFY.md only with observed evidence;
10. update TASKS.md and the linked GitHub Issue only where evidence changes status;
11. leave unresolved checks as PENDING_AWS, FAILED, or accepted risk.

Stop rather than broadening IAM when access is denied.
Stop rather than changing architecture during deployment.
Do not mutate resources outside the authorization envelope.
Do not deploy to another account, Region, environment, or stack.
Do not rotate secrets, delete data, or weaken controls unless explicitly
included in the authorization envelope.
```

## Prompt 11 — Post-deployment evidence reconciliation

```text
Reconcile the latest authorized deployment evidence.

Read:
- the root and applicable nested AGENTS.md files;
- PRD.md;
- TASKS.md;
- VERIFY.md;
- RUNBOOK.md;
- linked GitHub Issues and pull requests;
- the reviewed commit or artifact;
- deployment output and evidence from this session.

Use the installed aws-core plugin from Agent Toolkit for AWS.

Use the explicitly configured read-only profile unless a narrowly scoped
follow-up mutation is separately authorized.

Through aws-core, verify:
- caller identity, AWS account, Region, environment, and stack;
- exact deployed commit, image, or artifact;
- deployment result and stack events;
- primary-flow smoke tests;
- negative validation and authentication or authorization checks;
- logs, metrics, alarms, traces, and sensitive-data hygiene;
- backup, restore, rollback, failure, and teardown evidence performed;
- budget controls, recurring cost drivers, and unexpected billable resources;
- retained resources and residual risks;
- checks still pending.

Update VERIFY.md only with observed evidence.
Update TASKS.md and GitHub Issues only where deployment evidence changes status.
Update RUNBOOK.md only when the repeatable procedure itself changed.

Return:
1. exact deployment identity and artifact;
2. evidence produced;
3. failed or missing evidence;
4. unexpected AWS state;
5. remaining PENDING_AWS checks;
6. release decision and exact blockers.

Do not create, update, or delete AWS resources.
Do not repair deployment drift during reconciliation.
Create a separate scoped task for any required fix.
```

## Prompt 12 — Read-only residual-resource and teardown review

```text
Perform a read-only residual-resource, retention, billing, and teardown review
for the deployed stack.

Use the installed aws-core plugin from Agent Toolkit for AWS.

Target:
- Read-only AWS profile: [READ_ONLY_PROFILE]
- AWS account ID or approved alias: [ACCOUNT]
- AWS Region: [REGION]
- Environment: [ENVIRONMENT]
- Stack or application boundary: [STACK]
- Reviewed teardown procedure: [RUNBOOK_SECTION]
- Resources approved for deletion: [DELETE_SCOPE]
- Resources approved for retention: [RETAIN_SCOPE]

Before any other AWS call:
1. select the explicitly named read-only profile;
2. retrieve caller identity;
3. verify the account and Region exactly match the target;
4. stop on any mismatch.

Through aws-core, inspect:
- resources owned by the stack;
- resources referenced by but not owned by the stack;
- resources deleted automatically with the stack;
- retained S3 buckets, objects, DynamoDB tables, backups, snapshots, log groups,
  secrets, parameters, ECR images, ENIs, alarms, dashboards, and DNS records;
- deletion protection, retention policies, and removal policies;
- shared or cross-stack dependencies;
- data-loss and recovery implications;
- delayed or residual billing;
- exact teardown order;
- post-teardown residual checks.

Return:
1. verified identity and target;
2. complete delete, retain, and shared-resource inventory;
3. data-loss, recovery, dependency, and cost risks;
4. exact proposed teardown commands or procedure;
5. exact post-teardown verification plan;
6. blockers and unresolved ownership;
7. decision: TEARDOWN_BLOCKED or READY_FOR_TEARDOWN_AUTHORIZATION.

Update VERIFY.md only with read-only evidence actually observed.
Update RUNBOOK.md only when the repeatable teardown procedure needs correction.

Do not delete, detach, update, replace, or mutate AWS resources.
Do not infer ownership from naming alone.
```

## Prompt 13 — Execute an explicitly authorized teardown

```text
Execute teardown only within this authorization envelope.

Use the installed aws-core plugin from Agent Toolkit for AWS.

Authorization envelope:
- Write-capable AWS profile: [TEARDOWN_PROFILE]
- AWS account ID or approved alias: [ACCOUNT]
- AWS Region: [REGION]
- Environment: [ENVIRONMENT]
- Stack or application boundary: [STACK]
- Approved deletion scope: [DELETE_SCOPE]
- Approved retention scope: [RETAIN_SCOPE]
- Approved data-loss consequence: [DATA_LOSS]
- Expected residual resources: [EXPECTED_RESIDUALS]
- Expected billing after teardown: [EXPECTED_BILLING]
- Authorization granted by: [AUTHORIZER]
- Authorization reference or timestamp: [REFERENCE]

Preconditions:
- Prompt 12 returned READY_FOR_TEARDOWN_AUTHORIZATION;
- every placeholder above is resolved;
- ownership of every deletion target is verified;
- backup or restore requirements are satisfied;
- the teardown procedure matches RUNBOOK.md;
- the authorization covers this exact account, Region, environment, stack,
  resource set, and data-loss boundary.

Before teardown:
1. select the explicitly named write-capable profile;
2. retrieve caller identity;
3. verify the account and Region exactly match the authorization;
4. re-run the delete, retain, and shared-resource inventory;
5. stop if scope or ownership changed.

Delete only the explicitly approved resources and stack boundary.

After teardown, use read-only inspection to:
1. verify stack deletion status;
2. inventory expected and unexpected residual resources;
3. verify retained data and backups remain intact;
4. verify alarms, dashboards, log groups, ENIs, images, secrets, parameters,
   buckets, tables, snapshots, and DNS records against the approved plan;
5. record delayed billing or cost records that may remain;
6. update VERIFY.md with observed evidence;
7. update TASKS.md and linked GitHub Issues where status changes;
8. update RUNBOOK.md only when the repeatable procedure changed.

Stop rather than broadening IAM when deletion is denied.
Do not force-delete shared or unverified resources.
Do not delete resources outside the authorization envelope.
Do not claim zero residual cost until billing evidence supports it.
```

## Prompt 14 — Educational implementation and mentoring mode

Use this prompt when you want Codex to complete real work while teaching the
architecture, AWS concepts, bootstrap controls, engineering decisions, and
validation strategy.

```text
Work in educational implementation mode.

Target:
- Task: TASK-<ID>, GitHub Issue #<NUMBER>, or the explicitly stated scope.
- Model: use the model-selection guide in this file.
- AWS integration: use the installed aws-core plugin from Agent Toolkit for AWS.

Read:
- the root and applicable nested AGENTS.md files;
- the selected TASKS.md task and linked GitHub Issue;
- the relevant PRD.md or BUGFIX.md sections;
- VERIFY.md and RUNBOOK.md where relevant;
- affected code, tests, schemas, IaC, configuration, and recent Git history.

Use aws-core to retrieve relevant AWS skills and current AWS primary
documentation. Use read-only AWS inspection only when the target environment
and read-only profile are explicitly in scope. Do not perform an AWS mutation
without the exact authorization envelope required by this repository.

Before implementation, provide a concise teaching brief:

1. What part of the system this task changes.
2. Where the task sits in the bootstrap workflow.
3. How the affected components currently interact.
4. Which AWS services or software patterns are involved.
5. The task's acceptance criteria and proof requirements.
6. The main security, reliability, performance, cost, and operational risks.
7. The implementation approach and why it is appropriate.
8. Important alternatives considered and why they are not preferred here.
9. Which evidence can be produced locally and which remains PENDING_AWS.

During implementation, provide concise milestone updates. At meaningful
points, explain:

- what you inspected;
- what you discovered;
- why the finding matters;
- the relevant AWS or software-engineering concept;
- the tradeoff behind the next decision;
- how aws-core or AWS primary documentation informed the decision;
- what you will validate next.

Keep updates educational but focused:
- do not narrate every command or file read;
- do not expose hidden chain-of-thought;
- provide concise rationale and decision summaries;
- define unfamiliar terms when first used;
- distinguish repository facts from recommendations;
- distinguish local evidence from deployed AWS evidence;
- cite AWS primary guidance when service behavior or a recommendation matters.

While working:
- mark the selected task IN_PROGRESS before implementation;
- stay within the selected task or issue;
- implement code, tests, IaC, and safe failure handling together where applicable;
- include required example-based and property-based tests;
- update TASKS.md with meaningful progress, blockers, and validation;
- update VERIFY.md only with evidence actually produced;
- update RUNBOOK.md only when a repeatable procedure changes;
- update the linked GitHub Issue and pull request when access is available;
- stop before any unauthorized AWS mutation.

At completion, provide a learning recap with:

1. What changed.
2. How the final design or implementation works.
3. Why the chosen approach fits the requirements.
4. Which bootstrap stage and files were updated.
5. Which AWS Well-Architected pillars were affected.
6. What tests or evidence prove the outcome.
7. What remains unverified or PENDING_AWS.
8. Common failure modes and how to diagnose them.
9. One or two reusable lessons for future AWS projects.
10. Relevant interview or certification takeaways when applicable.

Do not create additional educational, planning, status, architecture, or
tutorial documents unless explicitly requested. Teach through progress
updates and the final recap.
```
