# Findings registry

This registry is intentionally conservative. A row is a research claim, not merely a file name. Add evidence links and build/version information before upgrading a claim's confidence.

| ID | Area | Finding | Status | Confidence | Build/version | Evidence |
|---|---|---|---|---|---|---|
| F-0001 | Research process | Runtime observations, static analysis, and implementation behavior must be recorded separately to avoid turning inference into fact. | Confirmed process rule | High | Repository-wide | `RECORD_TEMPLATE.md`, categorized source archive |
| F-0002 | Building and placement | The research corpus contains repeated investigations into selection, preview, snapping, blueprint authority, placement destination, and structure coordinates. | Evidence present; synthesis pending | Medium | Multiple recorded builds | `../research/source/mods-drive/Architect_Mod/` |
| F-0003 | Entities and observers | The corpus contains multiple investigations into player discovery, item observers, descriptors, ownership, ECS systems, and observer call paths. | Evidence present; synthesis pending | Medium | Multiple recorded builds | `../research/source/mods-drive/Architect_Mod/` |
| F-0004 | Settings and administration | Game settings, admin actions, multiplayer behavior, and backend protocols are recurring research areas with implementation work attached. | Evidence present; synthesis pending | Medium | Multiple recorded builds | `../research/source/mods-drive/Architect_Mod/` |
| F-0005 | Data formats | KFC/reference extraction and rebuilt reference artifacts are part of the research workflow. | Evidence present; reproducibility audit pending | Medium | Record per artifact | `../experiments/source/mods-drive/`, `../reference/` |

## Status vocabulary

- **Confirmed** — reproduced or directly evidenced with a documented procedure.
- **Strongly supported** — multiple independent evidence paths agree, but a remaining runtime or version gap exists.
- **Working hypothesis** — plausible interpretation requiring a targeted experiment.
- **Evidence present; synthesis pending** — source material exists, but no canonical conclusion has been written yet.
- **Disproved/obsolete** — contradicted by later evidence or invalidated by a game update.
