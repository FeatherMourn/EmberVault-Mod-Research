import json, tempfile, unittest, zipfile
from unittest.mock import patch
from pathlib import Path
from core.local_mods import LocalModService

class LocalModTests(unittest.TestCase):
    def setUp(self):
        self._running_patch = patch.object(LocalModService, '_running', return_value=False)
        self._running_patch.start()

    def tearDown(self):
        self._running_patch.stop()

    def test_running_game_detection_is_case_insensitive(self):
        self._running_patch.stop()
        try:
            with patch('subprocess.check_output', return_value='Enshrouded.exe          1234 Console                    1     42,000 K\n'):
                self.assertTrue(LocalModService._running())
        finally:
            self._running_patch.start()

    def test_research_only_package_requires_explicit_approval(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); source=root/'mod'; source.mkdir(); (source/'mod.json').write_text(json.dumps({'id':'research','loader':'EML','feature_state':'research-only'})); (source/'mod.lua').write_text('return {}')
            svc=LocalModService(root,root/'state'); pkg=svc.inspect(source); game=root/'game'; game.mkdir(); (game/'Enshrouded.exe').write_text('fake')
            with self.assertRaisesRegex(Exception, 'research-only'): svc.preview(pkg,game)
            self.assertEqual(svc.preview(pkg,game,allow_research=True)['identity'], 'research')

    def test_discovery_safe_zip_and_install_uninstall(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); downloads=root/'downloads'; downloads.mkdir(); game=root/'game'; game.mkdir(); (game/'Enshrouded.exe').write_text('fake')
            archive=downloads/'ember-test.zip'
            with zipfile.ZipFile(archive,'w') as z:
                z.writestr('mod.json',json.dumps({'id':'ember.test','name':'EMBER Test','version':'1.0','author':'Test','loader':'EML'})); z.writestr('README.md','manual'); z.writestr('config.json','{}')
            svc=LocalModService(root,root/'state'); svc.add_folder(downloads); pkg=svc.packages()[0]
            self.assertEqual(pkg.status,'recognized and supported')
            plan=svc.install(pkg,game); self.assertTrue((Path(plan['target'])/'config.json').is_file())
            self.assertIn('ember.test',svc.state['installed']); svc.uninstall('ember.test',game); self.assertFalse((game/'mods'/'ember.test'/'config.json').exists()); self.assertFalse((game/'mods'/'ember.test').exists())

    def test_remove_installed_preserves_user_modified_files(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); source=root/'mod'; source.mkdir(); (source/'mod.json').write_text(json.dumps({'id':'remove.test','loader':'EML'})); (source/'mod.lua').write_text('return {}')
            game=root/'game'; game.mkdir(); (game/'Enshrouded.exe').write_text('fake'); svc=LocalModService(root,root/'state'); svc.install(svc.inspect(source),game,allow_research=True)
            changed=game/'mods'/'remove.test'/'mod.lua'; changed.write_text('user change')
            result=svc.remove_installed('remove.test')
            self.assertEqual(result['preserved'], ['mod.lua']); self.assertTrue(changed.is_file()); self.assertNotIn('remove.test',svc.state['installed'])

    def test_enable_disable_moves_owned_deployment(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); source=root/'mod'; source.mkdir(); (source/'mod.json').write_text(json.dumps({'id':'toggle.test','loader':'EML'})); (source/'mod.lua').write_text('return {}')
            game=root/'game'; game.mkdir(); (game/'Enshrouded.exe').write_text('fake'); svc=LocalModService(root,root/'state'); svc.install(svc.inspect(source),game,allow_research=True)
            disabled=svc.set_enabled('toggle.test', False); self.assertFalse(disabled['enabled']); self.assertFalse((game/'mods'/'toggle.test').exists()); self.assertTrue((game/'mods'/'toggle.test.disabled').is_dir())
            enabled=svc.set_enabled('toggle.test', True); self.assertTrue(enabled['enabled']); self.assertTrue((game/'mods'/'toggle.test').is_dir())

    def test_replacements_keep_timestamped_restore_points(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); source=root/'mod'; source.mkdir(); (source/'mod.json').write_text(json.dumps({'id':'repeat','loader':'EML','version':'1.0.0'})); payload=source/'mod.lua'; payload.write_text('return {}')
            game=root/'game'; game.mkdir(); (game/'Enshrouded.exe').write_text('fake'); svc=LocalModService(root,root/'state'); pkg=svc.inspect(source)
            svc.install(pkg,game,allow_research=True)
            payload.write_text('return {changed=true}')
            # Re-inspect the source and replace the owned deployment.
            svc.install(svc.inspect(source),game,replace=True,allow_research=True)
            backups=list((root/'state'/'backups'/'repeat').iterdir())
            self.assertGreaterEqual(len(backups), 2)
            self.assertEqual(len(svc.list_backups('repeat')), 2)

    def test_backup_catalog_handles_legacy_root_backup(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); legacy=root/'state'/'backups'/'legacy'; legacy.mkdir(parents=True); (legacy/'mod.json').write_text('{}')
            catalog=LocalModService(root,root/'state').list_backups('legacy')
            self.assertEqual(catalog[0]['id'], 'legacy')
            self.assertTrue(catalog[0]['legacy'])

    def test_restore_point_restores_previous_owned_payload(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); source=root/'mod'; source.mkdir(); (source/'mod.json').write_text(json.dumps({'id':'restore.test','loader':'EML','version':'1.0.0'})); payload=source/'mod.lua'; payload.write_text('return {version=1}')
            game=root/'game'; game.mkdir(); (game/'Enshrouded.exe').write_text('fake'); svc=LocalModService(root,root/'state'); pkg=svc.inspect(source)
            svc.install(pkg,game,allow_research=True)
            payload.write_text('return {version=2}')
            svc.install(svc.inspect(source),game,replace=True,allow_research=True)
            restore_id=svc.list_backups('restore.test')[0]['id']
            result=svc.restore_backup('restore.test',restore_id,game)
            self.assertEqual(result['files'],2)
            self.assertIn('version=1',(game/'mods'/'restore.test'/'mod.lua').read_text())

    def test_empty_restore_removes_owned_deployment_directory(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); source=root/'mod'; source.mkdir();
            (source/'mod.json').write_text(json.dumps({'id':'empty.restore','loader':'EML','version':'1.0.0'}))
            (source/'mod.lua').write_text('return {}')
            game=root/'game'; game.mkdir(); (game/'Enshrouded.exe').write_text('fake')
            svc=LocalModService(root,root/'state'); svc.install(svc.inspect(source),game,allow_research=True)
            restore_id=svc.list_backups('empty.restore')[0]['id']
            result=svc.restore_backup('empty.restore',restore_id,game)
            self.assertEqual(result['files'],0)
            self.assertFalse((game/'mods'/'empty.restore').exists())

    def test_restore_point_rejects_invalid_identifier(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); svc=LocalModService(root,root/'state')
            with self.assertRaisesRegex(Exception, 'ownership'):
                svc.restore_backup('missing','../../escape',root/'game')
    def test_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); zpath=root/'bad.zip'
            with zipfile.ZipFile(zpath,'w') as z: z.writestr('../escape.txt','bad')
            p=LocalModService(root,root/'state').inspect(zpath); self.assertEqual(p.status,'invalid or unsafe')
    def test_json_config_backup_and_write(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); path=root/'config.json'; path.write_text('{"speed": 1}')
            old,new=LocalModService(root,root/'state').configure_json(path,{'speed':2,'enabled':True})
            self.assertEqual(old['speed'],1); self.assertEqual(json.loads(path.read_text())['speed'],2); self.assertTrue((root/'state'/'config-backups'/'config.json.bak').is_file())

    def test_install_rejects_tampered_package_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); source=root/'mod'; source.mkdir();
            (source/'mod.json').write_text(json.dumps({'id':'integrity.test','loader':'EML'}), encoding='utf-8')
            payload=source/'mod.lua'; payload.write_text('return {}', encoding='utf-8')
            from core.package_service import PackageService
            PackageService().create_manifest(source, 'integrity.test', '1.0.0')
            payload.write_text('return {tampered=true}', encoding='utf-8')
            svc=LocalModService(root,root/'state'); pkg=svc.inspect(source); game=root/'game'; game.mkdir(); (game/'Enshrouded.exe').write_text('fake')
            with self.assertRaisesRegex(Exception, 'integrity verification failed'):
                svc.install(pkg, game)

    def test_preview_requires_declared_dependencies(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); source=root/'mod'; source.mkdir()
            (source/'mod.json').write_text(json.dumps({'id':'dependent.test','loader':'EML','dependencies':[{'id':'base.test','version':'>=1.2.0'}]}))
            (source/'mod.lua').write_text('return {}')
            svc=LocalModService(root,root/'state'); pkg=svc.inspect(source); game=root/'game'; game.mkdir(); (game/'Enshrouded.exe').write_text('fake')
            with self.assertRaisesRegex(Exception, 'Missing or incompatible dependencies'):
                svc.preview(pkg, game)
            base=game/'mods'/'base.test'; base.mkdir(parents=True)
            (base/'mod.json').write_text(json.dumps({'id':'base.test','version':'1.2.3'}))
            self.assertEqual(svc.preview(pkg, game)['identity'], 'dependent.test')

    def test_invalid_dependency_constraint_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); source=root/'mod'; source.mkdir()
            (source/'mod.json').write_text(json.dumps({'id':'bad-dependency','loader':'EML','dependencies':[{'id':'base','version':'latest'}]}))
            (source/'mod.lua').write_text('return {}')
            svc=LocalModService(root,root/'state'); pkg=svc.inspect(source); game=root/'game'; game.mkdir(); (game/'Enshrouded.exe').write_text('fake')
            with self.assertRaisesRegex(Exception, 'Unsupported dependency version constraint'):
                svc.preview(pkg, game)

if __name__=='__main__': unittest.main()
