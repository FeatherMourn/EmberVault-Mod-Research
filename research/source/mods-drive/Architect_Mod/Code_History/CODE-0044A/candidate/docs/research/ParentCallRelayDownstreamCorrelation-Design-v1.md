# CODE-0005C — parent-call relay and stable-hook correlation

This is a staging-only design for build 1076226. The exact parent instruction
at `0x2807C8` is `E8 D3 54 65 00`, resolving to `0x8D5CA0`; its normal return
address is `0x2807CD`. Only that five-byte CALL would be replaced in a future,
separately authorized install.

The relay is a leaf MASM island. It loads an Architect-owned state pointer into
volatile R10, acquires a nonblocking busy bit, copies only RCX/RDX/R8/R9/RSP/RBP
scalars, publishes a generation, releases busy, loads the original helper into
R11, and tail-JMPs. Contention increments a drop counter and forwards directly.
It never dereferences RDX, reads the game buffer, calls C/C++ or game code,
changes RSP, touches `[RSP]`, rewrites the return address, or touches XMM/YMM.
RFLAGS are changed by the atomic bit operations, but the helper's first flag
read is its `cmp` at `0x8D5CB2`; this is a site-specific conditional contract,
not a universal flags guarantee.

The synthetic x64 harness proves argument preservation, original return-address
behavior, unchanged stack entry, generation publication, and tail return. It
does not prove Enshrouded execution safety. The relay source and harness are
not linked into `ArchitectNativeRuntime.dll`.

The existing stable BuildingPlaceEvent observer is the only proposed downstream
observation point. A capture is accepted only for a coherent relay generation,
RDX=`capturedRBP-0x30`, an independently verified parent-path stack marker,
same-thread stack-range evidence, and safe reads of `+0x38`/`+0x78`. Those
same-frame and lifetime checks are not yet proven, so correlation remains
`CORRELATION_UNPROVEN`.

The existing native worker is only a partial drain-host candidate; no production
ring integration or new hook was added. The CODE-0005C result is therefore
partial and fail-closed: `installNow=false` and
`gameHookInstallAuthorized=false`.
