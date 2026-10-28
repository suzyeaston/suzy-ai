"""Native MRT2 guard tests: launching the stage opts in once, not each page refresh."""
from pathlib import Path
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from suzy_ai.music.magenta_native_host import NativeMagentaHost, PROMPTS, ACTIONS


class NativeMRT2Tests(unittest.TestCase):
    def setUp(self):
        self.host = NativeMagentaHost(binary=Path("/nonexistent/MRT2"))

    def tearDown(self):
        self.host.close()

    def test_native_does_not_start_while_browser_is_open(self):
        self.assertEqual(self.host.status()["phase"], "not-running")
        self.assertFalse(self.host.status()["model_audio_confirmed"])
        self.assertFalse(self.host.status()["build_available"])
        self.assertIsNone(self.host.process)
        self.assertIn("pyramid", PROMPTS)
        self.assertIn("fishes", PROMPTS)
        self.assertNotEqual(PROMPTS["pyramid"], PROMPTS["fishes"])

    def test_reject_invalid_controls_without_forking_model(self):
        invalid = [
            ("chord", {"index": True}), ("chord", {"index": 4}),
            ("scene", {"scene":"bad"}), ("mix", {"value":2}),
            ("mix", {"value":"0.3"}), ("volume", {"value":-1}),
            ("mute", {"value":1}), ("start", {"model":"remote"}),
            ("release", {"index":1}), ("other",{}),
            ("tempo", {"bpm": 240}), ("tempo", {"bpm": True}),
            ("note", {"note": -1}), ("note", {"note": 128}),
            ("note-off", {"note": "60"}),
        ]
        for cmd,data in invalid:
            with self.subTest(action=cmd, data=data), self.assertRaises(ValueError):
                self.host.command(cmd, data)
        self.assertIsNone(self.host.process)

    def test_start_is_only_user_initiated_and_requires_binary(self):
        with patch("suzy_ai.music.magenta_native_host.platform.system", return_value="Darwin"):
            with self.assertRaisesRegex(RuntimeError, "not built"):
                self.host.command("start", {})
        self.assertIsNone(self.host.process)

    def test_distinct_real_native_actions_have_explicit_schemas(self):
        for op in ("start", "stop", "status", "scene", "mix", "volume", "mute", "chord", "release", "tempo", "note", "note-off"):
            self.assertIn(op, ACTIONS)
        self.assertEqual(ACTIONS["chord"], {"index"})
        self.assertEqual(ACTIONS["scene"], {"scene"})
        self.assertEqual(ACTIONS["show-au-ui"], set())
        self.assertEqual(ACTIONS["mute"], {"value"})
        self.assertEqual(ACTIONS["tempo"], {"bpm"})
        self.assertEqual(ACTIONS["note"], {"note"})

        self.assertEqual(ACTIONS["configure-prompts"], {"prompts"})

    def test_app_launch_starts_one_worker_and_reports_progress(self):
        with patch("suzy_ai.music.magenta_native_host.Thread") as thread:
            self.host.launch_async()
            self.host.launch_async()
            thread.assert_called_once()
            self.assertEqual(self.host.status()["phase"], "starting")
            self.assertFalse(self.host.status()["model_audio_confirmed"])
            self.assertIsNone(self.host.process)

    def test_failed_native_host_reports_error_without_faking_audio(self):
        self.host.launch_error = "MRT2 Small model missing"
        self.assertEqual(self.host.status()["phase"], "failed")
        self.assertIn("missing", self.host.status()["error"])
        self.assertFalse(self.host.status()["model_audio_confirmed"])

    def test_registered_mrt2_au_component_codes_match_official_manifest(self):
        # Google's current MRT2_AU.appex Info.plist registers MGR2, not
        # the older MGRT constant used in the implementation source.
        # Do not regress to looking only for an unregistered subtype.
        root = Path(__file__).resolve().parents[1]
        swift = (root / "apps/toaster-magenta/ToasterMagentaHost.swift").read_text()
        self.assertIn("0x4D475232", swift)  # MGR2, current AUv3
        self.assertIn("0x4D475254", swift)  # MGRT, legacy fallback
        self.assertIn("components(matching: googleMusicDevice)", swift)
        self.assertIn("currentMRT2", swift)
        self.assertIn("legacyMRT2", swift)

    def test_native_transport_is_moving_or_google_au_writes_silence(self):
        # Google's MRT2 render block requires UI play OR moving DAW transport.
        # A running AVAudioEngine alone is insufficient to hear the generator.
        source = (Path(__file__).resolve().parents[1]
                  / "apps/toaster-magenta/ToasterMagentaHost.swift").read_text()
        self.assertIn("unit.auAudioUnit.transportStateBlock =", source)
        self.assertIn("flags?.pointee = self.transportPlaying.load(ordering: .relaxed) ? .moving : []", source)
        self.assertIn("samplePosition?.pointee = seconds * 48000.0", source)
        self.assertIn('"transport_context_supplied": hostTransportSupplied', source)
        self.assertIn('"transport_moving":', source)
        self.assertLess(
            source.index("unit.auAudioUnit.transportStateBlock ="),
            source.index("try audio.start()"),
            "The AU must receive transport before render resources are started",
        )

    def test_native_transport_play_pause_is_lock_free_and_real(self):
        source = (Path(__file__).resolve().parents[1]
                  / "apps/toaster-magenta/ToasterMagentaHost.swift").read_text()
        self.assertIn("import Synchronization", source)
        self.assertIn("Atomic<Bool>", source)
        self.assertIn('SUZY_MRT2_TRANSPORT_AUTOPLAY', source)
        self.assertIn('case "transport-play":', source)
        self.assertIn('case "transport-pause":', source)
        self.assertIn('transportPlaying.store(false, ordering: .relaxed)', source)
        self.assertIn('"transport_playing"', source)
        self.assertIn('"native_loop_capture_supported": false', source)
        from suzy_ai.music.magenta_native_host import ACTIONS
        self.assertEqual(ACTIONS["transport-play"], frozenset())
        self.assertEqual(ACTIONS["transport-pause"], frozenset())

    def test_gate_off_diagnostic_defaults_to_existing_behavior(self):
        source = (Path(__file__).resolve().parents[1]
                  / "apps/toaster-magenta/ToasterMagentaHost.swift").read_text()
        self.assertIn('ProcessInfo.processInfo.environment["SUZY_MRT2_MIDI_GATE"] != "0"', source)
        self.assertIn('parameter(45, midiGateEnabled ? 1.0 : 0.0)', source)
        self.assertIn('"midi_gate_parameter_readback"', source)
        self.assertIn('"midi_gate_enabled"', source)

    def test_native_browser_chords_are_held_long_enough_for_neural_control(self):
        # A rapid mouse tap used to send an immediate note-off after a note-on,
        # unlike playing Google's on-screen AU keyboard. The AU responds to
        # frame-level pitch activity, so give short clicks time to be audible.
        source = (Path(__file__).resolve().parents[1]
                  / "apps/toaster-magenta/ToasterMagentaHost.swift").read_text()
        self.assertIn('SUZY_MRT2_CHORD_HOLD_MS', source)
        self.assertIn('Double(ProcessInfo.processInfo.environment', source)
        self.assertIn('?? 480', source)
        self.assertIn('private var pendingChordRelease: DispatchWorkItem?', source)
        self.assertIn('chordStartedAt = ProcessInfo.processInfo.systemUptime', source)
        self.assertIn('let remaining = max(0, minimumChordHoldSeconds - elapsed)', source)
        self.assertIn('DispatchQueue.main.asyncAfter(deadline: .now() + remaining, execute: work)', source)
        self.assertIn('case "release":\n            releaseChordAfterMinimumHold()', source)
        self.assertIn('private func cancelPendingChordRelease()', source)
        self.assertIn('pendingChordRelease?.cancel()', source)
        self.assertIn('case "chord":', source)
        self.assertLess(source.index('            noteOff()\n            held = notes[i]'),
                        source.index('            chordStartedAt = ProcessInfo.processInfo.systemUptime'))
        self.assertIn('"chord_min_hold_ms": Int(minimumChordHoldSeconds * 1000)', source)
        self.assertIn('"chord_release_pending": pendingChordRelease != nil', source)

    def test_reselecting_same_native_scene_does_not_cancel_current_notes(self):
        source = (Path(__file__).resolve().parents[1]
                  / "apps/toaster-magenta/ToasterMagentaHost.swift").read_text()
        start = source.index('        case "scene":')
        end = source.index('        case "mix":', start)
        scene = source[start:end]
        self.assertIn('if x != scene {', scene)
        self.assertIn('allNotesOff()', scene)
        self.assertLess(scene.index('if x != scene {'), scene.index('allNotesOff()'))
        self.assertNotIn('allNotesOff();scene = x;', scene)

    def test_implicit_cross_process_bookmark_is_explicitly_opt_in(self):
        source = (Path(__file__).resolve().parents[1]
                  / "apps/toaster-magenta/ToasterMagentaHost.swift").read_text()
        self.assertIn('SUZY_MRT2_BOOKMARK_MODE', source)
        self.assertIn('"implicit_cross_process"', source)
        self.assertIn('"explicit_app_scoped"', source)
        self.assertIn('options: implicit ? [] : [.withSecurityScope]', source)
        self.assertIn('"bookmark_self_resolution_verified"', source)
        self.assertIn('"bookmark_recipient_verified": false', source)
        # The diagnostic must not present a host-side self-check as
        # successful MLX initialization inside Google's AUv3 extension.
        self.assertIn('self.bookmarkScopeVerified = false', source)

    def test_google_custom_view_api_imports_and_links_coreaudiokit(self):
        root = Path(__file__).resolve().parents[1]
        swift = (root / "apps/toaster-magenta/ToasterMagentaHost.swift").read_text()
        build = (root / "scripts/build-toaster-magenta.sh").read_text()
        self.assertIn("import CoreAudioKit", swift)
        self.assertIn("-framework CoreAudioKit", build)
        self.assertIn("unit.auAudioUnit.requestViewController", swift)

    def test_google_native_picker_avoids_cross_identity_bookmark(self):
        source = (Path(__file__).resolve().parents[1]
                  / "apps/toaster-magenta/ToasterMagentaHost.swift").read_text()
        self.assertIn('SUZY_MRT2_MODEL_VIA_UI', source)
        self.assertIn('state.removeValue(forKey: "MGRT_ModelBookmark")', source)
        self.assertIn('state.removeValue(forKey: "MGRT_ModelName")', source)
        self.assertIn('unit.auAudioUnit.requestViewController', source)
        self.assertIn('case "show-au-ui": showGoogleAUInterface()', source)
        self.assertIn('app.run()', source)
        self.assertIn('"native_model_selection_required"', source)
        self.assertIn('"native_au_ui_visible"', source)

    def test_google_picker_action_requires_existing_native_process(self):
        with self.assertRaisesRegex(RuntimeError, "not running"):
            self.host.command("show-au-ui", {})
        # The action cannot start or fork a second native model.
        self.assertIsNone(self.host.process)

    def test_model_selector_reports_real_state_and_rejects_bookmark_mode(self):
        swift = (Path(__file__).resolve().parents[1]
                 / "apps/toaster-magenta/ToasterMagentaHost.swift").read_text()
        self.assertIn('"native_au_ui_error"', swift)
        self.assertIn('"native_au_ui_request_count"', swift)
        self.assertIn('guard selectModelInGoogleUI else', swift)
        self.assertIn('auUIRequestCount += 1', swift)
        self.assertIn('self.auUIError = "Google MRT2 AU did not return', swift)

    def test_four_native_au_prompt_slots_and_live_weights(self):
        from suzy_ai.music.magenta_native_host import PROMPTS, ACTIONS
        self.assertEqual(list(PROMPTS), [
            "pyramid", "fishes", "pyramid_violin", "fishes_guitar",
        ])
        self.assertEqual(ACTIONS["lead-mix"], {"scene", "value"})
        self.assertIn("violin", PROMPTS["pyramid_violin"])
        self.assertIn("nylon", PROMPTS["fishes_guitar"])
        swift = (Path(__file__).resolve().parents[1]
                 / "apps/toaster-magenta/ToasterMagentaHost.swift").read_text()
        self.assertIn('list.count == 4', swift)
        self.assertIn('state["MGRT_Prompts"] = weighted + (0..<2)', swift)
        for address in range(10, 16):
            self.assertIn(f'parameter({address},', swift)
        self.assertIn('case "lead-mix":', swift)
        self.assertIn('leadMix[which] = Float(x);configure()', swift)
        self.assertIn('"prompt_slot_count": prompts.count', swift)
        self.assertIn('"prompt_weights": (10...13).map', swift)
        # Original primary prompt wording is intentionally unchanged.
        self.assertIn(PROMPTS["pyramid"], swift)
        self.assertIn(PROMPTS["fishes"], swift)

    def test_lead_mix_requires_valid_scene_and_normalized_amount(self):
        for bad in (
            {"scene":"pyramid","value":-1},
            {"scene":"fishes","value":1.1},
            {"scene":"bad","value":0.3},
            {"scene":"pyramid","value":"0.5"},
            {"scene":"pyramid","value":True},
        ):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.host.command("lead-mix", bad)
        self.assertIsNone(self.host.process)

    def test_native_prompt_validation(self):
        bad = [
            {"prompts": ["", "nice"]},
            {"prompts": ["a" * 501, "nice"]},
            {"prompts": ["nice", 12]},
            {"prompts": "nice"},
        ]
        for data in bad:
            with self.subTest(data=data), self.assertRaises(ValueError):
                self.host.command("configure-prompts", data)


    def test_updates_native_binary_when_swift_source_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            binary = root / ".build" / "toaster-magenta-host"
            binary.parent.mkdir(parents=True)
            binary.write_text("old")
            source = root / "apps" / "toaster-magenta" / "ToasterMagentaHost.swift"
            source.parent.mkdir(parents=True)
            source.write_text("new")
            os.utime(binary, (1000, 1000))
            os.utime(source, (2000, 2000))
            host = NativeMagentaHost(binary=binary)
            completed = MagicMock()
            completed.returncode = 0
            completed.stdout = ""
            completed.stderr = ""
            with patch("suzy_ai.music.magenta_native_host.ROOT", root), \
                 patch("suzy_ai.music.magenta_native_host.EXECUTABLE", binary), \
                 patch("suzy_ai.music.magenta_native_host.platform.system", return_value="Darwin"), \
                 patch("suzy_ai.music.magenta_native_host.subprocess.run", return_value=completed) as build, \
                 patch.object(host, "_register_installed_au", return_value=None), \
                 patch.object(host, "_start"), \
                 patch.object(host, "_request", return_value={"phase": "host-running"}):
                host._launch_worker()
                build.assert_called_once()
                self.assertFalse(host.launching)
                self.assertEqual(host.launch_error, "")

    def test_registers_existing_official_au_extension_only(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            app = folder / "MRT2 (AU).app"
            extension = app / "Contents" / "PlugIns" / "MRT2_AU.appex"
            extension.mkdir(parents=True)
            result = MagicMock(returncode=0, stderr="", stdout="")
            with patch("suzy_ai.music.magenta_native_host.subprocess.run", return_value=result) as cmd:
                registered = self.host._register_installed_au(app_paths=[app])
            self.assertEqual(registered, str(app))
            cmd.assert_called_once()
            self.assertEqual(cmd.call_args.args[0], ["pluginkit", "-a", str(extension)])

    def test_does_not_mistake_jam_or_collider_for_audio_unit(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ["MRT2 - Jam.app", "MRT2 - Collider.app"]:
                (root / name).mkdir()
            with patch("suzy_ai.music.magenta_native_host.subprocess.run") as run:
                found = self.host._register_installed_au(
                    app_paths=[root / "MRT2 - Jam.app", root / "MRT2 - Collider.app"]
                )
            self.assertIsNone(found)
            run.assert_not_called()

    def test_registration_failure_gives_repair_path_without_bypassing_it(self):
        with tempfile.TemporaryDirectory() as temp:
            app = Path(temp) / "MRT2 (AU).app"
            (app / "Contents/PlugIns/MRT2_AU.appex").mkdir(parents=True)
            result = MagicMock(returncode=1, stderr="denied", stdout="")
            with patch("suzy_ai.music.magenta_native_host.subprocess.run", return_value=result):
                with self.assertRaisesRegex(RuntimeError, "Open MRT2"):
                    self.host._register_installed_au(app_paths=[app])


if __name__ == "__main__":
    unittest.main()
