# Stage 14 integration contract

Cross-module actions use an `Operation` as their audit envelope. The envelope
contains the operation ID, profile ID, capability, capability state, and
recovery expectation. `OperationService.integration_context()` converts that
envelope into the validated `IntegrationContext` contract.

Modules exchange stable record IDs and this context; they do not reach into
another module's private storage. The context is intentionally descriptive and
does not grant mutation authority.

## Handoff map

| Handoff | Contract boundary | Safety rule |
| --- | --- | --- |
| Mods → Profiles | profile ID and package deployment plan | package state is evaluated for the selected profile |
| Mods → Compatibility | compatibility findings and declared package IDs | incompatible packages are not deployed |
| Research → Knowledge | research ID and evidence references | only reviewed/published knowledge is exported |
| Research → Runtime Adapter | operation context and runtime evidence | adapter remains experimental and fail-closed |
| Content Creator → Research | stable research IDs and design references | content remains plan/design-only |
| Character Tools → Save Manager | profile ID and verified backup ID | save manager remains inspection/backup/restore-only |
| Trainer → Save Manager | profile ID and verified backup ID | trainer remains plan-only |
| All modules → Catalog | sanitized IDs and contract versions | private paths and raw records are excluded |

Every mutating or guarded handoff must retain the originating operation and
profile context. Recovery expectations describe what must be true before the
action is allowed; they do not bypass the existing risk gates.
