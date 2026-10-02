# Content Wizard UI Target

The supplied split-screen 3D Content Onboarding & Import Wizard is the visual
target for the beginner authoring experience.

## Product mapping

The current Control Center remains a Windows desktop application. The target
layout should therefore be implemented as a desktop wizard unless a separate
web front end is deliberately approved later. Do not create a disconnected
Next.js application that cannot create or validate Control Center projects.

| Supplied concept | Control Center behavior |
| --- | --- |
| Input & Concept | Choose the content type and name it in the Content Wizard. |
| Mesh & Geometry | Choose a donor item and, when supported, inspect model metadata. |
| Materials & Baking | Choose frame/bedding/trim colors and record material research. |
| Export | Validate, create the self-contained project, and prepare a test package. |
| 3D viewport | Show a real preview only when a verified asset renderer is available; otherwise show a clearly labelled donor fallback or research preview. |
| Mesh health | Report checks that were actually run; never invent triangle, UV, or topology results. |
| Game-ready badge | Use only for a capability with current same-build runtime evidence. Research-only visual changes must remain amber/research-labelled. |

## Required beginner flow

1. Select what to create: recolor, clone, or new project.
2. Select the donor item.
3. Select appearance changes with controls, not a free-form description alone.
4. Review the donor, requested changes, safety state, and preview policy.
5. Create one self-contained project.
6. Validate it before testing.
7. Test in an isolated research profile.
8. Record runtime evidence before calling the result game-ready.

## Preview and status rules

- A donor fallback must be labelled **Donor preview**.
- A generated approximation must be labelled **Research preview**.
- A real same-build rendered result may be labelled **Runtime verified** only
  after durable catalog/placement evidence is recorded.
- The UI must not display “Game-ready” merely because a JSON definition or
  package validates.

## Current implementation boundary

The desktop Content Wizard already implements donor selection, color swatches,
review, self-contained project creation, validation, and editing. The supplied
Three.js viewport remains a future presentation layer because original mesh
import and verified material/texture rendering are still research-gated.
