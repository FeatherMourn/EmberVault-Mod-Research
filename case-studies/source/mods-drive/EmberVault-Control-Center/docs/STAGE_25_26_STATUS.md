# Stages 25–26 — Distribution and Stable Release

## Delivered

- Release-channel and platform-aware update checks.
- Backup-before-update planning with user-data preservation.
- Hash-based repair planning that refuses automatic repair.
- Data-preserving uninstall planning that separates installation removal from
  user data.
- Fail-closed release-candidate audit based on Capability Governance Stable
  decisions.
- Control Center governance display for release-candidate readiness.
- Portable `1.0.0rc1` Windows and Linux bundles built from the validated wheel.
- Standalone distribution verifier and isolated installed-wheel smoke test.

## Safety and release boundary

Updates, repairs, and uninstall are review-only plans until an explicit,
recoverable installer workflow is approved. User data is preserved by design.
The 1.0 release candidate cannot claim Stable capabilities without complete
reproducibility, runtime, recovery, compatibility, ownership, and rollback
evidence. Unsupported live gameplay mutation remains outside the release claim.

## Verification

The release workflow is validated through unit tests, compilation, offscreen UI
smoke testing, isolated wheel installation, Windows/Linux bundle verification,
fresh wheel asset verification, and standalone catalog validation.
