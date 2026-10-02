# EmberVault catalog integration

The Control Center is the local authoring and safety surface. The EmberVault
website can consume the exported catalog without importing desktop runtime
state.

Each catalog snapshot includes a UTC `generated_at` timestamp so the receiving
site can identify stale or unexpectedly old handoffs.

`CatalogExportService` writes a JSON document with:

- `schema_version`
- `contract_versions` for module, package, research, content, and tuning-adapter contracts
- package manifests
- module manifests, including the canonical `process_mode` value (`embedded`
  or `separate`) for downstream display and filtering
- sanitized tuning-adapter records containing loader, supported game build,
  supported setting keys, feature state, process mode, and public evidence state;
  local evidence paths, recovery details, and mutation payloads are excluded
- knowledge entries
- explicitly published, sanitized research summaries with evidence counts and
  publication timestamps (never local evidence text or profile identifiers)
  and can be explicitly unpublished without deleting the local record. Changes
  to published evidence or status automatically retract publication.
- explicitly published, sanitized Content project summaries for projects marked
  ready (never local descriptions, profiles, or design-workspace details). A
  project can be unpublished without deleting its local design record, and any
  status change automatically retracts publication.
- seeded knowledge is public by default, while locally authored knowledge
  remains private until explicitly published; unpublished local entries are
  excluded from the catalog.

Paths are deliberately removed from exported records. Runtime folders,
profiles, save backups, logs, and research-local evidence are not published by
this export. The canonical validation document is
`contracts/catalog.schema.json`; package and module entries use the contract
versions declared in the export. The companion EmberVault public repository
accepts this handoff through `schemas/public-catalog.schema.json` and
`tools/verify_catalog.py` before attaching repository URLs, discussion links,
and moderation metadata on the web side.

Public knowledge records use `contracts/knowledge-entry.schema.json`; local
publication state is intentionally omitted from the public record.

Research handoffs use `contracts/research-summary.schema.json`; exported
summaries contain evidence counts only and never profile identifiers or
evidence text.

The desktop exporter validates the handoff before writing it, including all
declared module, package, research, and content contract versions and stable
identities for package/module records. Malformed public
records are rejected, and research or content records containing private
evidence, descriptions, profiles, or other local-only fields cannot be
exported as public catalog entries.

The Control Center can also publish the validated snapshot to a chosen local
repository folder as `embervault-catalog.json`. This is a reviewable handoff;
the desktop application does not commit, push, or modify the website remotely.
For a repeatable command-line handoff, run
`python tools/sync_catalog.py <website-repository-folder>`; by default it
includes repository-owned adapter and seeded knowledge assets. It writes only
the validated catalog file to the destination and leaves Git operations to the
repository workflow. Use `--data-root` for an isolated/test export.
The receiving website or repository can independently validate a snapshot with
`python tools/verify_catalog.py embervault-catalog.json` before accepting it;
the verifier has no dependency on the desktop runtime.

Guarded workers must return JSON with `contract_version: 1` and
`read_only: true`. Control Center rejects successful processes that do not
provide that contract, preserving the first-release mutation boundary. The
canonical result schema is `contracts/worker-result.schema.json`. Research
workers may additionally return a bounded `evidence` string array containing
observations; these observations must be read-only and are captured in the
operation log rather than written into game or save data.
Trainer workers may additionally return a bounded `checks` string array for a
readiness audit. The backup identifier is passed as context only; the worker
cannot mutate or restore it.
Content Creator workers may also return bounded `checks` describing their
design-workspace boundary; they must not touch live game content.
