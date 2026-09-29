import os
import tempfile
import unittest
from unittest.mock import patch

from suzy_ai.world import list_entities, list_teachings, teach


class WorldModelTests(unittest.TestCase):
    def test_exact_teaching_is_deduplicated(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"SUZY_AI_HOME": tmp}):
                first = teach(
                    entity_kind="album",
                    canonical="Björk::Homogenic",
                    name="Björk — Homogenic",
                    domain="music",
                    teaching_kind="album_review",
                    payload={"opinion": "volcanic and precise"},
                )
                second = teach(
                    entity_kind="album",
                    canonical="Björk::Homogenic",
                    name="Björk — Homogenic",
                    domain="music",
                    teaching_kind="album_review",
                    payload={"opinion": "volcanic and precise"},
                )
                self.assertFalse(first["duplicate"])
                self.assertTrue(second["duplicate"])
                self.assertEqual(len(list_entities("album")), 1)
                self.assertEqual(len(list_teachings(domain="music")), 1)

    def test_changed_opinion_is_history_not_duplicate_entity(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"SUZY_AI_HOME": tmp}):
                teach(
                    entity_kind="album",
                    canonical="Artist::Record",
                    name="Artist — Record",
                    domain="music",
                    teaching_kind="album_review",
                    payload={"opinion": "first reading"},
                )
                teach(
                    entity_kind="album",
                    canonical="artist::record",
                    name="Artist — Record",
                    domain="music",
                    teaching_kind="album_review",
                    payload={"opinion": "I changed my mind"},
                )
                self.assertEqual(len(list_entities("album")), 1)
                self.assertEqual(len(list_teachings(domain="music")), 2)

    def test_idiom_case_normalizes_to_one_entity(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"SUZY_AI_HOME": tmp}):
                teach(
                    entity_kind="idiom",
                    canonical="Hey Buds",
                    name="Hey Buds",
                    domain="language",
                    teaching_kind="idiom",
                    payload={"meaning": "friendly collective address"},
                )
                teach(
                    entity_kind="idiom",
                    canonical="hey buds",
                    name="hey buds",
                    domain="language",
                    teaching_kind="idiom",
                    payload={"meaning": "context changed slightly"},
                )
                self.assertEqual(len(list_entities("idiom")), 1)
                self.assertEqual(len(list_teachings(domain="language")), 2)


if __name__ == "__main__":
    unittest.main()
