import io
import unittest
from contextlib import redirect_stdout

from gui.launcher import main


class LauncherTests(unittest.TestCase):
    def test_capabilities_command_exposes_valid_audit(self):
        output = io.StringIO()
        with redirect_stdout(output):
            code = main(["--capabilities"])
        self.assertEqual(code, 0)
        self.assertIn('"schema": "control_center.capability_audit.v1"', output.getvalue())
        self.assertIn('"phase": 4', output.getvalue())

    def test_launcher_uses_audit_family_for_capabilities(self):
        source = __import__("pathlib").Path(__file__).parents[1] / "gui" / "launcher.py"
        text = source.read_text(encoding="utf-8")
        self.assertIn('glob("CAPABILITY_AUDIT_*.json")', text)


if __name__ == "__main__":
    unittest.main()
