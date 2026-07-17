---
name: launch-fastlane
description: Initialize, configure, inspect, or resume an AWS Codex Fastlane repository. Use for START AWS CODEX FASTLANE, BOOT-00, fresh GitHub-template or ZIP setup, brownfield adoption, doctor checks, or determining the next safe prompt.
---

# Launch Fastlane

1. Read the root `AGENTS.md` and the `BOOT-00` section of
   `prompts/CODEX-PROMPTS.md` completely.
2. Resolve the requested repository and setup mode to canonical absolute paths.
3. Run `python scripts/bootstrap_doctor.py --root <root> --json`. Use its
   classification, lifecycle, status, and `next_prompt`; do not infer a route
   from conversation history.
4. For `THIS_REPOSITORY`, ask at most one round containing project name,
   preferred Region, and development budget when they are not supplied. Run
   `bootstrap.py --in-place-template-instance` first with `--dry-run`, then
   without it only when the template preconditions pass.
5. For `ADOPT_EXISTING_REPOSITORY`, perform the exact BOOT-00 collision preview.
   Never choose an adoption action for the owner or use `--force`.
6. Apply the selected local Git mode exactly. Never add a remote or perform a
   GitHub or AWS action during launch.
7. Run the doctor again. Render the BOOT-00 receipt only from observed command
   output and repository state.
8. End with the canonical prefilled `START GUIDED INTAKE` command only when the
   doctor returns `INTAKE-10`.

Stop on a doctor error, path overlap outside the explicit in-place mode,
official source-repository protection, a dirty or modified template, a
collision without a confirmed decision map, or any source-of-truth conflict.
