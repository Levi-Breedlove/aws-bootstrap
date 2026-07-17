# Codex Prompt Templates

These prompts support the repository's requirements → analysis → design → tasks → execution → verification workflow.

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
| Successful post-deployment evidence reconciliation | Terra | High | Switch to Sol when smoke tests, IAM, telemetry, or AWS state are unexpected |
| Failed deployment investigation | Sol | High or Extra High | Use Max for a deeply coupled production failure |

### Prompt-by-prompt recommendations

| Prompt | Recommended selection |
|---|---|
| Prompt 1 — Analyze requirements before design | Sol, Extra High |
| Prompt 2 — Complete PRD technical design | Sol, Extra High |
| Prompt 3 — Analyze an active bugfix | Terra, High; Sol High/Extra High for high-risk defects |
| Prompt 4 — Generate the task checklist and GitHub plan | Terra, High |
| Prompt 5 — Execute one task | Terra, Medium by default |
| Prompt 6 — Execute ready tasks by safe waves | Terra, High |
| Prompt 7 — End-of-day GitHub synchronization | Luna, Low or Medium |
| Prompt 8 — Release-readiness review | Sol, Extra High |
| Prompt 9 — Post-deployment evidence reconciliation | Terra, High; Sol if investigation is required |
| Prompt 10 — Educational implementation and mentoring mode | Terra High for normal work; Sol High/Extra High for architecture or high-risk work |

### Ultra mode rules for task waves

Ultra is permitted only when all of these are true:

- the work divides into meaningful independent tasks;
- task dependencies are already satisfied;
- write sets do not overlap;
- tasks do not mutate the same stack, service, database, migration, or state;
- no task requires another task's generated output;
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
Do not create additional documentation merely to explain the work.
```

## Prompt 1 — Analyze requirements before design

```text
Analyze the full requirement set in PRD.md before producing or changing technical design.

Read:
- the root and applicable nested AGENTS.md files;
- all requirements, user stories, acceptance criteria, goals, non-goals,
  security, reliability, performance, cost, sustainability, data, and
  operational constraints in PRD.md;
- relevant existing code, tests, IaC, configuration, and Git history.

Use AWS MCP and current AWS primary documentation where AWS behavior affects
feasibility, security, quotas, reliability, deployment, or cost.

Reason across the complete requirement set, not one requirement at a time.

Identify:
1. logical inconsistencies;
2. ambiguities or unmeasurable language;
3. conflicting functional and non-functional constraints;
4. unstated assumptions or undefined concepts;
5. missing edge cases and boundary behavior;
6. missing failure, retry, timeout, recovery, and concurrency behavior;
7. missing security, privacy, cost, or operational requirements;
8. requirements that cannot be verified objectively;
9. proposed properties and invariants suitable for property-based testing;
10. decisions required before design.

Update only the PRD.md Requirements Analysis Gate:
- findings;
- assumptions;
- open decisions;
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
- blocking decisions have owners or resolutions.

Read AGENTS.md, PRD.md, the existing repository, and relevant ADRs.
Use AWS MCP and current AWS primary documentation.

Complete or update:
1. architecture overview and trust boundaries;
2. component responsibilities and interfaces;
3. data model, ownership, consistency, retention, and lifecycle;
4. Mermaid sequence diagrams for primary and failure flows;
5. data-flow diagrams;
6. authentication and authorization boundaries;
7. error taxonomy, retry ownership, timeouts, safe responses, and recovery;
8. AWS service choices and tradeoffs;
9. implementation boundaries, migration, rollout, rollback, and deferred work;
10. example-based testing strategy;
11. property-based testing properties, generated domains, preconditions,
    oracles, and boundary/shrinking focus;
12. deployed AWS and operational verification needs.

Preserve the approved requirements.
If design exposes a requirements conflict, return the analysis gate to BLOCKED.
Do not create a separate design document.
Do not generate tasks until design is coherent.
Do not implement code or mutate AWS.
```

## Prompt 3 — Analyze an active bugfix

```text
Analyze the reported defect using BUGFIX.md.

Read AGENTS.md, BUGFIX.md, relevant PRD.md requirements, code, tests,
configuration, IaC, logs or evidence, and Git history.

Establish:
1. exact current behavior;
2. exact expected behavior;
3. intentionally unchanged behavior;
4. reproducible steps and environment;
5. impact and severity;
6. confirmed evidence versus hypotheses;
7. root cause only when evidence supports it;
8. allowed scope and rollback boundary;
9. example regression tests;
10. property-based regression invariants.

