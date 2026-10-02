# Registered visual substitution live smoke

Date: 2026-09-27  
Build: `1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z`

The generated research-only probe `registered_visual_substitution_1076226`
was installed in isolation and launched successfully.

Observed startup markers:

- `VISUAL_ASSIGNMENT|ok=true`
- model changed from `4c7f1c3a-b448-4460-ad5e-a79b3859d2c1` to
  `159b5f47-aa61-4db9-8e64-06db850de6f6` on the clone;
- `DISCOVERED_CLONE|true`;
- `REGISTERED|itemId=3987654501|recipeId=3987654502`;
- item registry count `3520->3521` and recipe registry count `1954->1955`;
- typed UI set clone succeeded with `value=3987654502` and `sets=9`;
- placed entity remained `9b1b68dd-1d4f-408d-aaf8-5bb82badd7d5`;
- no panic or loader error was observed.

## Status

This proves the combined runtime graph reaches registration and UI linkage
while accepting a different model reference. It does not prove the placed
object visibly renders the replacement model, nor save persistence. Those
remain the human-visible validation gate. The probe was removed after the
session and the stable module inventory was restored.
