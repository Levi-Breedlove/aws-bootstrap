---
name: launch-fastlane
description: Welcome, initialize, configure, inspect, or resume an AWS Codex Fastlane repository. Use when the user says "init template", "initialize template", "start Fastlane", START AWS CODEX FASTLANE, BOOT-00, fresh GitHub-template or ZIP setup, brownfield adoption, doctor checks, or asks for the next safe prompt.
---

# Launch Fastlane

1. Read the root `AGENTS.md` and the `BOOT-00` section of
   `prompts/CODEX-PROMPTS.md` completely.
2. Welcome the owner and explain in two plain sentences that Fastlane turns an
   idea into approved requirements and a technical PRD, then builds only inside
   the Gate B boundary. Do not imply that setup authorizes AWS access.
3. Resolve the requested repository and setup mode to canonical absolute paths.
   Treat `init template` as `THIS_REPOSITORY`; use the existing Git repository
   when present and the BOOT-00 safe local baseline behavior when it is absent.
4. Run `python scripts/bootstrap_dependencies.py --root <root> --json`. Stop if
   the repository-scoped skills, project agents, or pinned Agent Toolkit for
   AWS marketplace are not `READY`.
5. Inspect the capabilities actually surfaced in this session. `aws-core` is
   available only when this session exposes an AWS Core-contributed skill or
   AWS MCP tool; never infer availability from the marketplace file alone. If
   it is absent, return the BOOT-00 toolkit setup receipt, explain that the
   pinned `INSTALLED_BY_DEFAULT` request needs repository trust or platform
   approval, and tell the owner to start a new Codex session with `init
   template`. Do not ask project questions or configure AWS credentials first.
6. Run `python scripts/bootstrap_doctor.py --root <root> --json`. Use its
   classification, lifecycle, status, and `next_prompt`; do not infer a route
   from conversation history.
7. For `THIS_REPOSITORY`, ask at most one round containing project name,
   preferred Region, and development budget when they are not supplied. Run
   `bootstrap.py --in-place-template-instance` first with `--dry-run`, then
   without it only when the template preconditions pass.
8. For `ADOPT_EXISTING_REPOSITORY`, perform the exact BOOT-00 collision preview.
   Never choose an adoption action for the owner or use `--force`.
9. Apply the selected local Git mode exactly. Never add a remote or perform a
   GitHub or AWS action during launch.
10. Run the dependency checker and doctor again. Render the BOOT-00 receipt only
   from observed command output, surfaced session capabilities, and repository
   state.
11. End with the canonical prefilled `START GUIDED INTAKE` command only when the
   doctor returns `INTAKE-10`.

Stop on a doctor error, path overlap outside the explicit in-place mode,
official source-repository protection, a dirty or modified template, a
collision without a confirmed decision map, or any source-of-truth conflict.
The AWS Core plugin is advisory capability, not a human gate decision and not
AWS mutation authorization.
