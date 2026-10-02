# Custom icon import evidence

The first live fixture run completed the runtime evidence chain on build
1076226:

- `IMPORTED_ICON|ok=true` — PNG decode, texture encoding, content creation,
  and `UiTextureResource` registration succeeded;
- `REGISTERED|itemId=3987654333|recipeId=3987654334` — the custom item and
  recipe remained registrable after the new content asset was created;
- `UI_LINKS|1|matching_sets=1` — the cloned recipe appeared in the UI catalog
  link structure;
- no panic or loader failure followed the import operation.

The machine-checkable verifier is `research/tools/verify_icon_import_log.py`.
It intentionally does not claim visual success: a screenshot and a fresh
restart session are still required before this becomes a production fixture.
