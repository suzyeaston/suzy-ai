"""Offline contract for citation-backed, opt-in 1990s musical reference cards."""
import unittest

from suzy_ai.music.era_knowledge import PACKS, knowledge_brief


class EraKnowledgeTests(unittest.TestCase):
    def test_named_references_retrieve_distinct_musical_actions(self):
        for query, expected in [
            ("Illmatic Nas boom bap", "illmatic-1994"),
            ("Baduizm Erykah R&B singing", "baduizm-1997"),
            ("A Tribe Called Quest low end theory bass", "low-end-theory-1991"),
            ("D'Angelo Brown Sugar keyboard", "brown-sugar-1995"),
            ("Lauryn Hill Miseducation vocals", "miseducation-1998"),
        ]:
            with self.subTest(query=query):
                result=knowledge_brief(query)
                self.assertTrue(result)
                self.assertEqual(result[0]["reference"], expected)
                self.assertTrue(result[0]["source_url"].startswith("https://"))
                self.assertNotEqual(result[0]["cue"], result[0]["proposed_action"])
                self.assertIn("NOT a transcription", result[0]["note"])

    def test_unknown_topic_does_not_fabricate_reference(self):
        self.assertEqual(knowledge_brief("unrelatedquasar"), [])

    def test_small_bounded_context_and_no_copyrighted_media(self):
        result=knowledge_brief("hip hop jazz rnb vocals", limit=3)
        self.assertLessEqual(len(result),3)
        self.assertGreater(len(result),0)
        self.assertTrue(all("source_label" in v and "source_url" in v for v in result))
        self.assertTrue(all(len(v["proposed_action"]) <= 210 for v in result))
        for pack in PACKS:
            self.assertEqual(set(pack), {"id","title","year","historical_context","sources","ideas"})
            for src in pack["sources"]:
                self.assertEqual(set(src), {"label","url"})
                self.assertTrue(src["url"].startswith("https://"))
            for idea in pack["ideas"]:
                self.assertTrue(0 <= idea["source_index"] < len(pack["sources"]))

    def test_reject_invalid_request(self):
        for arg in (None, [], "a" * 501):
            with self.assertRaises(ValueError): knowledge_brief(arg)
        for arg in (0, 6, True, 1.5, "3"):
            with self.assertRaises(ValueError): knowledge_brief("jazz",limit=arg)

    def test_unattributed_musical_reference_is_rejected(self):
        invalid = {**PACKS[0], "ideas": ({
            **PACKS[0]["ideas"][0], "source_index": 99
        },)}
        with self.assertRaises(ValueError):
            knowledge_brief("Illmatic",catalog=(invalid,))


if __name__=="__main__":
    unittest.main()
