# AWS Codex Fastlane Workflow

Fastlane turns an idea into owner-approved requirements, an AWS-reviewed design,
and a build constrained by an explicit construction boundary. It has two
routine business decision gates; setup and AWS mutation authorization are
separate safety checkpoints, not extra lifecycle gates.

## Friendly entrypoint

Start with:

```text
init template
```

Fastlane opens with a plain-language welcome, explains the four setup checks,
states that AWS will not be accessed, and gives one owner action at a time. A
typical opening is:

```text
Welcome to AWS Codex Fastlane.

I’ll help you turn your AWS project idea into clear requirements, an
AWS-reviewed technical design, and an organized build plan. You stay in
control: I will pause for your approval before design and again before
construction begins.

First, I’ll complete four short setup checks:

1. Verify this template and its local tools.
2. Verify the official AWS Core plugin.
3. Review and test its safety hook.
4. Confirm AWS skills and documentation are available.

Setup will not configure AWS credentials, access your AWS account, or create
cloud resources.

You can answer “I’m not sure—recommend one” whenever you want guidance.

Current step: Checking the Fastlane repository.
Progress: Step 1 of 4
```

## Setup response contract

Each paused response answers seven questions in this order:

1. What step am I on?
2. What did Fastlane observe?
3. Why does it matter?
4. What is the one action I must take?
5. What command, if any, must I run?
6. How do I resume?
7. Were AWS credentials, access, or authorization used?

The internal state code appears at the bottom for troubleshooting rather than
as the main heading. For example:

```text
Setup paused: AWS Core needs to be installed

I verified the repository, but official AWS Core is not available in this
session. It supplies the AWS skills and documentation checks Fastlane needs.

Your action: Open `/plugins`, install AWS Core from AWS Agent Toolkit, and
start a new session. Then send `continue setup`.

AWS credentials were not checked. AWS account access was not used.

Progress: Step 2 of 4
Technical status: AWS_CORE_INSTALLATION_REQUIRED
```

Both `init template` and `continue setup` reduce the currently observable state
and resume at the first unresolved check. Fastlane does not save global Codex,
plugin, login, or hook-trust state in the repository.

## Four setup checks

| Progress | Fastlane proves | Owner-controlled actions |
|---|---|---|
| Step 1 of 4 | Repository, initialization, doctor, Python, and `uvx` readiness | Install tools and sign in to Codex |
| Step 2 of 4 | One official `aws-core@agent-toolkit-for-aws` source | Register, install, enable/disable, and restart |
| Step 3 of 4 | Current hook source, trust observation, deny probe, and allow probe | Review and trust the exact hook definition |
| Step 4 of 4 | Explicit live `retrieve_skill` and `search_documentation` calls | Invoke `@AWS Core` verification |

Setup does not configure credentials, inspect credential stores, access an AWS
account, or call AWS mutation tools. See [Setup](SETUP.md).

## Lifecycle

| Phase | Outcome | Human decision |
|---|---|---|
| BOOT-00 | Template and official AWS Core verified | Owner performs setup actions; no business approval |
| INTAKE-10 / REQ-10 | Users, outcomes, scope, data, constraints, risk, cost posture, and success criteria recorded | Owner answers or asks Fastlane to recommend |
| Gate A / INTAKE-20 | Versioned requirements and assumptions reviewed | Owner approves requirements for design |
| DESIGN-10 | Technical PRD, AWS architecture, evidence, and construction envelope completed | None until design is ready |
| Gate B / DESIGN-20 | Exact design and bounded construction envelope reviewed | Owner approves construction |
| TASK-10 / BUILD | Dependency-aware tasks executed inside the approved boundary | No task-by-task approval unless a stop condition occurs |
| RELEASE-10 | Release evidence and readiness evaluated | Owner action only when the release contract requires it |
| AWS-10 | Read-only deployment and operational preflight | No mutation authority |
| AWS-20 / AWS-50 | Exact authorized AWS change or teardown | Separate expiring AWS authorization |
| AWS-30 / AWS-40 | Deployment evidence, operation, rollback, and recovery | Governed by the current authorization and runbook |

## Gate A: requirements approval

Before design, Fastlane asks short questions about the intended user, outcome,
scope, data, failure behavior, security, recovery, constraints, cost posture,
and measurable success. It identifies contradictions and proposed assumptions.

Gate A approves one exact requirements revision for design. It does not approve:

- a technical design;
- construction;
- GitHub publication;
- AWS credentials or account access; or
- AWS deployment or spending.

Only the named human owner can approve Gate A. AWS Core and other advisors may
provide evidence but cannot approve it.

## DESIGN-10: AWS-reviewed technical design

After Gate A, Fastlane uses official AWS Core to retrieve skills relevant to the
architecture and search current primary AWS documentation. Consequential
service, IAM, Region, security, reliability, observability, quota, and cost
decisions must be tied to observed sources.

For each material evidence item, `docs/project/VERIFY.md` records:

- phase;
- AWS Core capability used;
- official plugin source and invoked identity;
- retrieved skill or identifier;
- documentation topic and source references;
- design decision influenced, observation time, and current revision/artifact binding; and
- observed PASS or blocking status.

Generic web search, model memory, or a statement that AWS Core was used is not
enough. Missing required DESIGN-10 evidence keeps Gate B blocked.

## Gate B: design and construction boundary

Gate B approves the exact current PRD and a construction envelope containing:

- intended outcome and scope;
- permitted write paths and prohibited work;
- task, concurrency, and retry limits;
- test and checkpoint expectations;
- GitHub permissions; and
- planned AWS lane and boundaries.

After approval, Fastlane may create tasks and build without asking for approval
after every edit, but only inside that envelope. A changed requirement,
architecture, scope, risk, cost posture, or authority makes the applicable gate
stale and stops affected work.

## AWS authorization is separate

An AWS lane describes intended access; it does not grant it. Gate A and Gate B
are governance boundaries, not IAM controls. Before any AWS execution proposal,
AWS-10 must record fresh official AWS Core operational, deployment, IAM, and
service evidence.

Any mutation needs a separate exact owner authorization naming:

- AWS account, Region, and environment;
- allowed resources and operations;
- finite cost ceiling and billing dimensions;
- rollback or teardown plan; and
- expiration or earlier completion condition.

Tool availability, credentials, sandbox permission, prior access, or a passing
hook never substitutes for that authorization. Prefer a read-only default
identity and a separate short-lived elevated role for approved mutations.

## Stop and resume behavior

Fastlane stops when:

- a setup dependency or official AWS Core proof is missing;
- two AWS Core sources or conflicting hooks are enabled;
- a requirement or material design decision is unresolved;
- required AWS Core evidence is missing;
- a gate is pending, stale, or invalid;
- work would cross the approved construction boundary;
- observed state conflicts with project records;
- tests or evidence fail; or
- AWS scope, cost, rollback, or authorization is incomplete or expired.

Setup resumes with `continue setup`. Later phases resume from the state-derived
next prompt recorded by Fastlane. Resumption revalidates current evidence; it
does not infer approval from silence or previous tool availability.

## Successful setup handoff

When all four setup checks pass, Fastlane summarizes:

- repository and doctor checks passed;
- official AWS Core enabled;
- current hook reviewed;
- deny and allow probes passed;
- `retrieve_skill` and `search_documentation` passed;
- AWS credentials were not configured or checked; and
- no AWS account was accessed.

The owner then sends:

```text
START GUIDED INTAKE
```

From that point, Fastlane follows Gate A → design → Gate B → bounded build.
