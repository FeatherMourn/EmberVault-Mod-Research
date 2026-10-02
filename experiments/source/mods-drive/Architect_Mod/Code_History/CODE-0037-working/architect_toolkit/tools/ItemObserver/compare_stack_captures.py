#!/usr/bin/env python3
"""Incremental, multi-move stack candidate and context comparison."""
from __future__ import annotations
import argparse, json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

GOOD={"CAPTURE_COMPLETED","NO_BASELINE_CANDIDATES"}
def load(p:Path)->dict[str,Any]: return json.loads(p.read_text(encoding="utf-8-sig"))
def ckey(c:dict[str,Any])->tuple[str,int]: return c.get("address",c.get("requestedAddress","")).upper(),int(c.get("integerWidth",4))
def phase_name(label:str,index:int)->str: return f"move_{index}" if label=="move" else label

def load_session(manifest_path:Path)->tuple[dict[str,Any],list[dict[str,Any]],list[dict[str,Any]]]:
    manifest=load(manifest_path); captures=[]; failures=[]; move=0
    for entry in sorted(manifest.get("captures",[]),key=lambda x:x.get("sequence",0)):
        path=manifest_path.parent/entry["path"]
        if not path.exists(): failures.append({"path":str(path),"state":"MISSING_FILE"});continue
        cap=load(path);state=cap.get("validation",{}).get("state")
        if state not in GOOD: failures.append({"path":str(path),"label":cap.get("label"),"state":state});continue
        label=cap.get("label","unknown")
        if label=="move": move+=1
        cap["phaseId"]=phase_name(label,move);captures.append(cap)
    return manifest,captures,failures

def load_contexts(path:Path|None,session_id:str)->list[dict[str,Any]]:
    if not path or not path.exists(): return []
    manifest=load(path)
    if manifest.get("sessionId")!=session_id:return []
    rows=[]
    for entry in manifest.get("captures",[]):
        raw=Path(entry["path"]);p=raw if raw.is_absolute() else path.parent/raw
        if not p.exists() and not raw.is_absolute():
            bridge=next((parent for parent in (path.parent,*path.parents) if parent.name.lower()=="bridge"),None)
            if bridge:p=bridge/raw
        if p.exists():
            report=load(p)
            for row in report.get("candidates",[]): rows.append({**row,"captureId":report.get("captureId"),"timestampUtc":report.get("timestampUtc"),"phase":report.get("phase")})
    return rows

def context_differentials(rows:list[dict[str,Any]])->list[dict[str,Any]]:
    grouped=defaultdict(list)
    for row in rows: grouped[ckey(row)].append(row)
    output=[]
    for key,snaps in grouped.items():
        if len(snaps)<2:continue
        diffs=[]
        for left,right in zip(snaps,snaps[1:]):
            try:a=bytes.fromhex(left["contextHex"]);b=bytes.fromhex(right["contextHex"])
            except (KeyError,ValueError):continue
            changed=[i for i,(x,y) in enumerate(zip(a,b)) if x!=y]
            fields4=[i for i in range(0,min(len(a),len(b))-3,4) if a[i:i+4]!=b[i:i+4]]
            fields8=[i for i in range(0,min(len(a),len(b))-7,8) if a[i:i+8]!=b[i:i+8]]
            lp={(x["offset"],x["rawValue"]) for x in left.get("pointerLikeFields",[]) if "pointer" in x.get("classification","")};rp={(x["offset"],x["rawValue"]) for x in right.get("pointerLikeFields",[]) if "pointer" in x.get("classification","")}
            diffs.append({"from":left.get("phase"),"to":right.get("phase"),"changedByteOffsets":changed,"changed4ByteFieldOffsets":fields4,"changed8ByteFieldOffsets":fields8,"pointerFieldsStable":lp==rp,"sameRegionBase":left.get("region",{}).get("base")==right.get("region",{}).get("base"),"entireContextReplaced":len(changed)>len(a)*.75})
        output.append({"address":key[0],"integerWidth":key[1],"snapshots":len(snaps),"comparisons":diffs})
    fingerprints=defaultdict(list)
    for row in rows:
        if row.get("structuralFingerprint"):fingerprints[row["structuralFingerprint"]].append(row)
    relocated=[]
    for fingerprint,snaps in fingerprints.items():
        addresses={x.get("requestedAddress") for x in snaps}
        if len(addresses)>1:relocated.append({"classification":"POSSIBLE_RELOCATED_OBJECT","structuralFingerprint":fingerprint,"addresses":sorted(addresses),"phases":[x.get("phase") for x in snaps]})
    return output,relocated

