# Bed Clone Dependency Audit

The staged clone preserves the donor's external dependency graph. These references must be present in the eventual KFC/content package:

| Role | GUID |
|---|---|
| placed entity | `9b1b68dd-1d4f-408d-aaf8-5bb82badd7d5` |
| cursor/icon model | `4c7f1c3a-b448-4460-ad5e-a79b3859d2c1` |
| icon scene | `bb6e4131-f978-4707-bd0c-f573d59b1d37` |
| display name localization | `6c5c9ec4-53d0-4d34-a66b-16ce17592c51` |
| description localization | `70055d1e-9fab-4f4e-ab15-42a41701d80f` |
| lore localization | `2d9b42be-a3ec-453d-866b-9af710066832` |
| interaction sequence | `7294de78-fb4b-4045-928e-f38cc35dc353` |
| knowledge unlock | `37533fd3-f1d7-4c24-bf2b-1432a8ea8559` |

The staging subset now includes the three dependencies that were directly found by GUID in the extracted KFC archives:

- `TemplateResource/9b1b68dd-1d4f-408d-aaf8-5bb82badd7d5_39768775_0.json`
- `RenderModel/4c7f1c3a-b448-4460-ad5e-a79b3859d2c1_177394c7_0.json`
- `ActorSequenceResource/7294de78-fb4b-4045-928e-f38cc35dc353_9fd4a561_0.json`

The staging subset is still not a complete repackable content package because the scene/localization/knowledge-query references are represented through additional content or hash-based resources.

The direct runtime references that can be represented as standalone extracted resources are now staged. The remaining references were searched across the available KFC archive index. Localization, icon-scene, and knowledge-query references do not resolve to ordinary standalone resources in the subset; additional template/render/sequence references resolve into shared packed resources rather than a self-contained mod package.

## Closure result

- **Resolved and staged:** donor `TemplateResource`, cursor `RenderModel`, interaction `ActorSequenceResource`.
- **Resolved in packed data but not safely isolated:** shared template/render/sequence dependencies and hash-addressed scene data.
- **Not resolved as standalone resources:** display-name, description, lore, icon-scene, and knowledge-query references.
- **Live game status:** unchanged; no KFC archive was repacked and no game files were overwritten.

This is the stopping point for a safe EML-only workflow. A visible new bed requires a full KFC extraction/repack workflow with coordinated archive edits and validation against the exact game build; the EML runtime injection test demonstrated that manually appending registries is insufficient because the engine catalog remains unchanged.
