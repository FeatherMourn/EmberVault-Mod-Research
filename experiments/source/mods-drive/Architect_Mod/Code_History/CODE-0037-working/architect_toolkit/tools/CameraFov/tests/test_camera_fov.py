import json,unittest
from pathlib import Path
from tools.CameraFov.discover_camera_fov import classify_candidate,readback_gate,backend_classification
ROOT=Path(__file__).resolve().parents[3]
class CameraFovTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.state=json.loads((ROOT/'bridge/camera_fov_state.json').read_text());cls.registry=json.loads((ROOT/'runtime/admin_action_registry.json').read_text())
 def test_candidate_classification_and_unrelated_float(self):
  self.assertEqual(classify_candidate('keen::ecs::ClientCamera','fovY'),'RUNTIME_STATE')
  self.assertEqual(classify_candidate('keen::Fsr3UpscalerConstants','fTanHalfFOV'),'UNKNOWN')
 def test_build_and_static_defaults(self):
  self.assertTrue(self.state['build']['supported']);self.assertEqual(self.state['build']['revision'],1076226)
  values={x['candidateId']:x['defaultValue'] for x in self.state['candidates']};self.assertEqual(values['reflection-7028-fov'],65.0);self.assertEqual(values['reflection-1972-fov'],50.0)
 def test_no_writable_target_and_readback_gate(self):
  self.assertFalse(self.state['namedReadOnlyTargetRegistered']);self.assertEqual(self.state['registeredTargetCounts'],{'total':0,'readable':0,'writable':0})
  self.assertFalse(readback_gate(True,True,False));self.assertTrue(readback_gate(True,True,True))
 def test_backend_classification(self):
  self.assertEqual(backend_classification(True,False,False),'RESOURCE');self.assertEqual(backend_classification(False,True,False),'NATIVE_OBJECT');self.assertEqual(backend_classification(False,False,True),'NATIVE_MEMORY');self.assertEqual(backend_classification(),'NONE')
 def test_camera_modes_are_not_collapsed(self):
  self.assertTrue(self.state['cameraModes']['separated']);self.assertIsNone(self.state['cameraModes']['normalGameplay']);self.assertIsNone(self.state['cameraModes']['aimingZoom'])
 def test_no_mutation_command_enabled(self):
  explicit={x['commandId']:x for x in self.registry['actions']};self.assertNotIn('camera.fov.set',explicit)
  family=next(f for f in self.registry['actionFamilies'] if 'camera.fov' in f['commandIds']);self.assertNotEqual(family['status'],'PROVEN_BUILD_1076226');self.assertEqual(family['backend'],'RESOURCE')
 def test_router_and_shutdown_compatibility(self):
  runtime=(ROOT/'runtime/ArchitectRuntime.ps1').read_text();native=(ROOT/'runtime/native/source/ArchitectNativeRuntime.c').read_text();self.assertIn('Invoke-ArchitectBackendRoute',runtime);self.assertIn('Architect Native Runtime unloaded cleanly.',native)
 def test_conclusion(self):self.assertEqual(self.state['discoveryStatus'],'FOV_STATIC_CANDIDATES_ONLY');self.assertEqual(self.state['mutationReadiness'],'MUTATION_BLOCKED')
if __name__=='__main__':unittest.main()
