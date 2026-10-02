# Recovery guide

Stop Enshrouded before restore or quarantine operations. Control Center tracks
module ownership, backups, recorded versions, and last-known-good profiles.
Use the recovery report to restore owned files, then run live-loader isolation
and compatibility checks before launching again.

## Save backup and comparison

The Control Center can create a verified copy of the complete Enshrouded save
directory without editing the live files. Stop the game first, then run:

```text
python tools/save_backup.py backup <save-folder> <backup-folder> --label before-test
```

Each snapshot receives a timestamp, a manifest, and SHA-256 hashes. To compare
two snapshots after a controlled gameplay or research session:

```text
python tools/save_backup.py diff <before-snapshot> <after-snapshot>
```

The result lists added, removed, and changed files without exposing save
contents. Restore only into a separate destination until the result has been
validated:

```text
python tools/save_backup.py restore <snapshot> <restore-folder>
```

The tool rejects missing manifests, tampered snapshots, symlinks, and backup
destinations nested inside the source. Save editing is not enabled by this
workflow. The command also refuses to run while `enshrouded.exe` is detected.

For a read-only character-save inventory, use:

```text
python tools/inspect_save.py <save-folder>
```

This reports the active character and bounded KSC1 blob metadata only. It does
not decompress or write save data, and it does not claim world-save or quest
editing support.

## Portable Control Center shutdown verification

For a release smoke test, use the process-tree runner while Enshrouded is
closed:

```text
python tools/run_portable_launch_smoke.py dist/EnshroudedModHub.exe --output research/PORTABLE_LAUNCH_SMOKE_PROCESS_TREE_YYYYMMDD.json
```

The runner records responsiveness, all bootloader process IDs, and confirms
that no process from the launch remains. This is stronger than checking only
whether the visible window closed.

To locate the save folder without knowing its path, use:

```text
python tools/save_backup.py discover
```

This discovery is read-only and reports standard locations plus whether they
contain `characters-index`.
