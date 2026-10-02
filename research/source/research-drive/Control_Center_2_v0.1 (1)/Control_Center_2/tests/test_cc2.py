import tempfile
import unittest
from pathlib import Path
from cc2.catalog import CatalogError, as_id, normalize_guid, get_item, diagnostics, search_items
from cc2.planner import plan_new_item, save_plan
from cc2.graph import build_graph
from cc2.wizard import detect, RAKE, probe_status, install_probe, runtime_state

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'workspace' / 'catalog.sqlite3'


class CatalogTests(unittest.TestCase):
    @unittest.skipUnless(DB.is_file(), 'optional bundled catalog snapshot unavailable')
    def test_snapshot_and_relationships(self):
        d = diagnostics(DB)
        self.assertEqual(d['item_info'], 3609)
        self.assertEqual(d['registered_items'], 3520)
        self.assertEqual(d['recipes'], 1954)
        self.assertEqual(d['registered_without_iteminfo'], 0)
        self.assertEqual(d['contradictory_guid_numeric_refs'], 0)
        rows = search_items(DB, 'stone', 5)
        self.assertTrue(rows)
        detail = get_item(DB, rows[0]['guid'])
        self.assertEqual(detail['guid'], rows[0]['guid'])

    def test_invalid_fields_are_rejected(self):
        self.assertIsNone(as_id(-1))
        self.assertIsNone(as_id(True))
        self.assertIsNone(as_id(2**32))
        self.assertIsNone(normalize_guid('not-a-guid'))

    def test_wizard_detection_is_non_mutating_and_keeps_reference(self):
        data = detect(Path('Z:/not-an-install'), DB)
        self.assertTrue(data['installation']['available'])
        self.assertTrue(data['catalog']['available'])
        self.assertEqual(RAKE, 'f9abaf9b-060c-470d-a8c3-c7c567ebaa1e')

    def test_probe_install_identical_outdated_partial_and_unrelated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); game=root/'game'; (game/'mods').mkdir(parents=True)
            target=game/'mods'/'cc2_research_probe'
            self.assertEqual(probe_status(target)['status'],'absent')
            first=install_probe(game,root/'workspace')
            self.assertEqual(first['status'],'installed')
            self.assertEqual(probe_status(target)['status'],'identical')
            self.assertTrue(install_probe(game,root/'workspace')['continue'])
            (target/'src'/'mod.lua').write_text('old',encoding='utf-8')
            self.assertEqual(probe_status(target)['status'],'outdated')
            with self.assertRaises(CatalogError): install_probe(game,root/'workspace')
            replaced=install_probe(game,root/'workspace',replace=True)
            self.assertEqual(replaced['status'],'replaced')
            (target/'src'/'mod.lua').unlink()
            self.assertEqual(probe_status(target)['status'],'partial')
            install_probe(game,root/'workspace',replace=True)
            (target/'mod.json').write_text('{"id":"someone_else"}',encoding='utf-8')
            self.assertEqual(probe_status(target)['status'],'unrelated')
            with self.assertRaises(CatalogError): install_probe(game,root/'workspace',replace=True)

    def test_runtime_states_require_cc2_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); game=root/'game'; (game/'mods').mkdir(parents=True); (game/'export').mkdir()
            (game/'shroudtopia.json').write_text('{"export_directory":"export","enableLogging":true}',encoding='utf-8')
            self.assertEqual(runtime_state(game,DB)['state'],'probe_not_installed')
            install_probe(game,root/'workspace')
            self.assertEqual(runtime_state(game,DB)['state'],'installed_execution_unconfirmed')
            (game/'enshrouded.log').write_text('[CC2 OBSERVE] Probe loaded\nCC2 export failed: disabled',encoding='utf-8')
            self.assertEqual(runtime_state(game,DB)['state'],'executed_export_failed')
            (game/'export'/'cc2_probe_execution_1.json').write_text('not json',encoding='utf-8')
            self.assertEqual(runtime_state(game,DB)['state'],'export_created_collection_failed')
            (game/'export'/'cc2_probe_execution_1.json').write_text('{"probe":"cc2_research_probe"}',encoding='utf-8')
            self.assertEqual(runtime_state(game,DB)['state'],'complete_success')

    def test_probe_repair_normalizes_line_endings_and_verifies_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); game=root/'game'; (game/'mods').mkdir(parents=True)
            install_probe(game,root/'workspace')
            lua=game/'mods'/'cc2_research_probe'/'src'/'mod.lua'
            lua.write_bytes(lua.read_bytes().replace(b'\n',b'\r\n'))
            self.assertEqual(probe_status(game/'mods'/'cc2_research_probe')['status'],'identical')
            lua.write_text('genuine drift',encoding='utf-8')
            self.assertEqual(probe_status(game/'mods'/'cc2_research_probe')['status'],'outdated')
            result=install_probe(game,root/'workspace',replace=True)
            self.assertEqual(probe_status(game/'mods'/'cc2_research_probe')['status'],'identical')
            self.assertTrue(Path(result['backup']).is_dir())

    @unittest.skipUnless(DB.is_file(), 'optional bundled catalog snapshot unavailable')
    def test_graph_is_guid_resolved_and_fail_closed(self):
        graph = build_graph(DB, 'f9abaf9b-060c-470d-a8c3-c7c567ebaa1e')
        self.assertEqual(graph['validation']['status'], 'PASS')
        self.assertEqual(graph['nodes']['RecipeRegistryResource']['source']['field_path'], 'recipes[13]')
        self.assertEqual(graph['game_build'], 'UNKNOWN')

    @unittest.skipUnless(DB.is_file(), 'optional bundled catalog snapshot unavailable')
    def test_plan_is_not_deployable_and_cannot_overwrite(self):
        registered = search_items(DB, 'stone', 5)[0]
        plan = plan_new_item(DB, registered['guid'], slug='test_stone_clone', name='Test Stone Clone')
        self.assertEqual(plan['status'], 'EXPERIMENTAL_NOT_DEPLOYABLE')
        self.assertIsNone(plan['resource_graph']['ItemInfo']['new_numeric_item_id'])
        self.assertTrue(plan['safety']['no_game_mutation'])
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'plan.json'
            save_plan(plan, target)
            self.assertTrue(target.is_file())
            with self.assertRaises(CatalogError):
                save_plan(plan, target)
        # prevent accidental writes to the original KFC input root even if someone picks that folder
        with self.assertRaises(CatalogError):
            save_plan(plan, Path(plan['source_archive_fingerprints'][0]['kfc_root']) / 'oops.json')


if __name__ == '__main__':
    unittest.main()
