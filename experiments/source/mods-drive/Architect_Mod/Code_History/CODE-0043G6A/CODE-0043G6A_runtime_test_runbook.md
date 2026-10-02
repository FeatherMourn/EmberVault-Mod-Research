# CODE-0043G6A runtime-test runbook

This is an observe-only candidate. Do not deploy it to the installed game directory or treat the package as live proof without an approved runtime session.

1. Use one clean Enshrouded 1076226 session and the exact candidate package. Preserve the existing install and capture directory separately.
2. Open F7 -> Developer & Diagnostics. Start the native observation with `BEGIN CORRELATION`.
3. Select and mark each phase once, in order: BASELINE_IDLE, WALK, SPRINT_ACTIVE, SPRINT_RECOVERY, JUMP, POST_JUMP_RECOVERY, COMBAT_IDLE, MENU. Use the canonical MARK PHASE control; do not hand-edit command envelopes.
4. Exercise only the observe-only movement/stamina scenarios. Do not invoke mutation actions, patches, teleport, auto-loot, glider, or any unqualified feature.
5. End with the canonical END CAPTURE control, then copy the command, capture, status, and report artifacts into a new timestamped evidence directory. Do not merge with older bridge output.
6. Run `tools/CheatCorrelation/analyze_capture.py` against the new capture. A runtime result is valid only if build identity, phase sequence, sample bounds, and analyzer output all agree.

Expected artifact set: correlation command log, capture JSONL, native status, correlation status, report JSON/Markdown, and analyzer output. Any missing, stale, ambiguous, or build-mismatched artifact is a failed runtime attempt requiring a new clean session.

This runbook does not authorize mutation and does not itself establish runtime/gameplay proof.
