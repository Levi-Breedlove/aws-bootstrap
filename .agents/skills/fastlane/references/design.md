# Design phase

Use for DESIGN-10 and Gate B.

- Complete the whole-system architecture, security, data, failure, recovery,
  operations, cost, deployment, rollback, teardown, and verification design.
- Use official current AWS Core directly for material current AWS facts and
  record attributable documentation evidence. Generic connectors, memory, or
  challenger prose cannot replace those calls.
- Derive `DRV-*` records from approved requirements. Compare credible
  whole-system `CAND-*` designs against hard constraints first, then
  preferences. Evaluate a secure managed-serverless baseline for greenfield
  work unless a hard constraint makes it ineligible; never add a straw option
  or use arbitrary numerical scoring.
- Select one eligible `ARCH-*` as an agent recommendation. Record every
  rejected candidate, risk, mitigation, cost effect, scaling breakpoint,
  revisit trigger, and validation method. Use `NO_VIABLE_ALTERNATIVE` only when
  exactly one candidate satisfies the hard constraints.
- Map every approved requirement to the selected `ARCH-*`, concrete
  `COMP/API/DATA/CTRL` IDs, applicable property/test IDs, and `AWS-EV-*` IDs.
  Keep detailed live AWS Core invocation evidence in `docs/project/VERIFY.md`.
- Use the architecture challenger only after the proposal is complete and only
  for high-risk, hard-to-reverse, shared-infrastructure, isolation, recovery,
  or explicitly requested review.
- Require the challenger to return unsupported claims, unmet requirements,
  hard-constraint failures, IAM/isolation/recovery/cost/operations gaps, and
  concerns with rejected alternatives using current IDs. The coordinator fixes
  valid findings or records an evidence-backed rejection.
- The coordinator accepts or rejects each finding with evidence, updates
  existing Mermaid diagrams in place with the selected `ARCH-*` as their
  shared basis, and remains the sole writer.
- Require a current Gate A, complete readiness card, canonical construction
  envelope digest, selected architecture, complete traceability, current
  material AWS evidence, and exact owner Gate B receipt.
