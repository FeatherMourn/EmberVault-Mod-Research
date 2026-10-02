# CODE-0005B — `0x8D5CA0` site contract

The supported image decodes an exact 12-byte entry plan:

| RVA | Bytes | Instruction |
|---|---|---|
| `0x8D5CA0` | `40 57` | `push rdi` |
| `0x8D5CA2` | `48 83 EC 10` | `sub rsp,0x10` |
| `0x8D5CA6` | `4C 8B 09` | `mov r9,[rcx]` |
| `0x8D5CA9` | `48 8B FA` | `mov rdi,rdx` |

Continuation is `0x8D5CAC`; plan hash is
`78f1c9ad4e04328b8b585a891d613e64cfa79103bdc6acf7913f857f558d1641`.
There are no RIP-relative operands, relative branches, or supplied CFG edges
into the span. The span is fully covered by the CODE-0005A ordinary copy class.

Both known callsites are kept separate. At `0x2807C8` and `0x2810A3`, RCX is
`R15`, RDX is `RBP-0x30`, and R8D is `0x100`; R9's source is not reduced to a
stable expression. The helper's first instructions establish R9 and RDI, but
incoming nonvolatile state and flags cannot be handed to an unreviewed
observer without a site-specific wrapper.

The helper reads A from `[r9+0x498]` (zero-extended byte), R from
`[r9+0x4A0]` (zero-extended word), and B from `[r9+0x4A2]` (zero-extended
word). A is safe-equivalent because the helper first loads `[rcx]`; R and B
are conditional/later reads and entry-time observer reads are
`UNSAFE_OR_UNPROVEN`. The stack local `RBP-0x30` is live during the call, but a
concrete object bound covering both `+0x38` and `+0x78` is not proven.

Only two direct placement callers are retained in bounded evidence. Thread
ownership and reentrancy are unproven, so the existing SPSC ring is not site
compatible. The existing native worker is a partial drain-host candidate.

Result: `PARTIAL_STATIC`; installation remains disabled and no game hook was
built or installed.
