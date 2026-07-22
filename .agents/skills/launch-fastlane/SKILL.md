---
name: launch-fastlane
description: Welcome, initialize, inspect, or resume an AWS Codex Fastlane repository. Use when the user says "init template", "initialize template", "start Fastlane", BOOT-00, or asks for the next safe project step.
---

# Launch Fastlane

1. Read the root `AGENTS.md` and the complete `BOOT-00` contract in
   `prompts/CODEX-PROMPTS.md`.
2. Inspect `bootstrap.yaml`, `docs/project/PRD.md`, and repository state
   before producing owner-facing text.
   - If the project is initialized, skip the welcome, setup questions, and
     initializer. Run the dependency check and doctor, then resume the exact
     doctor-selected stage.
   - If it is an unconfigured template, run
     `python scripts/setup_assistant.py welcome` and reproduce stdout exactly
     once. That welcome asks for project name, preferred AWS Region, and
     optional budget in one reply; do not ask those values again.
3. Run `python scripts/bootstrap_dependencies.py --root . --json`. This
   checks repository assets only; it never proves AWS Core availability or
   grants AWS access.
4. For a fresh template, perform the existing dry-run-first in-place
   initialization after all three answers arrive. Preserve an owner hard cap;
   otherwise use `MINIMIZE_TOTAL_COST; HARD_CAP_NOT_STATED`. Keep every
   brownfield collision, source-repository, dirty-file, and Git safeguard.
5. Run `python scripts/bootstrap_doctor.py --root . --json` after
   initialization or resume. The doctor alone selects the lifecycle stage.
   Never restart BOOT-00 or repeat setup questions when it selects
   `INTAKE-10` or a later stage.
6. AWS Core is advisory during planning, not a BOOT-00 gate:
   - report `AVAILABLE` only for visible official
     `aws-core@agent-toolkit-for-aws`;
   - otherwise report `DEFERRED_UNTIL_DESIGN` and continue intake;
   - never install, change, pin, hash, probe, or trust a plugin or hook for the
     owner.
7. Return one exact routine status with these fields only:
   `Stage`, `Gate A`, `Gate B`, `AWS Core`, `AWS access`, and one
   `Next action`. Do not expose hashes, file counts, internal checks, or
   implementation narration.
8. Execute the one next action in the same response when possible. For
   `INTAKE-10`, ask its first one to three plain-language questions
   immediately. For a later stage, resume it directly.
9. Only when a material AWS design decision needs current evidence and official
   AWS Core is unavailable, give one owner action: enable AWS Core from Agent
   Toolkit for AWS in `/plugins` (register `aws/agent-toolkit-for-aws` only
   if absent), restart Codex, and send `CONTINUE AWS DESIGN`.

Setup never inspects AWS credentials, accesses an AWS account, creates cloud
resources, approves Gate A or Gate B, or grants AWS mutation authority.
