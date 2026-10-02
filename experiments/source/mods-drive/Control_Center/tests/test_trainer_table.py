from pathlib import Path
import sys

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from core.trainer_table import describe, inventory


def test_original_trainer_is_parseable_and_read_only():
    table = BASE.parent / "Cheat Tables" / "Enshrouded_Master_Trainer.CT"
    before = table.stat().st_mtime_ns
    info = describe(table)
    records = inventory(table)
    assert info["record_count"] == len(records)
    assert info["record_count"] > 0
    assert info["script_count"] > 0
    assert table.stat().st_mtime_ns == before
