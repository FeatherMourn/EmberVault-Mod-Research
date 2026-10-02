# Save Backup Guide

Control Center creates verified snapshots of the complete Enshrouded save folder. It never edits the live save during backup, comparison, or restore-to-separate-destination workflows.

## Start here

1. Close Enshrouded.
2. Open **Save Manager**.
3. Choose **Find my save folder** to confirm the detected location.
4. Choose **Create a backup** and give the snapshot a useful label.
5. Confirm that the snapshot is shown as verified before testing mods.

## Automatic backups

Save Manager can run a persisted schedule while Control Center is open. The headless runner at `tools/run_scheduled_save_backup.py` can also be called by Windows Task Scheduler. The included `Run Scheduled Save Backup.bat` provides a simple manual test or scheduler target. The runner refuses to copy while Enshrouded is running, skips disabled or not-yet-due schedules, verifies the result, and prunes only verified snapshots beyond the retention limit.

Automatic backups require a discoverable standard save folder containing `characters-index`. If the folder cannot be identified, the runner reports that condition and makes no changes.

## Restore and compare

- **Compare backups** reports added, removed, and changed files without exposing save contents.
- **Restore a backup** always asks for a separate destination. The live save is never overwritten automatically.
- A tampered or incomplete snapshot is rejected by its manifest and hash inventory.

If a backup is invalid, keep it for investigation and create a new verified snapshot before continuing.
