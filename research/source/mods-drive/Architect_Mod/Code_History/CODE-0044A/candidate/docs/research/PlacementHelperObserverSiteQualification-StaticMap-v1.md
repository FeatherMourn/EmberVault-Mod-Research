# CODE-0005 Placement Helper Observer Site Qualification

- Mode: `OFFLINE_STATIC_ONLY`; build revision `1076226`.
- Executable SHA-256: `AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781`.
- No process access, hooks, executable writes, or game-memory writes.

## Candidate sites

| Site | RVA | Status | Reason |
|---|---:|---|---|
| parent_call_2807B6 | `0x2807B6` | NOT_QUALIFIED | overwrite span contains relative control flow requiring relocation; relative helper CALL is not relocatable by the existing raw-copy trampoline |
| parent_call_2807C8 | `0x2807C8` | NOT_QUALIFIED | existing 15-byte detour span would split an instruction; overwrite span contains relative control flow requiring relocation |
| parent_call_2810A3 | `0x2810A3` | NOT_QUALIFIED | existing 15-byte detour span would split an instruction; overwrite span contains relative control flow requiring relocation |
| helper_entry_8DA7C0 | `0x8DA7C0` | NOT_QUALIFIED | existing 15-byte detour span would split an instruction; no reviewed helper-entry observer ABI/return-state wrapper exists; helper output lifetime and nonblocking drain are not proven for all callers |
| helper_entry_8D5CA0 | `0x8D5CA0` | NOT_QUALIFIED | no reviewed helper-entry observer ABI/return-state wrapper exists; helper output lifetime and nonblocking drain are not proven for all callers |
| parent_post_helper_2807CD | `0x2807CD` | NOT_QUALIFIED | existing 15-byte detour span would split an instruction; overwrite span contains relative control flow requiring relocation |
| parent_pre_resolver_280897 | `0x280897` | NOT_QUALIFIED | overwrite span contains relative control flow requiring relocation |

## Gate result

**NO_SAFE_OBSERVER_SITE.** Parent call boundaries contain split instructions or relative control flow that the existing raw-copy trampoline does not relocate. Helper-entry candidates lack a reviewed observer ABI, caller/lifetime proof, and validated nonblocking drain. No staging observer was built.

## Historical rejected paths

The resolver, selector, and function-entry detours remain explicitly non-eligible per their prior crash evidence.

## Next boundary

CODE-0005 requires a reviewed helper-entry ABI/trampoline that preserves all state and a proven nonblocking diagnostic drain, or offline debugger evidence of a lower-risk boundary. Do not install a detour from this map.
