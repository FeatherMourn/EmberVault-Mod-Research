"""Deterministic model of the CODE-0030 named-target safety contract."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Target:
 target_id:str;build:int;resolved:bool;readable:bool;writable:bool;evidence:bool;minimum:float;maximum:float;readback:bool;revert:bool

class NativeMemoryAdapter:
 def __init__(self,build=1076226,mutation_enabled=False):self.build=build;self.mutation_enabled=mutation_enabled;self.targets={};self.original={}
 def register(self,target):self.targets[target.target_id]=target
 def read(self,target_id,reader):
  t=self.targets.get(target_id)
  if self.build!=1076226:return {'state':'BUILD_UNSUPPORTED'}
  if not t or not t.resolved or not t.evidence:return {'state':'TARGET_UNRESOLVED'}
  try:value=reader(t)
  except (MemoryError,OSError,ValueError):return {'state':'BAD_PAGE'}
  if value is None:return {'state':'BAD_POINTER'}
  if not t.minimum<=value<=t.maximum:return {'state':'OUT_OF_RANGE'}
  return {'state':'COMPLETED','value':value}
 def write(self,target_id,value,reader,writer):
  t=self.targets.get(target_id)
  before=self.read(target_id,reader)
  if before['state']!='COMPLETED':return before
  if not self.mutation_enabled or not t.writable or not t.readback:return {'state':'MUTATION_DISABLED'}
  if not t.minimum<=value<=t.maximum:return {'state':'OUT_OF_RANGE'}
  self.original.setdefault(target_id,before['value']);writer(t,value);after=self.read(target_id,reader)
  if after.get('value')!=value:return {'state':'FAILED_READBACK','observed':after.get('value')}
  return {'state':'COMPLETED','value':value}
 def revert(self,target_id,reader,writer):
  if target_id not in self.original:return {'state':'REVERT_UNAVAILABLE'}
  return self.write(target_id,self.original[target_id],reader,writer)
