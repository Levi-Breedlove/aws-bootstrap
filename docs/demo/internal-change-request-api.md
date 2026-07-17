# Internal Change Request API — Local Fastlane Demonstration

This demonstration uses synthetic data and performs no AWS access or mutation.
It shows the user experience and then reports separately what the executable
smoke test actually proved.

## Scenario

An internal team needs a small API where signed-in employees can submit a
change request and read its status. The development release uses a `quick-mvp`
profile, `explicit-gate` AWS lane, `us-west-2`, and a `$20/month` ceiling.

The illustrative technical design uses API Gateway, Lambda, DynamoDB, and
CloudWatch. Approved access succeeds, unapproved access is denied, invalid or
oversized input is rejected, secrets remain outside code and logs, IAM actions
are limited to the workload, and stored data uses approved encryption.

## Illustrative Codex conversation

The wording below demonstrates the contract; it is not claimed as model test
output.

1. BOOT-00 reports `ACTIVE_GREENFIELD`, `INTAKE_REQUIRED`, and `INTAKE-10`.
2. Guided intake asks who submits requests, what the smallest useful release
   does, and how success will be observed.
3. Gate A presents the owner-confirmed scope, non-goals, accepted assumptions,
   and measurable requirement IDs.
4. Technical design proposes the four AWS services, access boundary, failure
   behavior, logs, cost controls, rollback, and teardown.
5. Gate B authorizes three local tasks and explicitly leaves AWS mutation
   unapproved.
6. Codex completes the local tasks and records local evidence.
7. AWS preflight reports that deployment cannot proceed because no exact AWS
   authorization record exists.

## Executed smoke test

Run:

```bash
python scripts/run_demo.py
python scripts/run_demo.py --json
```

The script copies the exact manifest inventory to a temporary directory,
configures that instance in place, and runs the actual doctor. It then executes
three local handler tests, proves that only `TASK-0001` is `READY`, and stops
AWS preflight because no exact authorization record exists. It never imports
an AWS SDK, reads credentials, calls an AWS endpoint, or writes outside its
temporary directory.

Expected summary:

```text
AWS CODEX FASTLANE — TESTED SHOWCASE

EXECUTED TEST OUTPUT
Result: PASS
Scenario: Internal Change Request API
Doctor: PASS
Bootstrap status: READY
Lifecycle: INTAKE_REQUIRED -> INTAKE-10
Gate A: BLOCKED
Gate B: BLOCKED
Evidence: NOT_READY
AWS authorization: NONE
Local control tests: 3 passed
Runnable tasks: TASK-0001
BACKLOG tasks excluded: TASK-0002, TASK-0003
AWS preflight: BLOCKED_AS_DESIGNED (No exact AWS authorization record exists.)
AWS API calls: 0; cloud cost: $0
```

The next section printed by the script is labeled
`ILLUSTRATIVE CODEX DIALOGUE — NOT EXECUTED OUTPUT` before it shows the intake,
Gate A, simulated technical design, and Gate B examples.
