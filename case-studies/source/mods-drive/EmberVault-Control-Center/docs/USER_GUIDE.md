# EmberVault Control Center user guide

## First launch

1. Open Home and choose the Enshrouded installation folder.
2. Confirm the Troubleshooter reports a readable installation.
3. Keep normal play in the Default profile.
4. Use Research or a custom profile for experiments.

## Mods

Open My Mods to import either a local package folder containing `package.json`
or an external mod folder containing `mod.json`, or a ZIP archive containing
either format. External `mod.json` metadata is adapted into EmberVault's
managed package contract without changing the source folder.
Packages are disabled by default and are enabled separately for each profile.
If a package declares `dependencies`, enable those packages first in the same
profile. Disable a package in every profile before removing it; packages that
other installed packages depend on must be removed last. A minimal manifest
looks like this:

```json
{
  "id": "embervault.example-mod",
  "name": "Example Mod",
  "version": "1.0.0",
  "package_type": "mod",
  "dependencies": []
}
```

Enabled packages can be checked with a deployment plan. The plan reports
missing packages and destination conflicts under the configured game `mods`
directory. Deployment is allowed only when every action is `ready`; existing
destinations block the operation, and partial failures remove newly created
destinations. Successful deployments carry an EmberVault ownership marker so
future removal can refuse unmarked or foreign destinations.
The Mods page exposes the same ownership-protected undeploy action. Deployment
records carry a versioned ownership marker, and the service can inspect managed,
external, and invalid destinations without changing them.
Deployment also refuses package sources containing symlinks.
The configured game directory must already exist; deployment will not create a
new game tree.
Only packages with `package_type: "mod"` can deploy to the game `mods` folder;
other package types remain isolated for their own modules.
Mods already present in the game folder with `mod.json` are shown as external
and can be imported deliberately; inspection itself does not copy or modify
them.
Troubleshooter also reports deployment conflicts and missing enabled-package
sources for each profile.

## Save safety

Save Manager can inspect a save folder, create a verified backup, re-verify a
backup, preview a restore, and restore after preserving the current state. It
does not edit save contents. Use Activity to review the recorded operation
history.

## Game Settings

Game Settings are staged per profile and do not modify the live game. Use the
setting buttons to change the selected profile, then export a JSON manifest for
review or import a previously exported manifest. Imports must belong to the
selected profile and use the `staged-only` contract; invalid or mismatched
manifests are rejected before the profile is changed. The tuning audit can
  inspect the staged manifest without applying it.

The experimental EML adapter is separate from ordinary staged settings. It
supports only the evidenced `baseCritChance` field on the pinned EML build.
Use the readiness, preview, staging, deployment, verification, and rollback
controls in that order. Deployment requires the Research profile, a verified
recovery point, and a closed game. A failed or missing EML readback rolls the
owned adapter back; it does not modify the existing Mod Hub.

## Research and tools

Research records belong to a selected profile and can collect evidence notes.
Use **Export latest research summary** for a profile-free handoff with an
evidence count; private evidence text is never included.
Character and Content Creator pages store project plans separately from live
game data. Trainer can store a backup-bound, plan-only session target and export
it without mutating the game. Content projects can classify furniture, building, recipe, or other
designs and track project-relative asset references; absolute paths and
traversal are rejected. Trainer, Research, and Content Creator execution remains guarded by
profile isolation and recovery requirements. Guarded workers are read-only in
this release and must return the versioned worker-result contract.

## Knowledge and integration

Knowledge contains the local safety and architecture guidance. Search it from
the Knowledge page. New entries are private until explicitly published, and
the page labels entries PUBLIC or PRIVATE. Export or publish the public catalog
JSON for the EmberVault website. The export excludes paths, saves, logs,
profiles, private knowledge, and private research evidence. **Publish catalog
to repository folder** writes a validated local `embervault-catalog.json`
handoff; the desktop app does not commit or push it.

## Release verification

Build a wheel with `python -m pip wheel . --no-deps --wheel-dir .release-check`,
then run `python tools/verify_release.py <wheel>` to verify the packaged QML
shell, contracts, seed data, embedded entrypoint, guarded workers, and example
package assets.
