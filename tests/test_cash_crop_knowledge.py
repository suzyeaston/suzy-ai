"""Source-attributed Canadian hip-hop knowledge without audio copying or network."""
import unittest

from suzy_ai.music.era_knowledge import PACKS, knowledge_brief


class CashCropKnowledgeTests(unittest.TestCase):
    def test_cash_crop_retrieves_vancouver_history_and_original_ideas(self):
        result=knowledge_brief("Rascalz Cash Crop Vancouver",limit=3)
        self.assertEqual(len(result),3)
        self.assertTrue(all(item["reference"]=="cash-crop-1997" for item in result))
        self.assertIn("vancouver-mc-pocket",{item["idea"] for item in result})
        self.assertTrue(all(item["source_url"].startswith("https://") for item in result))
        self.assertTrue(all("NOT a transcription" in item["note"] for item in result))

    def test_northern_touch_is_followon_not_original_album(self):
        pack=next(p for p in PACKS if p["id"]=="cash-crop-1997")
        self.assertIn("LATER",pack["historical_context"])
        self.assertIn("original 1997",pack["historical_context"])
        result=knowledge_brief("Northern Touch Vancouver Toronto collaboration")
        self.assertTrue(result)
        self.assertEqual(result[0]["reference"],"cash-crop-1997")
        self.assertTrue(any(entry["idea"]=="north-coast-call-response" for entry in result))

    def test_no_copying_music_in_reference_corpus(self):
        pack=next(p for p in PACKS if p["id"]=="cash-crop-1997")
        self.assertEqual(pack["year"],1997)
        self.assertEqual(len(pack["sources"]),3)
        self.assertEqual(len(pack["ideas"]),3)
        for item in pack["ideas"]:
            self.assertTrue(0 <= item["source_index"] < len(pack["sources"]))
            self.assertNotIn("audio",item)
            self.assertNotIn("melody",item)
            self.assertNotIn("transcription",item)
            self.assertLessEqual(len(item["action"]),210)


if __name__=="__main__":
    unittest.main()
