---
name: plan-fastlane
description: Turn a rough AWS project idea or brownfield change into owner-approved requirements and a complete technical PRD. Use for guided intake, requirements analysis, Gate A, AWS design, Gate B, assumptions, acceptance criteria, or construction-boundary planning.
---

# Plan Fastlane

1. Read the root `AGENTS.md`, current `PRD.md`, and only the canonical prompt
   section named by the doctor.
2. Run `python scripts/bootstrap_doctor.py --root . --json` before writing.
   Continue only through `INTAKE-10`, `REQ-10`, `INTAKE-20`, `DESIGN-10`, or
   `DESIGN-20` as returned.
3. During intake, ask no more than three related plain-language questions at a
   time. Separate owner facts, repository facts, recommendations, proposed
   assumptions, and open decisions.
4. Give requirements and assumptions stable IDs and make acceptance criteria
   observable. Preserve the brownfield contract when applicable.
5. Use current primary AWS documentation when a service fact affects design.
   Do not require AWS credentials and do not access an AWS account during
   planning.
6. Let the agent populate analysis and readiness cards. Require the exact
   current owner receipt for Gate A and Gate B; never accept assumptions or
   approve either gate on the owner's behalf.
7. Update only the files permitted by the active prompt and keep
   `bootstrap.yaml` as a derived mirror.
8. Run the doctor after each coordinator checkpoint and return its next route.

Stop when a material owner choice is missing, a source conflicts, an approval
is stale, or the proposed design or construction boundary exceeds the approved
requirements.
