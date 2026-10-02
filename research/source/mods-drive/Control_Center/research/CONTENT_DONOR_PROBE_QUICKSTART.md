# Content Donor Probe — Quick Start

This probe is read-only. It does not create items, alter registries, or modify saves.

1. Close Enshrouded.
2. Install or copy this probe as the active EML research mod.
3. Launch Enshrouded and load the main menu or a test world.
4. Close the game.
5. Collect the newest EML/game log.
6. Search for `[CC-CONTENT-PROBE]`.

The first useful result is a vanilla item with a stable `itemId`, `guid`, readable `debugName`, and populated `equipment`/`voxelObject`. We will use that item as the first donor. The next probe will inspect its nested fields and recipe membership before attempting any write.
