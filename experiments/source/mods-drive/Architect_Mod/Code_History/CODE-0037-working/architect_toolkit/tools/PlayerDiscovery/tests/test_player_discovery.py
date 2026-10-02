import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from analyze_player_discovery import (DISPROVEN, INSUFFICIENT, STRONG, analyze_events,
                                      analyze_file, render_text)


def event(sequence, phase, kind, value, entity="player-7", probe=None, side="client"):
    return {"sessionId": "session-a", "sequence": sequence, "tickMs": sequence * 10,
            "phase": phase, "probeId": probe or f"network_{kind.lower()}",
            "candidate": {"entityId": entity, "side": side,
                          "componentPointer": f"0x{1000 + sequence:x}"},
            "raw": {"float": value},
            "interpretation": {"candidateType": kind, "status": "EXPERIMENTAL"}}


class PlayerDiscoveryAnalyzerTests(unittest.TestCase):
    def test_stamina_pattern_detection(self):
        report = analyze_events([event(1, "BASELINE", "Stamina", 100),
                                 event(2, "SPRINT_ACTIVE", "Stamina", 55),
                                 event(3, "SPRINT_RECOVERY", "Stamina", 90)])
        signal = report["candidates"][0]["signals"][0]
        self.assertEqual(signal["status"], STRONG)
        self.assertEqual(len(signal["matchedPatterns"]), 2)

    def test_health_pattern_detection(self):
        report = analyze_events([event(1, "BASELINE", "Health", 100),
                                 event(2, "SPRINT_ACTIVE", "Health", 100),
                                 event(3, "DAMAGE", "Health", 72),
                                 event(4, "HEAL", "Health", 93)])
        self.assertEqual(report["candidates"][0]["signals"][0]["status"], STRONG)

    def test_contradiction_detection(self):
        report = analyze_events([event(1, "BASELINE", "Stamina", 80),
                                 event(2, "SPRINT_ACTIVE", "Stamina", 95),
                                 event(3, "SPRINT_RECOVERY", "Stamina", 60)])
        signal = report["candidates"][0]["signals"][0]
        self.assertEqual(signal["status"], DISPROVEN)
        self.assertEqual(len(signal["contradictions"]), 2)

    def test_insufficient_evidence(self):
        report = analyze_events([event(1, "BASELINE", "Mana", 100)])
        signal = report["candidates"][0]["signals"][0]
        self.assertEqual(signal["status"], INSUFFICIENT)
        self.assertEqual(signal["missingEvidence"], ["MANA_SPEND"])

    def test_entity_multi_signal_correlation_and_side_preservation(self):
        events = [event(1, "BASELINE", "Stamina", 100, probe="stamina-client"),
                  event(2, "SPRINT_ACTIVE", "Stamina", 60, probe="stamina-client"),
                  event(3, "SPRINT_RECOVERY", "Stamina", 95, probe="stamina-client"),
                  event(4, "BASELINE", "Health", 100, probe="health-server", side="server"),
                  event(5, "DAMAGE", "Health", 70, probe="health-server", side="server"),
                  event(6, "HEAL", "Health", 90, probe="health-server", side="server")]
        candidate = analyze_events(events)["candidates"][0]
        self.assertEqual(candidate["localPlayerOwnership"], "EXPERIMENTAL")
        self.assertEqual(candidate["clientServer"]["observedSides"], ["client", "server"])
        self.assertTrue(candidate["clientServer"]["possibleDuplication"])
        self.assertEqual({s["candidateType"] for s in candidate["signals"]}, {"Health", "Stamina"})

    def test_distinct_pointer_candidates_do_not_merge_without_entity(self):
        rows = [event(1, "BASELINE", "Mana", 10, entity=None),
                event(2, "MANA_SPEND", "Mana", 5, entity=None)]
        rows[0]["candidate"]["componentPointer"] = "0x1"
        rows[1]["candidate"]["componentPointer"] = "0x2"
        self.assertEqual(analyze_events(rows)["candidateCount"], 2)

    def test_malformed_input_is_reported_and_output_is_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "capture.jsonl"
            path.write_text(json.dumps(event(1, "BASELINE", "Mana", 10)) + "\n{bad\n", encoding="utf-8")
            first = analyze_file(path)
            second = analyze_file(path)
        self.assertEqual(first, second)
        self.assertEqual(first["diagnostics"][0]["code"], "MALFORMED_JSONL_LINE")
        self.assertEqual(render_text(first), render_text(second))

    def test_missing_file_fails_closed(self):
        report = analyze_file(Path("definitely-not-present-player-discovery.jsonl"))
        self.assertEqual(report["eventCount"], 0)
        self.assertEqual(report["diagnostics"][0]["code"], "CAPTURE_NOT_FOUND")

    def test_marker_only_capture_is_insufficient_without_fake_candidate(self):
        report = analyze_events([
            {"sessionId": "safe-zero-probe", "sequence": 1, "recordType": "marker", "phase": "BASELINE"},
            {"sessionId": "safe-zero-probe", "sequence": 2, "recordType": "marker", "phase": "DAMAGE"},
        ])
        self.assertEqual(report["eventCount"], 2)
        self.assertEqual(report["candidateCount"], 0)
        self.assertEqual(report["analysisStatus"], INSUFFICIENT)
        self.assertEqual(report["observedPhases"], ["BASELINE", "DAMAGE"])


if __name__ == "__main__":
    unittest.main()
