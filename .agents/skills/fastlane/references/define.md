# Define phase

Use for BOOT-00, INTAKE-10, REQ-10, and Gate A.

- Initialize dry-run-first or resume the derived stage. Never repeat completed
  setup questions.
- Ask no more than three related, plain-language owner decisions per response.
- Separate owner facts, repository facts, recommendations, proposed
  assumptions, and unresolved decisions.
- Give requirements and assumptions stable IDs and observable acceptance
  criteria. Preserve brownfield behavior and protected user work.
- Default cost posture to `MINIMIZE_TOTAL_COST; HARD_CAP_NOT_STATED`; preserve
  an owner cap exactly.
- Quick MVP uses no challenger by default. Use the requirements challenger only
  for ambiguity, contradictions, sensitive data, identity, payments,
  migrations, shared interfaces, high risk, or explicit owner request.
- Use AWS Core only when a current AWS fact materially affects feasibility.
- The coordinator writes analysis and the readiness card; only the owner may
  approve the exact Gate A receipt.
