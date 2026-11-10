"""Film Club must keep the authentic Pyramid loop engine and override view text only."""
from pathlib import Path
import re
import unittest

from suzy_ai.music.film_club_pyramid import (
    FILM_PROMPTS, PROMPT_IDS, ORIGINAL_PROMPTS, render_film_club_page
)
from suzy_ai.music.magenta_stage import PLAY_PAGE


class FilmClubPyramidTests(unittest.TestCase):
    def setUp(self):
        self.source = PLAY_PAGE.read_text(encoding="utf8")
        self.film = render_film_club_page(self.source, "test-stage-token")

    def test_original_source_and_existing_performance_controls_preserved(self):
        ids = set(re.findall(r'id="([^"]+)"', self.source))
        film_ids = set(re.findall(r'id="([^"]+)"', self.film))
        self.assertTrue(ids <= film_ids, sorted(ids - film_ids))
        for control in (
            "rhythm", "pedalClock", "nativeMemoryLoop", "silenceAllLoops",
            "nativeRecord-pyramid-chords", "nativeRecord-pyramid-lead",
            "nativeRecord-pyramid-textureLow", "nativeRecord-pyramid-textureHigh",
            "nativeRecord-drums-drums", "loopToggle-pyramid",
            "record-pyramid", "overdubAudio-pyramid", "vocalRecordPyramid",
            "savePyramidLoop", "setRecordStart", "setRecordStop", "aiEnable"
        ):
            self.assertIn(f'id="{control}"', self.film)
        for source in (
            "/toaster/arrangement.js",
            "/toaster/performance-timeline.js",
            "/toaster/track-view.js"
        ):
            self.assertIn(f'<script src="{source}">', self.film)
        self.assertIn("function startNativeInstrumentTake", self.film)
        self.assertIn("function toggleNativeSavedLoop", self.film)
        self.assertIn("function startAudioPrint", self.film)
        self.assertIn("function voiceLoop", self.film)
        self.assertIn("function emergencySilenceAllLoops", self.film)
        self.assertIn('id="filmClubCues"', self.film)
        self.assertEqual(
            PLAY_PAGE.read_text(encoding="utf8"), self.source,
            "Original Futureproof page must never be modified by rendering"
        )

    def test_five_different_prompts_are_only_in_film_view(self):
        self.assertEqual(len(PROMPT_IDS), 5)
        self.assertEqual(len(FILM_PROMPTS), 5)
        self.assertEqual(len(ORIGINAL_PROMPTS), 5)
        for id_, film_prompt, original_prompt in zip(
            PROMPT_IDS, FILM_PROMPTS, ORIGINAL_PROMPTS
        ):
            self.assertNotEqual(film_prompt, original_prompt)
            self.assertLessEqual(len(film_prompt), 500)
            self.assertIn(f'id="{id_}" maxlength="500">{film_prompt}</textarea>', self.film)
            self.assertNotIn(film_prompt + "</textarea>", self.source)
        self.assertIn("F♯", self.film)
        self.assertIn("Gmaj7", self.film)
        self.assertIn("A6", self.film)
        self.assertIn("FILM CLUB · PYRAMID / SOFT RESET", self.film)
        self.assertIn("shared Mac model", self.film)
        self.assertIn("restart", self.film.lower())

    def test_livelier_film_prompts_and_groove_control_preserve_pyramid_harmony(self):
        self.assertIn('id="filmGrooveEnergy"', self.film)
        self.assertIn('id="filmGrooveReadout"', self.film)
        for option in (
            'value="drive">Propulsive electronica / breaks',
            'value="frame">Frame-drum electro / syncopated',
        ):
            self.assertIn(option, self.film)
        piano, cello, violin, glass, drums = FILM_PROMPTS
        self.assertIn("syncopated", piano)
        self.assertIn("arpeggios", piano)
        self.assertIn("offbeat", cello)
        self.assertIn("modal", violin)
        self.assertIn("16th-note", glass)
        self.assertIn("breakbeat", drums)
        self.assertIn("hand-drum", drums)
        self.assertEqual(len(set(FILM_PROMPTS)), 5)
        # Don't ship song audio or change the original five prompt defaults.
        self.assertNotIn("<audio", self.film)
        for original in ORIGINAL_PROMPTS:
            self.assertNotIn(f">{original}</textarea>", self.film)
        self.assertIn("F♯", self.film)
        self.assertIn("Gmaj7", self.film)
        self.assertIn("A6", self.film)

    def test_native_google_prompt_bank_not_claimed_loaded_without_apply(self):
        # An HTML textarea is NOT the Google AU prompt bank. Show an
        # explicit control and honest verification status on the Film page.
        self.assertIn('id="filmSyncNativePrompts"', self.film)
        self.assertIn('id="filmNativePromptStatus"', self.film)
        self.assertIn('APPLY FILM CLUB SOUNDS TO MRT2', self.film)
        self.assertIn('NATIVE PROMPT BANK NOT YET VERIFIED', self.film)
        self.assertIn('shared Magenta generator', self.film)
        self.assertIn('id="filmManualBridge"', self.film)
        self.assertIn('id="filmCopyStatus"', self.film)
        self.assertEqual(self.film.count('data-prompt-copy='), 5)
        self.assertIn("Google's native Audio Unit window", self.film)
        self.assertNotIn('id="filmManualBridge"', self.source)
        self.assertNotIn('id="filmSyncNativePrompts"', self.source)

    def test_tokens_and_csp_sensitive_local_scripts(self):
        self.assertNotIn("__MAGENTA_TOKEN__", self.film)
        self.assertIn('const token="test-stage-token"', self.film)
        self.assertEqual(
            self.film.count('<script src="/film-club/soft-reset/film-club.js" defer>'), 1
        )
        self.assertNotIn('<script src="https:', self.film)
        self.assertIn('id="filmExportCues"', self.film)

    def test_missing_anchor_fails_closed_instead_of_weak_partial_view(self):
        with self.assertRaisesRegex(ValueError, "prompt"):
            render_film_club_page(
                self.source.replace('id="promptPyramid"', 'id="renamed"'),
                "token"
            )
        with self.assertRaisesRegex(ValueError, "anchor"):
            render_film_club_page(self.source.replace("</header>", ""), "token")


if __name__ == "__main__":
    unittest.main()
