# EmberVault

Public catalog, knowledge base, and research archive for Enshrouded modding.

## Repository purpose

This repository is the curated content foundation for the Embervault website.
It is intentionally separate from the EnshroudedModHub runtime repository:

- `content/mods/` contains public mod records.
- `content/research/` contains build-specific research summaries.
- `content/knowledge/` contains reusable guides and explanations.
- `content/compatibility/` contains build and compatibility records.
- `schemas/` defines the shape of records before they are published.

The Control Center can publish a sanitized `embervault-catalog.json` snapshot
for this repository. Validate an incoming snapshot before review with:

```text
python tools/verify_catalog.py embervault-catalog.json
python tools/verify_site.py
```

The public snapshot contract is documented in
`schemas/public-catalog.schema.json`; private profiles, save backups, logs,
and research evidence text must never be included in it.

The website should preserve the distinction between verified, experimental,
research-only, blocked, and unsupported work. A successful offline build or
runtime registration does not automatically prove visible in-game behavior.

## Preview the public site

The repository includes a dependency-free catalog frontend in `index.html`,
`site.css`, and `site.js`. Serve this folder with any static host or local
server; the frontend reads only the reviewed `embervault-catalog.json` file.
It provides public catalog, research, knowledge, and community entry points.
Accounts, moderation, forums, and submission approval require a future
server-backed service; the static frontend never treats contact links as
authenticated workflows.

The server-side community contract is documented in
`docs/COMMUNITY_PLATFORM.md` and `schemas/community.schema.json`.
Hosting and the boundary between the static catalog and future community
service are documented in `docs/DEPLOYMENT.md`.
The dependency-free `community_service.py` provides the local development and
review workflow for users, roles, submissions, projects, forums, publication,
and moderation; production authentication still belongs behind a server.

## Related repositories

- Runtime and Control Center: https://github.com/FeatherMourn/EnshroudedModHub
- Public content source: https://github.com/FeatherMourn/EmberVault-Web

## License

MIT. See [LICENSE](LICENSE).
