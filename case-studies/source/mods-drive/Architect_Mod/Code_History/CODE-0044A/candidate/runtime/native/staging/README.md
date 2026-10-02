# Native diagnostic staging

This directory is isolated from the live `runtime/native/ArchitectNativeRuntime.dll`.
It contains only a future read-only diagnostic contract. No staging binary is
built or deployed in the offline research batch because the current static
evidence does not yet prove the reflected non-ds BlobArray semantics or a
legitimate resource-manager pointer endpoint.

The contract in `BlueprintRuntimeDiagnosticPlan.h` is not part of the live
MSVC project and has no process access, detour, allocator, or memory-write
capability. It is deliberately limited to the fields that a later validated
consumer could report.

`ArchitectBlueprintCacheDiagnostic.c` is a source-only implementation of the
bounded equivalent lookup: it validates `RSI+0xF0`, follows the declared
bitmap/key/value ranges, reads one requested record, and derives at most 128
payload bytes. It does not call `0xCA90E0` and does not write game memory.
`blueprint_cache_diagnostic_schema.json` records the staged output contract.
