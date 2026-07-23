# Owner responses

- Lead with plain-language project status, not internal execution narration.
- Render routine status with `python scripts/fastlane_presenter.py owner
  --input-stdin`; do not hand-compose lifecycle routing.
- Present one concrete owner action. When none is needed, continue the selected
  phase instead of pausing at an internal checkpoint.
- Do not expose hashes, file counts, prompt IDs, or exhaustive receipts in
  routine conversation.
- Answer side questions directly, state whether project state changed, and
  restore the pending owner action with `python scripts/fastlane_presenter.py
  side-question --input-stdin` after rerunning the doctor.
- A side question never repeats a formal Gate A, Gate B, or AWS receipt. It
  restores the current deterministic action, including the existing approval
  action when one is pending.
- A pre-Gate-A AWS example must say:
  `Illustrative architecture candidate — not selected or approved.`
- Use `explain-fastlane` only for an explicit explanation request.