Update BUGFIX.md only.
Do not silently turn the bugfix into a new feature.
Do not generate tasks until expected and unchanged behavior are clear.
Do not implement code or mutate AWS.
```

## Prompt 4 — Generate executable tasks and GitHub plan

```text
Generate or update TASKS.md from the approved PRD.md design or BUGFIX.md.

Read AGENTS.md, PRD.md, BUGFIX.md when active, VERIFY.md, RUNBOOK.md,
existing TASKS.md, code, tests, IaC, and Git history.

Create discrete tasks with:
- stable TASK IDs;
- one observable outcome;
- explicit scope and non-scope;
- dependencies;
- affected write set and AWS resources;
- acceptance criteria;
- example and property-based test requirements;
- validation commands or evidence;
- rollback or cleanup implications;
- affected Well-Architected pillars;
- GitHub Issue state set to PENDING_SYNC when no issue exists.

Build a dependency graph and compute waves:
- Wave 1 has no dependencies;
- Wave N contains tasks whose dependencies are in earlier waves;
- reject cycles and missing dependencies.

Group tasks into the same wave only when they are logically independent.
Flag tasks that must be serialized because of overlapping files, shared state,
migrations, or AWS mutations.

Produce:
1. updated TASKS.md;
2. one proposed GitHub parent issue for the release;
3. one proposed native GitHub sub-issue per non-trivial task;
4. dependency, wave, priority, and evidence metadata;
5. recommended execution order.

When GitHub write access is available and the user authorizes issue creation,
create the parent and sub-issues and write their URLs back into TASKS.md.

Do not implement tasks.
Do not mutate AWS.
Do not create additional planning documents.
```

## Prompt 5 — Execute one task

```text
Execute only TASK-<ID> from TASKS.md.

Read AGENTS.md, the selected task, its dependencies, relevant PRD.md or
BUGFIX.md sections, VERIFY.md, RUNBOOK.md, code, tests, IaC, and Git history.

Before implementation:
- confirm dependencies are DONE or SKIPPED;
- confirm the task is READY;
- restate the outcome and scope;
- identify affected files and AWS resources;
- identify required example and property-based tests;
- identify security, reliability, performance, cost, rollback, and cleanup effects;
- identify whether AWS authorization is required.

Update the task to IN_PROGRESS and append a timestamped execution-log entry.

Implement only the selected task.
Provide concise real-time progress updates while working.
Update the task execution log for meaningful findings, blockers, validation,
and deviations.

Mark the task:
- BLOCKED when a material unresolved dependency prevents completion;
- DONE only when acceptance criteria and required local evidence pass.

Update VERIFY.md only with evidence actually produced.
Update RUNBOOK.md only if a repeatable procedure changed.
Link or update the GitHub Issue and pull request when access is available.

Do not execute unrelated tasks.
Do not mutate AWS without explicit authorization.
Do not mark AWS-only evidence as passed when pending.
```

## Prompt 6 — Execute all ready tasks by safe waves

```text
Execute all currently ready tasks from TASKS.md using dependency waves.

First run or reproduce:
python scripts/task_waves.py TASKS.md

Validate:
- no missing dependencies;
- no dependency cycles;
- all runtime dependencies are DONE or SKIPPED;
- tasks proposed for concurrency have disjoint write sets and no shared
  mutable AWS or application state.

Execute waves sequentially.
Within a wave, execute tasks concurrently only when safe.
Serialize tasks that edit overlapping files, modify the same stack or data
store, require migrations, share generated output, or require AWS mutation.

For every task:
- mark IN_PROGRESS at start;
- provide concise real-time progress;
- append meaningful execution-log entries;
- run task-specific validation;
- mark DONE, BLOCKED, or SKIPPED accurately;
- update VERIFY.md only with produced evidence;
- update the corresponding GitHub Issue when available.

Stop before any unauthorized AWS mutation.
Stop the affected dependency branch when a task becomes BLOCKED.
Do not create extra planning documents.
```

## Prompt 7 — End-of-day GitHub synchronization

```text
Synchronize TASKS.md with GitHub Issues for end-of-day project tracking.

Read AGENTS.md, TASKS.md, open issues, linked pull requests, and today's
validation results.

For every non-trivial task:
1. ensure a GitHub Issue exists;
2. include the stable TASK ID;
3. attach it as a native sub-issue of the release parent where supported;
4. mirror title, outcome, acceptance criteria, dependencies, wave, and status;
5. link the pull request;
6. summarize blockers and produced evidence;
7. update project fields for status, wave, priority, risk, and evidence;
8. write the Issue URL back into TASKS.md.

