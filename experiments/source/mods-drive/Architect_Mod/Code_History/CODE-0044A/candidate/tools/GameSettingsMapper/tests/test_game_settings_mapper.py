import json, unittest
from pathlib import Path
from tools.GameSettingsMapper.adapter_model import VALID_FIELDS, mutation_result, validate_request

ROOT=Path(__file__).resolve().parents[3]
NATIVE=(ROOT/'runtime/native/source/ArchitectNativeRuntime.c').read_text(encoding='utf-8')
OBSERVER=(ROOT/'runtime/native/source/GameSettingsObserver.c').read_text(encoding='utf-8')
HEADER=(ROOT/'runtime/native/source/GameSettingsObserver.h').read_text(encoding='utf-8')
REGISTRY=json.loads((ROOT/'runtime/admin_action_registry.json').read_text(encoding='utf-8'))

class GameSettingsMapperTests(unittest.TestCase):
    def test_build_gate_is_exact_and_canonical(self):
        start=NATIVE.index('game_settings_observer_initialize('); gate=NATIVE[start:start+350]
        for value in ('g_buildFingerprintValidated','g_buildingPlaceSignatureMatches == 1','SEMANTIC_SUPPORTED_PE_TIMESTAMP','SEMANTIC_SUPPORTED_IMAGE_SIZE'): self.assertIn(value,gate)
    def test_action_schema_and_observe_only_commands(self):
        ids={a['commandId']:a for a in REGISTRY['actions']}
        for command in ('gamesettings.inspect','gamesettings.capture.begin','gamesettings.capture.end'):
            self.assertTrue(ids[command]['enabled']); self.assertEqual(ids[command]['risk'],'read_only')
        family=next(f for f in REGISTRY['actionFamilies'] if f['adapter']=='GameSettingsAdapter')
        self.assertEqual(family['status'],'PLANNED')
    def test_field_and_value_validation_fails_without_proven_bounds(self):
        self.assertEqual(validate_request('notASetting',1)['state'],'UNSUPPORTED_FIELD')
        self.assertEqual(validate_request('factoryProductionSpeedFactor',1.0)['state'],'BOUNDS_UNPROVEN')
        self.assertEqual(validate_request('factoryProductionSpeedFactor',3.0,bounds=(0.5,2.0))['state'],'OUT_OF_BOUNDS')
    def test_no_completion_without_dispatch_readback_and_restore(self):
        self.assertEqual(mutation_result()['state'],'DISPATCH_UNPROVEN')
        self.assertEqual(mutation_result(dispatch_proven=True)['state'],'READBACK_FAILED')
        self.assertEqual(mutation_result(dispatch_proven=True,readback_success=True)['state'],'RESTORE_UNVERIFIED')
        self.assertEqual(mutation_result(dispatch_proven=True,readback_success=True,restore_success=True)['state'],'completed')
    def test_version_monotonicity_is_not_guessed(self):
        static=(ROOT/'bridge/game_settings_static_map.json')
        if static.exists(): self.assertEqual(json.loads(static.read_text())['runtime']['versionMonotonicity'],'UNSOLVED')
    def test_capture_is_bounded_and_zero_probe(self):
        self.assertIn('GAME_SETTINGS_CAPTURE_CAPACITY 64UL',HEADER); self.assertIn('GAME_SETTINGS_CAPTURE_BYTE_LIMIT (256UL * 1024UL)',HEADER)
        self.assertIn('probeInstalled\\\": false',NATIVE); self.assertNotIn('VirtualProtect',OBSERVER)
    def test_game_settings_are_separate_from_resource_adapters(self):
        game=next(f for f in REGISTRY['actionFamilies'] if f['adapter']=='GameSettingsAdapter')
        self.assertFalse(any(x.startswith(('glider.','world.fog','crafting.')) for x in game['commandIds']))
    def test_no_mutation_command_is_registered(self):
        ids={a['commandId'] for a in REGISTRY['actions']}
        self.assertNotIn('gamesettings.set',ids); self.assertNotIn('gamesettings.restore',ids); self.assertNotIn('gamesettings.restore_all',ids)

if __name__=='__main__': unittest.main()
