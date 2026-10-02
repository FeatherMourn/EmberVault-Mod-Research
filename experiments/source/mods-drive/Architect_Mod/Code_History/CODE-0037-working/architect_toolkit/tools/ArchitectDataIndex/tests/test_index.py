import hashlib
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from builder import build
from query_index import query

ROOT=HERE.parents[2]

class IndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.path=Path(cls.temp.name)/"index.sqlite"
        build(cls.path,ROOT)
        cls.db=sqlite3.connect(cls.path);cls.db.row_factory=sqlite3.Row
    @classmethod
    def tearDownClass(cls):cls.db.close();cls.temp.cleanup()
    def test_known_wand_source_from_local_export(self):
        rows=query(self.db,"item","1693828837")
        self.assertEqual(rows[0]["debug_name"],"Weapon_T1_1H_Wand_01_Fire")
    def test_known_stone_from_research_source(self):
        rows=query(self.db,"item","631520303")
        self.assertEqual(rows[0]["debug_name"],"Build_TerrainMaterial_T1_Stone")
    def test_reflected_itemstack_size(self):
        row=self.db.execute("SELECT reflected_size FROM resource_types WHERE name='keen::ItemStack'").fetchone()
        self.assertEqual(row[0],0x0C)
    def test_schema_has_all_core_tables(self):
        names={r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        required={"builds","resource_types","resources","items","item_registry","recipes","recipe_inputs","recipe_outputs","terrain_configs","building_configs","blueprints","blueprint_snap_rules","templates","template_components","attributes","attribute_groups","perks","skill_nodes","impact_programs","actor_sequences","map_markers","camera_states"}
        self.assertTrue(required<=names)
        self.assertTrue(self.db.execute("SELECT 1 FROM sqlite_master WHERE name='building_material_layers'").fetchone())
    def test_repeat_build_is_byte_deterministic(self):
        second=Path(self.temp.name)/"second.sqlite";build(second,ROOT)
        digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
        self.assertEqual(digest(self.path),digest(second))
    def test_missing_family_is_empty_not_fabricated(self):
        row=self.db.execute("SELECT status,row_count FROM coverage WHERE family='impact_programs'").fetchone()
        self.assertEqual(tuple(row),("UNAVAILABLE",0))
    def test_empty_material_query_is_graceful(self):
        rows=query(self.db,"material-id","128")
        self.assertTrue(rows)
        self.assertTrue(any(row.get("place_voxel_material_id") == 128 for row in rows if "place_voxel_material_id" in row))

    def test_kfc_bundle_is_ingested_when_present(self):
        self.assertGreaterEqual(self.db.execute("SELECT COUNT(*) FROM items").fetchone()[0], 3609)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM blueprint_snap_rules").fetchone()[0], 31)
        self.assertEqual(self.db.execute("SELECT source_bundle_sha256 FROM builds").fetchone()[0], "153BE9AF6875DB39594FDCAC7A08EE8B316C802BE8A426D24F0A9DFAE713C474")

    def test_unregistered_item_infos_remain_distinguishable(self):
        count=self.db.execute("SELECT COUNT(*) FROM items WHERE item_id NOT IN (SELECT item_id FROM item_registry WHERE item_id IS NOT NULL)").fetchone()[0]
        self.assertGreater(count, 0)

if __name__=="__main__":unittest.main()
