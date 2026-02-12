## Release-gate review instructions (en-US)

You are reviewing a **release candidate** diff where:
- **base** = previous release tag
- **head** = main

**Hard constraints**
- Provide ONLY one high-level walkthrough (no “getting ready”, no progress/status chatter).
- Do NOT include: related issues/PRs, suggested reviewers/labels, poems, casual conversation.

**What to produce**
1) Walkthrough grouped by topic:
   - Source changes
   - Examples changes
   - Tests changes
   - Docs changes (if any)
2) Breaking changes:
   - Explicit list of breaking changes
   - Who is impacted
   - Suggested migration/fixes (if not already applied)
3) Compatibility considerations:
   - Backward-compatibility risks
   - Default behavior changes
   - Public API / contract changes
4) User experience feedback (only if it affects behavior, clarity, or stability)

**Non-goals**
- Ignore style/lint-only feedback unless it changes behavior or public API.