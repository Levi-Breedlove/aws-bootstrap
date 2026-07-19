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
   its top-level status, repository-scoped skills, or project agents are not
   `READY`, or if the Agent Toolkit marketplace is not
   `DECLARED_AND_PINNED`. This check validates repository files only; it cannot
   prove that AWS Core is installed or callable. Preserve its exact expected
   hook contract and repository-hook inventory for the later `/hooks` review.
5. For `THIS_REPOSITORY`, ask at most one round containing project name,
   preferred Region, and development budget when they are not supplied. Run
   `bootstrap.py --in-place-template-instance` first with `--dry-run`, then
   without it only when the template preconditions pass.
6. For `ADOPT_EXISTING_REPOSITORY`, perform the exact BOOT-00 collision preview.
   Never choose an adoption action for the owner or use `--force`.
7. Apply the selected local Git mode exactly. Never add a remote or perform a
   GitHub or AWS action during launch.
8. Run `python scripts/bootstrap_doctor.py --root <root> --json`. Use its
   classification, lifecycle, status, and `next_prompt`; do not infer a route
   from conversation history. Do not probe for `pytest`, install Python
   packages, or run the maintainer test suite during launch.
9. Determine the current Codex surface from observed client context. AWS Core
   plugins are supported in the ChatGPT desktop app's Codex experience and
   Codex CLI, not the Codex IDE extension. When running in the IDE extension,
   print the BOOT-00 `SUPPORTED CODEX SURFACE REQUIRED` receipt and stop before
   AWS Core verification or intake. Do not download or invoke another Codex
   client as a workaround, including through `npx`. Do not register a
   marketplace, install a plugin, or install `uv`, `uvx`, `pipx`, or another
   package from the unsupported IDE surface.
10. On a supported surface, run `uvx --version` as a read-only prerequisite
    check. If `uvx` is missing, return the BOOT-00 `AWS CORE RUNTIME REQUIRED`
    receipt and stop. Point to the official AWS Agent Toolkit prerequisite and
    Astral `uv` installation guide. Do not install a runtime automatically;
    that requires a separate, explicit user action or approval.
11. On a supported surface, if the pinned plugin is not installed, enabled, and
    current, or if it cannot be distinguished from a generic AWS documentation
    connector, return the BOOT-00 AWS Core setup receipt and walkthrough.
    Direct the owner to `/plugins`, the `AWS Codex Fastlane Dependencies`
    marketplace, and the `AWS Core` install or update action; then tell them to
    restart Codex and reopen this repository.
12. Before the live plugin handshake, run `python3 --version` because the pinned
    AWS Core hook invokes that exact command. If unavailable, return the
    BOOT-00 `AWS CORE HOOK RUNTIME REQUIRED` receipt and stop. Open the Hooks
    page in Codex Settings, or `/hooks` in Codex CLI, and compare the plugin's
    current `PreToolUse` hook with the exact event,
    matchers, command, purpose, and expected file hashes reported by
    `bootstrap_dependencies.py`. Inventory every other active hook that can
    match Bash or AWS MCP tools. Stop on an unknown or conflicting hook. Never
    trust a hook for the owner or use `--dangerously-bypass-hook-trust`.
    Require the owner to trust the current AWS Core hook definition in Codex
    and then run BOOT-00's inert synthetic deny probe and harmless allow probe.
    Require the first to be blocked and the second to run; neither accesses
    AWS. Only then present and accept the exact BOOT-00 hook confirmation. A
    changed definition hash requires review again. After a passing
    confirmation, print the stable AWS Core hook approval receipt and tell the
    owner to send exactly:

   ```text
   @AWS Core
   VERIFY AWS CORE AND CONTINUE FASTLANE
   ```

   Stop before intake. Do not describe this as Gate A or Gate B.
13. For that explicit verification command, require the AWS Core plugin to
    expose and successfully exercise both `retrieve_skill` and
    `search_documentation`. Use only unauthenticated skill retrieval and a
    documentation query. A generic documentation namespace is insufficient;
    do not call `call_aws`, `run_script`, configure credentials, or access an
    AWS account. Print the stable AWS Core verification receipt, rerun the
    static checker and doctor, and continue only when every check passes.
14. Render the final BOOT-00 receipt only from observed command output, the
    exact hook confirmation, explicit plugin handshake, and repository state.
    End with the canonical prefilled `START GUIDED INTAKE` command only when
    the doctor returns `INTAKE-10`.

Stop on a doctor error, path overlap outside the explicit in-place mode,
official source-repository protection, a dirty or modified template, a
collision without a confirmed decision map, or any source-of-truth conflict.
The AWS Core plugin is advisory capability, not a human gate decision and not
AWS mutation authorization.
