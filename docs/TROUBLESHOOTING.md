# Troubleshooting Fastlane

Run these read-only checks from the repository root:

```text
python scripts/bootstrap_dependencies.py --root . --json
python scripts/bootstrap_doctor.py --root . --json
```

## `init template` keeps repeating setup

Read the doctor's `next_prompt`. If it is `INTAKE-10` or later, continue
that prompt and do not rerun BOOT-00. Missing AWS Core is not a reason to return
to setup.

## Two AWS Core entries or four hooks appear

An older template may have registered **AWS Codex Fastlane Dependencies** in
addition to the official **Agent Toolkit for AWS** marketplace.

1. Keep **AWS Core** under **Agent Toolkit for AWS**.
2. Disable or uninstall the copy under **AWS Codex Fastlane Dependencies**.
3. Optionally remove the retired marketplace:

   ```text
   codex plugin marketplace remove aws-codex-fastlane-dependencies
   ```

Never run the retired `codex plugin marketplace add .` command.

## AWS Core is missing during design

Project intake and Gate A can continue without it. When an AWS-specific design
step needs current AWS facts:

1. Open `/plugins`.
2. If **Agent Toolkit for AWS** is absent, run:

   ```text
   codex plugin marketplace add aws/agent-toolkit-for-aws
   ```

3. Enable **AWS Core** under **Agent Toolkit for AWS**.
4. Restart Codex and send:

   ```text
   CONTINUE AWS DESIGN
   ```

Do not install a second AWS Core when the official one is already available.
Fastlane does not pin the plugin version or commit.

## Codex CLI or local runtime is missing

Use the [official Codex CLI getting-started guide](https://learn.chatgpt.com/docs/codex/cli#getting-started).
Linux or WSL sandbox prerequisites and optional `uv` commands are in
[SETUP.md](SETUP.md). Installation remains owner-run.

## AWS Core research fails

Stop only the affected design or AWS operating step. Confirm the capability is
coming from `aws-core@agent-toolkit-for-aws`, restart Codex once, and retry
the same step. Do not restart project initialization, request hook screenshots,
compare hook hashes, or run synthetic probes.

## Doctor reports another blocker

Follow the single diagnostic named by the doctor. Preserve the repository,
dirty files, approved gates, and project ledgers; do not regenerate an active
project to clear an error.
