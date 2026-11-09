"""Contract: SOFT RESET is served from the same localhost stage, separately."""
import http.client
import threading
import unittest
from http.server import ThreadingHTTPServer

from suzy_ai.music.magenta_stage import MagentaStageHandler
from suzy_ai.music.magenta_midi import MagentaMidiBridge
from tests.test_magenta_midi import FakeRtMidi


class FilmClubStageTests(unittest.TestCase):
    def setUp(self):
        class Handler(MagentaStageHandler):
            pass

        self.bridge = MagentaMidiBridge(FakeRtMidi())
        Handler.bridge = self.bridge
        Handler.token = "test-token"
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.bridge.close()

    def get(self, path):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        conn.request("GET", path)
        res = conn.getresponse()
        status, content_type, content = res.status, res.getheader("Content-Type"), res.read()
        conn.close()
        return status, content_type, content

    def test_song_and_local_assets_available_without_touching_pyramid(self):
        for path, mime, marker in [
            ("/film-club/soft-reset/", "text/html", b"SOFT RESET"),
            ("/film-club/soft-reset/score.js", "text/javascript", b"buildScore"),
            ("/film-club/soft-reset/audio.js", "text/javascript", b"schedulePrint"),
            ("/film-club/soft-reset/app.js", "text/javascript", b"humanTakes"),
            ("/film-club/soft-reset/style.css", "text/css", b".transport"),
        ]:
            with self.subTest(path=path):
                status, content_type, body = self.get(path)
                self.assertEqual(status, 200)
                self.assertIn(mime, content_type)
                self.assertIn(marker, body)
        status, _, original = self.get("/toaster/live")
        self.assertEqual(status, 200)
        self.assertIn(b"PYRAMID", original)

    def test_exact_asset_allowlist_blocks_path_traversal(self):
        for path in ["/film-club/soft-reset/../../README.md",
                     "/film-club/soft-reset/config.json",
                     "/film-club/soft-reset/score.js.map"]:
            self.assertEqual(self.get(path)[0], 404)


if __name__ == "__main__":
    unittest.main()
