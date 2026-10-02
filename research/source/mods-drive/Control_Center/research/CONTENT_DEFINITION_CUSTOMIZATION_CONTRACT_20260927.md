# Content Definition Customization Contract

`research/templates/content_definition_customization_contract.json` is the
canonical starter definition for donor-based content work.

The compiler records each requested customization with a maturity status. The
currently verified authoring categories are identity, localization, recipe,
and layout. Icon, color, material, texture, model, and mechanics changes are
recorded as research-only until matching runtime evidence exists for the game
build.

Mechanics require an explicit preservation policy:

- `preserve` is the default and means the cloned item should retain donor
  behavior while visual or metadata research proceeds.
- `replace` is accepted only as an explicitly labeled research request; it is
  not silently emitted as a runtime mutation.

This contract separates author intent from runtime capability. Compiling a
definition creates a research-gated project and does not deploy anything to
the live game.
