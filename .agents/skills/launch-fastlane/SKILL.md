---
name: launch-fastlane
description: Delegate Fastlane initialization or resume. Use only when explicitly invoked by a compatibility workflow.
---

# Launch Fastlane Compatibility Alias

Delegate to `$fastlane` and preserve the user's `init template`, initialize,
resume, or BOOT-00 intent. Do not run an independent lifecycle, repeat setup
questions, or render a second status. The `fastlane` coordinator owns routing,
writes, checkpoints, and owner conversation.
