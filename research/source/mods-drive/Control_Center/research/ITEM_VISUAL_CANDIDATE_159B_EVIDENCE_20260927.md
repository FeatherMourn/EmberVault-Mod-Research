# Clone-only visual assignment evidence — 159b5f47

The candidate `159b5f47-aa61-4db9-8e64-06db850de6f6` was tested through the
Steam launch path inside the reversible isolated research profile.

Observed EML output:

```text
ASSIGN|true|
BEFORE|4c7f1c3a-b448-4460-ad5e-a79b3859d2c1
AFTER|159b5f47-aa61-4db9-8e64-06db850de6f6
ACTION|clone_only_no_registry_mutation
```

Interpretation:

- EML accepted the candidate `keen::RenderModel` GUID on a newly cloned
  `ItemInfo` resource.
- The donor model reference was replaced only on the clone.
- The probe explicitly did not publish the clone to item/recipe registries,
  did not overwrite the donor, and did not change the placed furniture model.
- This verifies runtime typed-field assignment for this candidate, not visible
  in-game substitution.

Status: `experimental` field assignment; placed appearance and complete visual
replacement remain `research-only`.
