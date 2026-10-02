from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from recorder import RecordingSession, ingest_semantic_jsonl, load_blueprint, save_blueprint, validate_blueprint  # noqa: E402
from coordinates import Q32_SCALE, encode_world, decode_world  # noqa: E402


def event(seq: int, logical: int, item: int = 81726253, material: int = 7, pos=None, sid: str = "s1") -> dict:
    return {"observer": "building_place", "status": "observed", "sessionId": sid, "rawEventSequence": seq, "threadId": seq + 100, "timestamp": f"tick:{seq}", "payload": {"trackingItemId": item, "material": material, "position": pos or [float(seq), 0.0, 0.0], "orientation": [0.0, 0.0, 0.0, 1.0], "volumeMin": [float(seq), 0.0, 0.0], "volumeMax": [float(seq + 1), 1.0, 1.0]}, "correlation": {"candidateLogicalPlacementId": logical, "candidatePair": True, "pairDeltaMs": 16}}


class RecorderTests(unittest.TestCase):
    def test_pair_collapses_once(self):
        s = RecordingSession()
        self.assertEqual(s.ingest([event(1, 1), event(2, 1)]), 1)
        self.assertEqual(len(s.placements), 1)
        self.assertEqual(s.statistics()["logicalPlacementCount"], 1)
        self.assertEqual(s.statistics()["buildingRawEventsInRecordingWindow"], 2)
        self.assertEqual(s.statistics()["pairedBuildingRawEvents"], 2)

    def test_distinct_logical_ids_are_not_deduped(self):
        s = RecordingSession()
        self.assertEqual(s.ingest([event(1, 1), event(2, 2)]), 2)

    def test_round_trip(self):
        s = RecordingSession(name="roundtrip")
        s.ingest([event(1, 1, pos=[10, 2, 3]), event(2, 1, pos=[10, 2, 3])]); s.stop()
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.architect.json"; save_blueprint(s, p); loaded = load_blueprint(p)
            self.assertEqual(loaded.placements[0]["raw"]["position"], [10.0, 2.0, 3.0])
            self.assertEqual(len(loaded.placements), 1)

    def test_q32_coordinates_are_lossless_and_bounds_translate(self):
        base = [16013785563136, 3624952397824, 6152540651520]
        rows = [event(1, 1, pos=base), event(2, 1, pos=base),
                event(3, 2, pos=[base[0] + 4 * Q32_SCALE, base[1], base[2]]),
                event(4, 2, pos=[base[0] + 4 * Q32_SCALE, base[1], base[2]])]
        s = RecordingSession(); self.assertEqual(s.ingest(rows), 2)
        self.assertEqual(s.placements[1]["raw"]["position"], [base[0] + 4 * Q32_SCALE, base[1], base[2]])
        self.assertEqual(s.placements[1]["derived"]["localPosition"], [4.0, 0.0, 0.0])
        self.assertEqual(s.statistics()["bounds"]["size"], [7.0, 1.0, 1.0])

    def test_non_building_rows_are_counted_once_and_windowed(self):
        s = RecordingSession(start_raw_event_sequence=10)
        self.assertEqual(s.ingest([{"rawEventSequence": 10, "observer": "other"}, {"rawEventSequence": 11, "observer": "other"}, event(12, 1)]), 1)
        self.assertEqual(s.statistics()["semanticStreamEventsObserved"], 2)
        self.assertEqual(s.statistics()["ignoredNonBuildingEvents"], 1)
        self.assertEqual(s.statistics()["buildingRawEventsInRecordingWindow"], 1)

    def test_coordinate_encode_decode(self):
        values = [-4.0, 0.0, 12.5]
        self.assertEqual(decode_world(encode_world(values)), values)

    def test_recorder_test_fixture_migrates_and_translates(self):
        fixture = Path(__file__).resolve().parents[3] / "blueprints" / "recorded" / "recorder_test_01.architect.json"
        loaded = load_blueprint(fixture)
        stats = loaded.statistics()
        self.assertEqual(stats["bounds"]["size"], [16.0, 6.0, 4.0])
        self.assertEqual(stats["buildingRawEventsInRecordingWindow"], 12)
        self.assertTrue(all(isinstance(value, int) for value in loaded.placements[0]["raw"]["position"]))

    def test_unresolved_logical_id_is_ambiguous(self):
        s = RecordingSession(); row = event(1, 1); row["correlation"] = None
        self.assertEqual(s.ingest([row]), 0); self.assertEqual(s.ambiguous_raw_events, 1)

    def test_session_rollover_cancels(self):
        s = RecordingSession(); s.ingest([event(1, 1, sid="a"), event(2, 2, sid="b")])
        self.assertEqual(s.state, "cancelled")

    def test_malformed_tail_is_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "events.jsonl"; p.write_text(json.dumps(event(1, 1)) + "\n{\"partial\":", encoding="utf-8")
            s = RecordingSession(); self.assertEqual(ingest_semantic_jsonl(p, s), 1)

    def test_validate_rejects_bad_schema(self):
        with self.assertRaises(ValueError): validate_blueprint({"schema": "bad"})


if __name__ == "__main__": unittest.main()
