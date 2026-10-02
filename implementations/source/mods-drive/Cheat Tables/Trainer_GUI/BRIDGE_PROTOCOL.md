# Local Cheat Engine bridge

1. Start `Run_Trainer_GUI.bat` once to create the local bridge directory.
2. In Cheat Engine, load the unchanged `Enshrouded_Master_Trainer.CT`, attach
   to `Enshrouded.exe`, then use **Lua Engine → File → Open** and select the
   actual `Trainer_GUI\cheat_engine_bridge.lua` file. Do not paste the script
   into the editor: relative module resolution requires the file path.
3. Keep `json.lua` beside `cheat_engine_bridge.lua`; it is the bundled,
   dependency-free MIT-licensed JSON library used by the bridge.
3. The Python client exchanges one request and one response at a time under
   `%LOCALAPPDATA%\EnshroudedTrainer\bridge`. Files are atomically replaced,
   bounded to 256 KiB, and bound to a random session and request ID.

Supported commands are `hello`, `enumerate`, `state`, `activate`,
`deactivate`, `set_value`, and `shutdown`. The bridge rejects group headers,
unapproved record types, invalid numbers, unknown IDs, stale sessions, and
arbitrary Lua or address expressions.

The current client is ready for integration and mock testing. Live activation
remains unvalidated until Cheat Engine and Enshrouded are available together.

The Qt dashboard polls `hello` asynchronously. A verified response supplies
the live process ID and record map; the dashboard checks that the PID currently
belongs to `Enshrouded.exe`, then renders script activation and readable value
states. Timeouts clear cached states and mark them unverified. Dashboard write
controls remain disabled in this read-only milestone.
