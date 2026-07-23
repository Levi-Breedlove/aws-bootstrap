# AWS Codex Fastlane Setup

Fastlane verifies its local planning tools before changing a fresh template.
Every check is read-only and every installation action remains owner-run.

## Normal first run

1. Install Codex CLI from the
   [official getting-started guide](https://learn.chatgpt.com/docs/codex/cli#getting-started),
   then sign in:

   ```text
   codex --version
   codex login
   codex login status
   ```

2. Create a repository with **Use this template**, open it in interactive
   Codex CLI, and send `init template`.
3. Fastlane checks Git, Python 3.11+, platform sandbox support, `uvx`, and
   official AWS Core. If anything is missing, it gives one copyable checklist.
4. Send `init template` again after completing that checklist.
5. Answer project name, preferred AWS Region, and optional budget exactly once.
6. Fastlane configures the template dry-run-first and begins Define.

If you do not have a hard budget, answer:

```text
minimize cost; no hard cap
```

## Official AWS Core

Fastlane uses the current official AWS Core from
`aws/agent-toolkit-for-aws`. It does not pin an AWS Core version or commit.
Installation and hook trust remain in the adopter's local Codex profile.

The prerequisite checklist reuses official AWS Core when already available.
When missing:

1. In interactive Codex, open `/plugins`.
2. If **Agent Toolkit for AWS** is absent, exit Codex and run:

   ```text
   codex plugin marketplace add aws/agent-toolkit-for-aws
   ```

3. Reopen `/plugins`, select **AWS Core** under **Agent Toolkit for AWS**,
   and enable it.
4. Restart Codex, reopen the project, and send `init template`.
5. Codex verifies attributable `retrieve_skill` and `search_documentation`
   capabilities without inspecting AWS credentials or accessing an account.

If Codex asks you to review plugin hooks, use its native `/hooks` screen.
Fastlane does not compare hook hashes, request screenshots, run synthetic hook
probes, inspect private trust storage, or ask for a separate trust receipt.

Official reference:

- [AWS Agent Toolkit plugin setup](https://docs.aws.amazon.com/agent-toolkit/latest/userguide/plugins.html)

## Platform prerequisites

### Linux or WSL2 sandbox

```bash
sudo apt update
sudo apt install bubblewrap
command -v bwrap
bwrap --version
```

WSL1 is unsupported; convert the distribution to WSL2 first.

### Astral uv

Fastlane first suggests `pipx install uv` when `pipx` is already available.
Otherwise it uses the current official Astral command for the detected platform.
Always verify:

```text
uvx --version
```

See the [official Astral installation guide](https://docs.astral.sh/uv/getting-started/installation/).

## Privacy and authority

Fastlane never stores Codex login data, plugin state, hook trust, usernames,
machine paths, CLI versions, AWS credentials, or AWS account details in the
template. Prerequisite observations exist only for the current check.

AWS Core may provide documentation and planning advice. It cannot approve
Gate A, Gate B, or an AWS change. Prerequisite success grants no AWS access.
AWS mutations still require the exact authorization record defined by
Fastlane.
