"""Offline evidence inventory for Architect's EML/Lua surface."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SRC=ROOT/"src/mod.lua";OUT=ROOT/"bridge/backend_capabilities.json"
def build():
 text=SRC.read_text(encoding="utf-8")
 def used(pattern):return bool(re.search(pattern,text))
 caps=[
  ("Lua runtime/version","UNRESOLVED","No runtime identity API or captured version exists."),
  ("require","AVAILABLE","Architect uses protected require for Config.Architect_Blueprint_Config."),
  ("package","UNRESOLVED","require does not independently prove package table exposure."),
  ("package.loadlib","UNRESOLVED","No supported call or runtime capture exists."),
  ("ffi","UNRESOLVED","No LuaJIT FFI evidence exists."),
  ("LuaJIT","UNRESOLVED","No runtime identity capture exists."),
  ("debug","UNRESOLVED","No use or captured availability exists."),
  ("io","AVAILABLE_RESTRICTED","Host-provided io.export is repeatedly used; arbitrary io functions are not established."),
  ("os","UNRESOLVED","No use or captured availability exists."),
  ("filesystem","AVAILABLE_RESTRICTED","io.export writes only through the host export surface."),
  ("environment variables","UNRESOLVED","No environment API evidence exists."),
  ("native module loading","UNRESOLVED","No supported DLL/native module loading path is evidenced."),
  ("DLL/export calls","UNRESOLVED","No host binding for calling DLL exports is evidenced."),
  ("host native bindings","AVAILABLE_RESTRICTED","game.assets resource get/create APIs are used."),
  ("EML resource APIs","AVAILABLE_RESTRICTED","get_resources_by_type, get_resource and create_resource are evidenced."),
  ("callbacks/events","UNRESOLVED","No runtime callback registration is present."),
  ("console/log","AVAILABLE","print is used."),
  ("reload behavior","AVAILABLE_RESTRICTED","Repository evidence requires startup/full restart for config application."),
 ]
 assert used(r'require\("Config\.Architect_Blueprint_Config"\)') and used(r'io\.export\(') and used(r'game\.assets\.get_resources_by_type')
 return {"schema":"architect.backend_capabilities.v1","generatedFrom":"offline_source_evidence","frameworkStatus":"FRAMEWORK_IMPLEMENTED","runtimeReadStatus":"NO_SAFE_MEMORY_READ_TARGET_AVAILABLE","runtimeMutationStatus":"NOT_PROVEN","luaEml":{"capabilities":[{"capability":a,"status":s,"evidence":e} for a,s,e in caps],"nativeModuleSupport":"UNRESOLVED","architectControlPath":{"decision":"EXISTING_COMMAND_BRIDGE","status":"AVAILABLE","reason":"No direct Lua-to-native export facility is proven; named commands remain centralized and fail closed."}},"adapters":{"LUA_API":"PARTIAL","VANILLA_ACTION":"PARTIAL","RESOURCE":"AVAILABLE_RESTRICTED","NATIVE_OBJECT":"UNSOLVED","NATIVE_MEMORY":"PARTIAL","NATIVE_HOOK":"PARTIAL","NONE":"UNAVAILABLE"},"nativeMemory":{"buildSupported":True,"mutationMasterGate":False,"registeredTargets":0,"readableTargets":0,"writableTargets":0,"lastBackendAction":None,"lastFailure":"NO_SAFE_MEMORY_READ_TARGET_AVAILABLE","arbitraryAddressApi":False,"contract":["resolve registered target","read and validate original","validate request","single scoped write","immediate readback","FAILED_READBACK on mismatch","retain original session value for supported revert"]},"revertModel":{"ORIGINAL_SESSION_VALUE":"captured immediately before first successful scoped mutation","KNOWN_VANILLA_DEFAULT":"only supplied by independent evidence; never inferred from session value"},"entityInspector":"FAIL_CLOSED","gameSettings":"UNSOLVED_BACKEND_CANDIDATES_ONLY"}
def main():OUT.write_text(json.dumps(build(),indent=2,sort_keys=True)+"\n",encoding="utf-8");print(f"wrote {OUT}")
if __name__=="__main__":main()
