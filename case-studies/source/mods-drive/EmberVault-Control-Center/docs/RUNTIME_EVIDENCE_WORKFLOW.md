# Runtime evidence workflow

## Adapter priority

EmberVault targets **EML first**. Shroudtopia support is planned as a future
adapter and is not the current live-mutation target.

The installed Enshrouded Mod Hub configuration surface is useful secondary
evidence, but it is not the first adapter target. This is deliberately
narrower than editing saves or client settings.

## Current finding

The currently installed loader exposes a mod-owned Lua configuration boundary
under:

`<game>/mods/enshrouded_mod_hub/src/Config/*.lua`

The generated configuration files return Lua tables. The mod entrypoint loads
those tables during initialization and applies values to selected runtime
resources. The loader log confirms the `shroudtopia` runtime is active, but
that alone is not proof that a particular setting was applied in-game. The
EML adapter must instead be based on the EML API and runtime evidence in the
EML research workspace.

## Experimental EML adapter boundary

The adapter may only:

- target an explicitly installed EML-compatible package;
- use an EML-owned input or resource boundary;
- write only keys declared by the adapter contract;
- create and verify a recovery backup before writing;
- require the game to be closed before mutation;
- report the exact file, key, old value, and new value;
- remain `experimental` until post-launch observations are recorded.

It must not edit saves, `enshrouded_local.json`, KFC archives, executables,
DLLs, or arbitrary Lua files. A Shroudtopia-specific implementation must not
be silently substituted for the EML adapter.

## Evidence sequence

1. Record game executable and loader versions, file hashes, and the target
   profile.
2. Create a disposable test profile/world and a verified backup.
3. Capture the baseline configuration and a baseline in-game observation.
4. Apply one setting change through the adapter while the game is closed.
5. Launch the game with the same mod set and record loader/mod logs.
6. Verify the intended behavior in-game, not just in the edited file.
7. Close the game, restore the recovery backup, and verify the baseline again.
8. Record the result as `experimental`, `verified`, or `rejected`.

No adapter is promoted to `verified` without both a reproducible mapping and
successful rollback evidence.

## Initial key mapping

The first safe candidate is `player_level_cap` in
`progression_balancing.lua`. It has a clear numeric input and a visible
in-game verification path. The remaining keys should be tested one at a time
because the mod may clamp values or apply them only to a particular runtime
resource.
