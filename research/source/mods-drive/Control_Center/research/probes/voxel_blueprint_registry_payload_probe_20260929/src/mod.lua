local P='[CC-BLUEPRINT-PAYLOAD:voxel_blueprint_registry_payload_probe_20260929] '
local G='3064d35d-7342-40ca-bdc9-aad58f83bf45'
local T='keen::VoxelBlueprintItemRegistryResource'
local function l(k,v) print(P..k..'|'..tostring(v or '')) end
local function safe(fn) return pcall(fn) end
l('BEGIN','build=1076226|api='..tostring(game.api_version)..'|read_only=true|bounded=true')
if tostring(game.api_version)~='1.3' then l('RESULT','api_mismatch'); return {} end
local ok,r=pcall(function() return game.assets.get_resource(G,T,0) end)
l('LOOKUP','ok='..tostring(ok)..'|found='..tostring(r~=nil))
if not ok or not r then l('RESULT','resource_lookup_failed'); return {} end
local dok,d=pcall(function() return r.data end)
l('PAYLOAD','ok='..tostring(dok)..'|type='..type(d))
if not dok or (type(d)~='table' and type(d)~='userdata') then l('RESULT','payload_read_failed'); return {} end
local bok,items=pcall(function() return d.blueprintItems end)
l('FIELD|blueprintItems','ok='..tostring(bok)..'|type='..type(items))
if not bok or (type(items)~='table' and type(items)~='userdata') then l('RESULT','blueprint_items_unavailable'); return {} end
local lok,count=pcall(function() return #items end)
l('FIELD|blueprintItems_length','ok='..tostring(lok)..'|value='..tostring(count))
if not lok then l('RESULT','blueprint_items_length_unavailable'); return {} end
local first=nil; local last=nil
local fok,fv=pcall(function() return items[1] end)
local eok,ev=pcall(function() return items[count] end)
if fok then first={index=1,item=fv} end
if eok and count>0 then last={index=count,item=ev} end
l('FIELD|blueprintItems_count','ok=true|value='..tostring(count))
local function describe(label,row)
  if not row then return end
  local iok,iv=pcall(function() return row.item end)
  l(label..'_item','ok='..tostring(iok)..'|value='..tostring(iv))
  local dok2,dv=pcall(function() return row.dimensions end)
  l(label..'_dimensions','ok='..tostring(dok2)..'|value='..tostring(dv))
end
describe('FIRST',first); describe('LAST',last)
l('BOUNDARY','created=false|registered=false|mutated=false|attached=false|world=false|save=false')
l('RESULT','blueprint_registry_payload_read_complete'); l('END','build=1076226'); return {}
