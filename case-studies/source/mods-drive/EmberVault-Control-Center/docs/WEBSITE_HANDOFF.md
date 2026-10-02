# EmberVault website handoff

The Control Center is the local authoring and safety surface. The public
EmberVault repository is the reviewable catalog and website content source.

## Refresh the public catalog

From the Control Center repository, run:

```text
python tools/sync_catalog.py "I:\My Drive\Enshrouded Mods\EmberVault"
```

This writes only `embervault-catalog.json` into the selected repository folder.
It does not commit, push, or modify the public repository’s content records.

## Validate before review

From the public EmberVault repository, run:

```text
python tools/verify_catalog.py embervault-catalog.json
```

The public repository also runs this check through
`.github/workflows/catalog.yml` on pushes and pull requests.

## Publication boundary

The catalog contains public package/module metadata, published knowledge,
completed research summaries, and ready content-project summaries. It does not
contain profiles, save backups, logs, research evidence text, local paths, or
private unpublished records. Git commits and pull requests remain the review
and moderation boundary for public publication.
