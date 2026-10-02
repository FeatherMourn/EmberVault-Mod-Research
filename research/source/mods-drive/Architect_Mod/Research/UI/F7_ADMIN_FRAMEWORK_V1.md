# F7 Admin Framework v1

`runtime/ArchitectRuntime.ps1` now owns two independent WinForms surfaces:

* **F8** retains the existing Architect Builder form and command shape.
* **F7** opens the Admin / Inspector form.  It has Dashboard, Character Editor,
  Item Editor, Command Palette, and Diagnostics pages.

The F7 form writes version-1 commands to the existing atomic `bridge/command.json`
transport.  The existing executor remains the only consumer of that file.  It
recognizes actions in the `player.*` and `item.*` namespaces and routes them to
`Dispatch-AdminCommand`; F7 buttons and palette selections call the same
`Write-AdminCommand` function. `Invoke-AdminConsoleCommand` is the advanced
debug entry point for text such as `player.stamina fill`; it normalizes that
text into the same command message. Advanced callers may also submit the
schema directly:

```json
{
  "version": 1,
  "commandId": "unique-id",
  "action": "player.stamina.fill",
  "parameters": {}
}
```

Responses are written to `bridge/executor_ack.json`; lifecycle history is
bounded to the latest 64 entries in `bridge/admin_history.json`. Current UI
state is published in `bridge/admin_state.json`, and executor diagnostics list
the dispatcher, module states, registered-command count, and last admin result.

`bridge/item_capture.json` is the Item Observer schema-v1 input. The executor
accepts only a fresh native capture with `selectionState: valid` and
`confidence.itemIdentity: proven`; otherwise `item.inspect` returns an explicit
`no_selection`, `stale_selection`, `ambiguous_selection`, or
`signature_mismatch` result. It never reuses the last observed item.

## Capability policy

All player mutations and item mutations are registered but **unsupported** for
the current build. Health/stamina/mana recovery entries are marked
**experimental**. `item.inspect`, `item.id`, and `item.hash` are **read-only**
requests, but no selected-inventory structure is mapped yet, so they return an
explicit `read_only` result instead of fabricated data. F7 disables mutation
buttons and never reports a request as completed.

The native runtime continues to be the existing placement observation runtime.
No player/inventory offset, signature, hook, structure, or write path was added.
The next research step is a bounded read-only capture that correlates a known
inventory selection change with candidate player/inventory state before any
item value is displayed or edited.
