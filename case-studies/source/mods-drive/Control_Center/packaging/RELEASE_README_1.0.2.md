# Enshrouded Mod Hub 1.0.2

This release includes the Content Studio custom-icon workflow, structured
definition compiler, CLI compiler, transactional project rollback, and the
Research Lab icon-evidence catalog.

This current-source rebuild also reads EML Lua API version evidence from the
latest runtime session and blocks enabled modules with incompatible, missing,
or malformed explicit API requirements before deployment changes game files.
The installer was rebuilt and verified to contain the exact portable payload,
preserve user profiles during upgrade, and remove only owned files on uninstall.

All custom content remains research-gated until its EML runtime behavior and
fresh in-game rendering evidence are independently verified.

Use the Control Center dashboard or:

```text
python tools/compile_content_definition.py definition.json output
```
