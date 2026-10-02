-- Enshrouded Trainer local bridge. Run inside Cheat Engine after loading the
-- original table and attaching to Enshrouded. File-only, session-bound API.
-- It never executes Lua received from the GUI and never accepts raw addresses.
local bridgeRoot = os.getenv('LOCALAPPDATA') .. '\\EnshroudedTrainer\\bridge'
local requestFile = bridgeRoot .. '\\request.json'
local responseFile = bridgeRoot .. '\\response.json'
local timer
local source = debug.getinfo(1, 'S').source
local scriptPath = source and source:match('^@(.+)$')
if not scriptPath then error('Run cheat_engine_bridge.lua as a file from Trainer_GUI; pasted Lua has no reliable module directory.') end
local scriptDir = scriptPath:match('^(.+)[/\\][^/\\]+$')
if not scriptDir then error('Could not determine bridge script directory.') end
package.path = scriptDir .. '\\?.lua;' .. scriptDir .. '/?.lua;' .. package.path
local jsonLib = require('json')

local function writeAtomic(path, value)
  local temp = path .. '.tmp.' .. tostring(os.clock()):gsub('%.','')
  local f = assert(io.open(temp, 'wb')); f:write(jsonLib.encode(value)); f:close(); os.remove(path); os.rename(temp, path)
end
local function reply(req, ok, payload, err)
  writeAtomic(responseFile, {protocol=1, session=req.session, request_id=req.request_id, ok=ok, payload=payload or {}, error=err or ''})
end
local function records()
  local out = {}
  local list = getAddressList()
  for i=0,list.Count-1 do
    local r=list.getMemoryRecord(i)
    out[tostring(r.ID)] = {id=r.ID, description=r.Description, type=r.Type, address=r.Address or '', group=r.IsGroupHeader, active=r.Active}
  end
  return out
end
local function attachedProcess()
  return getOpenedProcessID and getOpenedProcessID() or 0
end
local function utf8Bytes(value)
  local out={}; for i=1,#value do out[#out+1]=string.format('%02X',string.byte(value,i)) end; return table.concat(out,' ')
end
local function handle(req)
  if type(req) ~= 'table' or req.protocol ~= 1 or type(req.session) ~= 'string' or type(req.request_id) ~= 'string' then return end
  if req.command == 'hello' then
    local actual=records(); local expected=req.payload and req.payload.expected_records or {}; local mismatch=''
    for _,item in ipairs(expected) do
      local got=actual[tostring(item.id)]
      if not got or got.description ~= item.description then
        mismatch='table record mismatch at ID '..tostring(item.id)
        if got then mismatch=mismatch..' expected_bytes='..utf8Bytes(item.description)..' actual_bytes='..utf8Bytes(got.description) end
        break
      end
    end
    if mismatch ~= '' or #expected ~= 0 and #expected ~= (function() local n=0; for _ in pairs(actual) do n=n+1 end; return n end)() then return reply(req,false,{},mismatch ~= '' and mismatch or 'table record count mismatch') end
    return reply(req, true, {bridge_version='1.0', process_id=attachedProcess(), table_verified=true, records=actual})
  end
  if req.command == 'enumerate' then return reply(req, true, {process_id=attachedProcess(), records=records()}) end
  local id = tonumber(req.payload and req.payload.id); local r = id and getMemoryRecordByID(id)
  if not r then return reply(req, false, {}, 'record not found: '..tostring(id)) end
  if req.command == 'state' then return reply(req, true, {id=id, active=r.Active, value=r.Value, address=r.Address or '', type=r.Type}) end
  if req.command == 'activate' or req.command == 'deactivate' then
    if r.IsGroupHeader or r.Type ~= vtAutoAssembler then return reply(req, false, {}, 'record is not an approved Auto Assembler script') end
    r.Active = req.command == 'activate'; return reply(req, true, {id=id, active=r.Active})
  end
  if req.command == 'set_value' then
    if r.IsGroupHeader or r.Type == vtAutoAssembler then return reply(req, false, {}, 'record is not an editable value record') end
    local value=req.payload.value; if type(value) ~= 'number' or value ~= value or value == math.huge or value == -math.huge then return reply(req,false,{},'invalid numeric value') end
    r.Value=tostring(value); return reply(req,true,{id=id,value=r.Value})
  end
  if req.command == 'shutdown' then if timer then timer.destroy(); timer=nil end; return reply(req,true,{stopped=true}) end
  reply(req, false, {}, 'unsupported command')
end
timer=createTimer(nil); timer.Interval=100; timer.OnTimer=function()
  local f=io.open(requestFile,'rb'); if not f then return end; local raw=f:read('*a'); f:close(); os.remove(requestFile)
  if #raw > 262144 then return end
  local ok,req=pcall(jsonLib.decode,raw); if ok then pcall(handle,req) end
end
showMessage('Enshrouded Trainer bridge started. Session files: '..bridgeRoot)
