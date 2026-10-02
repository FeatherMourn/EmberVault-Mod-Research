# EML mapped-variant boundary — build 1076226

## Confirmed behavior

Some reflected resource fields that appear as ordinary graph collections are exposed to Lua as `MappedVariantValue` userdata. Calling `pairs()` on the wrapper is invalid and produces:

```text
bad argument #1 to 'for iterator' (table expected, got MappedVariantValue)
```

The EML loader handled the failed research probe by skipping mod initialization for that session; the game process stayed alive. The probe was then removed and the stable profile restored.

## Safe access contract

Mapped variants must be accessed through their exposed fields:

```lua
local variant_type = value.type
local payload = value.value
```

Only the payload may be inspected further, and only after checking its Lua type and whether `pairs(payload)` is supported. A probe must wrap each access in `pcall` and must never assign during a discovery run.

## Current AI result

The enemy behavior action field is confirmed to be a mapped variant at runtime. A follow-up `.type`/`.value` probe did not produce a complete payload readback in its session, so the underlying action schema remains unresolved. AI cloning remains research-only.

The packaged helper was validated in a fresh isolated session. It loaded without a Lua/module error, but the session produced no variant readback beyond the initial probe marker. The result is recorded as inconclusive; the helper is not being treated as proof that the underlying AI payload is accessible.

## Required EML/tooling improvement

Control Center probe generators should emit a mapped-value-safe inspector rather than raw `pairs()` calls. The inspector should report:

- wrapper type;
- variant type;
- payload type;
- payload field names when enumerable;
- a structured access error when not enumerable;
- no mutation and automatic rollback.
