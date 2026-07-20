---
name: plan-fastlane
description: Turn a rough AWS project idea or brownfield change into owner-approved requirements and a complete technical PRD. Use for guided intake, requirements analysis, Gate A, AWS design, Gate B, assumptions, acceptance criteria, or construction-boundary planning.
---

# Plan Fastlane

1. Read the root `AGENTS.md`, current `docs/project/PRD.md`, and only the canonical prompt
   section named by the doctor.
2. Run `python scripts/bootstrap_dependencies.py --root . --json` and require
   the current session's completed BOOT-00 verification for
   `aws-core@agent-toolkit-for-aws`, including successful live `retrieve_skill`
   and `search_documentation` calls. A generic AWS documentation connector,
   installation record, or prose claim is insufficient. Then run
   `python scripts/bootstrap_doctor.py --root . --json` before writing.
   Continue only through `INTAKE-10`, `REQ-10`, `INTAKE-20`, `DESIGN-10`, or
   `DESIGN-20` as returned.
3. During intake, ask no more than three related plain-language questions at a
   time. Separate owner facts, repository facts, recommendations, proposed
   assumptions, and open decisions.
4. Give requirements and assumptions stable IDs and make acceptance criteria
   observable. Default to `MINIMIZE_TOTAL_COST; HARD_CAP_NOT_STATED`; preserve
   an owner-supplied cap's exact ISO currency and amount as
   `MINIMIZE_TOTAL_COST; HARD_CAP: <ISO_CURRENCY> <OWNER_AMOUNT>` (for example,
   `MINIMIZE_TOTAL_COST; HARD_CAP: USD 20.00`); ask for a
   number only when the owner has a hard cap or a material decision requires
   one. Preserve the brownfield contract when applicable.
5. Use the read-only `fastlane-requirements-reviewer` for Gate A analysis and
   the read-only `fastlane-aws-advisor` when AWS feasibility or design facts
   are material. The coordinator remains the sole PRD and lifecycle writer.
6. Use AWS Core and current primary AWS documentation when a service fact
   affects requirements or a gate recommendation. For every `DESIGN-10` run,
   make fresh live `retrieve_skill` and `search_documentation` calls through
   `aws-core@agent-toolkit-for-aws` for the proposed architecture. Record in
   `docs/project/VERIFY.md` one independently attributed row for each
   capability. Each row records source `aws/agent-toolkit-for-aws`, identity
   `aws-core@agent-toolkit-for-aws`, observed current semantic version, actor
   `CODEX_LIVE_TOOL_CALL`, capability input/output, decision influenced,
   observation time, current DES-revision binding, PASS/FAIL,
   `Credentials inspected` = `NO`, and `AWS account accessed` = `NO`; the
   documentation row also records returned official AWS sources. Missing,
   failed, generic, unattributed, cached, or stale evidence blocks Gate B
   readiness. Do not require AWS credentials or access an AWS account during
   planning, and do not pin evidence to the last-tested plugin version.
7. For greenfield design, evaluate a secure managed serverless baseline first.
   Minimize total expected cost and idle resources, preserve required security
   and recovery controls, compare scaling breakpoints, and record measurable
   expansion triggers. Do not force serverless when verified workload fit says
   otherwise.
8. Let the agent populate analysis and readiness cards. Require the exact
   current owner receipt for Gate A and Gate B; Gate A must bind the exact
   readiness-card cost posture. Never accept assumptions or approve either gate
   on the owner's behalf.
9. Update only the files permitted by the active prompt and keep
   `bootstrap.yaml` as a derived mirror.
10. Run the doctor after each coordinator checkpoint and return its next route.

Stop when a material owner choice is missing, a source conflicts, an approval
is stale, or the proposed design or construction boundary exceeds the approved
requirements.
AWS Core and every project agent are advisors only; neither can approve a gate
or turn available AWS tools into authorization.
