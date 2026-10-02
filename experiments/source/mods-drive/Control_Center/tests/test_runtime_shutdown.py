import unittest
from pathlib import Path


class RuntimeShutdownTests(unittest.TestCase):
    SOURCE_ROOT = Path(r"H:\enshroudedresearch\external\kfc-parser-source\crates")

    def test_proxy_detach_does_not_run_rust_cleanup_from_dllmain(self):
        for proxy in ("dinput8-proxy", "dbghelp-proxy"):
            source = (self.SOURCE_ROOT / proxy / "src" / "lib.rs").read_text(encoding="utf-8")
            detach = source.split("DLL_PROCESS_DETACH =>", 1)[1].split("_ =>", 1)[0]
            self.assertNotIn("init::deinit", detach, proxy)
            self.assertTrue("thread-local" in detach or "TLS" in detach, proxy)


if __name__ == "__main__":
    unittest.main()
