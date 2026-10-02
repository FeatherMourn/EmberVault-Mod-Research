# CODE-0042G5H — Closeout blocker audit

Date: 2026-09-21
Build: Enshrouded 1076226

Independent verification result:
`G5H closeout is BLOCKED pending source/parity cleanup.`

Verified Current identity:
- Length: 458779 bytes
- SHA-256: `B88E1388EDFE7CA6412C695667E1237CA7B4CA8D0EF29FC8B14844F8979A6AC0`

Verified prior G5G identity:
- Length: 449290 bytes
- SHA-256: `D82ECDA9A9EAAC7837B22B640235D1C4DC63FF947A88B843D06537F1DCC0BB1B`

Verified registry:
- SHA-256: `7F2F5C38B75AF24B45728D5D6B6FBD5A9420BE51BF52888DD008AE77B0E21AA8`

Findings:

1. Current added an out-of-scope dead backup function:
   `Render-MultiplayerQuestsPageLegacy`
   The G5H goal allowed product edits only to `Render-MultiplayerQuestsPage`.

2. The active responsive renderer lost several pre-G5H state-dependent presentation semantics:
   - quarantine toggle ON/OFF background selection;
   - selected category highlight;
   - quest status color mapping;
   - per-quest quarantine state color;
   - per-quest status/reset state color;
   - missing-ID disabled BackColor/ForeColor.

3. The new legacy function retains the old fixed-pixel source patterns, so whole-file regex/string parity assertions can falsely pass by matching dead legacy code instead of the active renderer.

4. Independent named-function comparison confirms all required quest helpers and protected G5B-G5G renderers are otherwise source-identical. A trailing blank-line-only difference was observed at the end of `Show-F8Category`; it is nonfunctional formatting, not evidence of F8 feature work.

Disposition:
- Do NOT mark G5H closed yet.
- Remove the legacy function.
- Restore state-dependent presentation parity inside the active responsive renderer.
- Scope the TEMP parity fixture to the active renderer function/AST.
- Rerun full regression before closure.
