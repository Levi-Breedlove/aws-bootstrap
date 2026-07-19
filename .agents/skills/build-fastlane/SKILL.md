---
name: build-fastlane
description: Generate, execute, pause, or resume dependency-aware Fastlane tasks after Gate B. Use for TASK-10, BUILD-10, BUILD-20, autonomous construction, task claims, checkpoints, evidence, blockers, or release-readiness work.
---

# Build Fastlane

1. Read the root and applicable nested `AGENTS.md` files, current
   `docs/project/PRD.md`, `docs/project/TASKS.md`, and the prompt section named by the doctor.
2. Run `python scripts/bootstrap_doctor.py --root . --json`. Do not generate or
   execute tasks unless Gate B and its REQ/DES/AUTH basis are current.
3. Use `python scripts/task_waves.py docs/project/TASKS.md` for dependency planning and
   `--ready` for eligibility. Never treat `BACKLOG` as runnable.
4. Keep one coordinator as the sole writer of ledgers, shared manifests,
   generated outputs, and GitHub state. Assign workers only disjoint approved
   paths and external-state sets.
5. Start, claim, reconcile, checkpoint, pause, complete, and resume through
   `task_waves.py`; do not hand-edit coordinator state.
6. Execute only the current task write and command boundary. Route all AWS
   mutation to `AWS-20`; BUILD prompts never deploy directly.
7. Validate the integrated diff and required checks after each task or wave.
   Use the read-only `fastlane-evidence-reviewer` for boundary and evidence
   review when a wave or release claim is material. Record only observed
   evidence in `docs/project/VERIFY.md`, then run the doctor.
8. Continue autonomously while work is ready and inside Gate B. Pause on a
   stale gate, unsafe interrupted run, exhausted attempt budget, boundary
   change, or missing external authority.

Do not claim success from plans, mocks, unexecuted commands, or worker prose.
