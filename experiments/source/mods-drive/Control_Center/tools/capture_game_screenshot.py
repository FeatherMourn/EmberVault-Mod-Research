"""Capture a timestamped Windows screenshot for a running Enshrouded probe session."""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def capture(output: Path, process_name: str = "enshrouded", evidence_kind: str | None = None) -> dict:
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    command = r'''
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class CaptureWin32 {
 [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);
 [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
}
'@
$p = Get-Process -Name '__PROCESS__' -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $p) { throw 'The requested game process is not running.' }
$bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$rect = New-Object CaptureWin32+RECT
if ($p.MainWindowHandle -ne [IntPtr]::Zero -and [CaptureWin32]::GetWindowRect($p.MainWindowHandle, [ref]$rect)) {
    $width = $rect.Right - $rect.Left
    $height = $rect.Bottom - $rect.Top
    if ($width -gt 0 -and $height -gt 0) {
        $bounds = New-Object System.Drawing.Rectangle($rect.Left, $rect.Top, $width, $height)
    }
}
$bmp = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height)
$graphics = [System.Drawing.Graphics]::FromImage($bmp)
$graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
$bmp.Save('__OUTPUT__', [System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$bmp.Dispose()
'''.replace("__PROCESS__", process_name).replace("__OUTPUT__", str(output).replace("'", "''"))
    result = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", command], capture_output=True, text=True)
    if result.returncode != 0 or not output.is_file():
        detail = (result.stderr or result.stdout).strip() or "screenshot capture failed"
        raise RuntimeError(detail)
    return {
        "schema": "control_center.game_screenshot.v1",
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "process": process_name,
        "capture_mode": "game_window_or_primary_screen",
        **({"evidence_kind": evidence_kind} if evidence_kind else {}),
        "path": str(output),
        "size": output.stat().st_size,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--process", default="enshrouded")
    parser.add_argument("--evidence-kind", choices=("catalog", "item_info", "recipe", "placed_item", "localization", "gameplay", "other"))
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = capture(args.output, args.process, args.evidence_kind)
    rendered = json.dumps(result, indent=2) + "\n"
    print(rendered, end="")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
