# EmberVault web release checklist

- [x] Validate the sanitized catalog snapshot.
- [x] Validate the public site assets and privacy boundary.
- [x] Parse and review the community schema.
- [x] Test account roles, submissions, moderator review, publication, forums,
      projects, and moderation actions.
- [x] Confirm private/local data is excluded from public snapshots.
- [x] Confirm static hosting and future server boundaries are documented.
- [x] Run JavaScript syntax validation.

The static site is the public presentation layer. Production authentication,
authorization, rate limiting, and persistent community hosting must remain
server-side.
