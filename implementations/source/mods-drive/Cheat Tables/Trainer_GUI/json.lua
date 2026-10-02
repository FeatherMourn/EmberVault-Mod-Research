-- Minimal dependency-free JSON codec for Lua 5.1+.
-- Copyright (c) 2026 Enshrouded Trainer project. MIT License.
-- This file is bundled for the bridge and does not execute input as code.
local M = { null = {} }
local function esc(s) return s:gsub('[%z\1-\31\\"]', function(c) local n=c:byte(); local map={['"']='\\"',['\\']='\\\\',['\b']='\\b',['\f']='\\f',['\n']='\\n',['\r']='\\r',['\t']='\\t'}; return map[c] or string.format('\\u%04x',n) end) end
local function encode(v, stack)
  local t=type(v)
  if v==M.null then return 'null' end
  if t=='nil' then return 'null' elseif t=='boolean' then return tostring(v) elseif t=='number' then if v~=v or v==math.huge or v==-math.huge then error('invalid JSON number') end; return string.format('%.14g',v)
  elseif t=='string' then return '"'..esc(v)..'"' elseif t~='table' then error('unsupported JSON type: '..t) end
  stack=stack or {}; if stack[v] then error('cannot encode cyclic table') end; stack[v]=true
  local max=0; local count=0; for k in pairs(v) do if type(k)=='number' and k>max and k%1==0 then max=k end; count=count+1 end
  local a={}; if count==max then for i=1,max do a[#a+1]=encode(v[i],stack) end; stack[v]=nil; return '['..table.concat(a,',')..']' end
  for k,val in pairs(v) do if type(k)~='string' then error('JSON object keys must be strings') end; a[#a+1]=encode(k,stack)..':'..encode(val,stack) end; stack[v]=nil; return '{'..table.concat(a,',')..'}'
end
M.encode=encode
local function decode(s)
  local i=1; local function ws() while s:sub(i,i):match('%s') do i=i+1 end end
  local parse
  local function str()
    i=i+1; local out={}
    while i<=#s do local c=s:sub(i,i); if c=='"' then i=i+1; return table.concat(out) end; if c=='\\' then i=i+1; local e=s:sub(i,i); local m={['"']='"',['\\']='\\',['/']='/',b='\b',f='\f',n='\n',r='\r',t='\t'}; if m[e] then out[#out+1]=m[e]; i=i+1 elseif e=='u' then local h=s:sub(i+1,i+4); if not h:match('^%x%x%x%x$') then error('invalid unicode escape') end; local cp=tonumber(h,16); if cp<128 then out[#out+1]=string.char(cp) elseif cp<2048 then out[#out+1]=string.char(192+math.floor(cp/64),128+cp%64) else out[#out+1]=string.char(224+math.floor(cp/4096),128+math.floor(cp/64)%64,128+cp%64) end; i=i+5 else error('invalid escape') end else out[#out+1]=c; i=i+1 end end; error('unterminated string')
  end
  local function num() local st=i; i=i+1; while s:sub(i,i):match('[%d%.eE%+%-]') do i=i+1 end; local n=tonumber(s:sub(st,i-1)); if not n then error('invalid number') end; return n end
  function parse() ws(); local c=s:sub(i,i); if c=='"' then return str() elseif c=='-' or c:match('%d') then return num() elseif s:sub(i,i+3)=='true' then i=i+4; return true elseif s:sub(i,i+4)=='false' then i=i+5; return false elseif s:sub(i,i+3)=='null' then i=i+4; return M.null elseif c=='[' then i=i+1; local a={}; ws(); if s:sub(i,i)==']' then i=i+1; return a end; while true do a[#a+1]=parse(); ws(); c=s:sub(i,i); if c==']' then i=i+1; return a elseif c~=',' then error('expected array separator') end; i=i+1 end elseif c=='{' then i=i+1; local o={}; ws(); if s:sub(i,i)=='}' then i=i+1; return o end; while true do ws(); if s:sub(i,i)~='"' then error('expected object key') end; local k=str(); ws(); if s:sub(i,i)~=':' then error('expected colon') end; i=i+1; o[k]=parse(); ws(); c=s:sub(i,i); if c=='}' then i=i+1; return o elseif c~=',' then error('expected object separator') end; i=i+1 end else error('unexpected JSON token at '..i) end end
  local v=parse(); ws(); if i<=#s then error('trailing JSON data') end; return v
end
M.decode=decode
return M
