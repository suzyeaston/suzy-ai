import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from suzy_ai.events import timeline_event
from suzy_ai.paths import ensure_home
from suzy_ai.store import append_event, read_events


class CoreTests(unittest.TestCase):
    def test_private_home_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"SUZY_AI_HOME": tmp}):
                root = ensure_home()
                self.assertEqual(root, Path(tmp).resolve())
                self.assertTrue((root / "memory").is_dir())
                self.assertTrue((root / "world").is_dir())
                self.assertTrue((root / "models").is_dir())

    def test_timeline_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"SUZY_AI_HOME": tmp}):
                event = timeline_event(
                    stream="music",
                    kind="scene",
                    source="test",
                    unit="bar",
                    value=4,
                    payload={"name": "test scene"},
                )
                append_event(event)
                events = read_events("music")
                self.assertEqual(len(events), 1)
                self.assertEqual(events[0]["payload"]["name"], "test scene")

    def test_event_is_json_serializable(self):
        event = timeline_event(
            stream="world",
            kind="note",
            source="test",
            unit="iso8601",
            value="2026-09-28T16:00:00-07:00",
            payload={"text": "hello"},
        )
        json.dumps(event)


if __name__ == "__main__":
    unittest.main()
