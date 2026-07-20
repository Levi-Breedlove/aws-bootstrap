# AWS Codex Fastlane Setup

This guide takes a new user from an empty machine to `START GUIDED INTAKE`.
Fastlane provides instructions and verification; the repository never installs
software, signs in, changes plugin state, trusts hooks, or configures AWS for you.

## What you need

- Git
- Python 3.11 or newer
- `python` for Fastlane commands and the literal `python3` command required by
  the current AWS Core safety hook
- Astral `uv`, including `uvx`
- Codex CLI or another Codex surface that supports plugins
- AWS Core from the official AWS Agent Toolkit marketplace

Codex CLI is the recommended host for a local checkout. ChatGPT desktop
Work/Codex can also use plugins. Plugins are not available in Chat mode, the
Codex IDE extension, or mobile. See [OpenAI's plugin guide](https://learn.chatgpt.com/docs/plugins).

No AWS account, credentials, or numeric budget is needed for setup.

## 1. Install the local tools

Choose one platform below. Run installation commands yourself, review commands
before execution, and use your organization's approved package sources when
applicable.

### Windows native

Open PowerShell as your normal user. WinGet may prompt for package agreements.

```powershell
winget install --id Git.Git -e --source winget
winget install --id Python.Python.3.12 -e --source winget
winget install --id astral-sh.uv -e
powershell -ExecutionPolicy ByPass -c "irm https://chatgpt.com/codex/install.ps1 | iex"
```

Close and reopen PowerShell so PATH changes take effect, then run:

```powershell
git --version
python --version
python3 --version
uvx --version
codex --version
```

Both Python commands matter: Fastlane examples use `python`, while the current
official AWS Core hook launches `python3`. Some native Windows Python installs
do not expose `python3`. If `python3 --version` fails, do not create an alias,
wrapper, shim, or modified copy of AWS Core. Use WSL2 for this workflow until
the official hook has a verified native-Windows launcher.

Official references: [Codex CLI](https://learn.chatgpt.com/docs/codex/cli),
[Python downloads](https://www.python.org/downloads/windows/), and
[uv installation](https://docs.astral.sh/uv/getting-started/installation/).

### Windows with WSL2

If WSL2 is not installed, follow [Microsoft's WSL guide](https://learn.microsoft.com/windows/wsl/install).
The normal owner-run starting command from an administrator PowerShell window is:

```powershell
wsl --install -d Ubuntu
```

Restart Windows if prompted. Open Ubuntu and install the Linux prerequisites:

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python-is-python3 curl
curl -LsSf https://astral.sh/uv/install.sh | sh
curl -fsSL https://chatgpt.com/codex/install.sh | sh
```

Close and reopen the WSL shell, then verify:

```bash
git --version
python --version
python3 --version
uvx --version
codex --version
```

Keep the repository inside the WSL filesystem for the cleanest permissions and
tool behavior, for example `~/code/my-project`, rather than mixing Windows and
Linux executables in the same checkout.

### macOS

Install Git with the Xcode command-line tools if it is not already present:

```bash
xcode-select --install
```

With Homebrew, install Python and uv. Then use the official Codex installer:

```bash
brew install python@3.12 uv
curl -fsSL https://chatgpt.com/codex/install.sh | sh
```

Open a new terminal and verify:

```bash
git --version
python3 --version
uvx --version
codex --version
```

On macOS, `python3` is an accepted interpreter for Fastlane project scripts if
the unversioned `python` command is absent. Do not change the AWS Core hook; it
already requires `python3`.

Official references: [Codex CLI](https://learn.chatgpt.com/docs/codex/cli),
[Python downloads](https://www.python.org/downloads/macos/), and
[uv installation](https://docs.astral.sh/uv/getting-started/installation/).

### Linux

On Debian or Ubuntu:

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python-is-python3 curl
curl -LsSf https://astral.sh/uv/install.sh | sh
curl -fsSL https://chatgpt.com/codex/install.sh | sh
```

On Fedora, use the equivalent distribution packages:

```bash
sudo dnf install git python3 python-unversioned-command curl
curl -LsSf https://astral.sh/uv/install.sh | sh
curl -fsSL https://chatgpt.com/codex/install.sh | sh
```

Open a new shell and verify:

```bash
git --version
python --version
python3 --version
uvx --version
codex --version
```

If your distribution intentionally provides only `python3`, use `python3` for
Fastlane project scripts. Never redirect the AWS Core hook to an unreviewed
runtime.

## 2. Create your project repository

Select [Use this template](https://github.com/Levi-Breedlove/aws-bootstrap/generate)
and create a new repository under your account or organization. Clone that new
repository; do not initialize the Fastlane maintainer repository in place.

```text
git clone https://github.com/<OWNER>/<PROJECT>.git
cd <PROJECT>
```

Use an existing clean Git checkout when Fastlane asks about the local Git setup.
If you received a future supported release archive without Git history, choose
the baseline-commit option offered during setup.

## 3. Sign in to Codex

Authentication is owner-managed and remains in your Codex profile, not the
repository.

```text
codex login
codex login status
```

Complete the browser or device flow when prompted. Fastlane checks only your
reported or current-session status; it must not read credential stores.

## 4. Run the instruction-only prerequisite check

From the project root, use the same Python interpreter that will run Fastlane:

```text
python scripts/setup_assistant.py status --root . --json
python scripts/setup_assistant.py guide --root .
```

On macOS or Linux where `python` is intentionally absent, replace `python` with
`python3`. The assistant reports status and prints owner-run instructions. It
does not install, launch, sign in, register, trust, or access AWS.

Resolve `LOCAL_PREREQUISITES_REQUIRED`, `CODEX_LOGIN_VERIFICATION_REQUIRED`, or
`HOOK_RUNTIME_REQUIRED` before continuing.

## 5. Register the official AWS marketplace

If **AWS Agent Toolkit** already appears in `/plugins`, do not add a second
marketplace. Otherwise, exit Codex if it is open and run this from a terminal:

```text
codex plugin marketplace add aws/agent-toolkit-for-aws
```

This follows the [official AWS Agent Toolkit installation](https://docs.aws.amazon.com/agent-toolkit/latest/userguide/plugins.html).
The accepted plugin identity is:

```text
aws-core@agent-toolkit-for-aws
```

Fastlane no longer registers a repository-local pinned marketplace.

## 6. Launch Codex in the repository

```text
codex -C . --sandbox workspace-write --ask-for-approval on-request
```

The sandbox and platform approval policy still apply. These flags do not grant
business approval or AWS authority.

## 7. Install or reuse official AWS Core

Inside Codex, enter:

```text
/plugins
```

Open the **AWS Agent Toolkit** marketplace and inspect **AWS Core**.

- If official AWS Core is already installed and enabled, reuse it.
- If it is installed but disabled, enable it yourself.
- If it is missing, install it yourself from that marketplace.
- If an older `aws-core@aws-codex-fastlane-dependencies` entry is enabled,
  disable it before continuing.
- If two AWS Core sources are enabled, keep only the official entry.
- If the source cannot be verified, stop instead of guessing.

Fastlane never changes these settings. After any install or enable/disable
change, start a new Codex session in the repository so bundled skills, MCP
tools, and hooks load. See [Existing AWS Core](EXISTING-AWS-CORE.md) for every
branch.

## 8. Start or resume Fastlane

In the new session, send:

```text
init template
```

Fastlane welcomes you, runs the safe repository checks, and responds with one
owner action at a time. If setup pauses or the conversation is interrupted,
send:

```text
continue setup
```

The state reducer rechecks observable evidence and resumes at the first
unresolved step. Repository checks cannot prove global plugin or hook state;
those observations must occur in the supported Codex session.

## 9. Review the AWS Core hook

When Fastlane reports `HOOK_REVIEW_REQUIRED`, enter:

```text
/hooks
```

Confirm the current safety hook comes from official AWS Core. Review every
other enabled hook that can match shell or AWS MCP tools; Codex can run multiple
matching hooks concurrently. Unknown or conflicting hook sources stop setup.

Trust the exact current definition yourself through Codex. Never use
`--dangerously-bypass-hook-trust`. Installation or enablement does not
automatically trust a plugin hook, and a changed definition requires review
again.

Then send `continue setup`. Fastlane asks Codex to run two local shell probes.
They must run through Codex so the `PreToolUse` hook sees them; do not run them
as ordinary terminal tests.

Expected deny probe:

```text
python3 -c "if False: client.get_secret_value(SecretId='FASTLANE_SYNTHETIC_DO_NOT_USE')"
```

The hook must block it before execution. The `if False` body is inert and no
AWS request should occur.

Expected allow probe:

```text
python3 -c "print('FASTLANE_HOOK_ALLOW_PROBE')"
```

It must print exactly:

```text
FASTLANE_HOOK_ALLOW_PROBE
```

The probes use no AWS credentials, secret values, or AWS account access.

## 10. Prove that AWS Core is being used

Installation alone is not proof. When Fastlane reports
`AWS_CORE_HANDSHAKE_REQUIRED`, explicitly invoke the plugin:

```text
@AWS Core
VERIFY AWS CORE AND CONTINUE FASTLANE
```

A passing receipt must identify the official plugin source and show live
success for both:

- `retrieve_skill`, including the retrieved skill identifier; and
- `search_documentation`, including the query and returned AWS source links.

BOOT-00 must not call `call_aws`, `run_script`, an AWS account API, credential
tools, or a generic documentation connector as a substitute. Model memory,
prior chat content, and installation metadata are not proof.

## 11. Begin guided intake

After repository checks, hook probes, and both AWS Core capability calls pass,
Fastlane returns `READY_FOR_INTAKE`. Send:

```text
START GUIDED INTAKE
```

Setup is complete. No AWS credentials were configured or checked and no AWS
account was accessed. Continue with [the Fastlane workflow](WORKFLOW.md).

## Expected setup progress

| Progress | Outcome |
|---|---|
| Step 1 of 4 | Template and local tools verified |
| Step 2 of 4 | One official AWS Core source verified |
| Step 3 of 4 | Hook reviewed and deny/allow probes passed |
| Step 4 of 4 | Live AWS Core skill and documentation calls passed |

For failures, see [Troubleshooting](TROUBLESHOOTING.md). For why Fastlane follows
the moving official source, see [Dependency policy](DEPENDENCY-POLICY.md).
