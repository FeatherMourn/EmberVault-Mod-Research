# Capability Boundaries

This summary carries forward the original Control Center’s verified capability audit. It is intentionally conservative: a feature is not treated as stable merely because a test can demonstrate part of it.

## Verified boundaries

- Module lifecycle and recovery workflows can be isolated and restored.
- Safe resource metadata lookup is supported by the original research baseline.
- Clone-only render-model assignment has been verified for the documented build boundary.
- Offline builder workflows can be prepared and reviewed without changing the live game.

## Experimental boundaries

- Identity, localization, and recipe-layout changes require build-specific validation.
- Module lifecycle deployment and game-tuning writes require a verified connector and rollback point.

## Research-only boundaries

- Original mesh asset import.
- Custom interactions, AI enemy archetypes, quest progression, animation, and world-generation changes.
- Visual substitutions and advanced resource-backed catalogs.

## Unsupported boundary

- Multiplayer authority changes are not treated as supported by the Control Center.

Always check the active game build, preserve a verified backup, and keep research-only behavior isolated from normal profiles.
