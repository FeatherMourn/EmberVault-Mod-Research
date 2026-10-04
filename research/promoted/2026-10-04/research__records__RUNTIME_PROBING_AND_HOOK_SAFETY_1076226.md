# Runtime probing and hook safety — revision 1076226

- Topic: runtime probing / native hooks / observer infrastructure
- Status: confirmed safety boundary; no production observer site authorized
- Confidence: high for the recorded static qualification results; portability requires a new build audit
- Build: revision `1076226` and associated v0.38.0 staging records

## Supported conclusions

The research infrastructure can plan whole-instruction spans, validate expected bytes, reject unsupported relocation cases, roll back synthetic transactions, and record bounded diagnostic events. Those are harness/staging capabilities only.

For the researched placement helper and related observer candidates, the parent call sites contain split instructions or relative control flow that the existing raw-copy trampoline cannot safely relocate. Helper-entry candidates lack a reviewed ABI, output lifetime proof, unwind safety, and a proven nonblocking drain host. One later candidate removed an earlier relocation blocker but remained only `PARTIAL_STATIC`; it did not authorize installation.

The backend capability probe did not identify a safe native-memory read target. Native mutation, arbitrary object resolution, raw pointers from Lua/F7, and fallback-to-hook behavior are explicitly unavailable or fail closed.

## Evidence

- `../source/mods-drive/Architect_Mod/Code_History/CODE-0037-working/architect_toolkit/docs/research/PlacementHelperObserverSiteQualification-StaticMap-v1.md`
- `../source/mods-drive/Architect_Mod/Code_History/CODE-0037-working/architect_toolkit/docs/research/PlacementHelperObserverSiteRequalification-CODE-0005A-v1.md`
- `../source/mods-drive/Architect_Mod/Code_History/CODE-0037-working/architect_toolkit/docs/research/PlacementHelperObserverSiteRequalification-CODE-0005B-v1.md`
- `../source/mods-drive/Architect_Mod/Code_History/CODE-0037-working/architect_toolkit/docs/research/ObserverTrampolineDiagnosticInfrastructure-v1.md`
- `../source/mods-drive/Architect_Mod/Code_History/CODE-0037-working/architect_toolkit/docs/research/Backend-CODE-0030-NativeMemoryFoundation.md`
- `../source/mods-drive/Architect_Mod/Code_History/CODE-0037-working/architect_toolkit/docs/research/Backend-CODE-0031-LiveBackendFoundation.md`

## Modding implications

Offline scanners, synthetic harnesses, static maps, and bounded staging packages are currently safer and more mature than live native observation. A candidate site must not be promoted from a static map to a live hook without exact-build validation, relocation/ABI proof, bounded nonblocking capture, unwind/lifetime analysis, and a rollback plan.

## Open questions

- Can a future build expose a supported observer boundary without native detouring?
- Can a reviewed relocator cover the remaining instruction classes without weakening safety gates?
- What out-of-hook drain host can prove bounded behavior and lifetime safety?
