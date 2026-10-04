import json
import unittest
from pathlib import Path

from src.research_index import load_candidates
from src.research_records import migrate_seed_records


class ResearchRecordMigrationTests(unittest.TestCase):
    def test_migration_adds_version_and_gap_fields(self):
        path = Path(__file__).parents[1] / "research" / "candidates" / "INITIAL_CATALOG_CANDIDATES_20261004.json"
        source = load_candidates(path)
        migrated = migrate_seed_records(source)
        self.assertEqual(len(migrated), 8)
        self.assertTrue(all(record["record_schema_version"] == 1 for record in migrated))
        self.assertTrue(all("contradictions" in record for record in migrated))

    def test_migration_does_not_change_seed_claims(self):
        path = Path(__file__).parents[1] / "research" / "candidates" / "INITIAL_CATALOG_CANDIDATES_20261004.json"
        source = load_candidates(path)
        migrated = migrate_seed_records(source)
        self.assertEqual(
            [record["supported_claims"] for record in migrated],
            [record["supported_claims"] for record in source],
        )
        self.assertEqual(json.dumps(source, sort_keys=True), json.dumps(load_candidates(path), sort_keys=True))
