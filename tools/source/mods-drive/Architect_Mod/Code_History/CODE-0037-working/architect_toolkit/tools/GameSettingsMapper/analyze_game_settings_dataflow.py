"""Bounded offline convergence scan for CODE-0025 (build 1076226 only)."""
from __future__ import annotations
import hashlib, json, struct
from bisect import bisect_right
from pathlib import Path
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64, CS_OP_IMM, CS_OP_MEM
from capstone.x86 import X86_REG_RIP

ROOT=Path(__file__).resolve().parents[2]; EXE=ROOT.parents[1]/"enshrouded.exe"; TYPES=ROOT.parents[1]/".cache/types.json"
OUT=ROOT/"bridge/game_settings_dataflow_map.json"; EXPECTED="AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781"
TYPE_IDS=(2702,2703,2784,3410,4311)

def occurrences(data:bytes, needle:bytes, limit=4096):
    out=[]; pos=0
    while len(out)<limit:
        pos=data.find(needle,pos)
        if pos<0: break
        out.append(pos); pos+=1
    return out

def build():
    sha=hashlib.sha256(EXE.read_bytes()).hexdigest().upper()
    if sha!=EXPECTED: raise RuntimeError(f"unsupported executable {sha}")
    pe=pefile.PE(str(EXE),fast_load=False); base=pe.OPTIONAL_HEADER.ImageBase
    raw=json.loads(TYPES.read_text(encoding="utf-8")); rows=raw.get("types",raw); by={int(x['index']):x for x in rows}
    sections=[]
    for s in pe.sections:
        sections.append((s.Name.rstrip(b'\0').decode(errors='replace'),s.VirtualAddress,s.get_data()))
    text_name,text_rva,text=next(x for x in sections if x[0]=='.text')
    anchors=[]
    for idx in TYPE_IDS:
        t=by[idx]
        names=sorted({t['name'],t.get('impactName',''),t.get('qualifiedName','')} - {''})
        for name in names:
            for sn,sr,data in sections:
                for off in occurrences(data,name.encode()+b'\0',64): anchors.append({'kind':'type_string','typeIndex':idx,'label':name,'section':sn,'rva':sr+off})
        for key in ('nameHash','impactHash','qualifiedHash','internalHash'):
            value=t.get(key)
            if value is None: continue
            for sn,sr,data in sections:
                for off in occurrences(data,struct.pack('<I',value),128): anchors.append({'kind':key,'typeIndex':idx,'label':t['qualifiedName'],'section':sn,'rva':sr+off})
    # Follow explicit data pointers/RVAs only outside .text; this recovers descriptor ownership without pretending every scalar match is a descriptor.
    frontier={}
    for a in anchors:
        if a['kind']=='type_string' and a['section']!='.text': frontier.setdefault(a['rva'],set()).add(a['typeIndex'])
    anchor_types={r:set(v) for r,v in frontier.items()}; pointer_edges=[]
    for depth in range(3):
        new={}
        for target in sorted(frontier):
            needles=((struct.pack('<Q',base+target),'va64'),(struct.pack('<I',target),'rva32'))
            for sn,sr,data in sections:
                if sn=='.text': continue
                for needle,encoding in needles:
                    for off in occurrences(data,needle,256):
                        source=sr+off; type_ids=sorted(frontier[target]); pointer_edges.append({'depth':depth+1,'sourceRva':f'0x{source:X}','targetRva':f'0x{target:X}','section':sn,'encoding':encoding,'typeIndexes':type_ids}); new.setdefault(source,set()).update(type_ids);anchor_types.setdefault(source,set()).update(type_ids)
        frontier=new
    anchor_rvas=set(anchor_types)
    md=Cs(CS_ARCH_X86,CS_MODE_64);md.detail=True
    instructions=list(md.disasm(text,base+text_rva))
    starts=[]; bounds=[]
    for e in getattr(pe,'DIRECTORY_ENTRY_EXCEPTION',[]):
        b=e.struct.BeginAddress; end=e.struct.EndAddress
        if text_rva<=b<text_rva+len(text): starts.append(b);bounds.append((b,end))
    zipped=sorted(zip(starts,bounds));starts=[x[0] for x in zipped];bounds=[x[1] for x in zipped]
    def bound(rva):
        i=bisect_right(starts,rva)-1
        return bounds[i] if i>=0 and bounds[i][0]<=rva<bounds[i][1] else (rva,rva+1)
    evidence={}
    calls=[]
    for ins in instructions:
        rva=ins.address-base; b,e=bound(rva); key=(b,e); bucket=evidence.setdefault(key,{'descriptorRefs':[],'consumedC4':[],'aggregate90':[]})
        for op in ins.operands:
            if op.type==CS_OP_MEM:
                if op.mem.base==X86_REG_RIP:
                    target=ins.address+ins.size+op.mem.disp-base
                    if target in anchor_rvas: bucket['descriptorRefs'].append({'rva':f'0x{rva:X}','targetRva':f'0x{target:X}','typeIndexes':sorted(anchor_types[target]),'instruction':f'{ins.mnemonic} {ins.op_str}'})
                if op.mem.disp==0xC4: bucket['consumedC4'].append({'rva':f'0x{rva:X}','instruction':f'{ins.mnemonic} {ins.op_str}'})
                if abs(op.mem.disp)==0x90: bucket['aggregate90'].append({'rva':f'0x{rva:X}','instruction':f'{ins.mnemonic} {ins.op_str}'})
            elif op.type==CS_OP_IMM:
                if op.imm==0x90: bucket['aggregate90'].append({'rva':f'0x{rva:X}','instruction':f'{ins.mnemonic} {ins.op_str}'})
        if ins.mnemonic=='call' and ins.operands and ins.operands[0].type==CS_OP_IMM: calls.append((rva,ins.operands[0].imm-base))
    candidates=[]
    for (b,e),ev in evidence.items():
        kinds=sum(bool(ev[k]) for k in ev)
        if not kinds: continue
        # An offset alone is weak. Emit only intersections, plus descriptor-linked functions for preserved negative evidence.
        if kinds<2 and not ev['descriptorRefs']: continue
        callers=[f'0x{x:X}' for x,t in calls if b<=t<e][:64]; callees=[f'0x{t:X}' for x,t in calls if b<=x<e][:64]
        relation=[]
        if ev['descriptorRefs']: relation.append('descriptor/data anchor reference')
        if ev['consumedC4']: relation.append('memory operand displacement +0xC4')
        if ev['aggregate90']: relation.append('0x90 immediate/displacement')
        strong=len(relation)>=3; observe=len(relation)>=2 and bool(ev['descriptorRefs'])
        candidates.append({'candidateId':f'GS-CAND-{len(candidates)+1:03d}','rva':f'0x{b:X}','functionEndRva':f'0x{e:X}','callers':callers,'callees':callees,'dataReferences':ev['descriptorRefs'][:32],'consumedVersionEvidence':ev['consumedC4'][:32],'aggregateSizeEvidence':ev['aggregate90'][:32],'likelySide':'unknown','relationshipReasons':relation,'contradictions':['No authoritative owner, action payload argument, event role, or side is established by these syntactic intersections.'],'classification':'EXPERIMENTAL_BUILD_1076226' if observe else 'INFERRED_BUILD_1076226','uniqueSignature':None,'overwrittenBytesUnderstood':False,'runtimeHookEligibility':'STRONG_OBSERVE_CANDIDATE' if strong else ('OBSERVE_CANDIDATE' if observe else 'NO')})
    comparable=[]
    consumed=by[2784].get('structFields',{})
    for name,v in consumed.items():
        if 'consumed' in name and name.endswith('Action'):
            comparable.append({'actionVersionField':name,'offset':f"0x{v['dataOffset']:X}",'submitter':'UNSOLVED','serverConsumer':'UNSOLVED','consequence':'UNSOLVED','classification':'PROVEN_STATIC_BUILD_1076226 layout only'})
    return {'schemaVersion':1,'build':{'revision':1076226,'sha256':sha,'peTimestamp':f'0x{pe.FILE_HEADER.TimeDateStamp:08X}','imageSize':f'0x{pe.OPTIONAL_HEADER.SizeOfImage:08X}'},'method':{'descriptorPointerDepth':3,'arbitraryMemoryScan':False,'runtimeAccess':False},'registrationAnchors':anchors,'descriptorPointerEdges':pointer_edges,'comparableVersionedActions':comparable,'candidates':candidates,'convergence':{'dispatchCandidateIds':[],'readbackCandidateIds':[],'safeObserveHookJustified':False,'result':'NO_STATIC_CONVERGENCE','mutationBlockedBy':['No defensible action dispatch/consumer boundary','No independent authoritative readback/event boundary','Version semantics and authority unresolved']}}

def main():
    result=build();OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8');print(f"wrote {OUT} anchors={len(result['registrationAnchors'])} edges={len(result['descriptorPointerEdges'])} candidates={len(result['candidates'])} convergence={result['convergence']['result']}")
if __name__=='__main__':main()
