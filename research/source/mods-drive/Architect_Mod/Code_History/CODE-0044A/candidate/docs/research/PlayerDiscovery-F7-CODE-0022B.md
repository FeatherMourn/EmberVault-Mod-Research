# CODE-0022B — F7 Player Discovery controls

F7 exposes the temporary discovery workflow under **Research**, separate from
Character Editor. The three registered commands are `read_only`:

| Action | Parameters | Effect |
|---|---|---|
| `player.discovery.begin` | none | Queue the start of one bounded discovery capture. |
| `player.discovery.mark` | `phase` | Queue one predefined test-phase marker. |
| `player.discovery.end` | none | Queue capture shutdown and flush. |

The dispatcher validates `player.discovery.mark` against this exact allowlist:
`BASELINE`, `SPRINT_ACTIVE`, `SPRINT_RECOVERY`, `MANA_SPEND`, `MANA_RECOVERY`,
`DAMAGE`, `HEAL`, `INVENTORY`, `FAST_TRAVEL`, and `POST_TRAVEL`. Empty or
unknown markers return `invalid_marker` and are not published.

After validation, F7 atomically replaces
`bridge/player_discovery_command.json` with a schema-v1 envelope containing
only the command ID, action, optional predefined phase, source, `readOnly:
true`, and UTC timestamp. The native discovery harness watches this dedicated
file; the existing `bridge/command.json` executor path and ACK behavior remain
unchanged. A `completed` executor ACK means only that the read-only envelope
was validated and queued. It does not claim that capture began, that a probe
is active, or that any candidate was identified.

The Command Palette uses the same registry. The diagnostic console accepts:

```text
player discovery begin
player discovery mark SPRINT_ACTIVE
player discovery end
```

No `set`, `fill`, `max`, `infinite`, regeneration, movement, inventory, or ECS
mutation command is introduced. Existing Character Editor mutation entries
remain `unsupported`, and its mutation button remains disabled.

## Operator flow

Open F7 → Research, select **Begin Capture**, then mark the predefined phases
as the corresponding normal gameplay actions occur. Select **End Capture**
after `POST_TRAVEL`. Check `bridge/executor_ack.json` for command validation and
`bridge/player_discovery_status.json` for native acceptance/capture status.
The dedicated handoff file is diagnostic coordination only and is not runtime
evidence.
