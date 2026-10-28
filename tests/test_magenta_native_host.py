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
        self.assertIn("flags?.pointee = .moving", source)
        self.assertIn("samplePosition?.pointee = seconds * 48000.0", source)
        self.assertIn('"transport_context_supplied": hostTransportSupplied', source)
        self.assertIn('"transport_moving":', source)
        self.assertLess(
            source.index("unit.auAudioUnit.transportStateBlock ="),
            source.index("try audio.start()"),
            "The AU must receive transport before render resources are started",
        )

    def test_gate_off_diagnostic_defaults_to_existing_behavior(self):
        source = (Path(__file__).resolve().parents[1]
                  / "apps/toaster-magenta/ToasterMagentaHost.swift").read_text()
        self.assertIn('ProcessInfo.processInfo.environment["SUZY_MRT2_MIDI_GATE"] != "0"', source)
        self.assertIn('parameter(45, midiGateEnabled ? 1.0 : 0.0)', source)
        self.assertIn('"midi_gate_parameter_readback"', source)
        self.assertIn('"midi_gate_enabled"', source)

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
