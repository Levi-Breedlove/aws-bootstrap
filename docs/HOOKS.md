# Optional Fastlane hooks

Fastlane works without repository hooks. The opt-in pack adds native Codex
guardrails around the existing doctor and authorization contracts; it does not
create a new policy source or approval path.

## Enable manually

1. Review `.codex/hooks.fastlane.example.json` and
   `.codex/hooks/fastlane_hook.py` in this repository.
2. Copy the example only after that review:

   ```bash
   cp .codex/hooks.fastlane.example.json .codex/hooks.json
   ```

   In PowerShell:

   ```powershell
   Copy-Item .codex/hooks.fastlane.example.json .codex/hooks.json
   ```

3. Restart Codex, enter `/hooks`, and review the resulting native trust prompt.
4. Keep the trust decision in your local Codex profile. Do not commit
   `.codex/hooks.json` or any client trust state.

To disable the pack, remove the manually copied `.codex/hooks.json`. The
reviewed example remains unchanged.

## What each event does

| Event | Bounded behavior |
|---|---|
| `SessionStart` | Runs the doctor read-only and adds short stage, gate, owner-action, and AWS-authority context. |
| `PreToolUse` | Blocks only clearly unauthorized AWS access or mutation, teardown, GitHub publication, and writes outside the repository. AWS documentation tools remain available. |
| `PermissionRequest` | Never auto-allows escalation. It denies a clearly out-of-bound request; otherwise the normal owner approval prompt remains. |
| `PostToolUse` | Runs the smallest applicable validation and returns bounded corrective context on failure. It never records evidence automatically. |
| `Stop` | Continues only when the doctor reports automatic continuation, no owner action, and no formal receipt. `stop_hook_active` prevents loops. |

The handler reads only the current event fields needed for these decisions. It
does not read chat transcripts, log prompts or tool inputs, inspect credentials,
persist secrets, change lifecycle state, or access AWS.

## Authority boundary

Hooks are defense in depth. A hook allow or lack of a denial is not Gate A,
Gate B, GitHub authority, AWS authority, or teardown authority. Codex sandbox
and owner approvals still apply, and the existing Fastlane doctor, receipts,
construction envelope, and AWS authorization remain authoritative.

Codex can load matching hooks from several sources and may run them
concurrently. Review the complete `/hooks` inventory, not just this pack. See
the current [Codex hooks documentation](https://learn.chatgpt.com/docs/hooks)
for native event, trust, and configuration behavior.
