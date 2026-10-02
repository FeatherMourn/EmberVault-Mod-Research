# EML UI catalog cloning

The bed test established that `keen::FbUiBundle` crafting entries are typed fixed-size arrays. Appending to `set.entries` raises a bounds error (`expected index in range [1, 9], got 10`) and can terminate the game during initialization.

The valid route is:

1. Find the donor recipe ID in `tree.groups[*].sets[*].entries[*]`.
2. Deep-copy the containing `set`.
3. Replace the donor entry inside the copied set with a typed `keen::HashKey32` resource whose value is the new recipe ID.
4. Append the copied set to `group.sets`.

Runtime evidence from the live log:

- donor set entries: 9
- donor entry index: 8
- groups before: 8
- groups after: 9
- new entry value: `3987654322`

This preserves the vanilla set and creates an independent UI catalog set. The separate ItemInfo and RecipeRegistry descriptors are registered through EML's upgraded runtime asset API.
