# Security Policy

## Supported version

Security corrections are applied to the latest release and `main`.

## Report a concern

Use GitHub's private vulnerability reporting for this repository when it is
available. Otherwise, contact the repository owner privately before publishing
details that would make exploitation easier. Do not include credentials,
customer data, production identifiers, or active access tokens in a report.

Include the affected version or commit, the observable behavior, a minimal
reproduction using synthetic data, and the safeguard that should have held.

## Expected controls

Contributions and generated projects should prove that:

- approved access succeeds and unapproved access is denied;
- secrets stay out of code and logs, including source, fixtures, and release
  artifacts;
- invalid or oversized input is rejected at the boundary;
- IAM permits only required actions;
- sensitive data uses approved encryption;
- deployment and teardown remain inside the named account, Region,
  environment, resource, operation, cost, rollback, and expiration boundary.

Do not hide a discovered defect to keep a review green. Record product defects
in `BUGFIX.md` or an authorized private issue and preserve evidence without
publishing sensitive details.
