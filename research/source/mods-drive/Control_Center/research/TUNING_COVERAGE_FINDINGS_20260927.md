# Game tuning coverage findings — build 1076226

The initial machine-readable audit compares the complete extracted reflection
inventory with the current Control Center module manifests.

- Reflected resource families inspected: **131**
- Families currently targeted by modules: **22**
- Families not currently targeted: **109**
- Control Center modules: **28**
- User-facing settings: **101**

The 109 uncovered families are a backlog, not a list of guaranteed editable
settings. The reflection inventory includes rendering, animation, world,
network, internal registries, and other engine resources that may be read-only,
unsupported, server-authoritative, or unsafe to patch. Each uncovered family
must be triaged into one of four states: verified, experimental,
research-only, or unsupported.

The next tuning expansion should prioritize families in these categories:

1. balance and progression;
2. items, equipment, recipes, loot, and resources;
3. building, materials, farming, and world rules;
4. buffs, skills, interactions, and AI;
5. presentation and convenience settings.

The reusable report tool is `tools/report_tuning_coverage.py`, and its current
output is `research/TUNING_COVERAGE_1076226.json`.
