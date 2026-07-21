---
name: launch-fastlane
description: Welcome, initialize, inspect, or resume an AWS Codex Fastlane repository. Use when the user says "init template", "initialize template", "start Fastlane", BOOT-00, or asks for the next safe project step.
---

# Launch Fastlane

1. Read the root `AGENTS.md` and the complete `BOOT-00` contract in
   `prompts/CODEX-PROMPTS.md`.
2. Before any custom explanation, run:

   ```text
   python scripts/setup_assistant.py welcome
   ```

   Reproduce its stdout exactly. This keeps the first-run welcome stable.
3. Run `python scripts/bootstrap_dependencies.py --root . --json`. This is a
   repository check only. It never proves that AWS Core is installed or grants
   AWS access.
4. Inspect the repository and doctor before writing. For an unconfigured
   template, ask once for the missing project name, preferred AWS Region, and
   development budget posture. Accept either a finite cap with currency or
   "minimize cost; no hard cap", then perform the existing dry-run-first
   in-place initialization. Preserve an owner-supplied hard cap; otherwise use
   `MINIMIZE_TOTAL_COST; HARD_CAP_NOT_STATED`. Keep all brownfield collision,
   source-repository, dirty-file, and Git safeguards unchanged.
5. Run `python scripts/bootstrap_doctor.py --root . --json` after
   initialization or resume. Never restart BOOT-00 when the doctor already
   routes to intake or a later lifecycle prompt.
6. AWS Core is advisory during planning, not a BOOT-00 gate:
   - if official `aws-core@agent-toolkit-for-aws` is visibly available, report
     `AVAILABLE`;
   - otherwise report `DEFERRED_UNTIL_DESIGN` and continue;
   - never install, enable, disable, update, trust, hash, or probe a plugin or
     hook for the owner.
7. Return this compact receipt:

   ```text
   AWS CODEX FASTLANE — READY
   Setup: READY_FOR_INTAKE
   Project: <name>
   Region: <region>
   Doctor: PASS
   AWS Core: <AVAILABLE|DEFERRED_UNTIL_DESIGN>
   Next prompt: <doctor route>
   AWS access: NOT USED
   ```

8. If the route is `INTAKE-10`, begin its first one to three
   plain-language questions immediately. Do not require another start command.
   If the project is farther along, resume the doctor-selected prompt without
   repeating setup.

Setup never inspects AWS credentials, accesses an AWS account, creates cloud
resources, approves Gate A or Gate B, or grants AWS mutation authority.
