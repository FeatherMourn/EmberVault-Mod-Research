# CODE-0005B requalification delta

`0x8D5CA0` now has a re-derived, instruction-complete 12-byte plan and no
unsupported relocation in that span. This removes the earlier relocation
blocker only. Site-specific wrapper state/flags, output bounds and lifetime,
conditional A/R/B read safety, producer ownership/reentrancy, unwind safety,
and a proven production drain host remain unresolved.

The site is therefore `PARTIAL_STATIC`, not
`STATICALLY_ELIGIBLE_WITH_CODE_0005A_INFRA`. `installNow=false` and
`gameHookInstallAuthorized=false`; all other CODE-0005 candidates retain their
prior rejection status.
