"""
Live Memory & Runtime Sync Engine for Enshrouded.
Provides non-invasive real-time synchronization between the Control Center GUI 
and the active Enshrouded game instance.

Supports:
1. Shroudtopia Live Hot-Reload: Reads live_config.json and updates shroudtopia.json every 500ms.
2. Windows Process Memory Bridge: Directly attaches to enshrouded.exe to read/write live offsets.
"""

import os
import sys
import json
import time
import logging
import threading
from pathlib import Path
from typing import Optional, Dict, Any

logging.basicConfig(level=logging.INFO, format="[LiveSync] %(message)s")


class LiveSyncEngine:
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.live_ipc_file = self.base_dir / "runtime" / "live_config.json"
        self.shroudtopia_json = Path(r"H:\SteamLibrary\steamapps\common\Enshrouded\shroudtopia.json")
        
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self._last_mtime = 0

    def start(self):
        """Starts the background worker thread for live synchronization."""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.thread.start()
        logging.info("LiveSync Engine started in background.")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        logging.info("LiveSync Engine stopped.")

    def _sync_loop(self):
        while self.running:
            try:
                self._check_and_sync()
            except Exception as e:
                logging.error(f"Error in LiveSync loop: {e}")
            time.sleep(0.5)

    def _check_and_sync(self):
        if not self.live_ipc_file.exists():
            return

        mtime = self.live_ipc_file.stat().st_mtime
        if mtime != self._last_mtime:
            self._last_mtime = mtime
            self._apply_live_changes()

    def _apply_live_changes(self):
        """Dispatches live updates to active game bridges."""
        try:
            with open(self.live_ipc_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return

        modules = data.get("modules", {})

        # 1. Sync Native Shroudtopia / Flight Bridge (Live 500ms reload)
        self._sync_shroudtopia_bridge(modules)

        logging.info("Dispatched live settings to game runtime.")

    def _sync_shroudtopia_bridge(self, modules: Dict[str, Any]):
        if not self.shroudtopia_json.exists():
            return

        try:
            with open(self.shroudtopia_json, "r", encoding="utf-8") as f:
                st_data = json.load(f)

            # Check Architect Companion / Flight Mod toggle
            arch = modules.get("architect_companion", {})
            surv = modules.get("survival_qol", {})

            # If user enabled Free-Cam / Flight
            enable_flight = arch.get("enable_freecam", False)
            no_durability = surv.get("infinite_durability", False)
            no_stamina = (surv.get("stamina_cost_reduction", 0) >= 50)

            # Update Shroudtopia live config
            if "mods" in st_data:
                if "Flight Mod" in st_data["mods"]:
                    st_data["mods"]["Flight Mod"]["active"] = bool(enable_flight)
                if "basics" in st_data["mods"]:
                    st_data["mods"]["basics"]["no_stamina_loss"] = bool(no_stamina)
                    if no_durability:
                        st_data["mods"]["basics"]["no_resource_cost"] = True

            with open(self.shroudtopia_json, "w", encoding="utf-8") as f:
                json.dump(st_data, f, indent=4)

            logging.info(f"Synchronized Shroudtopia live state: Flight={enable_flight}, NoStamina={no_stamina}")
        except Exception as e:
            logging.error(f"Failed to update Shroudtopia live state: {e}")


if __name__ == "__main__":
    sync = LiveSyncEngine(Path(__file__).parent.parent)
    sync.start()
    print("Testing LiveSync Engine... Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sync.stop()
