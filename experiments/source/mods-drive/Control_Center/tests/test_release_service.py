import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from core.content_project import ContentProjectGenerator
from core.release_service import ReleaseService
from core.local_mods import LocalModService


class ReleaseServiceTests(unittest.TestCase):
    def setUp(self):
        self._running_patch = patch.object(LocalModService, '_running', return_value=False)
        self._running_patch.start()

    def tearDown(self):
        self._running_patch.stop()

    def test_build_release_creates_archive_and_metadata(self):
        base = Path(r"I:\My Drive\Enshrouded Mods\Control_Center")
        with tempfile.TemporaryDirectory() as td:
            project = ContentProjectGenerator(base, Path(td) / "ids.json").create(Path(td) / "project", "release_mod", "Release Project", "Tester")
            archive, metadata = ReleaseService().build_release(project, Path(td) / "releases", channel="beta", notes=["test release"])
            self.assertTrue(archive.is_file()); self.assertTrue(metadata.is_file()); self.assertIn('"channel": "beta"', metadata.read_text(encoding="utf-8"))

    def test_invalid_channel_is_rejected(self):
        base = Path(r"I:\My Drive\Enshrouded Mods\Control_Center")
        with tempfile.TemporaryDirectory() as td:
            project = ContentProjectGenerator(base, Path(td) / "ids.json").create(Path(td) / "project", "release_mod", "Release Project", "Tester")
            with self.assertRaises(Exception): ReleaseService().build_release(project, Path(td) / "releases", channel="unsupported")

    def test_release_verification_checks_hash_and_build(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(r"I:\My Drive\Enshrouded Mods\Control_Center")
            temp_root = Path(td)
            project = ContentProjectGenerator(base, temp_root / "ids.json").create(temp_root / "project", "release_mod", "Release Project", "Tester")
            archive, metadata = ReleaseService().build_release(project, temp_root / "releases", compatible_game_builds=[">=1076226"])
            verified = ReleaseService().verify_release(archive, metadata, "1077000")
            self.assertTrue(verified["verified"])
            archive.write_bytes(archive.read_bytes() + b"tampered")
            with self.assertRaises(Exception): ReleaseService().verify_release(archive, metadata)

    def test_release_verification_rejects_archive_without_required_manifests(self):
        with tempfile.TemporaryDirectory() as td:
            import zipfile
            archive = Path(td) / "bad.zip"; metadata = Path(td) / "bad.release.json"
            with zipfile.ZipFile(archive, "w") as package:
                package.writestr("mod.lua", "return {}")
            metadata.write_text(__import__("json").dumps({
                "schema": "control_center.release.v1", "archive": archive.name,
                "sha256": ReleaseService()._hash(archive), "compatible_game_builds": [],
            }), encoding="utf-8")
            with self.assertRaises(Exception): ReleaseService().verify_release(archive, metadata)

    def test_release_refuses_overwriting_existing_channel_artifacts(self):
        base = Path(r"I:\My Drive\Enshrouded Mods\Control_Center")
        with tempfile.TemporaryDirectory() as td:
            project = ContentProjectGenerator(base, Path(td) / "ids.json").create(Path(td) / "project", "release_mod", "Release Project", "Tester")
            output = Path(td) / "releases"
            ReleaseService().build_release(project, output, version="1.0.0")
            with self.assertRaisesRegex(Exception, "already exists"):
                ReleaseService().build_release(project, output, version="1.0.0")

    def test_release_verification_rejects_malformed_metadata_fields(self):
        with tempfile.TemporaryDirectory() as td:
            import json, zipfile
            archive = Path(td) / "mod-1.0.0.zip"
            with zipfile.ZipFile(archive, "w") as package:
                package.writestr("package.json", "{}")
                package.writestr("mod.json", "{}")
            metadata = Path(td) / "mod-1.0.0.release.json"
            record = {"schema": "control_center.release.v1", "id": "mod", "version": "1.0.0", "channel": "stable", "archive": archive.name, "sha256": ReleaseService()._hash(archive), "compatible_game_builds": [], "dependencies": [], "capabilities": []}
            for field, value in (("channel", "preview"), ("version", "1.0"), ("dependencies", "bad"), ("capabilities", [""])):
                invalid = dict(record); invalid[field] = value
                metadata.write_text(json.dumps(invalid), encoding="utf-8")
                with self.assertRaises(Exception): ReleaseService().verify_release(archive, metadata)

    def test_install_release_requires_verified_channel_and_installs_transactionally(self):
        base = Path(r"I:\My Drive\Enshrouded Mods\Control_Center")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); game = root / "game"; (game / "mods").mkdir(parents=True)
            project = ContentProjectGenerator(base, root / "ids.json").create(root / "project", "release_mod", "Release Project", "Tester")
            archive, metadata = ReleaseService().build_release(project, root / "releases", channel="beta")
            with self.assertRaises(Exception): ReleaseService().install_release(archive, metadata, game, allowed_channels={"stable"})
            result = ReleaseService().install_release(archive, metadata, game, allowed_channels={"beta"}, allow_research=True)
            self.assertTrue(result["installed"])
            self.assertTrue((Path(result["install_plan"]["target"]) / "mod.json").is_file())

    def test_catalog_releases_filters_channels_and_orders_versions(self):
        base = Path(r"I:\My Drive\Enshrouded Mods\Control_Center")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = ContentProjectGenerator(base, root / "ids.json").create(root / "project", "release_mod", "Release Project", "Tester")
            service = ReleaseService()
            service.build_release(project, root / "releases", version="1.0.0", channel="stable")
            service.build_release(project, root / "releases", version="2.0.0", channel="beta")
            catalog = service.catalog_releases(root / "releases", package_id="release_project", channels={"beta"})
            self.assertEqual([entry["version"] for entry in catalog], ["2.0.0"])
            self.assertTrue(catalog[0]["verified"])

    def test_install_release_blocks_downgrade_without_explicit_approval(self):
        base = Path(r"I:\My Drive\Enshrouded Mods\Control_Center")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); game = root / "game"; (game / "mods").mkdir(parents=True)
            service = ReleaseService()
            newer_project = ContentProjectGenerator(base, root / "newer-ids.json").create(root / "newer", "release_mod", "Release Project", "Tester", version="2.0.0")
            older_project = ContentProjectGenerator(base, root / "older-ids.json").create(root / "older", "release_mod", "Release Project", "Tester", version="1.0.0")
            newer, newer_meta = service.build_release(newer_project, root / "releases", channel="beta")
            older, older_meta = service.build_release(older_project, root / "releases", channel="beta")
            service.install_release(newer, newer_meta, game, allowed_channels={"beta"}, allow_research=True)
            with self.assertRaisesRegex(Exception, "downgrade"):
                service.install_release(older, older_meta, game, allowed_channels={"beta"}, allow_research=True)


if __name__ == "__main__":
    unittest.main()
