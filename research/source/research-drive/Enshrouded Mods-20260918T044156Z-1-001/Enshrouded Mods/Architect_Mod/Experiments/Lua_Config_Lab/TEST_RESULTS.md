# Test results

Run date: 2026-09-22
Command: `python -m unittest discover -s tests -t .`

```
Ran 76 tests in ~1.0s
OK
```

All 76 automated tests pass.

## Coverage

| Area | Tests | Notes |
|---|---|---|
| Schema parser | `test_schema_parser.py` | parses without error; regression counts (4854 classes / 768 aliases / 21442 fields); inheritance; enum alias choices |
| Type conversion & expressions | `test_type_parser.py` | `lua_class_to_resource_type`; all primitives; `Guid`, `ObjectReference<T>`, `Array<T>`, `StaticArray<T,N>`, `Bitmask<T>`, `Variant<T>`, optional `?`, nested generics |
| Validation | `test_validation.py` | integer ranges (u8/i8/u16/u32/u64/i64), bool, finite float, enum accept/reject, GUID accept/reject |
| Field paths | `test_field_paths.py` | nested valid path, missing path, missing nested field, traversal, array-indexed path, array-requires-index, enum classification |
| Profiles | `test_profiles.py` | save→reload semantic equality, version preserved, stable/change-sensitive hash, validation |
| Lua generator | `test_lua_generator.py` | deterministic output, string escaping, number emission (int/float/refusal), match selector, precondition, invalid-path raises |
| KFC roots | `test_kfc_roots.py` | 131 roots present, each resolves to exactly one class, 864 direct fields, roots marked, reachable nested classes non-empty |
| Provenance & results | `test_provenance_results.py` | SHA-256 determinism, provenance record, local result store append/reload, result-value validation |

## GUI smoke test

A manual (non-`unittest`) smoke test instantiated the full `MainWindow`,
selected `keen::BalancingTable` → `playerBaseStamina`, built a validated edit,
added it to the profile, and generated Lua successfully:

```
build_edit err= None
generated lua length= 6518
GUI smoke test OK
```

## CLI verification

* `parse` reported the expected regression counts.
* `generate` produced the deterministic Lua body.
* `export` produced a complete EML mod directory
  (`mod.json`, `src/mod.lua`, `profile.json`, `generated_manifest.json`).
