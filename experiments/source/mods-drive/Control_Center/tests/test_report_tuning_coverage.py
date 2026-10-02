import json, subprocess, sys, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
class TuningCoverageTests(unittest.TestCase):
    def test_reports_covered_and_uncovered_families(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); mods=root/'modules'; (mods/'one').mkdir(parents=True)
            (root/'inventory.json').write_text(json.dumps({'build':'x','families':[
                {'family':'Covered','reflected_types':[{'name':'keen::Covered'}]},
                {'family':'Missing','reflected_types':[{'name':'keen::Missing'}]}]}))
            (mods/'one'/'module.json').write_text(json.dumps({'id':'one','target_kfc_resources':['keen::Covered'],'settings':[{'key':'a'}]}))
            r=subprocess.run([sys.executable,'tools/report_tuning_coverage.py',str(root/'inventory.json'),str(mods)],cwd=ROOT,capture_output=True,text=True,check=True)
            report=json.loads(r.stdout)
            self.assertEqual(report['covered_family_count'],1)
            self.assertEqual(report['uncovered_family_count'],1)
            self.assertEqual(report['user_setting_count'],1)
            self.assertEqual(report['families'][0]['priority'],4)
            self.assertEqual(report['research_queue'][0]['family'],'Missing')
            self.assertEqual(report['research_queue'][0]['priority'],4)
            output=root/'research'/'queue.json'
            subprocess.run([sys.executable,'tools/report_tuning_coverage.py',str(root/'inventory.json'),str(mods),'--output',str(output)],cwd=ROOT,capture_output=True,text=True,check=True)
            saved=json.loads(output.read_text())
            self.assertEqual(saved['schema'],'control_center.tuning_coverage.v1')
            self.assertEqual(saved['research_queue'][0]['family'],'Missing')
if __name__ == '__main__': unittest.main()
