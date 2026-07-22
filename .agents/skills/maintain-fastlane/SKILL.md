---
name: maintain-fastlane
description: Maintain Fastlane prompts, scripts, skills, manifests, packaging, or CI. Use only for framework work, never adopter application planning.
---

# Maintain Fastlane

1. Confirm the request targets the reusable framework, not an adopter project.
2. Read root and scoped `AGENTS.md` files and preserve unrelated changes.
3. Keep lifecycle, receipts, authorization, and package boundaries
   deterministic; skills guide while scripts validate exact state.
4. Change the smallest coherent engine surface and direct regression tests.
   Do not start BOOT/INTAKE/DESIGN/BUILD, add a lifecycle stage, duplicate an
   authority, or hide setup behavior.
5. Refresh `bootstrap.manifest.json` only after source edits are final.
6. Run focused tests, the full suite, manifest and deterministic package
   checks, and `git diff --check` before publication.

Never install software, change Codex/plugin state, inspect credentials, access
an AWS account, approve a gate, or publish beyond the owner's GitHub scope.