def compare_one(manifest_path:Path,context_manifest:Path|None,top_n:int)->dict[str,Any]:
    manifest,captures,failures=load_session(manifest_path);session_id=manifest.get("sessionId","");contexts=load_contexts(context_manifest,session_id)
    maps=[{ckey(c):c for c in cap.get("candidates",[])} for cap in captures];phase_ids=[cap["phaseId"] for cap in captures];labels=[cap.get("label") for cap in captures]
    duplicates=[Counter((c.get("value"),c.get("integerWidth",4)) for c in cap.get("candidates",[])) for cap in captures]
    keys=set().union(*(m.keys() for m in maps)) if maps else set();context_by_key=defaultdict(list)
    for row in contexts:context_by_key[ckey(row)].append(row)
    ranked=[]
    for key in keys:
        observed={phase_ids[i]:maps[i][key]["value"] for i in range(len(maps)) if key in maps[i]};score=0;reasons=[];lifecycle=[]
        baseline_i=next((i for i,x in enumerate(labels) if x=="baseline"),None);split_i=next((i for i,x in enumerate(labels) if x=="split"),None);merge_i=max((i for i,x in enumerate(labels) if x=="merge"),default=None)
        if baseline_i is not None and key in maps[baseline_i]:score+=2;reasons.append("EXACT_BASELINE_VALUE");lifecycle.append("BASELINE_EXISTING")
        if split_i is not None and key in maps[split_i]:
            if baseline_i is not None and key not in maps[baseline_i]:score+=5;reasons.append("APPEARS_AT_SPLIT_WITH_EXPECTED_VALUE");lifecycle.append("SPLIT_CREATED")
            elif baseline_i is not None and maps[baseline_i][key]["value"]!=maps[split_i][key]["value"]:score+=6;reasons.append("VALUE_TRACKED_IN_PLACE");lifecycle.append("VALUE_TRACKED_IN_PLACE")
        move_hits=0
        if split_i is not None and key in maps[split_i]:
            split_value=maps[split_i][key]["value"]
            for i,label in enumerate(labels):
                if label=="move" and key in maps[i] and maps[i][key]["value"]==split_value:move_hits+=1;score+=3
            if move_hits:reasons.append(f"SURVIVED_{move_hits}_MOVE_CAPTURES");lifecycle+=(["SURVIVED_MOVE"]*move_hits)
        if merge_i is not None and key in maps[merge_i]:score+=6;reasons.append("PRESENT_WITH_MERGED_VALUE");lifecycle.append("MERGED_SURVIVOR")
        if captures:
            peak=max((duplicates[i][(maps[i][key].get("value"),key[1])] for i in range(len(maps)) if key in maps[i]),default=0)
            if peak>=1000:score-=2;reasons.append("DUPLICATE_VALUE_AMBIGUOUS")
        crows=context_by_key.get(key,[])
        if crows:
            active=sum(x.get("matchesExpectedValue") is True for x in crows);stale=sum(x.get("matchesExpectedValue") is False for x in crows);score+=active*4-stale*6
            if active:reasons.append(f"EXPECTED_VALUE_CONFIRMED_IN_{active}_IMMEDIATE_CONTEXTS")
            if stale:reasons.append(f"VALUE_CHANGED_BEFORE_CONTEXT_{stale}_TIMES");lifecycle.append("TRANSIENT")
            fingerprints={x.get("structuralFingerprint") for x in crows if x.get("structuralFingerprint")}
            if len(crows)>1 and len(fingerprints)==1:score+=4;reasons.append("CONTEXT_STRUCTURE_REPEATED")
        last_seen=max((i for i,m in enumerate(maps) if key in m),default=-1)
        if last_seen>=0 and last_seen<len(maps)-1:lifecycle.append("DISAPPEARED")
        sample=maps[last_seen][key] if last_seen>=0 else {}
        ranked.append({"address":key[0],"integerWidth":key[1],"score":score,"lifecycle":list(dict.fromkeys(lifecycle))or["UNKNOWN"],"reasons":reasons or["UNKNOWN"],"observedTransitions":observed,"moveCapturesSurvived":move_hits,"region":{"base":sample.get("regionBase"),"size":sample.get("regionSize"),"type":sample.get("regionType"),"protection":sample.get("protection"),"relativeOffset":hex(int(key[0],16)-int(sample.get("regionBase","0x0"),16))},"contextCaptures":len(crows),"structuralFingerprints":sorted({x.get("structuralFingerprint") for x in crows if x.get("structuralFingerprint")})})
    ranked.sort(key=lambda x:(-x["score"],x["address"],x["integerWidth"]));current=maps[-1] if maps else {};current_ranked=[x for x in ranked if (x["address"],x["integerWidth"]) in current and x["score"]>0]
    differentials,relocated=context_differentials(contexts);have=set(labels);state="INCREMENTAL_COMPARISON_COMPLETED" if {"baseline","split"}<=have else "INSUFFICIENT_CAPTURES"
    return {"schemaVersion":3,"sessionId":session_id,"state":state,"phaseSequence":phase_ids,"availablePhases":sorted(have),"missingPhases":[x for x in ("baseline","split","move","merge") if x not in have],"failedOrIncompleteCaptures":failures,"rankedCandidates":ranked,"topCandidates":ranked[:50],"targetedContextAddresses":[x["address"] for x in current_ranked[:top_n]],"targetedContextPhase":phase_ids[-1] if phase_ids else None,"contextSnapshots":len(contexts),"contextDifferentials":differentials,"possibleRelocatedObjects":relocated}

