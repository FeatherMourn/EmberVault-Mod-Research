# BlenderTools guide

Use BlenderTools to create or export a model, then use Control Center to review
the export before it can affect the game.

## Safe workflow

1. Export a complete folder from BlenderTools and keep the original export as your source copy.
2. Open **Content Studio** and choose **Check BlenderTools export**.
3. Select the folder containing `mod.json`, `render_data.bin`, `validation.json`, and `src`.
4. Review the validation result. Failed or incomplete exports stay out of the game.
5. Stage the validated copy, then open **Research Lab** and choose **Start guided test**.
6. Capture and catalog the in-game result. Treat it as experimental until evidence is recorded.

Control Center copies the export into its project area and does not modify the original BlenderTools folder. A successful package check is not proof that the game will render the asset; runtime testing is separate.
