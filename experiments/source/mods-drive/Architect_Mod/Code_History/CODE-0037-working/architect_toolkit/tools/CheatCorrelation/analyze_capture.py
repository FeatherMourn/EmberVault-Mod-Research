"""Offline CODE-0033 movement/stamina correlation analyzer."""
from __future__ import annotations
import argparse,json,struct
from collections import Counter,defaultdict
from pathlib import Path
PHASES={"BASELINE_IDLE","WALK","SPRINT_ACTIVE","SPRINT_RECOVERY","JUMP","POST_JUMP_RECOVERY","COMBAT_IDLE","MENU"}
def f32(bits): return struct.unpack("<f",struct.pack("<I",int(bits)&0xffffffff))[0]
def load(path):
 rows=[];warnings=[]
 if not path.exists():return rows,["capture missing"]
 for n,line in enumerate(path.read_text(encoding="utf-8",errors="replace").splitlines(),1):
  try:
   row=json.loads(line)
   if row.get("phase") in PHASES and row.get("kind") in {"movement","stamina"}:rows.append(row)
  except Exception:warnings.append(f"malformed line {n}")
 return rows,warnings
def movement(rows):
 r=[x for x in rows if x["kind"]=="movement"]
 if not r:return {"result":"NO_CORRELATION","classification":"NO_SAMPLES","sampleCount":0}
 groups=Counter((x.get("context"),x.get("threadId")) for x in r); top,count=groups.most_common(1)[0]; phases={x["phase"] for x in r if (x.get("context"),x.get("threadId"))==top}
 active={"WALK","SPRINT_ACTIVE","JUMP"}&phases; idle="BASELINE_IDLE" in phases
 if len(groups)==1 and idle and len(active)>=2: result,classification="CONVERGED","STRONG_LOCAL_PLAYER_CORRELATION"
 elif count/len(r)>=.6 and active:result,classification="PARTIAL","PARTIAL_CORRELATION"
 else:result,classification="AMBIGUOUS","AMBIGUOUS_MULTI_ENTITY"
 return {"result":result,"classification":classification,"sampleCount":len(r),"stableContext":top[0],"threadId":top[1],"dominantSamples":count,"distinctContexts":len(groups),"phases":sorted(phases),"targetBackend":"NATIVE_HOOK" if result=="CONVERGED" else None}
def stamina(rows):
 r=[x for x in rows if x["kind"]=="stamina"]
 if not r:return {"result":"NO_CORRELATION","classification":"NO_SAMPLES","sampleCount":0}
 groups=defaultdict(list)
 for x in r:groups[(x.get("context"),x.get("selector"))].append(x)
 ranked=[]
 for key,g in groups.items():
  vals=defaultdict(list)
  for x in g:vals[x["phase"]].append(int(x.get("valueBits",0)))
  drain=vals["SPRINT_ACTIVE"];recovery=vals["SPRINT_RECOVERY"]
  decreases=len(drain)>1 and drain[-1]<drain[0];increases=len(recovery)>1 and recovery[-1]>recovery[0]
  ranked.append((decreases+increases,len(g),key,decreases,increases))
 ranked.sort(reverse=True,key=lambda x:(x[0],x[1]));score,count,key,decreases,increases=ranked[0]
 if score==2 and len(groups)==1:result,classification="CONVERGED","STRONG_LOCAL_PLAYER_CORRELATION"
 elif score>=1:result,classification="PARTIAL","PARTIAL_CORRELATION"
 else:result,classification=("AMBIGUOUS","AMBIGUOUS_MULTI_ENTITY") if len(groups)>1 else ("NO_CORRELATION","NO_BEHAVIOR_CORRELATION")
 return {"result":result,"classification":classification,"sampleCount":len(r),"stableContext":key[0],"selector":key[1],"dominantSamples":count,"distinctContextSelectors":len(groups),"drainObserved":decreases,"recoveryObserved":increases,"targetBackend":"NATIVE_HOOK" if result=="CONVERGED" else None}
def analyze(rows,warnings=None):
 m=movement(rows);s=stamina(rows);converged=[k for k,v in (("movement",m),("stamina",s)) if v["result"]=="CONVERGED"]
 return {"schema":"architect.cheat_correlation_report.v1","movement":m,"stamina":s,"overall":"CONVERGED" if converged else ("PARTIAL" if "PARTIAL" in {m["result"],s["result"]} else "NO_CORRELATION"),"code0034Recommended":bool(converged),"recommendedCandidate":("stamina" if "stamina" in converged else converged[0]) if converged else None,"warnings":warnings or []}
def main():
 root=Path(__file__).resolve().parents[2];p=argparse.ArgumentParser();p.add_argument("--capture",type=Path,default=root/"bridge"/"cheat_correlation_capture.jsonl");p.add_argument("--output",type=Path,default=root/"bridge"/"cheat_correlation_report.json");a=p.parse_args();rows,warnings=load(a.capture);report=analyze(rows,warnings);a.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8");print(report["overall"]);return 0
if __name__=="__main__":raise SystemExit(main())
