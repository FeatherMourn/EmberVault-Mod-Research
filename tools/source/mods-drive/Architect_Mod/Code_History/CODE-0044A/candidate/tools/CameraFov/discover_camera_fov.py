"""CODE-0032 deterministic offline Camera FOV evidence map."""
from __future__ import annotations
import hashlib,json,sqlite3,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];TYPES=ROOT.parents[1]/'.cache/types.json';EXE=ROOT.parents[1]/'enshrouded.exe';DB=ROOT/'data/architect_game_data_1076226.sqlite';OUT=ROOT/'bridge/camera_fov_state.json'
EXPECTED='AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781'
SPECS=(
 (7028,'keen::g38_options::common::user::GraphicsSettings','fov',0,'STATIC_CONFIG','user graphics option; live settings owner and propagation are unresolved'),
 (1972,'keen::FOVModifierSettings','fov',0,'CAMERA_MODE_PROFILE','nested in camera mode configuration; not independently the active camera'),
 (1990,'keen::CameraModifierConfig','fovSettings',704,'CAMERA_MODE_PROFILE','configuration aggregate; active mode and loaded instance unresolved'),
 (1992,'keen::CameraSimpleConfig','fovSettings',184,'CAMERA_MODE_PROFILE','simple camera profile; active mode unresolved'),
 (1994,'keen::CameraStatesManager','cameraStates',0,'CAMERA_MODE_PROFILE','45-state manager referenced by root/shared resources; local KFC instances unavailable'),
 (2759,'keen::ecs::ClientCamera','fovY',44,'RUNTIME_STATE','embedded in ClientPlayerInputData at +0x20, but no live ECS instance/owner resolver'),
 (1609,'keen::three_c::DebugMessageCamera','fov',1864,'RUNTIME_STATE','diagnostic-shaped effective value; producer and accessible live instance unresolved'),
 (3920,'keen::SceneCamera','fovY',96,'CAMERA_MODE_PROFILE','scene/cinematic camera candidate, not normal gameplay proof'),
 (4379,'keen::FbUiCharacterView','fov',24,'UI_ONLY','character-view UI camera, not gameplay'),
 (5268,'keen::Fsr3UpscalerConstants','fTanHalfFOV',108,'UNKNOWN','derived render constant, not an owner'),
)
def classify_candidate(type_name,field_name):
 if type_name=='keen::g38_options::common::user::GraphicsSettings' and field_name=='fov':return 'STATIC_CONFIG'
 if type_name in {'keen::FOVModifierSettings','keen::CameraModifierConfig','keen::CameraSimpleConfig','keen::CameraStatesManager','keen::SceneCamera'}:return 'CAMERA_MODE_PROFILE'
 if type_name in {'keen::ecs::ClientCamera','keen::three_c::DebugMessageCamera'}:return 'RUNTIME_STATE'
 if type_name.startswith('keen::FbUi'):return 'UI_ONLY'
 return 'UNKNOWN'
def readback_gate(owner_proven,consumer_proven,independent_readback):return all((owner_proven,consumer_proven,independent_readback))
def backend_classification(resource_owner=False,object_owner=False,memory_target=False):
 return 'RESOURCE' if resource_owner else ('NATIVE_OBJECT' if object_owner else ('NATIVE_MEMORY' if memory_target else 'NONE'))
def f32_default(t,off):
 b=bytes(t.get('defaultValue',[]));return struct.unpack_from('<f',b,off)[0] if len(b)>=off+4 else None
def build():
 sha=hashlib.sha256(EXE.read_bytes()).hexdigest().upper()
 if sha!=EXPECTED:raise RuntimeError(f'unsupported executable {sha}')
 types=json.loads(TYPES.read_text(encoding='utf-8'))['types'];candidates=[]
 for index,qname,field,offset,role,contra in SPECS:
  t=types[index];f=t.get('structFields',{}).get(field)
  if t.get('qualifiedName')!=qname or not f or int(f['dataOffset'])!=offset:raise RuntimeError(f'reflection mismatch {qname}.{field}')
  if classify_candidate(qname,field)!=role:raise RuntimeError(f'classification mismatch {qname}.{field}')
  attrs=f.get('attributes',{});candidates.append({'candidateId':f'reflection-{index}-{field}','reflectionIndex':index,'typeName':qname,'fieldName':field,'fieldOffset':f'0x{offset:X}','valueType':types[f['type']].get('qualifiedName'),'defaultValue':f32_default(t,offset),'minimum':attrs.get('min',{}).get('value'),'maximum':attrs.get('max',{}).get('value'),'candidateRole':role,'evidenceSource':'.cache/types.json build 1076226','evidenceStatus':'PROVEN_STATIC_BUILD_1076226','contradictions':[contra]})
 con=sqlite3.connect(DB);camera_rows=con.execute('select count(*) from camera_states').fetchone()[0];coverage=con.execute("select status,row_count,limitation from coverage where family='camera_states'").fetchone();con.close()
 return {'schema':'architect.camera_fov_state.v1','build':{'revision':1076226,'sha256':sha,'supported':True},'discoveryStatus':'FOV_STATIC_CANDIDATES_ONLY','mutationReadiness':'MUTATION_BLOCKED','candidates':candidates,'resourceEvidence':{'cameraStateRows':camera_rows,'coverage':{'status':coverage[0],'rowCount':coverage[1],'limitation':coverage[2]} if coverage else None,'gameAssetsTypeIdentityAvailable':True,'loadedInstanceObserved':False,'startupOrSessionLive':'UNKNOWN'},'owner':{'classification':'UNRESOLVED','candidate':'GraphicsSettings -> CameraStatesManager/profile -> ClientCamera.fovY','proven':False,'reason':'Reflection establishes configuration and runtime-state shapes but not the loaded instances or copy/derivation chain.'},'consumers':[],'refresh':{'classification':'UNKNOWN','evidence':'No camera update/resource-change consumer with preserved FOV provenance was recovered.'},'readback':{'classification':'UNRESOLVED','bestCandidate':'keen::ecs::ClientCamera.fovY +0x2C','independent':False,'currentValue':None,'reason':'Runtime-state layout is proven, but live component ownership and an independently accessible getter are not.'},'cameraModes':{'separated':True,'knownStaticModel':'CameraStatesManager contains 45 CameraStateConfig records with CameraId and per-profile FOV settings.','activeMode':None,'normalGameplay':None,'aimingZoom':None,'build':None,'gliding':None,'cinematic':'SceneCamera is a separate candidate; applicability unresolved.'},'luaResourceAccess':{'identifyType':True,'enumerateAttemptArchitecturallySupported':True,'localCameraInstancesAvailable':False,'inspectLiveField':False,'reloadOrRefresh':'UNRESOLVED','mutation':False},'backendClassification':{'preferred':'RESOURCE','current':'NONE','alternativeCandidates':['NATIVE_OBJECT'],'nativeMemoryEligible':False},'namedReadOnlyTargetRegistered':False,'registeredTargetCounts':{'total':0,'readable':0,'writable':0},'mutationEligible':False,'failureReason':'No proven loaded owner, camera consumer/refresh path, or independent effective-FOV readback.','runtimeChanged':False}
def main():OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(build(),indent=2,sort_keys=True)+'\n',encoding='utf-8');print(f'wrote {OUT} conclusion=FOV_STATIC_CANDIDATES_ONLY')
if __name__=='__main__':main()
