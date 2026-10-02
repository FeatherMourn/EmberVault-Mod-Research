# Stage 20 migration and recovery status

EmberVault now has a repository-wide migration service for local JSON data. It
previews files before changing them, stamps records with schema version 1,
creates a timestamped backup and report before applying changes, quarantines
malformed records, and restores from a migration backup.

Migration is exposed in the Control Center as a preview-first, operation-tracked
workflow. It does not mutate game saves, deployed mods, or external content;
those remain governed by their existing ownership and recovery boundaries.

Future schema changes must add explicit handlers and historical fixtures rather
than silently changing record shapes.
