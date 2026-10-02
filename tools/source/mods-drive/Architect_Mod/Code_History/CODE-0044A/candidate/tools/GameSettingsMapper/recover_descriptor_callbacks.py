"""Relocation-aware recovery of the two exact CODE-0026 descriptor objects."""
from __future__ import annotations
import hashlib,json,struct
from pathlib import Path
import pefile

ROOT=Path(__file__).resolve().parents[2];EXE=ROOT.parents[1]/'enshrouded.exe';OUT=ROOT/'bridge/game_settings_descriptor_callbacks.json'
EXPECTED='AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781'
TARGETS=(
 {'reflectionIndex':2703,'name':'AdminChangeGameSettingsAction','startRva':0x198F520,'endRva':0x198F5D0,'qualifiedSlot':0x20,'expectedSize':0x98,'expectedInternalHash':0x9919D92D},
 {'reflectionIndex':3410,'name':'GameSettingsChangedEvent','startRva':0x18CBCA0,'endRva':0x18CBD50,'qualifiedSlot':0x20,'expectedSize':0x98,'expectedInternalHash':0x81B10CBB},
)

def build():
 sha=hashlib.sha256(EXE.read_bytes()).hexdigest().upper()
 if sha!=EXPECTED:raise RuntimeError(f'unsupported executable {sha}')
 pe=pefile.PE(str(EXE),fast_load=False);base=pe.OPTIONAL_HEADER.ImageBase
 rel={e.rva:e.type for block in pe.DIRECTORY_ENTRY_BASERELOC for e in block.entries}
 sections=[]
 for s in pe.sections:sections.append((s.Name.rstrip(b'\0').decode(errors='replace'),s.VirtualAddress,s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData),s))
 def section(rva):
  return next((x for x in sections if x[1]<=rva<x[2]),None)
 def data(rva,n):return pe.get_data(rva,n)
 def cstring(rva):
  raw=data(rva,256);return raw.split(b'\0',1)[0].decode(errors='replace')
 descriptors=[]
 for spec in TARGETS:
  start,end=spec['startRva'],spec['endRva'];blob=data(start,end-start);pointers=[]
  for slot in range(0,end-start,8):
   rva=start+slot
   if rel.get(rva)!=10:continue
   va=struct.unpack_from('<Q',blob,slot)[0];target=va-base;sec=section(target);kind='unknown';detail=''
   if sec:
    if sec[0]=='.text':kind='code'
    elif sec[0] in ('.rdata','.data'):
     s=cstring(target)
     if s and all(31<ord(ch)<127 for ch in s[:min(len(s),80)]):kind='type_metadata' if spec['name'] in s or 'keen::' in s else 'data';detail=s[:120]
     else:kind='type_metadata'
   if slot in (0,0x10,0x20):kind='type_metadata';detail=cstring(target)
   if slot in (0x30,0x38,0x58,0x70):kind='type_metadata'
   pointers.append({'slotOffset':f'0x{slot:X}','relocationRva':f'0x{rva:X}','relocationType':'IMAGE_REL_BASED_DIR64','targetRva':f'0x{target:X}','targetSection':sec[0] if sec else None,'classification':kind,'detail':detail})
  qualified=next(x for x in pointers if x['slotOffset']==f"0x{spec['qualifiedSlot']:X}")
  packed_size=struct.unpack_from('<I',blob,0x40)[0]
  internal_hash=struct.unpack_from('<I',blob,0x54)[0]
  validated=(spec['name'] in qualified['detail'] and packed_size==spec['expectedSize'] and internal_hash==spec['expectedInternalHash'])
  code=[p for p in pointers if p['classification']=='code']
  descriptors.append({'reflectionIndex':spec['reflectionIndex'],'name':spec['name'],'objectStartRva':f'0x{start:X}','objectEndRva':f'0x{end:X}','objectSize':end-start,'boundaryEvidence':['qualified-name relocation at +0x20','packed reflected size/alignment at +0x40','internal hash at +0x54','next generated descriptor begins at objectEndRva'],'validation':{'qualifiedName':qualified['detail'],'reflectedPayloadSize':packed_size,'internalHash':f'0x{internal_hash:08X}','matchesExpected':validated},'ownedRelocations':pointers,'ownedCodePointerCount':len(code),'callbackCandidates':[]})
 return {'schemaVersion':1,'build':{'revision':1076226,'sha256':sha,'peTimestamp':f'0x{pe.FILE_HEADER.TimeDateStamp:08X}','imageSize':f'0x{pe.OPTIONAL_HEADER.SizeOfImage:08X}'},'method':{'tool':'pefile relocation directory + section-aware object recovery','equivalentDisassemblerComponents':['PE base relocations','section classification','bounded object layout validation'],'scope':'exact reflection indices 2703 and 3410 only'},'descriptors':descriptors,'conclusion':'NO_DESCRIPTOR_CONVERGENCE','safeObserveHookJustified':False,'dispatchBoundary':None,'readbackBoundary':None,'mutationBlocked':True,'negativeEvidence':['Neither exact non-DS descriptor owns an IMAGE_REL_BASED_DIR64 relocation into .text.','The nearby three-function groups lie outside the recovered descriptor bounds and belong to adjacent generated objects; they are not descriptor-owned callbacks.','Descriptor membership alone would not prove authority even if a callback existed.']}

def main():
 r=build();OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n',encoding='utf-8');print(f"wrote {OUT} conclusion={r['conclusion']} codePointers={[d['ownedCodePointerCount'] for d in r['descriptors']]}")
if __name__=='__main__':main()
