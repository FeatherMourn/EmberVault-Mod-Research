# Control Center Roadmap

Control Center is the central hub for the Enshrouded modding and maintenance workflow. Every screen should answer three questions immediately: what can I do here, what should I click first, and what happens next?

## Current foundation

- Home provides game, project, backup, and next-action status.
- Game Tuning stages beginner-friendly settings until Review & Apply.
- Mod Manager owns install, update, removal, compatibility, and recovery paths.
- Content Studio and Research Lab provide wizard-based authoring and controlled testing.
- Save Manager creates verified snapshots and restores only to an explicitly chosen destination.
- Save Manager supports persisted automatic schedules, retention pruning, integrity status, comparison, and a headless scheduler runner.
- Save Editor remains read-only/protected until save-format write boundaries are verified, with an explicit capability safety matrix.
- Troubleshooter provides a complete read-only health check with runtime, loader, mod, compatibility, content, and log summaries.
- Guides & Help includes searchable topics, screenshots/examples, and dedicated BlenderTools, Research Lab, and Save Backup guides.
- The installer source and deterministic docs bundle include the beginner wizard, BlenderTools, Research Lab, Mod Installation, and Save Backup guides.
- A shared context service connects profile name/module count, project, installed-mod, backup, runtime, and warning state for the Home hub and related modules.
- Profile selection persists across restarts, the quick profile loader uses the structured profile configuration, and core workflows keep the active profile visible.
- Contextual help is dedicated for every major screen and explains the available task, first click, next step, and related guide path.

## Delivery order

1. [x] Keep Home as the shared status hub and make backup/project/profile state visible.
2. [x] Expand Save Manager with automatic schedules, retention, integrity checks, and snapshot comparison.
3. [x] Build the Troubleshooter hub with guided checks for folder, loader, mods, profiles, logs, and save backups.
4. [x] Expand Guides & Help with searchable topics, screenshots, and contextual examples.
5. [x] Build Save Editor as a protected advanced module with explicit capability states and write protection.
6. [x] Connect core modules through one shared project/profile/backup context and surface warnings consistently on Home.
7. [x] Add a safe runtime-recovery action to Troubleshooter for one identifiable failing mod.
8. [x] Expand contextual help on every screen and deeper profile-aware workflows.

## Safety gates

- Never overwrite the original save automatically.
- Do not apply staged tuning or mod changes without explicit review.
- Do not launch controlled tests while the game is already running.
- Keep research-only and unsupported capabilities clearly labeled.
- Preserve existing user profiles and recoverable backups during upgrades.

## Verification baseline

The current source tree passes 733 automated tests. Release metadata, installer-source coverage, documentation audit/bundle generation, backup policy behavior, shared context, and the GUI compilation path are included in that baseline.

## Definition of done

The roadmap is complete when a beginner can start at Home, select a profile, protect a save, create or install content, test it in isolation, diagnose failures, and recover safely without needing to understand the underlying file layout or loader details.
