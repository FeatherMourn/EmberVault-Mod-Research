"""Offline structural validator for the independently authored Phase 1 table."""
from pathlib import Path
import hashlib
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).parent
TABLE = ROOT / "Enshrouded_Independent_Phase1.CT"
EXE = Path(r"H:\SteamLibrary\steamapps\common\Enshrouded\enshrouded.exe")
EXPECTED_HASH = "AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781"

text = TABLE.read_text(encoding="utf-8")
root = ET.fromstring(text)
assert root.tag == "CheatTable"
assert len(root.findall("./CheatEntries/CheatEntry")) >= 4
descriptions = "\n".join(x.text or "" for x in root.findall("./CheatEntries/CheatEntry/Description"))
assert "[00] DIAGNOSTICS & INFRASTRUCTURE" in descriptions
assert "[04] EXPERIMENTAL / HIGH RISK (DISABLED BY DEFAULT)" in descriptions
assert text.count("[ENABLE]") == text.count("[DISABLE]")
assert "exactly one match" in text
assert "unregisterSymbol" in text
assert "No allocations" in text
assert "Independent_AOB_Scan" in text
assert "expected exactly 1 match" in text
assert "Independent_Cleanup" in text
assert "getAddressList" in text
assert "record.Active = false" in text

actual_hash = hashlib.sha256(EXE.read_bytes()).hexdigest().upper()
assert actual_hash == EXPECTED_HASH, (actual_hash, EXPECTED_HASH)

print("TABLE_XML=OK")
print("ENABLE_DISABLE_PARITY=OK")
print("REQUIRED_INFRASTRUCTURE=OK")
print(f"EXECUTABLE_SHA256={actual_hash}")
print("LIVE_GAMEPLAY_VALIDATION=REQUIRED_BY_USER")
