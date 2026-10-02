# Item Observer Runtime Descriptor Registration Discovery v6

## Proven

`Invoke-ItemDescriptorRuntimeCapture.ps1` is a passive, one-shot diagnostic.
It verifies the v3-v5 executable SHA-256 before opening Enshrouded with
`PROCESS_QUERY_INFORMATION | PROCESS_VM_READ`. It never writes process memory,
injects a DLL, installs a hook, or scans outside the loaded module.

For a validated run it will inspect only the four known descriptor RVAs, then
search loaded `.data` and `.rdata` for exact relocated descriptor pointers.

## Runtime validation

The first launch correctly returned `MODULE_NOT_FOUND` while Enshrouded was
closed. A subsequent live, build-validated capture completed with all four
descriptors readable at relocated module addresses.

## Live descriptors / module references / owners

The loaded module contains 4,642 aligned exact pointer references across its
`.rdata`/`.data` sections. This demonstrates that these generic descriptors are
materialized broadly at runtime, but it does **not** identify an inventory
owner: the capture intentionally does not assign owner semantics from a single
pointer reference.

The validated capture is classified `STATIC_REFERENCES_ONLY`: all 4,642
references are file-backed relocated `.rdata`, while `ownerCandidates`,
`runtimePointerChains`, and `runtimeObjects` are empty. `RUNTIME_OWNER_FOUND`
is reserved for a capture containing an actual owner candidate.

## Descriptor path status

**ACTION STRING / DESCRIPTOR PATH — DEPRIORITIZED.** The action names lead into
generic descriptor/type metadata, and passive runtime inspection revealed only
relocated static `.rdata` relationships rather than inventory-operation state.
The tools and reports remain preserved for future evidence-led use.

## Time-series result

The command is manual and one-shot. Capture at main menu, world loaded,
inventory open, and after a normal backpack interaction; compare only
descriptor-related references between captures.

## No-hook decision

**NOT READY.** This experiment discovers only exact pointer references inside
the loaded module. It cannot establish item selection or inventory semantics
by itself.

## Run

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools\ItemObserver\Invoke-ItemDescriptorRuntimeCapture.ps1
```

Expected output: `bridge/item_observer_runtime_descriptor_capture.json`.
On build mismatch, missing module, unreadable descriptor, or zero module
references, the report records an explicit state and stops safely.

## Next research step

Compare controlled captures to find references that change with world and
inventory initialization. If no descriptor-related reference changes, deprioritize
these generic descriptors and move to vanilla transfer-state signals.
