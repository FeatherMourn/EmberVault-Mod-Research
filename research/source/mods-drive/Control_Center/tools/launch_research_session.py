"""Launch Enshrouded through Steam and wait for a fresh EML log session."""
from __future__ import annotations
import argparse, json, subprocess
import sys
import time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from core.profile_launch import ProfileLaunchService
from core.save_backup import game_is_running


def wait_for_game_process(timeout: float = 15.0, interval: float = 0.5) -> bool:
    """Wait briefly for Steam to finish starting the game process."""
    deadline = time.monotonic() + max(0.0, timeout)
    while True:
        if game_is_running():
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(max(0.05, interval))

def launch_and_wait(game_dir: Path, log_path: Path, baseline_size: int, timeout: float) -> dict:
    game_dir=Path(game_dir).resolve(); log_path=Path(log_path)
    if not (game_dir/"Enshrouded.exe").is_file(): raise ValueError("Enshrouded.exe was not found")
    if game_is_running(): raise ValueError("Enshrouded is already running; close it before starting a research session")
    subprocess.Popen(["explorer.exe", f"steam://rungameid/{ProfileLaunchService.GAME_APP_ID}"])
    started=ProfileLaunchService.wait_for_eml_session(log_path, baseline_size, timeout=timeout)
    process_observed = wait_for_game_process()
    return {"schema":"control_center.research_session_launch.v1","steam_uri":f"steam://rungameid/{ProfileLaunchService.GAME_APP_ID}","log":str(log_path),"baseline_size":baseline_size,"fresh_session_observed":started,"game_process_observed":process_observed}

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("game_dir",type=Path); parser.add_argument("log",type=Path); parser.add_argument("--baseline-size",type=int,required=True); parser.add_argument("--timeout",type=float,default=60); parser.add_argument("--output",type=Path); args=parser.parse_args()
    result=launch_and_wait(args.game_dir,args.log,args.baseline_size,args.timeout); rendered=json.dumps(result,indent=2); print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered+"\n",encoding="utf-8")
    return 0 if result["fresh_session_observed"] and result["game_process_observed"] else 2
if __name__=="__main__": raise SystemExit(main())
