import unittest
from unittest.mock import patch
from pathlib import Path
from tools.launch_research_session import launch_and_wait
class LaunchResearchSessionTests(unittest.TestCase):
    def test_uses_session_wait_and_reports_success(self):
        with patch("tools.launch_research_session.subprocess.Popen"), patch("tools.launch_research_session.game_is_running", side_effect=[False, True]), patch("tools.launch_research_session.ProfileLaunchService.wait_for_eml_session", return_value=True):
            with __import__('tempfile').TemporaryDirectory() as td:
                game=Path(td); (game/"Enshrouded.exe").write_text(""); result=launch_and_wait(game,game/"x.log",1,1)
                self.assertTrue(result["fresh_session_observed"])
                self.assertTrue(result["game_process_observed"])

    def test_records_loader_without_game_as_incomplete(self):
        with patch("tools.launch_research_session.subprocess.Popen"), patch("tools.launch_research_session.game_is_running", return_value=False), patch("tools.launch_research_session.wait_for_game_process", return_value=False), patch("tools.launch_research_session.ProfileLaunchService.wait_for_eml_session", return_value=True):
            with __import__('tempfile').TemporaryDirectory() as td:
                game=Path(td); (game/"Enshrouded.exe").write_text(""); result=launch_and_wait(game,game/"x.log",1,1)
                self.assertTrue(result["fresh_session_observed"])
                self.assertFalse(result["game_process_observed"])

    def test_process_wait_retries_until_game_is_ready(self):
        from tools.launch_research_session import wait_for_game_process
        with patch("tools.launch_research_session.game_is_running", side_effect=[False, False, True]), patch("tools.launch_research_session.time.sleep"), patch("tools.launch_research_session.time.monotonic", side_effect=[0, 0, 0, 1]):
            self.assertTrue(wait_for_game_process(timeout=5, interval=0.1))

    def test_refuses_to_start_over_an_existing_game(self):
        with patch("tools.launch_research_session.game_is_running", return_value=True):
            with __import__('tempfile').TemporaryDirectory() as td:
                game=Path(td); (game/"Enshrouded.exe").write_text("")
                with self.assertRaises(ValueError):
                    launch_and_wait(game, game/"x.log", 1, 1)
