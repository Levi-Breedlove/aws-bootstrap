# Existing AWS Core Installations

Fastlane reuses an existing official AWS Core installation. It does not require
a private copy or a frozen marketplace entry.

## Required identity

The only accepted source is:

```text
Marketplace repository: aws/agent-toolkit-for-aws
Marketplace identity:   agent-toolkit-for-aws
Plugin identity:        aws-core@agent-toolkit-for-aws
Dependency policy:      OFFICIAL_CURRENT
```

An AWS Core name or version alone is not enough to prove source identity.
Inspect the marketplace group and plugin details in `/plugins`.

## Inspect your installation

1. Use Codex CLI or another plugin-capable Codex surface.
2. Enter `/plugins`.
3. Open the Installed view and the marketplace groups.
4. Record every enabled entry named AWS Core and its marketplace.
5. Follow the matching branch below.

Fastlane can reason from current-session observations and owner-confirmed
details, but it must not inspect or persist your global Codex profile.

## Decision table

| What you find | Owner action | Fastlane result |
|---|---|---|
| Official AWS Core installed and enabled | Reuse it; start a new session if its state just changed | Continue to hook review |
| Official AWS Core installed but disabled | Enable it and start a new session | `AWS_CORE_ENABLE_REQUIRED` until observed |
| Official marketplace present, plugin absent | Install AWS Core from `/plugins`, then start a new session | `AWS_CORE_INSTALLATION_REQUIRED` |
| Official marketplace absent | Register it with the command below | `OFFICIAL_MARKETPLACE_REQUIRED` |
| Old Fastlane-pinned AWS Core only | Disable it, install the official entry, and start a new session | Installation remains blocked |
| Official and old pinned entries both enabled | Disable the old pinned entry and start a new session | `AWS_CORE_DUPLICATE_BLOCKED` |
| AWS Core from an unknown marketplace | Disable or remove the unknown entry; verify the official source | `AWS_CORE_SOURCE_UNVERIFIED` |
| Official version newer than Fastlane's last-tested version | Keep it; repeat hook review, probes, and live handshake | Do not block on version alone |

Fastlane never installs, enables, disables, removes, or updates a plugin for
you.

## Register the official marketplace

Run this yourself from a terminal if **AWS Agent Toolkit** is absent:

```text
codex plugin marketplace add aws/agent-toolkit-for-aws
```

Then launch Codex, open `/plugins`, install AWS Core, and start a new session.
This is the installation path documented by the
[AWS Agent Toolkit user guide](https://docs.aws.amazon.com/agent-toolkit/latest/userguide/plugins.html).

## Migrate from the old Fastlane pin

Earlier Fastlane revisions advertised a second AWS Core identity from the
`aws-codex-fastlane-dependencies` marketplace. Do not use that entry as a
fallback.

1. Open `/plugins` and identify both sources before changing anything.
2. Disable the old `aws-core@aws-codex-fastlane-dependencies` entry yourself.
3. Register `aws/agent-toolkit-for-aws` if its marketplace is absent.
4. Install or enable `aws-core@agent-toolkit-for-aws` yourself.
5. Start a new Codex session in the repository.
6. Send `continue setup`.
7. Review the current official hook and rerun both probes.
8. Complete the explicit live AWS Core handshake.

Do not edit plugin cache files, copy plugin directories, rewrite hook commands,
or bypass hook trust to perform the migration.

## Why two sources are blocked

Codex identifies a plugin by its plugin and marketplace names, so two entries
called AWS Core can be separately installed. Both may contribute overlapping:

- AWS skills;
- an AWS MCP server and tool names; and
- `PreToolUse` hook definitions.

Codex loads matching hooks from all enabled sources, and multiple matching
command hooks can start concurrently. One source does not replace another.
Duplicate sources therefore make it difficult to prove which plugin supplied a
skill, tool, or blocking decision. Fastlane fails closed until one official
source remains.

See [OpenAI's hook behavior](https://learn.chatgpt.com/docs/hooks) for the
multiple-source execution model.

## Reverification after updates

AWS Core updates when the official marketplace refreshes. A newer version is
not automatically a failure and is not automatically trusted. Start a new
session and repeat:

1. source inspection in `/plugins`;
2. current hook inspection and owner trust in `/hooks`;
3. the inert deny and harmless allow probes; and
4. the explicit `retrieve_skill` and `search_documentation` handshake.

The version recorded by Fastlane is compatibility context, not a security
guarantee. See [Dependency policy](DEPENDENCY-POLICY.md).
