# Architect Builder UX Inspiration Research — 2026-09-19

Status: USER-CONFIRMED PRODUCT REQUIREMENT / EXTERNAL RESEARCH
Game build context: Enshrouded 1076226
Subsystem: F8 Build / Building UX

## User requirement
Treat a Satisfactory-style Zoop workflow and comparative research into builder UX from Satisfactory, Vintage Story, Minecraft, and similar voxel/building games as first-class Architect product requirements. This requirement was underrepresented in prior project summaries.

## External observations
### Satisfactory
- Zoop is a build mode for many structural pieces. It previews and places up to 10 pieces along a one-dimensional direction; a separate Vertical mode handles vertical repetition.
- Build modes are switchable from the active build tool, and Quick Switch cycles related buildables without leaving the placement workflow.
- Snapping/grid guidance and soft/hard clearance feedback are integrated with placement.
Sources:
- https://satisfactory.wiki.gg/wiki/Build_Gun
- https://satisfactory.wiki.gg/wiki/Patch_0.5.0.0

### Vintage Story
- Chiseling exposes a context-sensitive tool-mode menu with grid size, rotation, flip, and naming; blocks can be edited at 16x16x16 microvoxel resolution.
- Creative WorldEdit has both command and GUI control. Tools include paint brush, raise/lower, air brush, erode, import, eraser, grow/shrink, line, lake/flood fill, and tree generation, with radius/depth/draw/apply modes.
- Creative mode combines unlimited blocks, flight/noclip, item spawning, and world-editing tools.
Sources:
- https://wiki.vintagestory.at/Chisel
- https://wiki.vintagestory.at/How_to_use_WorldEdit/en
- https://wiki.vintagestory.at/Creative_mode

### Minecraft
- Creative inventory emphasizes category tabs, search, pick-block, and saved hotbars/toolbars.
- Vanilla commands expose setblock/fill/clone for bulk editing, while structure blocks provide save/load/copy-paste workflows.
Sources:
- https://learn.microsoft.com/en-us/minecraft/creator/documents/commandspopularcommands?view=minecraft-bedrock-stable
- https://learn.microsoft.com/en-us/minecraft/creator/documents/structures/introductiontostructureblocks?view=minecraft-bedrock-stable
- https://minecraft.fandom.com/wiki/Creative

## Architect product translation
### Named first-class feature: Architect Zoop
Candidate modes:
- SINGLE
- LINE / ZOOP
- VERTICAL
- PLANE / RECTANGLE
- WALL
- FLOOR
- STACK
- ARRAY
- REPEAT-TO-TARGET

Core UX:
- First click anchors start.
- Mouse movement chooses axis/direction/count.
- Ghost preview shows every candidate piece before commit.
- Mouse wheel or hotkeys adjust count/spacing.
- Axis lock and snap override controls.
- Validation colors distinguish valid, overlapping, and blocked placements.
- One commit should remain an Architect transaction for undo/history when that infrastructure is proven.

### Builder Mode / Tool Mode UI
Adopt a context-sensitive F8 tool-mode selector inspired by Satisfactory Build Modes and Vintage Story tool modes, rather than requiring users to navigate deep menus for every operation.

Potential modes/tools:
- place single
- zoop line
- vertical stack
- plane/rectangle fill
- hollow/outline rectangle
- line between two points
- copy/clone selection
- move/rotate/mirror/flip selection
- replace material
- paint/material brush
- erase/dismantle brush
- terrain raise/lower/flatten/smooth/erode
- circle/ring/cylinder/wall/floor procedural planners

### Fast material/build-piece selection
- Searchable catalog.
- Categories/favorites/recent items.
- Pick-block / eyedropper behavior from world target.
- Saved builder hotbars/palettes.
- Quick-cycle variants within a build family.

### Selection and reusable structures
- Two-corner/bounding-box selection.
- Save selection as Architect blueprint/project asset.
- Copy/paste with rotation/mirror/offset preview.
- Structure library with metadata and thumbnails when feasible.

## Enshrouded engineering constraint
Do not implement bulk placement as arbitrary world-memory writes. Prefer REUSE -> EXTEND -> COMPOSE -> AUGMENT around validated vanilla placement primitives. Architect Zoop should be an operation planner that generates a sequence/set of legitimate Enshrouded placements through a validated Build Adapter, with preview/validation before commit. Exact live placement/preview authority remains evidence-gated.

## Proposed proof sequence
1. Define planner-only Zoop geometry independent of game mutation: start point + axis + count + spacing -> planned placements.
2. Reuse known vanilla/building shape placement representations for preview/planning where possible.
3. Prove one safe repeated-placement path using legitimate placement calls/events on a test world.
4. Add preview of all planned placements before commit.
5. Add vertical and plane modes only after line Zoop is runtime-proven.
6. Add undo/history only when reversible world-edit transaction support is independently proven.

Evidence status:
- User desire for Zoop/comparative builder UX: PROVEN USER REQUIREMENT.
- External game mechanics: EXTERNAL RESEARCH.
- Architect implementation details above: PLANNED/INFERRED until Enshrouded integration is validated.
