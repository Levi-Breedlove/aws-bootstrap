# Security Policy

## Supported state

Security corrections are applied to `main` and its current release artifact.

## Report a concern

Use GitHub's private vulnerability reporting for this repository when it is
available. Otherwise, contact the repository owner privately before publishing
details that would make exploitation easier. Do not include credentials,
customer data, production identifiers, or active access tokens in a report.

Include the affected version or commit, the observable behavior, a minimal
reproduction using synthetic data, and the safeguard that should have held.

## Expected controls

This template and generated projects should prove that:

- approved access succeeds and unapproved access is denied;
- secrets stay out of code and logs, including source, fixtures, and release
  artifacts;
- invalid or oversized input is rejected at the boundary;
- IAM permits only required actions;
- sensitive data uses approved encryption;
- AWS Core is loaded only from the official Agent Toolkit repository revision
  pinned in the validated repo marketplace; a changed source or revision stops
  bootstrap dependency validation;
- Codex client installation, repository-marketplace registration, plugin
  selection, session launch, and hook trust are owner-run steps; Fastlane gives
  exact instructions but never performs those actions;
- the uv assistant provides owner-run instructions only; it never executes a
  package manager, installer, runtime probe, or child process and never
  forwards the adopter's environment;
- Codex login, plugin installation, hook trust, client paths, usernames, and
  session history remain in the adopter's local Codex profile and are never
  written into tracked files, `bootstrap.yaml`, or the release ZIP;
- executable plugin hooks remain disabled until the owner reviews and trusts
  the exact current definition; Fastlane never bypasses hook trust;
- deployment and teardown remain inside the named account, Region,
  environment, resource, operation, cost, rollback, and expiration boundary.

Do not hide a discovered defect to keep a review green. Record product defects
in `docs/project/BUGFIX.md` or an authorized private issue and preserve evidence without
publishing sensitive details.
