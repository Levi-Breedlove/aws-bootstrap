# Contributing

Contributions should keep AWS Codex Fastlane understandable to a first-time
user and mechanically safe for a long-running agent.

## Before opening a pull request

1. Start from the current `main` branch and keep the change focused.
2. Preserve the two-gate lifecycle and exact authorization boundaries.
3. Update the manifest when a release file is added, removed, moved, or changed.
4. Run:

   ```bash
   python -m unittest discover -s tests -v
   python scripts/package_release.py --check
   ```

5. Review the generated archive inventory and confirm no ZIP, checksum, secret,
   credential, local state, or user-specific path is tracked.

## Pull request expectations

Explain the user-visible outcome, why it is needed, affected contracts, tests
run, and any remaining AWS-only verification. Keep one authoritative home for
each fact rather than adding duplicate planning documents.

Changes that alter Gate A, Gate B, task states, AWS authorization, evidence, or
release behavior require matching runtime tests. User-facing instructions must
route directly to the real bootstrap action.
