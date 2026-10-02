local P='[CC-WATER-DISPLACING:water_displacing_single_donor_probe_36234b22_1076226] '
local G='36234b22-85f2-4001-ac56-002b379d0d88'
local T='keen::WaterDisplacingResource'
local function l(k,v) print(P..k..'|'..tostring(v or '')) end
l('BEGIN','build=1076226|api='..tostring(game.api_version)..'|read_only=true|bounded=true')
if tostring(game.api_version)~='1.3' then l('RESULT','api_mismatch'); return {} end
local ok,r=pcall(function() return game.assets.get_resource(G,T,0) end); l('LOOKUP','ok='..tostring(ok)..'|found='..tostring(r~=nil))
if not ok or not r then l('RESULT','resource_lookup_failed'); return {} end
local dok,d=pcall(function() return r.data end); l('PAYLOAD','ok='..tostring(dok)..'|type='..type(d))
if not dok or not d then l('RESULT','payload_read_failed'); return {} end
local a=d.displacingDataHashes; l('FIELD|hash_count','ok=true|value='..tostring(#a)); l('FIELD|first_size','ok=true|value='..tostring(a[1].size)); l('FIELD|first_hash0','ok=true|value='..tostring(a[1].hash0)); l('FIELD|last_hash2','ok=true|value='..tostring(a[#a].hash2))
l('BOUNDARY','hash_content=false|created=false|registered=false|mutated=false|attached=false|world=false|save=false'); l('RESULT','water_displacing_payload_read_complete'); l('END','build=1076226'); return {}
