# AWS Codex Fastlane Setup

Fastlane keeps first run intentionally small. Project intake does not wait for
AWS Core, hook review, AWS credentials, or an AWS account.

## Normal first run

1. Create a repository with **Use this template** and open it in Codex.
2. Send:

   ```text
   init template
   ```

3. Answer the project name, preferred AWS Region, and development budget.
4. Codex configures the template, runs the doctor, and begins guided intake.

If you do not have a hard budget, answer:

```text
minimize cost; no hard cap
```

No plugin setup is required to complete intake or Gate A.

## Official AWS Core

Fastlane uses the current official AWS Core from
`aws/agent-toolkit-for-aws`. It does not pin an AWS Core version or commit.
Installation and hook trust remain in the adopter's local Codex profile.

When technical AWS design begins, Codex first reuses AWS Core if it is already
available. If it is missing, Codex gives this one-time setup:

1. In interactive Codex, open `/plugins`.
2. If **Agent Toolkit for AWS** is absent, exit Codex and run:

   ```text
   codex plugin marketplace add aws/agent-toolkit-for-aws
   ```

3. Reopen `/plugins`, select **AWS Core** under **Agent Toolkit for AWS**,
   and enable it.
4. Restart Codex, reopen the project, and send:

   ```text
   CONTINUE AWS DESIGN
   ```

If Codex asks you to review plugin hooks, use its native `/hooks` screen.
Fastlane does not compare hook hashes, request screenshots, run synthetic hook
probes, or ask for a separate trust receipt.

Official references:

- [AWS Agent Toolkit plugin setup](https://docs.aws.amazon.com/agent-toolkit/latest/userguide/plugins.html)
- [Codex plugins](https://learn.chatgpt.com/docs/plugins)

## Missing local tools

Install only what your chosen Codex surface actually needs.

### Codex CLI

Follow the [official getting-started guide](https://learn.chatgpt.com/docs/codex/cli#getting-started),
then verify:

```text
codex --version
codex login
codex login status
```

### Linux or WSL sandbox

```bash
sudo apt update
sudo apt install bubblewrap
command -v bwrap
bwrap --version
```

### Astral uv

AWS Core uses `uvx`. On Linux or WSL with `pipx` already installed:

```bash
pipx install uv
uvx --version
```

On Windows:

```powershell
winget install --id astral-sh.uv --exact --source winget
uvx --version
```

See the [official Astral installation guide](https://docs.astral.sh/uv/getting-started/installation/)
for other supported methods.

## Privacy and authority

Fastlane never stores Codex login data, plugin state, hook trust, usernames,
machine paths, AWS credentials, or AWS account details in the template.

AWS Core may provide documentation and planning advice. It cannot approve
Gate A, Gate B, or an AWS change. AWS mutations still require the exact
authorization record defined by Fastlane.
