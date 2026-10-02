# CODE-0005 Runtime Capture Runbook

## Current status

The CODE-0005 Gate 1 qualifier returned `NO_SAFE_OBSERVER_SITE`. No staging
observer DLL was built or deployed, and no runtime capture is available.

## Why there is no deployment procedure yet

The parent call boundaries at `0x2807B6`, `0x2807C8`, `0x2810A3`, the
post-helper boundary, and the pre-resolver boundary require relocation or
split-instruction handling beyond the existing raw-copy `write_abs_jump`
mechanism. The helper-entry candidates require a new reviewed ABI/return-state
wrapper and a proven caller/lifetime/nonblocking-drain contract. That work is
not authorized by this delivery and remains fail-closed.

Do not attach to Enshrouded, deploy a DLL, write bridge commands, or run a
placement experiment for CODE-0005.

## Required future evidence

Before any observer build, provide a reviewed helper-entry or lower-risk
call-boundary design that proves whole-instruction relocation, register/flags
preservation, stack alignment, output-buffer lifetime, bounded Architect-owned
logging, and exact uninstall restoration. The existing rejected resolver,
selector, and function-entry detours remain ineligible.

