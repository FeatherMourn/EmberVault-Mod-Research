import importlib.util,json,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];S=importlib.util.spec_from_file_location("cc",ROOT/"tools"/"CheatCorrelation"/"analyze_capture.py");M=importlib.util.module_from_spec(S);S.loader.exec_module(M)
def row(kind,phase,context="0x1",selector=0,value=0,thread=7):return {"kind":kind,"phase":phase,"context":context,"selector":selector,"valueBits":value,"threadId":thread}
class AnalyzerTests(unittest.TestCase):
 def test_zero_samples(self):self.assertEqual("NO_SAMPLES",M.analyze([])["movement"]["classification"])
 def test_movement_converges(self):
  rows=[row("movement",p) for p in ("BASELINE_IDLE","WALK","SPRINT_ACTIVE","JUMP")];self.assertEqual("CONVERGED",M.analyze(rows)["movement"]["result"])
 def test_movement_ambiguous(self):
  rows=[row("movement","WALK",hex(i)) for i in range(5)];self.assertEqual("AMBIGUOUS",M.analyze(rows)["movement"]["result"])
 def test_stamina_converges(self):
  rows=[row("stamina","SPRINT_ACTIVE",selector=4,value=x) for x in (100,70,30)]+[row("stamina","SPRINT_RECOVERY",selector=4,value=x) for x in (30,60,100)];self.assertEqual("CONVERGED",M.analyze(rows)["stamina"]["result"])
 def test_deterministic(self):
  rows=[row("movement",p) for p in ("BASELINE_IDLE","WALK","SPRINT_ACTIVE")];self.assertEqual(json.dumps(M.analyze(rows),sort_keys=True),json.dumps(M.analyze(rows),sort_keys=True))
 def test_malformed(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"x.jsonl";p.write_text('{bad\n',encoding="utf-8");rows,w=M.load(p);self.assertFalse(rows);self.assertTrue(w)
if __name__=="__main__":unittest.main()
