---
name: launch-fastlane
description: Welcome, initialize, configure, inspect, or resume an AWS Codex Fastlane repository. Use when the user says "init template", "initialize template", "start Fastlane", START AWS CODEX FASTLANE, BOOT-00, fresh GitHub-template or ZIP setup, brownfield adoption, doctor checks, or asks for the next safe prompt.
---

# Launch Fastlane

1. Read the root `AGENTS.md` and the complete `BOOT-00` contract in
   `prompts/CODEX-PROMPTS.md`. Treat `init template`, `initialize template`,
   `start Fastlane`, and `continue setup` as entrypoints to one idempotent
   state machine. The first three begin with `THIS_REPOSITORY`; `continue setup`
   resumes at the first unresolved state without repeating completed actions.
2. Begin with BOOT-00's friendly four-step greeting. Each paused response must
   explain the current step, observation, why it matters, exactly one owner
   action, how to resume, and the safety posture. Put `Progress: Step n of 4`
   before the technical state code. Use `reduce_setup` and
   `render_setup_response` from `scripts/setup_assistant.py`; do not hand-build
   a competing state transition or receipt.
3. Resolve repository, setup mode, and target to canonical absolute paths.
   Run `python scripts/bootstrap_dependencies.py --root <root> --json` before a
   project question or write. Require its top-level status, repository skills,
   project agents, and official-current AWS Core policy to be ready. Static
   metadata is not evidence that AWS Core is installed, enabled, callable, or
   used.
4. For `THIS_REPOSITORY`, ask once for missing project name and preferred
   Region. Preserve any owner-supplied hard cap exactly; otherwise use
   `MINIMIZE_TOTAL_COST; HARD_CAP_NOT_STATED`. Dry-run in-place initialization,
   initialize only after all safety checks pass, and run the doctor. For
   brownfield adoption, perform BOOT-00's exact collision preview and require
   the complete hash-bound owner decision map before any adoption write. Never
   choose an adoption action, use `--force`, add a remote, or access GitHub/AWS.
5. Use `scripts/setup_assistant.py` only for instruction-only prerequisite
   status or guidance. Ask the owner to verify `uvx --version` visibly. The
   owner installs tools, logs in, registers a
   marketplace, changes plugin state, starts sessions, and trusts hooks. Never
   inspect credentials or persist global Codex/plugin/trust state. Plugins must
   be managed in interactive Codex CLI, ChatGPT web Work mode, or ChatGPT
   desktop Work/Codex; the Codex IDE extension is unsupported.
6. Accept only the official plugin identity
   `aws-core@agent-toolkit-for-aws`. Resolve observed plugin state as follows:
   - already enabled: reuse it and continue;
   - installed but disabled: `AWS_CORE_ENABLE_REQUIRED`;
   - official marketplace present but plugin absent:
     `AWS_CORE_INSTALLATION_REQUIRED` and direct the owner to `/plugins`;
   - official marketplace absent: `OFFICIAL_MARKETPLACE_REQUIRED` with owner-run
     `codex plugin marketplace add aws/agent-toolkit-for-aws`;
   - official and old Fastlane-pinned copies enabled:
     `AWS_CORE_DUPLICATE_BLOCKED`, naming both sources;
   - only an old pinned copy: ask the owner to disable it and install/enable the
     official source; and
   - unknown source: `AWS_CORE_SOURCE_UNVERIFIED`.
   Never enable, disable, install, remove, or update a plugin for the owner.
7. Before the live handshake, require the current official AWS Core
   `PreToolUse` hook to be visible in `/hooks`, readable, sourced from the
   official plugin, and accompanied by a conflict-free inventory of all hooks
   matching Bash or AWS MCP tools. Only the owner reviews and trusts it. Return
   `HOOK_REVIEW_REQUIRED` with the currently visible official definition/source
   and matching-hook inventory, ask the owner to review and trust it, then ask
   for exactly `continue setup`. Treat that reply as the owner's attestation
   bound only to that current definition and inventory; renew it after any
   change. Never claim persisted trust was machine-observed or persist local
   paths, session details, hook-trust state, or trust-database data. Do not hash
   an external checkout, require a multiline approval card, alter hook state,
   or bypass trust. Never use `--dangerously-bypass-hook-trust`. Missing
   `python3` returns `HOOK_RUNTIME_REQUIRED`. After the attestation, run the
   BOOT-00 inert deny and harmless allow probes through the normal tool path.
   The first must be blocked before execution and the second must print the
   exact marker. Neither accesses AWS.
8. After owner-attested hook review and passing probes, return
   `AWS_CORE_HANDSHAKE_REQUIRED` and ask the owner to send exactly:

   ```text
   @AWS Core
   VERIFY AWS CORE AND CONTINUE FASTLANE
   ```

   Stop before intake; this is setup, not Gate A or Gate B.
9. That explicit invocation must visibly exercise both official AWS Core
   capabilities. Call `retrieve_skill` requesting exactly `aws-serverless` and
   record its nonempty canonical returned identifier. Call
   `search_documentation` with exactly `AWS Lambda security best practices for
   serverless applications, including least-privilege IAM and input
   validation` and record returned official AWS references. Accept neither
   installation metadata, a generic connector, cached content, earlier
   conversation, nor prose claims. Each capability row records source
   `aws/agent-toolkit-for-aws`, identity `aws-core@agent-toolkit-for-aws`,
   observed current semantic version, actor `CODEX_LIVE_TOOL_CALL`, input and
   output, time, Fastlane-version binding, PASS/FAIL,
   `Credentials inspected` = `NO`, and `AWS account accessed` = `NO`. A newer
   official version remains valid. Do not call `call_aws`, `run_script`,
   inspect/configure credentials, or access an AWS account.
10. Rerun the dependency checker and doctor after the handshake. Return
    `READY_FOR_INTAKE` only when repository/doctor checks, official source,
    owner-attested hook review, both probes, and both complete attributable live
    capability rows pass. Otherwise render the first unresolved state. End with
    `START GUIDED INTAKE` only when the doctor routes to `INTAKE-10`; missing
    BOOT-00 evidence must route back to `BOOT-00`.

Stop on a doctor error, path overlap outside the explicit in-place mode,
official source-repository protection, a dirty or modified template, a
collision without a confirmed decision map, or any source-of-truth conflict.
The AWS Core plugin is advisory capability, not a human gate decision and not
AWS mutation authorization.
