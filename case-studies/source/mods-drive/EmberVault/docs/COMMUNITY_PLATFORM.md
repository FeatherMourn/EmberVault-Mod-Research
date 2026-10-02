# EmberVault community platform contract

The public repository is the reviewable content source. A future server-backed
site may provide accounts, roles, project collaboration, forums, moderation,
and submissions, but it must consume the contracts in
`schemas/community.schema.json` and the sanitized catalog contract.

Publication rules:

- New records begin as drafts or submissions and are not public by default.
- A moderator or maintainer must approve a submission before publication.
- Suspended accounts cannot publish, review, or moderate.
- Private profiles, backup metadata, local paths, logs, and research evidence
  text never enter public records.
- Moderation actions require an identified moderator, target, reason, and
  timestamp.
- Forum content can be locked, hidden, or archived without deleting its audit
  history.

The current static frontend presents public catalog and community entry points;
it does not claim to implement authentication or server-side authorization.

The checked-in `content/community.json` file is a reviewed public snapshot;
the site verifier rejects projects that are not explicitly public/published and
threads that are hidden.
