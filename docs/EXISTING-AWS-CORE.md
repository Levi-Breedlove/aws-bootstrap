# Existing AWS Core

Reuse an existing official AWS Core. Do not reinstall it merely because
Fastlane starts or because `init template` is sent again.

The accepted source is:

```text
Marketplace: aws/agent-toolkit-for-aws
Plugin: aws-core@agent-toolkit-for-aws
```

Fastlane follows the current official release and does not pin a version or
commit.

## What to do

| What you see | Action |
|---|---|
| One AWS Core under **Agent Toolkit for AWS** | Keep it and continue |
| Official AWS Core is disabled | Enable it, restart Codex, and resume the affected AWS step |
| Agent Toolkit marketplace is absent | Run `codex plugin marketplace add aws/agent-toolkit-for-aws`, then enable AWS Core |
| Both official and **AWS Codex Fastlane Dependencies** copies | Keep the official copy; disable or uninstall the retired copy |
| Only the retired Fastlane copy | Add the official marketplace, enable official AWS Core, then remove the retired copy |
| Unknown AWS Core source | Do not use it for Fastlane evidence; select the official source |

The retired local marketplace can be removed with:

```text
codex plugin marketplace remove aws-codex-fastlane-dependencies
```

Never register the repository itself with `codex plugin marketplace add .`.

Codex owns plugin installation and hook trust in its native UI. Fastlane does
not compare cached hook files, request screenshots, run synthetic probes, or
create a separate trust receipt.
