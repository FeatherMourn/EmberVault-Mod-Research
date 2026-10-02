import subprocess
import sys
from pathlib import Path

def test_headless():
    base_dir = Path(__file__).parent.parent
    sys.path.append(str(base_dir))
    from core.manager import ModuleManager
    manager = ModuleManager(base_dir)
    print("Discovered modules:", list(manager.modules.keys()))
    assert "survival_qol" in manager.modules, "survival_qol missing"
    assert "architect_companion" in manager.modules, "architect_companion missing"
    
    # Test updating a setting
    manager.update_setting("architect_companion", "camera_fov", 95, is_dynamic=True)
    manager.compile_master_lua()
    
    with open(base_dir / "runtime" / "live_config.json") as f:
        live = f.read()
    print("Live config verified:\n", live)

if __name__ == "__main__":
    test_headless()
