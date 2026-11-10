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
        self.assertIn('id="filmControlBar"', self.film)
        self.assertEqual(
            PLAY_PAGE.read_text(encoding="utf8"), self.source,
            "Original Futureproof page must never be modified by rendering"
        )

    def test_oversized_screenshot_sections_are_gone_but_audio_stays_available(self):
        # No giant composition, audition, cue-card or expanded recording
        # surface. The original recorder is still accessible on demand.
        self.assertIn('id="filmControlBar"', self.film)
        self.assertIn('id="filmInstrumentTools"', self.film)
        self.assertIn('id="filmCueTools"', self.film)
        self.assertIn('id="filmRecordStudio"', self.film)
        self.assertNotIn('id="filmRecordStudio" open', self.film)
        self.assertNotIn('id="filmClubCues"', self.film)
        self.assertNotIn('id="filmAuditionPanel"', self.film)
        self.assertNotIn('class="film-cue-grid"', self.film)
        self.assertNotIn('class="film-recorder-spotlight"', self.film)
        self.assertNotIn('FILM CLUB · PYRAMID AFTERIMAGE · COMPOSITION MODE', self.film)
        self.assertNotIn('🔴 FILM CLUB RECORDING', self.film)
        for id_ in ('setRecordStart', 'setRecordStop', 'setRecordMic',
                    'setRecordStatus'):
            self.assertEqual(self.film.count(f'id="{id_}"'), 1)
            self.assertEqual(self.source.count(f'id="{id_}"'), 1)
        self.assertLess(self.film.index('</header>'),
                        self.film.index('id="filmControlBar"'))
        self.assertLess(self.film.index('id="filmRecordStudio"'),
                        self.film.index('id="rhythm"'))
        self.assertIn('async function startSetRecording()', self.film)
        self.assertIn('function stopSetRecording()', self.film)
        self.assertIn('<details class="advanced-session"><summary>',
                      self.source)
        self.assertNotIn('id="filmRecordStudio"', self.source)

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
        self.assertIn('data-chord="3"><kbd>V</kbd><b>E</b>', self.film)
        self.assertIn("FILM CLUB: Z X C V", self.film)
        self.assertIn("Em → E7 → Am → E", self.film)
        self.assertIn("PYRAMID / ACCELERANDO · THE LIVING LOOP", self.film)
        self.assertIn('data-chord="1"><kbd>X</kbd><b>E7</b>', self.film)
        self.assertIn('pyramid:["Z","X","C","V"]', self.film)
        self.assertIn('KeyV:"v"', self.film)
        self.assertIn('harmony==="pyramid"?"accelerando":harmony', self.film)
        self.assertIn('harmony:which==="pyramid"?"accelerando":"fishes"', self.film)
        self.assertIn('names:["Em","E7","Am","E"]', self.film)
        self.assertIn('notes:[[52,55,59,64],[52,56,59,62],[57,60,64,69],[52,56,59,64]]', self.film)
        self.assertIn('names:["F♯","Gmaj7","A6","F♯"]', self.source)
        self.assertNotIn('KeyV:"v"', self.source)
        self.assertIn("FILM CLUB · PYRAMID / SOFT RESET", self.film)
        self.assertIn("never stopped by this control", self.film)
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
        self.assertIn("acoustic jazz grand piano", piano)
        self.assertIn("felt-hammer", piano)
        self.assertIn("bouncing eighth-note ostinatos", piano)
        self.assertIn("offbeat eighths", cello)
        self.assertIn("two-bar 3+3+2 cello ostinato", cello)
        self.assertIn("sixteenth-note replies", violin)
        self.assertIn("syncopated ostinatos", glass)
        self.assertIn("Bouncy urgency", drums)
        self.assertIn('value="58" aria-label="Main electro pulse density"', self.film)
        self.assertIn('for="filmGrooveEnergy">58%</output>', self.film)
        self.assertIn('value="62" aria-label="Layered syncopated counter-rhythm volume"', self.film)
        self.assertIn('for="filmCounterRhythm">62%</output>', self.film)
        self.assertIn("BRIGHTER GROOVE:", self.film)
        self.assertIn("Em, E7, Am, E", piano)
        self.assertIn("100 BPM", piano)
        self.assertIn("cello", cello)
        self.assertIn("harmonium", cello)
        self.assertIn("warm E2 and A2", cello)
        self.assertIn("3+3+2", drums)
        self.assertIn("100 BPM", drums)
        self.assertIn("half-time", drums)
        self.assertIn("long legato", violin)
        self.assertIn("granular", glass)
        self.assertIn('id="filmCounterRhythm"', self.film)
        self.assertIn('id="filmCounterReadout"', self.film)
        self.assertIn('id="filmGrooveEnergy"', self.film)
        self.assertIn('id="filmNoteHold"', self.film)
        self.assertIn('id="filmAuditionStatus"', self.film)
        self.assertIn('id="filmAuditionBlend"', self.film)
        self.assertIn('data-film-audition="cello"', self.film)
        self.assertIn('id="filmNoteHoldValue"', self.film)
        self.assertNotIn('id="filmNoteHold"', self.source)
        self.assertNotIn('id="filmCounterRhythm"', self.source)
        self.assertIn('value="house">Electro house · four-on-the-floor',
                      self.film)
        self.assertEqual(len(set(FILM_PROMPTS)), 5)
        # Don't ship song audio or change the original five prompt defaults.
        self.assertNotIn("<audio", self.film)
        for original in ORIGINAL_PROMPTS:
            self.assertNotIn(f">{original}</textarea>", self.film)
        self.assertIn('data-chord="3"><kbd>V</kbd><b>E</b>', self.film)
        self.assertIn('data-chord="1"><kbd>X</kbd><b>E7</b>', self.film)
        self.assertIn('pyramid:["Z","X","C","V"]', self.film)
        self.assertIn('KeyV:"v"', self.film)
        self.assertIn('harmony==="pyramid"?"accelerando":harmony', self.film)
        self.assertIn('harmony:which==="pyramid"?"accelerando":"fishes"', self.film)
        self.assertIn('names:["Em","E7","Am","E"]', self.film)
        self.assertIn('notes:[[52,55,59,64],[52,56,59,62],[57,60,64,69],[52,56,59,64]]', self.film)
        self.assertIn('names:["F♯","Gmaj7","A6","F♯"]', self.source)
        self.assertNotIn('KeyV:"v"', self.source)

    def test_native_google_prompt_bank_not_claimed_loaded_without_apply(self):
        # An HTML textarea is NOT the Google AU prompt bank. Show an
        # explicit control and honest verification status on the Film page.
        self.assertIn('id="filmSyncNativePrompts"', self.film)
        self.assertIn('id="filmNativePromptStatus"', self.film)
        self.assertIn('UPDATE FILM CLUB SOUNDS SAFELY', self.film)
        self.assertIn('id="filmOpenGooglePrompts"', self.film)
        self.assertIn('id="filmGoogleEditorStatus"', self.film)
        self.assertIn('NO RESTART', self.film)
        self.assertNotIn('↻ APPLY FILM CLUB SOUNDS TO MRT2', self.film)
        self.assertIn('CHECKING NATIVE HOST', self.film)
        self.assertIn('never stopped by this control', self.film)
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
        self.assertEqual(
            self.film.count('<script src="/film-club/soft-reset/audition.js" defer>'), 1
        )
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
