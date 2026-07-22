# Deliver phase

Use for TASK-10, BUILD-10, BUILD-20, and RELEASE-10.

- Require a current approved Gate B and current REQ/DES/AUTH basis.
- Generate dependency-aware tasks and use `scripts/task_waves.py`; only READY
  tasks with satisfied dependencies may run.
- The coordinator alone writes code and ledgers. Preserve task IDs, write and
  command boundaries, attempt budgets, checkpoints, and protected paths.
- Run applicable example, property, integration, security, recovery, and IaC
  validation. Record only observed results in VERIFY and operational facts in
  RUNBOOK.
- For release-readiness or task decisions that depend on a current AWS fact,
  consult official current AWS Core directly. If unavailable,
  pause only the affected AWS-specific task with one recovery action; never
  guess or restart intake.
- Continue autonomously while work remains current, ready, safe, and inside
  Gate B. Pause on validation failure, stale state, exhausted attempts, scope
  change, or missing external authority.
- Route AWS mutation through AWS-10/AWS-20 and GitHub mutation through the
  approved envelope or current explicit owner request.