Do not copy full execution logs into GitHub.
Do not close an issue unless the task is DONE and acceptance criteria pass.
Do not change implementation.
Report any drift that could not be reconciled.
```

## Prompt 8 — Release-readiness review

```text
Review the repository for release readiness.

Read AGENTS.md, PRD.md, BUGFIX.md when active, TASKS.md, VERIFY.md,
RUNBOOK.md, ADRs, GitHub Issues, pull requests, code, tests, IaC, and CI.

Return:
1. exact release outcome and version;
2. requirements-analysis and design status;
3. incomplete or blocked tasks;
4. example and property-based test status;
5. six-pillar Well-Architected readiness;
6. passed local gates;
7. AWS evidence still pending;
8. release-blocking and accepted risks;
9. deployment, rollback, restore, and teardown readiness;
10. cost exposure and primary drivers;
11. decision: NOT_READY, READY_WITH_ACCEPTED_RISK, or READY.

Cite repository evidence for every claim.
Do not deploy or mutate AWS.
Do not create a separate readiness document.
```

## Prompt 9 — Post-deployment evidence reconciliation

```text
Reconcile the latest authorized deployment evidence.

Read AGENTS.md, PRD.md, TASKS.md, VERIFY.md, RUNBOOK.md, linked Issues and
pull requests, and deployment evidence from this session.

Verify:
- exact deployed commit, image, or artifact;
- AWS account and Region;
- deployment result;
- smoke tests;
- authentication and authorization checks;
- logs, metrics, alarms, and sensitive-data hygiene;
- rollback, restore, failure, and teardown evidence performed;
- budget and cost controls;
- residual risks and pending checks.

Update VERIFY.md only with observed evidence.
Update TASKS.md and GitHub Issues only where deployment evidence changes status.
Update RUNBOOK.md only when the procedure itself changed.
Return the release decision and exact remaining blockers.
```

## Prompt 10 — Educational implementation and mentoring mode

Use this prompt when you want Codex to complete real work while teaching the
architecture, AWS concepts, engineering decisions, and validation strategy.

```text
Work in educational implementation mode.

Target:
- Task: TASK-<ID>, GitHub Issue #<NUMBER>, or the explicitly stated scope.
- Model: use the model-selection guide in this file.
- AWS guidance: use the configured AWS MCP and current AWS primary documentation.

Read:
- the root and applicable nested AGENTS.md files;
- the selected TASKS.md task and linked GitHub Issue;
- the relevant PRD.md or BUGFIX.md sections;
- VERIFY.md and RUNBOOK.md where relevant;
- affected code, tests, schemas, IaC, configuration, and recent Git history.

Before implementation, provide a concise teaching brief:

1. What part of the system this task changes.
2. How the affected components currently interact.
3. Which AWS services or software patterns are involved.
4. The task's acceptance criteria and proof requirements.
5. The main security, reliability, performance, cost, and operational risks.
6. The implementation approach and why it is appropriate.
7. Important alternatives considered and why they are not preferred here.

During implementation, provide concise milestone updates. At meaningful
points, explain:

- what you inspected;
- what you discovered;
- why the finding matters;
- the relevant AWS or software-engineering concept;
- the tradeoff behind the next decision;
- what you will validate next.

Keep updates educational but focused:
- do not narrate every command or file read;
- do not expose hidden chain-of-thought;
- provide concise rationale and decision summaries;
- define unfamiliar terms when first used;
- distinguish repository facts from recommendations;
- distinguish local evidence from deployed AWS evidence;
- cite AWS primary guidance when a service behavior or recommendation matters.

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
4. Which AWS Well-Architected pillars were affected.
5. What tests or evidence prove the outcome.
6. What remains unverified or PENDING_AWS.
7. Common failure modes and how to diagnose them.
8. One or two reusable lessons for future AWS projects.
9. Relevant interview or certification takeaways when applicable.

Do not create additional educational, planning, status, architecture, or
tutorial documents unless explicitly requested. Teach through progress
updates and the final recap.
```

### Recommended model for educational mode

| Educational task | Model |
|---|---|
| Normal implementation with teaching | Terra, High |
| Architecture or requirements mentoring | Sol, High or Extra High |
| Security, IAM, concurrency, migration, or failure analysis | Sol, High |
| Mechanical walkthrough or GitHub synchronization | Luna, Medium |
| High-stakes final review with teaching | Sol, Extra High or Max |

