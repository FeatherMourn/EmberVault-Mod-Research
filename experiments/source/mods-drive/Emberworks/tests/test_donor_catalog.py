import unittest
import json
import tempfile
from pathlib import Path

from blueprint_library import DonorIndex, parse_content_probe_lines


class DonorCatalogTests(unittest.TestCase):
    def test_parses_and_deduplicates_probe_records(self):
        lines = [
            'x [CC-CONTENT-PROBE] ITEM|2|guid=g-1|itemId=10|debugName=Wall|category=BuildTools"',
            'x [CC-CONTENT-PROBE] ITEM|2|guid=g-1|itemId=10|debugName=Wall|category=BuildTools"',
            'x [CC-CONTENT-PROBE] ITEM|3|guid=g-2|itemId=11|debugName=Door|category=BuildTools"',
        ]
        records = parse_content_probe_lines(lines)
        self.assertEqual([record.guid for record in records], ["g-2", "g-1"])
        self.assertEqual(records[0].debug_name, "Door")

    def test_index_searches_name_category_and_item_id(self):
        records = parse_content_probe_lines([
            'x [CC-CONTENT-PROBE] ITEM|2|guid=g-1|itemId=10|debugName=Stone Wall|category=BuildTools"',
            'x [CC-CONTENT-PROBE] ITEM|3|guid=g-2|itemId=11|debugName=Iron Door|category=BuildTools"',
        ])
        index = DonorIndex(records)
        self.assertEqual(len(index.search("stone")), 1)
        self.assertEqual(len(index.search("11", category="BuildTools")), 1)

    def test_index_reloads_generated_json(self):
        records = parse_content_probe_lines([
            'x [CC-CONTENT-PROBE] ITEM|2|guid=g-1|itemId=10|debugName=Stone Wall|category=BuildTools"',
        ])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "donors.json"
            path.write_text(json.dumps([record.__dict__ for record in records]), encoding="utf-8")
            self.assertEqual(len(DonorIndex.from_json(path).search("stone")), 1)


if __name__ == "__main__":
    unittest.main()
