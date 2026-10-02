# EmberVault deployment

## Static catalog

The current public site is dependency-free and can be hosted by GitHub Pages,
Cloudflare Pages, Netlify, or any static file host. Deploy the repository root
with `index.html` as the entry point. The site reads `embervault-catalog.json`
from the same origin.

Before deployment, run:

```text
python tools/verify_catalog.py embervault-catalog.json
python tools/verify_site.py
```

The GitHub Actions catalog workflow runs both checks on pushes and pull
requests. Catalog updates should be reviewed before the hosting branch is
published.

## Future community service

Forums, accounts, roles, moderation, and submissions require a server-backed
service. It must keep authentication and authorization server-side, use the
records in `schemas/community.schema.json`, and publish only approved records.
The static site must never receive save backups, local paths, private research
evidence, session tokens, or moderator credentials.

The service should export an approved public snapshot into this repository;
the static site remains a read-only presentation layer. Failed or rejected
submissions remain private to the review system and are not copied into the
public catalog.
