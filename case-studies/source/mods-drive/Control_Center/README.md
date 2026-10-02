# Enshrouded Mod Control Center

The Control Center is the primary dashboard for Enshrouded tuning, EML/KFC
runtime modules, custom-content projects, compatibility checks, diagnostics,
profiles, packaging, and recovery.

## Start here

Run `Run_Control_Center.bat`. It opens the unified application through
`gui/launcher.py`. The older `app.py`, `visual_builder.py`, and
`simple_editor.py` tools remain available only as explicit legacy routes:

```text
python gui/launcher.py --legacy app
python gui/launcher.py --legacy visual_builder
python gui/launcher.py --legacy simple_editor
```

For support or update checks without opening the dashboard, use the same
front door in headless mode:

```text
python gui/launcher.py --status --game-dir "H:\SteamLibrary\steamapps\common\Enshrouded"
```

This prints the machine-readable health report used by the dashboard.

To inspect the current platform boundaries without opening the dashboard:

```text
python gui/launcher.py --capabilities
```

This prints the versioned capability audit and exits nonzero if its evidence
map is invalid. Each capability is labeled `verified`, `experimental`,
`research-only`, or `unsupported`.

## Safe workflow

1. Select and validate the Enshrouded installation.
2. Choose or clone a profile, optionally assigning a world ID.
3. Review module dependencies, compatibility, and update warnings.
4. Validate or generate content projects in Content Studio.
5. Inspect donor resources and create a non-destructive clone plan.
6. Import extracted JSON resources into a generated project; the importer assigns a stable identity, regenerates hashes, and validates before accepting the change.
7. Import a PNG through **Content Studio → Import Custom Icon**, or add `icon`
   and `icon_slug` to a structured definition and compile it in one step.
8. Automate the same workflow with `python tools/compile_content_definition.py definition.json output`.
   Offline build plans can be checked with `python tools/report_build_plan.py catalog.json plan.json --inventory inventory.json`.
   Donor visual dependencies can be inventoried with `python tools/report_visual_dependencies.py resource.json`; add `--candidate candidate.json` for a read-only substitution plan.
   Module decisions can be explained with `python tools/report_module_graph.py modules/`.
   Donor patch plans can be reviewed with `python tools/report_patch_plan.py donor.json keen::ItemInfo changes.json`.
   Gameplay research boundaries can be exported with `python tools/report_gameplay_feasibility.py`.
   The combined offline release gate is `python tools/verify_milestone.py`.
9. Preview deployment and apply only after review.
10. Use health reports, searchable logs, quarantine, and support bundles when diagnosing failures.

Projects can declare donor/candidate resource pairs in `donor_validation`.
Those pairs are schema-compared during validation; missing donor fields or
type changes block the project before deployment.

The platform keeps custom content separate from vanilla files and creates
reversible backups before owned deployments. Research-only modules and
packages require explicit approval.

Imported icons are integrity-tracked project assets. A valid packaged PNG does
not by itself prove that the game will consume or render it; the build-specific
EML texture-resource route must be separately verified with runtime evidence
and fresh in-game visual evidence.

## Developer resources

- `sdk/README.md` — stable SDK contract and examples.
- `docs/RETROFIT_STATUS_MATRIX_20260926.md` — evidence and limitations for all 50 upgrades.
- `research/staging/bed_clone_kfc_subset_1076226` — verified bed compatibility fixture.
- `research/runtime/kfc_content_registry.lua` — reusable runtime helper.
- `research/runtime/kfc_localization_registry.lua` — research-only binary localization helper.

## Module maturity audits

Module manifests should declare `feature_state` as `stable`, `experimental`,
`research-only`, or `disabled`. Legacy workspaces may still be inspected in
compatibility mode, while production-oriented audits can fail closed:

```text
python tools/report_module_graph.py modules --strict-metadata
```

The command exits with code `2` when a module is missing valid maturity
metadata or another graph issue is present. The built-in module set currently
passes this strict audit; third-party live mods are audited separately by
`tools/verify_live_loader.py` and must be isolated until explicitly classified.
- `research/probes/localization_runtime_1076226` — deterministic localization probe for the recorded build.
- `research/CAPABILITY_LIMITATIONS_REPORT_20260927.md` — current verified capability and limitation baseline.
- `research/templates/CONTENT_DEFINITION_WITH_ICON.md` — structured authoring example for icon-backed content.

## Verification

From the Control Center directory:

```text
python -m unittest discover -s tests -p "test*.py"
```

The fixture proves the runtime bed-registration route for the recorded game
build. Localization injection, broader model import, and other donor-specific
content classes remain capability-gated until independently verified.
