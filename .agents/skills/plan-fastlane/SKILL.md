---
name: plan-fastlane
description: Turn a rough AWS project idea or brownfield change into owner-approved requirements and a complete technical PRD. Use for guided intake, requirements analysis, Gate A, AWS design, Gate B, assumptions, acceptance criteria, or construction-boundary planning.
---

# Plan Fastlane

1. Read the root `AGENTS.md`, current `docs/project/PRD.md`, and only the canonical prompt
   section named by the doctor.
2. Run `python scripts/bootstrap_dependencies.py --root . --json` and require
   the current task's explicit `@AWS Core` verification receipt with successful
   `retrieve_skill` and `search_documentation` checks. A generic AWS
   documentation connector is insufficient. Then run
   `python scripts/bootstrap_doctor.py --root . --json` before writing.
   Continue only through `INTAKE-10`, `REQ-10`, `INTAKE-20`, `DESIGN-10`, or
   `DESIGN-20` as returned.
3. During intake, ask no more than three related plain-language questions at a
   time. Separate owner facts, repository facts, recommendations, proposed
   assumptions, and open decisions.
4. Give requirements and assumptions stable IDs and make acceptance criteria
   observable. Preserve the brownfield contract when applicable.
5. Use the read-only `fastlane-requirements-reviewer` for Gate A analysis and
   the read-only `fastlane-aws-advisor` when AWS feasibility or design facts
   are material. The coordinator remains the sole PRD and lifecycle writer.
6. Use AWS Core and current primary AWS documentation when a service fact
   affects requirements, a gate recommendation, or design. Record what was
   verified and any unavailable fact. Do not require AWS credentials and do
   not access an AWS account during planning.
7. Let the agent populate analysis and readiness cards. Require the exact
   current owner receipt for Gate A and Gate B; never accept assumptions or
   approve either gate on the owner's behalf.
8. Update only the files permitted by the active prompt and keep
   `bootstrap.yaml` as a derived mirror.
9. Run the doctor after each coordinator checkpoint and return its next route.

Stop when a material owner choice is missing, a source conflicts, an approval
is stale, or the proposed design or construction boundary exceeds the approved
requirements.
AWS Core and every project agent are advisors only; neither can approve a gate
or turn available AWS tools into authorization.
