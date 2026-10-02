# Runtime feasibility record

## Evidence

The local EML source and documentation currently state that:

- asset modifications are supported before the game starts;
- runtime modification is still work in progress and cannot currently be used;
- the runtime DLL loader loads libraries and retains them, but does not expose a
  world, player, entity, or construction API.

The Emberworks runtime probes independently confirm that the Lua environment can
enumerate and create asset resources, but expose `game.world`, `game.player`, and
`game.actions` as unavailable in the current build.

The public EML documentation remains consistent with this result: its getting
started guide describes the `runtime` capability as work in progress and not yet
usable. Reference: https://brabb3l.github.io/kfc-parser/eml/develop/getting_started.html

## Consequence

Worldwright capture, in-game copy/paste, Zooping placement, Wand placement,
Chiselcraft placement, restoration mutation, and Kinetic in-world machinery
cannot be marked runtime-verified through the current EML surface. Their offline
engines and simulated undo/redo remain implemented and tested.

This is an external runtime-surface blocker, not a failed offline implementation.
The next valid promotion path is either an EML release that exposes runtime game
objects/actions or a separately verified native integration that provides those
objects safely. No unsafe memory patching is treated as completion evidence.
