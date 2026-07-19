# Application Engineering Guide

These instructions apply under `app/` and inherit the root `AGENTS.md`.

## Plain-language summary

Build only the approved application behavior. Keep access checks on the server,
validate outside input, keep secrets out of code and logs, preserve approved
interfaces, and prove the result with observable tests. The exact task boundary
and completion evidence remain in `../docs/project/TASKS.md` and `../docs/project/VERIFY.md`.

## Agent reference — exact application rules

- Follow the existing framework and module boundaries before adding abstractions.
- Keep business logic separate from transport, persistence, and provider integration.
- Validate and bound external input at the application boundary.
- Enforce authorization server-side.
- Avoid exposing stack traces, internal identifiers, secrets, or sensitive fields.
- Use structured, minimal, safe logging.
- Make dependency timeouts and retries explicit.
- Preserve backward compatibility unless an approved requirement changes it.
- Add tests for success, invalid input, authorization, boundaries, concurrency, and dependency failures.
- Do not put AWS credentials or privileged AWS logic in client-side code.

## Completion

Run the application formatter, linter, type checker, tests, build, and relevant security checks before claiming completion.

Do not repeat requirements or design here. Refer to `../docs/project/PRD.md`. Execute work from `../docs/project/TASKS.md`.
