# ShroudForge external research audit

## Source

- Repository: https://github.com/bonsaibauer/shroudforge
- Reviewed reference: tag `1.6.6`
- Retrieved: 2026-10-13
- License shown by the repository: MIT
- Scope: external architecture and documentation review only

## Classification

`partially-verified` / `external-reference`

This audit records what the public repository documents. It does not promote
ShroudForge runtime behavior to Ember Vault capability and does not authorize
installation, live-game modification, process hooks, or in-game testing.

## Reusable research areas

- Build-scoped profiles and target-specific capability boundaries.
- Mod manifest, identifier, Lua entry-point, and syntax validation.
- EML-style package and API conventions.
- Offline authoring concepts: templates, settings metadata, API reference, and
  package layout.
- Mod discovery, update staging, and backup-oriented workflow concepts for a
  future Mod Manager comparison.
- World Editor evidence boundaries, including separate treatment of placement,
  persistence, multiplayer routing, and undo reliability.
- Explicit distinction between proven, beta, and open capabilities.

## Evidence limits

- The repository documents a current client profile for build `1076226`, but
  that does not establish compatibility with every Ember Vault build.
- Runtime hooks, KFC/ECS access, EML compatibility, multiplayer behavior, and
  world-editor persistence are described as beta or requiring additional live
  validation.
- A declared client/server target does not prove end-to-end gameplay behavior.
- ShroudForge evidence remains external evidence until independently reproduced
  and recorded in Ember Vault's own evidence model.

## Ember Vault mapping

| Area | Use | Boundary |
|---|---|---|
| Mod Research | Index external APIs, profiles, package conventions, and limitations | Read-only reference; no automatic capability promotion |
| Content Creator | Compare templates, manifests, settings, and compatibility metadata | Design-only; runtime remains unverified |
| Mod Manager | Study discovery, update, staging, and backup workflows | Control Center owns mutations and recovery |
| Game Tuning | Reference settings and profile concepts | No runtime hook adoption from this audit |
| Troubleshooter | Add external failure-mode and compatibility categories | Diagnostic evidence only |

## Decision

Use ShroudForge as a high-value external reference and comparison target. Do
not copy runtime code or depend on it until source/dependency review, license
preservation, build compatibility review, and independent evidence capture are
complete. The next safe follow-up is to compare its manifest/profile/settings
metadata against the existing Content Creator and Mod Manager contracts using
synthetic fixtures only.
