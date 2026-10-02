# External Content Route — build 1076226

## Tooling found

The local KFC parser is:

`H:\enshroudedresearch\tools\kfc unpacked\kfc-parser.exe`

It supports:

- `unpack --game-directory ... --output ... --filter ...`
- `repack --game-directory ... --input ...`

The repack command explicitly operates on the game archive and creates a backup of the origin `.kfc`. It is not a normal EML mod deployment step.

## Implication for custom furniture

A true new furniture item would need to be added to the staged KFC resource set before the game builds its indexed catalog. At minimum, the staged package would need coordinated records for:

- `ItemInfo`;
- `RecipeRegistryResource`;
- `ItemRegistryResource`;
- `ItemKnowledgeResource`;
- `FbUiBundle` recipe tree;
- localization records;
- placed entity/template dependencies;
- any visual/icon/content hashes required by the donor.

## Safe next step

Do not repack the live installation yet. First create a disposable copied game-data staging directory, extract only the donor-related resource families, and validate that the parser can round-trip the untouched subset or a complete archive copy. Only after that should a cloned record be introduced.

The EML-only experiment already established that runtime resource creation does not publish new assets into the indexed catalog.

## 2026-09-26 rebuilt-writer result

The upstream `cli-legacy` repacker was rebuilt locally with Rust and tested against the staged archive. After repacking the staged extracted resource set, a filtered unpack found `3611` `keen::ItemInfo` descriptors, including the custom descriptor:

`f93dbabe-339c-294a-a948-715d027c916d_b5ce8765_0.json`

This means the external archive route can preserve a genuinely new descriptor. A guarded wrapper is available at:

`Control_Center/research/tools/repack_custom_content.ps1`

The wrapper refuses to target the live Enshrouded directory and is intended for staged copies until the complete dependency set is validated.

The repacked staged archive was then unpacked and verified. The custom recipe ID `3987654322` survives in the `keen::FbUiBundle` descriptor, while the custom item descriptor survives in `keen::ItemInfo`. The staged archive is therefore structurally ready for an in-game validation pass; the live installation remains unchanged.

## Runtime patch-pass finding

EML rebuilds the live KFC from its backup during startup, so static edits to the live archive can be overwritten. The bed probe now applies the custom recipe’s typed zero-valued `Extern` requirements and `CC_Custom_Bed_001_Recipe` label during EML’s own patch pass. A post-launch unpack of the actual live KFC verified both query IDs as `0` and the custom label in the registered recipe.

## Runtime validation note

Replacing the valid bed UI slot was stable. A later experiment that changed the typed recipe requirement fields to `null` caused a startup crash, so that variant was reverted immediately from `H:\Enshrouded_LiveBackup_20260926_custom_content_unlocktest`. Typed requirement structures must be preserved while extending EML; visibility changes need to use valid query/resource types rather than null values.

## 2026-09-29 staged repack validation

The staging writer and repack wrapper were hardened after the first isolated
repack exposed two packaging issues:

- Windows PowerShell had emitted UTF-8 BOMs that the KFC parser rejected;
- `CLONE_MANIFEST.json` and donor backup descriptors were being passed to the
  parser as if they were game resources.

The writer now emits BOM-free UTF-8 and the wrapper supplies a temporary
descriptor-only input directory. A disposable game copy was repacked and
round-tripped successfully:

- parser repacked `10/10` descriptors;
- post-repack unpack completed `3613/3613` descriptors;
- the custom item, item registry, recipe registry, knowledge link, UI recipe
  link, and independent recipe GUID all pass the offline fixture verifier;
- client catalog rendering remains explicitly unverified.

Evidence: `research/probe_sessions/bed_clone_postrepack_verification_20260929.json`.

The live installation was not repacked. The disposable copy's original KFC is
preserved as `enshrouded.kfc.prevalidation_20260929`.

## Direct-client versus EML launch boundary — 2026-09-29

After the successful repack, a normal EML launch was inspected. EML rebuilt
the disposable archive from its backup, and the custom records were absent in
the post-launch unpack. This confirms that static archive edits alone are not
durable under the current EML startup path.

The same disposable copy was then launched for 20 seconds with only
`dinput8.dll` temporarily moved aside. The client process remained alive with
the repacked archive present and no panic observed; the loader DLL was restored
afterward. This is launch-acceptance evidence, not catalog or placement proof.

Evidence: `research/probe_sessions/bed_clone_external_archive_direct_launch_20260929.json`.

The next implementation target is therefore an explicit external-content
deployment mode: either preserve the repacked KFC during EML startup or apply
the complete staged records through an EML patch pass before the client builds
its indexed catalog.

## EML CLI deployment breakthrough — 2026-09-29

The existing controlled bed-clone probe was installed only in the disposable
copy and executed with EML's offline CLI patch mode. The run created and
registered the independent item and recipe, added one knowledge link and one
UI recipe link, and reported `Applied 6 patches`. A post-patch KFC unpack passed
all archive-registration checks and contained 3,614 descriptors.

This establishes a practical deployment route: staged external content can be
published through an EML patch pass before client startup, avoiding the proxy
startup behavior that restores the archive from its backup. The probe was
removed after the run and the live installation was not touched.

Evidence: `research/probe_sessions/bed_clone_eml_cli_patch_deployment_20260929.json`.

The repeatable validator is `tools/validate_external_content_route.py`. It
refuses the live game directory, runs the EML CLI patch pass, performs a
filtered post-patch unpack, and evaluates the archive-registration checks
without claiming client rendering. A fresh validator run passed all five
content checks and confirmed `Applied 6 patches`; the research probe was then
removed from the disposable copy.

The remaining gate is now genuinely in-game: launch with the CLI-patched
archive and verify the native catalog tile, item preview, placement, and save
persistence.

### Repeatable disposable-copy command

From the Control Center directory, the safe research loop is:

```text
python tools/validate_external_content_route.py <disposable-game-copy> \
  --probe research/probes/bed_clone_injection_1076226 \
  --item-id 3987654321 --recipe-id 3987654322 \
  --debug-name CC_Custom_Bed_001 --recipe-guid auto \
  --output research/probe_sessions/external_route_validation.json
```

The validator installs the probe only when needed, checks the pinned build,
runs the EML CLI patch pass, verifies the extracted content graph, discovers
the generated recipe GUID, and removes the probe afterward. It refuses the
live installation. Passing this command proves archive publication only; it
does not promote catalog rendering, placement, persistence, or multiplayer
behavior.