def main()->int:
    root=Path(__file__).resolve().parent;parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--manifest",type=Path,default=(root/"../../bridge/item_observer_stack_session.json").resolve());parser.add_argument("--context-manifest",type=Path,default=(root/"../../bridge/item_observer_stack_context_session.json").resolve());parser.add_argument("--additional-manifest",type=Path,action="append",default=[]);parser.add_argument("--additional-context-manifest",type=Path,action="append",default=[]);parser.add_argument("--top-context",type=int,default=10);parser.add_argument("--output",type=Path,default=(root/"../../bridge/item_observer_stack_comparison.json").resolve());args=parser.parse_args()
    sessions=[compare_one(args.manifest.resolve(),args.context_manifest.resolve(),args.top_context)];sessions += [compare_one(p.resolve(),args.additional_context_manifest[i].resolve() if i<len(args.additional_context_manifest) else None,args.top_context) for i,p in enumerate(args.additional_manifest)]
    patterns=defaultdict(list)
    for session in sessions:
        for row in session["topCandidates"]:patterns[(tuple(row["lifecycle"]),row["region"].get("type"),row["region"].get("size"),row["region"].get("relativeOffset"))].append({"sessionId":session["sessionId"],"address":row["address"],"score":row["score"]})
    cross=[{"classification":"CROSS_SESSION_STRUCTURAL_BEHAVIOR_MATCH","signature":{"lifecycle":k[0],"regionType":k[1],"regionSize":k[2],"relativeOffset":k[3]},"candidates":v} for k,v in patterns.items() if len({x["sessionId"] for x in v})>1];fingerprints=defaultdict(list)
    for session in sessions:
        for row in session["rankedCandidates"]:
            for fp in row["structuralFingerprints"]:fingerprints[fp].append({"sessionId":session["sessionId"],"address":row["address"]})
    cross_context=[{"classification":"CROSS_SESSION_CONTEXT_FINGERPRINT_MATCH","structuralFingerprint":fp,"candidates":rows} for fp,rows in fingerprints.items() if len({x["sessionId"] for x in rows})>1]
    result={"schemaVersion":3,"tool":"compare_stack_captures.py","timestampUtc":datetime.now(timezone.utc).isoformat(),**sessions[0],"sessions":sessions,"crossSessionMatches":cross,"crossSessionContextMatches":cross_context,"interpretation":"Incremental lifecycle evidence is observational. Immediate value confirmation and repeatable context are required before candidateStackObject status.","safety":"Offline JSON comparison only; no process access or mutation."};args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(f"{result['state']}; phases={','.join(result['phaseSequence'])}; candidates={len(result['rankedCandidates'])}; wrote {args.output}");print("targeted context: "+(",".join(result["targetedContextAddresses"])or"none"));return 0
if __name__=="__main__":raise SystemExit(main())
