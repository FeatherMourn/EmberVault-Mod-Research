# Runtime adapter status

Stage 18 expands the adapter framework without claiming unsupported gameplay
surfaces. The EML adapter remains experimental and supports only the evidenced
`baseCritChance` scalar on EML API 1.3 and Enshrouded build 1076226.

The Control Center now exposes a compatibility report containing adapter ID and
version, loader/API, supported builds, supported keys, compatibility state, and
the reserved Shroudtopia adapter boundary. An incompatible report is fail-closed.

Additional EML settings require independent evidence packets. Shroudtopia must
provide separate loader detection, configuration mapping, backup rules,
verification, rollback, and compatibility evidence; it must not inherit EML
assumptions.
