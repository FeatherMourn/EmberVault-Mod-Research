# Stage 22 — Research and Knowledge Collaboration

Stage 22 adds collaboration primitives to the isolated Research workspace while
keeping publication sanitized and evidence-bound.

## Delivered so far

- Relative evidence attachments with private source paths excluded from reports.
- Bounded runtime-log import that stores sanitized text evidence only.
- Reproducibility scoring based on hypothesis, evidence, reproduction steps,
  build identity, and completed outcome.
- Comparison runs, discussion notes, and sanitized research reports.
- Control Center actions and status summaries for comparisons, discussion, and
  reproducibility reporting.

## Safety boundary

Imported logs do not authorize gameplay mutation. Reports contain counts and
reproducibility metadata rather than private source paths or raw project data.
Existing profile, operations, adapter, promotion, and publication gates remain
the authority for runtime evidence and public release.

## Completion status

Experiment-template selection, evidence inspection, research filtering, and
research-to-knowledge promotion are exposed through the Control Center. A
promoted record becomes a private knowledge draft and must be published
explicitly.
