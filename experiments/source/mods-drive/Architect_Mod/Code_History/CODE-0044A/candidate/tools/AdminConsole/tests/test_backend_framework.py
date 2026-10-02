import json,subprocess,unittest
from pathlib import Path
from tools.AdminConsole.native_memory_model import NativeMemoryAdapter,Target
ROOT=Path(__file__).resolve().parents[3]

class BackendFrameworkTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.catalog=json.loads((ROOT/'runtime/admin_action_registry.json').read_text())
  cls.caps=json.loads((ROOT/'bridge/backend_capabilities.json').read_text())
 def test_valid_backend_enum_and_registry_compatibility(self):
  valid={'LUA_API','VANILLA_ACTION','RESOURCE','NATIVE_OBJECT','NATIVE_MEMORY','NATIVE_HOOK','NONE'}
  self.assertTrue(all(a['backend'] in valid for a in self.catalog['actions']))
  self.assertTrue(all(f['backend'] in valid for f in self.catalog['actionFamilies']))
 def test_invalid_backend_rejection_routing_and_no_fallback(self):
  module=str(ROOT/'runtime/BackendRouter.psm1').replace("'","''")
  script=f"Import-Module '{module}' -Force;$r=New-ArchitectBackendRouter;$a=[pscustomobject]@{{commandId='x';backend='BAD';enabled=$true;evidenceStatus='PROVEN_BUILD_1076226';failureReason='x'}};(Invoke-ArchitectBackendRoute -Action $a -Router $r)|ConvertTo-Json -Compress"
  out=subprocess.run(['powershell','-NoProfile','-Command',script],capture_output=True,text=True);self.assertEqual(out.returncode,0,out.stderr);self.assertEqual(json.loads(out.stdout)['state'],'INVALID_BACKEND')
  text=(ROOT/'runtime/BackendRouter.psm1').read_text();self.assertIn('no fallback attempted',text)
 def test_backend_router_successful_dispatch(self):
  module=str(ROOT/'runtime/BackendRouter.psm1').replace("'","''")
  script=f"Import-Module '{module}' -Force;$r=New-ArchitectBackendRouter;$r.RESOURCE['x']={{param($p) [ordered]@{{success=$true;state='COMPLETED';value=$p.value}}}};$a=[pscustomobject]@{{commandId='x';backend='RESOURCE';enabled=$true;evidenceStatus='PROVEN_BUILD_1076226';failureReason='x'}};(Invoke-ArchitectBackendRoute -Action $a -Router $r -Parameters @{{value=7}})|ConvertTo-Json -Compress"
  out=subprocess.run(['powershell','-NoProfile','-Command',script],capture_output=True,text=True);self.assertEqual(out.returncode,0,out.stderr);value=json.loads(out.stdout);self.assertTrue(value['success']);self.assertEqual(value['value'],7)
 def test_native_object_is_separate_named_adapter(self):
  text=(ROOT/'runtime/NativeObjectAdapter.psm1').read_text()
  self.assertIn('Register-NativeObjectCapability',text);self.assertIn('OBJECT_UNRESOLVED',text)
  self.assertNotIn('WriteProcessMemory',text);self.assertNotIn('address',text.lower())
 def target(self,**kw):
  data=dict(target_id='known',build=1076226,resolved=True,readable=True,writable=True,evidence=True,minimum=0,maximum=500,readback=True,revert=True);data.update(kw);return Target(**data)
 def test_memory_rejections(self):
  a=NativeMemoryAdapter(build=1);a.register(self.target());self.assertEqual(a.read('known',lambda _:1)['state'],'BUILD_UNSUPPORTED')
  a=NativeMemoryAdapter();a.register(self.target(resolved=False));self.assertEqual(a.read('known',lambda _:1)['state'],'TARGET_UNRESOLVED')
  a=NativeMemoryAdapter();a.register(self.target());self.assertEqual(a.read('known',lambda _:(_ for _ in ()).throw(MemoryError()))['state'],'BAD_PAGE');self.assertEqual(a.read('known',lambda _:None)['state'],'BAD_POINTER');self.assertEqual(a.read('known',lambda _:501)['state'],'OUT_OF_RANGE')
 def test_mutation_readback_revert_contract(self):
  box={'v':10};reader=lambda _:box['v'];writer=lambda _,v:box.__setitem__('v',v)
  a=NativeMemoryAdapter();a.register(self.target());self.assertEqual(a.write('known',20,reader,writer)['state'],'MUTATION_DISABLED')
  a.mutation_enabled=True;bad=lambda _,v:None;self.assertEqual(a.write('known',20,reader,bad)['state'],'FAILED_READBACK')
  self.assertEqual(a.write('known',20,reader,writer)['state'],'COMPLETED');self.assertEqual(a.revert('known',reader,writer)['state'],'COMPLETED');self.assertEqual(box['v'],10)
 def test_no_arbitrary_address_surfaces_and_clean_shutdown(self):
  ids=[a['commandId'] for a in self.catalog['actions']]+sum((f['commandIds'] for f in self.catalog['actionFamilies']),[])
  self.assertFalse(any('memory.read' in x or 'memory.write' in x for x in ids))
  lua=(ROOT/'src/mod.lua').read_text();self.assertNotIn('WriteProcessMemory',lua);self.assertNotIn('memory.write',lua)
  native=(ROOT/'runtime/native/source/ArchitectNativeRuntime.c').read_text();self.assertIn('Architect Native Runtime unloaded cleanly.',native)
 def test_diagnostics_and_no_proof_overclaim(self):
  self.assertEqual(self.caps['frameworkStatus'],'FRAMEWORK_IMPLEMENTED');self.assertEqual(self.caps['runtimeReadStatus'],'NO_SAFE_MEMORY_READ_TARGET_AVAILABLE');self.assertEqual(self.caps['runtimeMutationStatus'],'NOT_PROVEN');self.assertEqual(self.caps['nativeMemory']['registeredTargets'],0);self.assertFalse(self.caps['nativeMemory']['mutationMasterGate'])

if __name__=='__main__':unittest.main()
