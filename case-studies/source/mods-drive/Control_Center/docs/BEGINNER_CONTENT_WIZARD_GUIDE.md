# Beginner Content Wizard Guide

This is the normal way to create or recolor an item. You do not need to know
what a donor, KFC resource, GUID, manifest, or EML registry is.

## Create a recolored item

1. Open **Content Studio**.
2. Click **Open Content Wizard**.
3. Choose **Change the color or appearance of an existing item**.
4. Give the new item a name.
5. Choose the starting item. The tested Wooden Bed is currently available as
   the beginner starting item.
6. Click each color swatch to choose the frame, bedding, and trim colors.
7. If needed, adjust **Scale and placement**. Width, height, and depth change
   the requested visual transform; X, Y, and Z change the requested offset.
8. Choose a preview policy. **Donor fallback** is the safe default. **Custom
   research** records an experiment request but is not treated as proven.
9. Review the summary and click **Create test variant**.

The wizard creates a separate project. It does not overwrite the original
item or change the live game.

## Import a BlenderTools asset

1. Open **Content Studio** and click **Open Content Wizard**.
2. Choose **Bring in a 3D asset from BlenderTools**.
3. Select the folder exported by BlenderTools.
4. Control Center checks the manifest, render data, hashes, and required
   metadata before copying the export into `custom_content/imports`.
5. Review the staged import in Content Studio and validate it before any
   research test.

If validation reports that the model exceeds 65,535 vertices, reduce the
generated mesh in BlenderTools or export a topology-preserving replacement.
This limit applies to full-topology exports and is a packaging safeguard; it
does not mean the game has successfully imported the model.

An imported asset is labeled **RESEARCH-ONLY**. It is never installed
automatically, and a successful file check does not prove that the game can
render or persist the asset. A same-build in-game screenshot, persistence
evidence, and rollback evidence are still required.

## Review or edit a project

Under **Known Content Projects**:

- **Open** shows the item name, colors, and current safety status.
- **Edit colors** lets you change the colors without creating another project.
- **Validate** checks the project before testing.
- **Export** creates a package for sharing or backup.

When you open a project, the review also shows its saved runtime color plan.
That is the exact set of colors the isolated recolor probe will use; you do
not need to copy or re-enter those values.

## Test the project

After validation, keep Enshrouded closed while preparing the test. Use the
Control Center launch path and the research-only profile. The project must be
tested in-game before it can be described as a working visual recolor.

For the simplest first test, open **Research Lab** and click **Start guided
test**. The guided window takes you through **Choose project**, **Validate**,
**Prepare safe test**, and **Launch game** in order. If a step is unavailable,
finish the previous step first; this is intentional and prevents an unfinished
project from being launched accidentally.

For a recolor project, click **Create color probe** after selecting the
project. Control Center generates the isolated research artifact from the
saved swatches. It does not install it automatically; review it first, then
use the research-only installation workflow when you are ready.

## If something goes wrong

Stop the test, close Enshrouded, and use the recovery or quarantine tools in
Control Center. Do not edit files inside the live game installation manually.

The wizard can create and describe a recolor definition, but actual material
and texture rendering remains research-gated until same-build runtime
evidence confirms the visual change.

The packed color assignment itself is now accepted by EML on the current
research build. This is an API-level result, not visual proof. Promotion still
requires screenshots of the catalog tile and the placed item from the same
game session. The current runtime boundary is recorded in
`research/probe_sessions/typed_color_combination_runtime_evidence_20260930.json`
and checked by `tools/verify_typed_color_combination_evidence.py`.

When you capture a screen from Research Lab, Control Center saves a matching
JSON sidecar beside the image. The sidecar identifies the capture as
`catalog`, `item_info`, `recipe`, `placed_item`, `localization`, `gameplay`, or
`other`. Research Lab
only counts a capture when the sidecar, timestamp, category, and image file
pass `tools/verify_game_screenshot_evidence.py`. This confirms that the file
is usable evidence; it does not confirm that the recolor worked. The catalog,
item-information, recipe, and placed-item screenshots still need to be reviewed
together before any capability can be promoted.

For the four gameplay screens, use the matching capture button in this order:

1. Start the game through Control Center and open the Carpenter/build menu.
2. Select the test item so its catalog tile is clearly visible, then choose
   **Catalog** in the Research Lab capture row.
3. Open the item's information panel, then choose **Item info**.
4. Open the item's crafting recipe and station, then choose **Recipe**.
5. Place the test item in the world so its appearance is clearly visible, then
   choose **Placed item**.

The capture dialog will tell you which screen to prepare before saving. Do not
use a loading screen or the main menu as proof of any of these screens.

If you already used the game's screenshot key or another capture tool, use the
matching **Import catalog screenshot**, **Import item-info screenshot**,
**Import recipe screenshot**, or **Import placed-item screenshot** button in
Research Lab instead. Choose the saved image, and Control Center will copy it
into the research session folder and create the matching evidence sidecar for
you. The imported image is still review-only: it must visibly show the
requested item, and it does not promote the feature automatically.

Scale, offset, and preview-policy values are authoring requests saved in the
project definition. They do not claim that the engine will render the
transform or custom preview; those behaviors still require same-build visual
screenshots and persistence evidence.

## Advanced options

The **Show advanced options** button is intended for experienced authors. It
contains donor inspection, resource planning, recipe editing, localization,
asset import, release packaging, and other internal operations. New users do
not need these controls for the normal wizard workflow.
