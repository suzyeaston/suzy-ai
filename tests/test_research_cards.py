"""Offline provenance / opt-in tests for report-derived musical research."""
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from suzy_ai.music.research_cards import CARDS, research_brief, validate_cards
from suzy_ai.music.qwen_composer import CompositionError, LocalQwenComposer


def phrase():
    return {"status": "monophonic_candidate", "bpm_supplied": 100,
            "duration_seconds": 4,
            "notes": [
                {"midi_note": 60, "confidence": .99, "start_beats": 0},
                {"midi_note": 64, "confidence": .99, "start_beats": 1.5},
                {"midi_note": 67, "confidence": .99, "start_beats": 3},
            ]}


class EvidenceCardsTests(unittest.TestCase):
    def test_all_six_album_sets_and_real_provenance(self):
        validate_cards()
        self.assertEqual(len(CARDS), 12)
        query_map = (
            ("Illmatic Nas Queensbridge", "illmatic-1994"),
            ("Baduizm Erykah vocal", "baduizm-1997"),
            ("Low End Theory Tribe bass", "low-end-theory-1991"),
            ("Brown Sugar Dangelo keys", "brown-sugar-1995"),
            ("Miseducation Lauryn Hill", "miseducation-1998"),
            ("Rascalz Cash Crop Vancouver", "cash-crop-1997"),
        )
        for query, album in query_map:
            with self.subTest(album=album):
                result = research_brief(query)
                self.assertTrue(result)
                self.assertEqual(result[0]["reference_album"], album)
                self.assertIn("https://", result[0]["source_url"])
                self.assertTrue(result[0]["source_supports"])
                self.assertIn("NOT album transcription", result[0]["note"])

    def test_absent_evidence_is_not_invented_and_output_is_small(self):
        self.assertEqual(research_brief("galacticquasarbeats"), [])
        self.assertEqual(research_brief(""), [])
        result = research_brief("Illmatic boom bap", limit=2)
        self.assertLessEqual(len(result), 2)
        self.assertTrue(all(len(v["proposed_action"]) <= 200 for v in result))
        for card in CARDS:
            self.assertEqual(set(card["source"]), {"author", "title", "date", "kind", "url"})
            self.assertTrue(card["uncertainty"])
            self.assertTrue(card["controls"])
            self.assertTrue(card["hypothetical"])
            self.assertNotIn("audio", card)
            self.assertNotIn("melody", card)
            self.assertNotIn("lyrics", card)

    def test_fails_without_attribution_or_duplicate_cards(self):
        with self.assertRaises(ValueError):
            validate_cards((CARDS[0], CARDS[0]))
        missing_src = dict(CARDS[0], source={"title": "Unattributed"})
        with self.assertRaises(ValueError):
            research_brief("illmatic", catalog=(missing_src,))
        for limit in (0, 4, True, "2", 1.5):
            with self.assertRaises(ValueError):
                research_brief("illmatic", limit=limit)

    def test_chronology_is_explicitly_not_conflated(self):
        b = next(c for c in CARDS if c["id"] == "baduizm-1997-philly-boundary")
        self.assertIn("Mama's Gun", b["historical_claim"])
        self.assertIn("2000", b["historical_claim"])
        d = next(c for c in CARDS if c["id"] == "brown-sugar-1995-keys-core")
        self.assertIn("Voodoo", d["uncertainty"])
        self.assertTrue(any(c["album"] == "cash-crop-1997" for c in CARDS))


class QwenResearchWiringTests(unittest.TestCase):
    def test_optin_only_and_generated_citation_must_match_retrieval(self):
        requests = []
        ref = research_brief("Illmatic Queensbridge", limit=2)[0]["reference"]

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_POST(self):
                payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                requests.append(payload)
                data = json.dumps({"model": "fake-local-test",
                    "message": {"role": "assistant", "content": json.dumps({
                        "notes": [[0.5, 69, 0.3, 66], [2.5, 62, 0.5, 60]],
                        "used_reference": ref if "source_supports" in payload["message"] else None,
                    })}}).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            composer = LocalQwenComposer(f"http://127.0.0.1:{server.server_address[1]}/v1", timeout=1.0)
            plain = composer(phrase(), instruction="Illmatic Queensbridge")
            self.assertEqual(plain["references_offered"], [])
            self.assertIsNone(plain["reference_used"])
            grounded = composer(phrase(), instruction="Illmatic Queensbridge", use_deep_research=True)
            self.assertEqual(grounded["reference_used"], ref)
            self.assertIn(ref, grounded["references_offered"])
            self.assertEqual(requests[0]["use_memory"], False)
            self.assertEqual(requests[1]["history"], [])
            self.assertNotIn("source_supports", requests[0]["message"])
            self.assertIn("source_supports", requests[1]["message"])
            self.assertIn("NOT album transcription", requests[1]["message"])
            self.assertLess(len(requests[1]["message"]), 6500)
            with self.assertRaises(CompositionError):
                composer(phrase(), instruction="Illmatic", use_deep_research=True,
                         use_era_knowledge=True)
            self.assertEqual(len(requests), 2)
        finally:
            server.shutdown(); server.server_close(); thread.join()


if __name__ == "__main__":
    unittest.main()
