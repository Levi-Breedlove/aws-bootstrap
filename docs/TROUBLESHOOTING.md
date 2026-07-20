# Troubleshooting Fastlane Setup

Fastlane setup is intentionally resumable. Correct the first unresolved item,
start a new Codex session when plugin state changed, and send:

```text
continue setup
```

Do not repeat completed owner actions unless Fastlane reports that their current
evidence is unavailable or stale.

## Quick diagnosis

Run the instruction-only assistant from the repository root:

```text
python scripts/setup_assistant.py status --root . --json
python scripts/setup_assistant.py guide --root .
```

On macOS or Linux, use `python3` for these project scripts when `python` is not
provided. The assistant does not install anything or inspect credential stores.

## Common problems

| Symptom or state | Likely cause | Owner action |
|---|---|---|
| `codex` is not recognized | Codex is missing or the terminal has stale PATH state | Follow the official installer, reopen the terminal, run `codex --version` |
| `CODEX_LOGIN_VERIFICATION_REQUIRED` | Current authentication was not verified | Run `codex login`, then `codex login status` |
| `uvx` is not recognized | uv is missing or PATH was not refreshed | Install uv from Astral's guide, reopen the shell, run `uvx --version` |
| Python is older than 3.11 | Unsupported project runtime | Install Python 3.11+ and reopen the terminal |
| `HOOK_RUNTIME_REQUIRED` on Windows | Native Windows does not expose `python3` | Use WSL2; do not create an alias, shim, or modified plugin |
| `OFFICIAL_MARKETPLACE_REQUIRED` | AWS Agent Toolkit is not registered | Run the official marketplace command below |
| `AWS_CORE_INSTALLATION_REQUIRED` | Marketplace exists but AWS Core is absent | Install AWS Core yourself in `/plugins` and start a new session |
| `AWS_CORE_ENABLE_REQUIRED` | Official AWS Core is installed but disabled | Enable it yourself and start a new session |
| `AWS_CORE_DUPLICATE_BLOCKED` | More than one AWS Core source is enabled | Keep only `aws-core@agent-toolkit-for-aws`, then start a new session |
| `AWS_CORE_SOURCE_UNVERIFIED` | The enabled source cannot be tied to the official marketplace | Inspect `/plugins`; disable unknown sources rather than guessing |
| AWS Core was just installed but tools are missing | Bundled capabilities load in new sessions | Start a new CLI session or chat in the repository |
| `HOOK_REVIEW_REQUIRED` | The current hook definition is not trusted | Inspect all matching sources in `/hooks` and trust the exact official definition yourself |
| `HOOK_PROBES_REQUIRED` | Hook review is complete but behavior lacks evidence | Send `continue setup` and let Codex run both local probes |
| Deny probe executes | AWS Core safety hook did not block the pattern | Stop; verify source, hook enablement, trust, and conflicts |
| Allow probe is blocked or output changes | Hook conflict or runtime failure | Inspect every matching hook and verify `python3` |
| `AWS_CORE_HANDSHAKE_REQUIRED` | Plugin behavior has not been proven live | Explicitly invoke `@AWS Core` with the verification command |
| `AWS_CORE_VERIFICATION_BLOCKED` | One or both required capabilities failed or used the wrong source | Preserve the receipt, verify the official source, restart, and retry |
| Doctor reports unresolved template values before initialization | Stock template is not configured yet | Continue BOOT-00; this is expected before safe initialization |
| A newer AWS Core version is reported | Official marketplace moved beyond the last-tested version | Re-review hooks and rerun probes/handshake; do not downgrade automatically |
| Plugins are unavailable | Current surface is unsupported | Use Codex CLI, ChatGPT desktop Work/Codex, or supported web Work; not Chat mode, IDE, or mobile |

Official marketplace command:

```text
codex plugin marketplace add aws/agent-toolkit-for-aws
```

Official plugin identity:

```text
aws-core@agent-toolkit-for-aws
```

## Codex installation or login fails

Use the current [Codex CLI installation guide](https://learn.chatgpt.com/docs/codex/cli)
rather than a copied third-party command. After installation, close and reopen
the terminal:

```text
codex --version
codex login
codex login status
```

Fastlane never reads Codex credentials. Do not paste tokens, cookies, device
codes, or credential-file contents into setup output or a GitHub issue.

## `uvx` is unavailable

Install uv using the [official Astral instructions](https://docs.astral.sh/uv/getting-started/installation/),
open a new terminal, and run:

```text
uvx --version
```

`uvx` starts the AWS MCP proxy packaged by AWS Core. Codex login does not depend
on uv, but the AWS Core MCP capability handshake does. Fastlane's setup
assistant prints instructions only and must not execute the installer.

## Native Windows lacks `python3`

The Fastlane project runtime and AWS Core hook are separate requirements:

- Fastlane needs Python 3.11+ and ordinarily invokes `python`.
- The current official AWS Core hook invokes the literal `python3` command.

If `python --version` succeeds but `python3 --version` fails, the hook cannot be
verified on that native setup. Do not create a PowerShell alias, copy an
executable, add a repository wrapper, or edit the installed plugin. Those
workarounds change what was reviewed and are not part of the supported contract.
Use WSL2/Ubuntu and follow [the setup guide](SETUP.md#windows-with-wsl2).

## The official marketplace or plugin is missing

Register the marketplace yourself, then use `/plugins`:

```text
codex plugin marketplace add aws/agent-toolkit-for-aws
```

Install or enable AWS Core under **AWS Agent Toolkit**, then start a new session.
Do not use `codex plugin marketplace add .`; that was the removed pinned flow.

## More than one AWS Core is enabled

Do not continue with ambiguous tools and hooks. In `/plugins`, keep only:

```text
aws-core@agent-toolkit-for-aws
```

Disable the old pinned or unknown entry yourself and start a new session.
Fastlane never changes plugin state. See [Existing AWS Core](EXISTING-AWS-CORE.md).

## Hook review or probes fail

1. Enter `/hooks`.
2. Confirm the expected hook source is official AWS Core.
3. Inventory all other hooks matching shell or AWS MCP tool names.
4. Confirm hooks are enabled and the exact current definition is trusted.
5. Confirm `python3 --version` succeeds in the Codex environment.
6. Run the probes only through Codex so `PreToolUse` can inspect them.

Never use `--dangerously-bypass-hook-trust`. Never disable a conflicting hook
silently; identify it for the owner. The deny probe must be blocked before
execution, while the allow probe must print only `FASTLANE_HOOK_ALLOW_PROBE`.
Neither probe should access AWS.

## The AWS Core handshake fails

Send the exact explicit invocation:

```text
@AWS Core
VERIFY AWS CORE AND CONTINUE FASTLANE
```

A valid receipt needs live PASS results from both `retrieve_skill` and
`search_documentation`, plus official source identity and returned AWS source
references. It must also state that credentials were not checked and AWS account
access was not used.

Do not accept generic web search, a documentation connector, model memory, or a
prose claim as proof. BOOT-00 must not invoke `call_aws` or `run_script`.

## Collect safe diagnostic information

When reporting a setup defect, include only:

- Fastlane version or commit;
- operating system and whether Windows is native or WSL2;
- `python --version`, `python3 --version`, `uvx --version`, and
  `codex --version` output;
- the technical setup state;
- plugin marketplace names without local cache paths; and
- a redacted hook or capability receipt containing no credentials or private
  project data.

Never publish tokens, usernames, home-directory paths, credential-store
contents, AWS account IDs, secret values, or production resource identifiers.
