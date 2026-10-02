# Semantic Capture Analyzer

The Semantic Capture Analyzer reads existing Architect bridge artifacts and
produces deterministic JSON and Markdown research summaries. It never launches
or attaches to Enshrouded and does not load or modify the native runtime.

From the Architect Toolkit root:

```powershell
python tools/SemanticCaptureAnalyzer/analyze.py
```

The default input is `bridge/`. Outputs are:

- `bridge/analysis/latest_semantic_capture_report.json`
- `bridge/analysis/latest_semantic_capture_report.md`

Analyze a copied or sanitized bundle with:

```powershell
python tools/SemanticCaptureAnalyzer/analyze.py --input C:\captures\session --output C:\captures\session\analysis
```

All listed bridge inputs are optional. Malformed JSON and truncated JSONL lines
become warnings; valid records continue to be analyzed. Events are grouped by
`sessionId`, and status-bearing files are compared with the selected current
session to expose mixed or stale artifacts.

Inventory arithmetic and pointer-stride findings use capture assessments:
`SUPPORTED_BY_CAPTURE`, `CONTRADICTED_BY_CAPTURE`, or
`INSUFFICIENT_EVIDENCE`. These do not silently alter the project's separate
`PROVEN`, `INFERRED`, `EXPERIMENTAL`, `UNSOLVED`, and `DISPROVEN` states.

Building pairs retain their raw records and compare complete payload equality,
timing, threads, contexts, callers, and returns. The analyzer never assigns
client/server sides. Item/material names are loaded only from explicit local
JSON indexes matching item/material/KFC index naming conventions; otherwise raw
IDs remain unresolved.

The analyzer also accepts future `create_building_item_action` records. It
normalizes the reflected `versionRaw`, `selectedIndexRaw`, and `itemIdRaw`
fields, resolves IDs only through the offline ArchitectDataIndex, and reports a
nearest committed placement as a conservative correlation. A nearby equal ID
is never promoted to a causal relationship, and lifecycle labels remain
`unknown` until a validated native consumer supplies selection/preview/cancel/
commit evidence. The v0.21/v0.22 static maps intentionally leave that observer
disabled. The analyzer is also schema-ready for a future bounded
`client_player_input_snapshot` record and reports its candidate base plus the
reflected create/building-stock fields without promoting ownership from a
single action-shaped pointer.

Run the analyzer tests with:

```powershell
python -m unittest discover -s tools/SemanticCaptureAnalyzer/tests -p "test_*.py" -v
```

The v0.25 `scan_building_snap_static.py` tool is intentionally separate from
capture analysis. It decodes only bounded, build-locked placement ranges and
emits `bridge/building_snap_static_map.json`; it performs no process access and
sets `observerDecision.install` to `false` until a preview transform boundary
is independently validated.
