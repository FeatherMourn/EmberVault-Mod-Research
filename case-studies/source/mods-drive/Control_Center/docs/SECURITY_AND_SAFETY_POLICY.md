# Security and Safety Policy

## Scope

Control Center is a local mod-authoring and recovery tool. It must preserve the
game installation, keep experimental work isolated, and make every mutation
reviewable and reversible.

## Safety rules

- Never edit vanilla archives or game binaries in place when a runtime or
  project-local route is available.
- Validate paths, manifests, resource types, game build, and EML build before
  a module runs.
- Treat unknown capabilities and unverified resource types as restricted.
- Keep research probes out of the stable profile unless the user explicitly
  adopts verified evidence.
- Create and verify backups before owned deployment or configuration changes.
- Use quarantine and recorded-version restore after an authoritative failure.
- Do not silently overwrite user-owned files or silently downgrade releases.
- Stop a probe on panic, crash, invalid registration, or unexpected resource
  mutation; preserve the log and evidence instead.

## Trust boundaries

Control Center does not claim that a valid JSON definition, imported image, or
successful offline compilation proves that the game will consume the content.
Runtime evidence is required for each promoted capability. Client-only results
must not be described as multiplayer-safe.

## Recovery

If launch or shutdown fails, use the stable/recovery profile, inspect the health
report, quarantine the identified module, and restore the recorded version.
Keep the original evidence and recovery report for diagnosis. Never delete a
backup merely to make a failed profile appear healthy.

## Release review

Every release must pass the milestone verifier, include current hashes and
version metadata, preserve user files during upgrade/uninstall checks, and
identify stable, experimental, research-only, and unsupported capabilities.
