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
  Gate B. After each reconciled task or wave, rerun the doctor and continue in
  the same turn when it returns `NONE_CONTINUE_AUTOMATICALLY`.
- Derive owner-visible task progress only from the doctor's task totals and
  task-ID fields through `fastlane_presenter.py`; never estimate progress from
  narration.
- Pause only on validation failure, stale state, exhausted attempts, scope
  change, missing external authority, or another declared stop condition.
- Route AWS mutation through AWS-10/AWS-20 and GitHub mutation through the
  approved envelope or current explicit owner request.
