# Development Acceleration Plan

## Purpose

Shorten the time from a research question to a trustworthy capability result
without putting the stable game installation at risk.

## Standard capability cycle

Every new capability follows the same bounded cycle:

1. Define one hypothesis and one success marker.
2. Generate a deterministic probe from a versioned donor/template.
3. Run static validation, build compatibility checks, and live preflight.
4. Install only the owned probe in an isolated profile.
5. Run one controlled game session and capture the fresh EML log.
6. Catalog machine-readable evidence and record the exact build/hash.
7. Promote, repeat, or classify the capability as research-only/unsupported.
8. Remove the probe and restore the stable profile automatically.

Do not combine unrelated hypotheses in one probe. This keeps failures
diagnosable and allows independent research tracks to proceed in parallel.

### One-command cycle preparation

The setup portion is now automated by `tools/prepare_research_cycle.py`:

```text
python tools/prepare_research_cycle.py \
  research/SAFE_METADATA_RESOURCE_TYPES_20260928.json \
  research/cycles/<cycle-id> \
  --game-dir H:\\SteamLibrary\\steamapps\\common\\Enshrouded \
  --expected-build "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z"
```

It validates the policy schema, generates a read-only suite for verified
resource families, preserves quarantined types in the cycle report, and can
capture live preflight without launching the game. The generated
`RESEARCH_CYCLE.json` is the handoff artifact for the controlled-session
step. This intentionally does not install or launch anything automatically.

The preparation command can also carry one staged runtime probe into the
cycle package. It records a deterministic SHA-256 over that probe's relative
paths and file contents, and cycle validation rejects later mutations. This
keeps the exact probe used for installation linked to the runtime evidence
while preserving dry-run and isolated-profile safeguards.

For a staged runtime probe, use `tools/install_research_probe.py`. It is
dry-run by default and connects manifest/dependency validation to the existing
transactional backup and restore service. Applying a probe requires explicit
`--install` (an alias for `--apply`) and research approval; the game must be stopped. The stable profile
should still be protected by an isolated smoke profile before applying.

### Launch verification gate

Starting `Enshrouded.exe` is not sufficient evidence that EML loaded. Steam,
the proxy, and the game process can be alive while the expected EML log remains
unchanged. Record the log size before launch and require
`ProfileLaunchService.wait_for_eml_session` (or the equivalent
`eml_session_started` check) to observe log growth before waiting for probe
markers. If the log does not grow within the bounded timeout, classify the
session as `loader_not_observed`, stop evidence collection, and restore the
stable profile. This prevents false-positive runtime sessions and avoids
manual inspection of stale logs.

## Highest-leverage work order

1. Resolve the runtime metadata API boundary. This unlocks generic discovery,
   reduces hard-coded donor assumptions, and accelerates every later probe.
2. Verify visible rendering of the registered model substitution. This is the
   decision point for visual customization versus an engine-imposed limit.
3. Finish custom localization consumption in the UI.
4. Generalize the content compiler from the bed fixture to furniture classes,
   then resources and recipes.
5. Promote the reusable probe lifecycle into a single Control Center action.
6. Only after those foundations are stable, investigate original assets,
   interactions, AI, quests, and multiplayer authority.

## Parallel tracks

- **Runtime/API track:** EML exposure, resource metadata, typed graph access.
- **Content track:** clone identity, recipes, localization, layout, visuals.
- **Platform track:** manifests, dependencies, profiles, rollback, diagnostics.
- **Authoring track:** definition editor, validation, generated probes, reports.
- **Gameplay research track:** interactions, AI, quests, builder assistance.

Each track must publish a small evidence artifact and never change the stable
profile as a side effect of research.

## Automation targets

- One command/action for generate → validate → preflight → install.
- One command/action for fresh-log capture → evidence catalog → cleanup.
- Automatic build mismatch refusal before a probe reaches the game.
- Automatic owned-folder cleanup and stable-profile restoration after a run.
- Capability matrix updates from evidence records rather than manual status edits.
- Parallel offline analysis wherever live game access is unnecessary.

## Promotion rule

An experimental capability becomes supported only after runtime acceptance,
in-game behavior, restart persistence, clean-profile validation, update/rollback
validation, and a documented recovery path. Until then, the Control Center must
show the capability boundary explicitly.

## Current acceleration bottlenecks

- Metadata enumeration is now verified for five safe resource families on the
  current build. `keen::TemplateResource` remains quarantined because its
  single-resource lookup can block before returning; generic discovery must
  continue using the approved type policy.
- Registered visual substitution has runtime registration evidence, but visible
  in-game rendering still needs human verification.
- Custom localization registration exists, but UI consumption is not yet
  promoted to supported.

## Baseline

- Control Center milestone gate: 408 tests passing.
- Stable profile remains isolated from research-only probes.
- Every promotion decision must reference a versioned evidence artifact.
