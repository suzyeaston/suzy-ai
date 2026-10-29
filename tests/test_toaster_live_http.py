"""HTTP tests: guarded TOASTER computer-keyboard endpoints and honest state."""
import http.client
import json
import threading
import unittest
from http.server import ThreadingHTTPServer

from suzy_ai.music.magenta_stage import MagentaStageHandler
from suzy_ai.music.magenta_midi import MagentaMidiBridge
from suzy_ai.music.toaster_performance import ToasterPerformance
from tests.test_magenta_midi import FakeRtMidi


class LiveToasterHttpTests(unittest.TestCase):
    def setUp(self):
        class Handler(MagentaStageHandler):
            pass
        self.bridge = MagentaMidiBridge(FakeRtMidi())
        self.perf = ToasterPerformance(self.bridge)
        Handler.bridge = self.bridge
        Handler.performance = self.perf
        Handler.token = "test-live-token"
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.perf.close()
        self.bridge.close()

    def call(self, method, route, body=None, token=True, origin=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        headers = {}
        if method == "POST":
            headers["Content-Type"] = "application/json"
            if token:
                headers["X-Suzy-Token"] = "test-live-token"
            if origin:
                headers["Origin"] = origin
        conn.request(method, route, json.dumps(body if body is not None else {}) if method == "POST" else None, headers)
        r = conn.getresponse()
        raw = r.read()
        status = r.status
        conn.close()
        if raw.startswith(b"{"):
            return status, json.loads(raw)
        return status, raw.decode("utf-8")

    def test_live_page_is_local_and_keyboard_playable(self):
        status, html = self.call("GET", "/toaster/studio")
        self.assertEqual(status, 200)
        self.assertIn("SUZY//TOAST", html)
        self.assertIn("test-live-token", html)
        self.assertIn("data-pad=", html)
        self.assertIn("navigator.mediaDevices.getUserMedia", html)
        self.assertIn("MediaRecorder", html)
        self.assertIn("CONNECT COLLIDER DIRECT",html)
        self.assertIn("real rehearsal verification", html)
        self.assertNotIn("__MAGENTA_TOKEN__", html)

    def test_owned_loop_rack_js_and_visible_three_lane_controls(self):
        status, html = self.call("GET", "/toaster/studio")
        self.assertEqual(status, 200)
        self.assertIn('<script src="/toaster/loop-rack.js"></script>', html)
        for name in ("rackChord", "rackVocal", "rackAI", "rackImport",
                     "rackLayers", "rackExport", "rackProgress"):
            self.assertIn(f'id="{name}"', html)
        self.assertIn("VE-22", html)
        self.assertIn("Actual AI only:", html)
        status, js = self.call("GET", "/toaster/loop-rack.js")
        self.assertEqual(status, 200)
        self.assertIn("root.SuzyLoopRack=Rack", js)
        self.assertIn("MediaRecorder", js)
        self.assertIn("getDisplayMedia", js)
        self.assertIn("decodeAudioData", js)

    def test_new_simple_play_is_default_and_presets_are_honest(self):
        status, html = self.call("GET", "/toaster/live")
        self.assertEqual(status, 200)
        self.assertIn("SUZY//TOAST", html)
        self.assertIn("Smiling pink toaster", html)
        self.assertIn('id="rhythm"', html)
        self.assertIn('id="deck-pyramid"', html)
        self.assertIn('id="deck-fishes"', html)
        self.assertIn("RECORD FIRST LOOP", html)
        self.assertIn("LOOP VOICE", html)
        self.assertIn("auto Scarlett", html)
        self.assertIn("MRT2 prompt:", html)
        self.assertIn("ENABLE MAGENTA", html)
        self.assertIn('id="aiGoogleModel"', html)
        self.assertIn('id="aiTransport"', html)
        self.assertIn('aiFetch(on?"transport-pause":"transport-play")', html)
        self.assertIn('s.transport_playing===true', html)
        self.assertIn('id="aiModelHelp"', html)
        self.assertIn('s.native_model_selection_required!==true', html)
        self.assertIn('s.native_au_ui_requested===true', html)
        self.assertIn('!aiNativeReady || s.native_au_ui_requested===true', html)
        self.assertIn('to switch this native AU to Google', html)
        self.assertIn('Restarting native AU in Google model-selection mode', html)
        self.assertNotIn('selector unavailable in bookmark mode', html)
        self.assertIn('state.native_au_ui_visible', html)
        self.assertIn('s.native_au_ui_error', html)
        self.assertIn('grid-template-columns:repeat(2,minmax(0,1fr))', html)
        self.assertIn('aiFetch("show-au-ui")', html)
        self.assertIn('native_model_selection_required', html)
        self.assertIn("Model audio must be tested by ear", html)
        self.assertIn("OfflineAudioContext", html)
        self.assertIn("function midi(which,index)", html)
        self.assertIn("function midiRelease()", html)
        self.assertIn("SCENES=", html)
        self.assertIn("VE-22", html)
        self.assertIn("Native Google Magenta AU is optional", html)
        self.assertNotIn("__MAGENTA_TOKEN__", html)
        self.assertNotIn("CONNECT COLLIDER DIRECT", html)
        self.assertNotIn("AUDIO ROUTING + MIXER", html)

    def test_live_arranger_is_editable_and_served_locally(self):
        status, html = self.call("GET", "/toaster/live")
        self.assertEqual(status, 200)
        for needle in ('id="arrCues"', 'id="arrArm"', 'id="arrNext"',
                       'id="arrProgress"', 'window.SuzyArrangement',
                       'arranger.onCycle(count/8)', 'onCue:c=>', 'onChord:c=>'):
            self.assertIn(needle, html)
        code, js = self.call("GET", "/toaster/arrangement.js")
        self.assertEqual(code, 200)
        self.assertIn("root.SuzyArrangement=Arrangement", js)
        self.assertIn('root.localStorage.setItem(KEY', js)
        self.assertIn("this.endBar=bar+this.cues[0].bars", js)
        self.assertIn("this.skip=true", js)
        self.assertNotIn("eval(", js)

    def test_vocal_worklet_headroom_and_browser_buffering(self):
        code, html = self.call("GET", "/toaster/live")
        self.assertEqual(code, 200)
        for marker in ('id="vocalHeadroom"', 'id="browserLatency"',
                       'id="vocalPeak"', 'latencyHint:', 'createDynamicsCompressor',
                       'new AudioWorkletNode(', 'audioWorklet.addModule(',
                       'near-clip samples:', 'Scarlett input gain'):
            self.assertIn(marker, html)
        self.assertNotIn("ctx.createScriptProcessor(1024", html)
        code, js = self.call("GET", "/toaster/vocal-capture.js")
        self.assertEqual(code, 200)
        for marker in ("extends AudioWorkletProcessor",
                       'registerProcessor("suzy-vocal-capture"',
                       "this.data[start+i]=sample", "this.hot++", "currentFrame"):
            self.assertIn(marker, js)

    def test_real_song_track_lanes_and_long_loop_capture(self):
        status, html = self.call("GET", "/toaster/live")
        self.assertEqual(status, 200)
        for literal in (
            'id="tracks-pyramid"', 'id="tracks-fishes"',
            '/toaster/track-view.js', 'window.SuzyTrackView',
            'songCycleSteps(which)', 'songCycleSeconds(which)',
            'const origin=transportEpoch+(layer.loopOriginStep??((layer.arrStartBar??0)*8))*tickSeconds()', 'function layerPlaybackPhase(which,layer,at)', 'function nextSongBoundary(which,n)',
            'r.first', 'recording.endAt', 'firstStep',
            'ctx.sampleRate*120', '"vocal"', 'd.anchorStep=r.beginAt',
            'd.lengthSteps=length', 'Math.min(256',
            'Export full cycle of one selected song'
        ):
            self.assertIn(literal, html)
        self.assertIn('master cycle. Import this WAV into Logic.', html)

        status, js = self.call("GET", "/toaster/track-view.js")
        self.assertEqual(status, 200)
        for literal in (
            "root.SuzyTrackView=Tracks",
            '["chords","KEYS"',
            '["vocal","VOICE"',
            '["ai","MAGENTA"',
            '"track-midi-note"', '"track-wave-bar"',
            "peakBins(layer.buffer)", "this.onRemove(which,layer.id)"
        ):
            self.assertIn(literal, js)

        status, worklet = self.call("GET", "/toaster/vocal-capture.js")
        self.assertEqual(status, 200)
        self.assertIn("Math.floor(sampleRate*120)", worklet)
        self.assertIn("this.port.postMessage", worklet)

    def test_first_take_determines_song_cycle_without_resetting_native_au(self):
        _, html = self.call("GET", "/toaster/live")
        self.assertIn('first:!d.locked', html)
        self.assertIn('endAt:beginAt+(d.locked?d.lengthSteps:256)', html)
        self.assertIn('recording.endAt=recording.first?', html)
        self.assertIn('r.endAt-r.beginAt', html)
        self.assertIn('finishQueued:false', html)
        self.assertIn('if(r.first){d.locked=true;d.lengthSteps=length;d.anchorStep=r.beginAt;d.loopEnabled=true;}', html)
        self.assertIn('if(take.first){d.locked=true;d.lengthSteps=actualSteps;d.anchorStep=take.firstStep;}', html)
        self.assertIn('if(!d.layers.length){', html)
        self.assertIn('d.locked=false;d.lengthSteps=16;d.anchorStep=0;d.loopEnabled=true;', html)
        self.assertIn('updateRecordControls(which);', html)
        self.assertIn('id="loopToggle-pyramid"', html)
        self.assertIn('id="loopToggle-fishes"', html)
        self.assertNotIn('id="loopBars-pyramid"', html)
        self.assertNotIn('id="loopBars-fishes"', html)
        self.assertIn('■ DONE → LOOP', html)
        self.assertIn('play your phrase, press DONE', html)
        self.assertIn('songLayerAudible(which,l,Math.floor(count/8))', html)
        self.assertNotIn('for(const d of Object.values(decks))d.anchorStep=0;', html)
        self.assertNotIn("createScriptProcessor(1024", html)
        self.assertIn("native_au_ui_visible", html)

    def test_balanced_multitimbral_overdub_and_key_undo(self):
        code, html = self.call("GET", "/toaster/live")
        self.assertEqual(code, 200)
        # Real, existing pad buttons remain visible, not moved into a collapsed drawer.
        self.assertIn('id="classicDecks" class="chord-center"', html)
        self.assertLess(html.index('id="pads-pyramid"'), html.index('id="trackWorkspace"'))
        for which in ("pyramid", "fishes"):
            for marker in (f'id="instrument-{which}"',
                           f'id="keyDown-{which}"',
                           f'id="keyUp-{which}"',
                           f'id="keyUndo-{which}"',
                           f'id="keyReset-{which}"'):
                self.assertIn(marker, html)
        for marker in ('id="mixBoth"', 'id="liveLevel"', 'id="loopLevel"',
                       'const INSTRUMENTS={', 'function makeVoice(',
                       'const instrument=decks[which].instrument;',
                       'h.event={step,index,holdSteps:1,instrument};',
                       'e.instrument||"keys"',
                       'd.keyHistory.push(next)',
                       'd.keyHistoryIndex--;setKey(which,d.keyHistory[d.keyHistoryIndex],false);',
                       'updateOverdubBalance();',
                       'Math.sqrt(Math.max(1,active))'):
            self.assertIn(marker, html)

    def test_each_song_displays_true_loop_pass_and_bar(self):
        code, js = self.call("GET", "/toaster/track-view.js")
        self.assertEqual(code, 200)
        for marker in ('track-loop-label-', 'track-loop-fill-',
                       '"↻ LOOPING"', '"● RECORDING · PRESS DONE"',
                       'fill.style.width=((phase/length)*100)+"%"'):
            self.assertIn(marker, js)

    def test_full_arrangement_and_local_voice_follow_are_served(self):
        code, html = self.call("GET", "/toaster/live")
        self.assertEqual(code, 200)
        for marker in ('id="fullViewport"', 'id="fullLanes"',
                       'id="fullPlayhead"', 'id="fullRuler"',
                       'id="fullZoom"', 'id="fullFit"',
                       'id="voiceFollow"', '/toaster/performance-timeline.js',
                       'fullTimeline=new window.SuzyPerformanceTimeline'):
            self.assertIn(marker, html)
        for endpoint, markers in (
            ("/toaster/performance-timeline.js",
             ("root.SuzyPerformanceTimeline=PerformanceTimeline",
              "this.onEdit(which,layer.id,start,end)",
              'block.addEventListener("pointerdown"',
              'handle.addEventListener("pointerdown"',
              'this.zoom=clamp(')),
            ("/toaster/voice-follow.js",
             ('registerProcessor("suzy-voice-follow"',
              'this.port.postMessage({type:"pitch",note,confidence})',
              "Math.sqrt(energy/data.length)"))):
            status, script = self.call("GET", endpoint)
            self.assertEqual(status, 200)
            for marker in markers:
                self.assertIn(marker, script)

    def test_single_visible_timeline_and_live_mic_monitoring(self):
        status, page = self.call("GET", "/toaster/live")
        self.assertEqual(status, 200)
        self.assertIn('id="fullArrangement"', page)
        self.assertIn('<section class="arranger" aria-label="Legacy automation cue editor" hidden>', page)
        self.assertIn('id="monitorVoice"', page)
        self.assertIn('id="monitorLevel"', page)
        self.assertIn('id="monitorReverb"', page)
        self.assertIn('id="localKeysSolo"', page)
        for marker in ('id="fullCopy"', 'id="fullCut"', 'id="fullPaste"',
                       'id="fullSplit"', 'id="fullDelete"'):
            self.assertIn(marker, page)
        for marker in ('async function startVoiceMonitor()',
                       'monitorSource.connect(monitorFilter)',
                       'monitorDry.connect(mainBus)',
                       'monitorSend.connect(verb)',
                       'const firstStep=Math.max(stepNumber,Math.ceil((ctx.currentTime-transportEpoch)/tickSeconds()))',
                       'loopOriginStep:d.anchorStep,arrStartBar:0',
                       'function toggleLocalKeysOnly()',
                       'onAction:({action,selected,target,clipboard})',
                       'sourceOffsetBars:(layer.sourceOffsetBars||0)+(splitBar-start)'):
            self.assertIn(marker, page)
        status, script = self.call("GET", "/toaster/performance-timeline.js")
        self.assertEqual(status, 200)
        for marker in ('this.perform(action)',
                       'this.clipboard={which:selected.which,kind:selected.kind',
                       'this.onAction({action,selected,target:{...this.target},clipboard:this.clipboard})'):
            self.assertIn(marker, script)

    def test_monitor_record_playback_distinctions_and_timeline_transport(self):
        status, page = self.call("GET", "/toaster/live")
        self.assertEqual(status, 200)
        for marker in ('id="vocalRecordState"', 'id="vocalLoopState"',
                       'id="vocalRecordPyramid"', 'id="vocalRecordFishes"',
                       'id="timelinePlay"', 'id="timelineStop"', 'id="timelineRewind"',
                       'id="vocalEchoMode"', 'id="vocalEchoLevel"',
                       'id="vocalEchoFeedback"', 'id="vocalAir"'):
            self.assertIn(marker, page)
        for implementation in (
            'function updateVocalState()', 'function updateTransportUI()',
            'async function timelineStop()', 'async function timelineRewind()',
            'function updateVoiceEcho()', 'vocalEchoDelay=ctx.createDelay(2.0)',
            'vocalEchoTone.type="lowpass"',
            'vocalEchoTone.connect(vocalEchoFeedbackNode)',
            'vocalEchoFeedbackNode.connect(vocalEchoDelay)',
            'd.voiceBus.connect(vocalEchoInput)',
            'monitorFilter.connect(vocalEchoInput)',
            'songLayerAudible(which,l,bar)',
            'MONITOR ON → ',
            'Browser loops only · Native Magenta independent',
        ):
            self.assertIn(implementation, page)

    def test_separate_per_song_violin_and_guitar_leads_and_local_drum_grooves(self):
        status, page = self.call("GET", "/toaster/live")
        self.assertEqual(status, 200)
        self.assertLess(page.index('id="pads-pyramid"'), page.index('id="lead-pyramid"'))
        self.assertLess(page.index('id="pads-fishes"'), page.index('id="lead-fishes"'))
        for marker in ('id="lead-pyramid"', 'id="lead-fishes"',
                       'id="leadLevel-pyramid"', 'id="leadLevel-fishes"',
                       'id="leadOctave-pyramid"', 'id="leadOctave-fishes"',
                       'id="leadPlay-pyramid"', 'id="leadPlay-fishes"',
                       'id="drumMeter"', 'id="drumStyle"', 'id="drumStatus"',
                       'value="3/4"', 'value="4/4"', 'value="6/8"', 'value="5/4"',
                       'value="pulse"', 'value="brush"', 'value="trip"',
                       'value="broken"'):
            self.assertIn(marker, page)
        for marker in ('function setLead(which,instrument)',
                       'function setLeadOctave(which,value)',
                       'function setLeadLevel(which,value)',
                       'async function auditionLead(which)',
                       'function drumPattern(count)',
                       'function setDrumGroove(meter=drumMeter,style=drumStyle)',
                       'const playedMidi=midi+d.leadOctave;',
                       'const voice=(localInstrumentAudible(scene)||localAudioOverdubActive(scene))?makeVoice(scene,playedMidi,start,instrument,.14,true,"lead"):null;',
                       'DRUM_STEPS=Object.freeze({"3/4":6,"4/4":8,"5/4":10,"6/8":6})'):
            self.assertIn(marker, page)
        # The same 4/4 recording bar lengths remain intentional.
        self.assertIn('Math.floor(count/8)', page)
        self.assertIn('Song loops and arrangement still use the existing 4/4 grid.', page)

    def test_clickable_transport_ruler_locates_audio_in_named_song_sections(self):
        status, page = self.call("GET", "/toaster/live")
        self.assertEqual(status, 200)
        for marker in (
            'function locateTimelineBar(rawBar)',
            'function currentTransportBar()',
            'function sectionAtBar(bar)',
            'let parkedBar=0,seekRevision=0;',
            'const when=ctx.currentTime+.10;',
            'nextStepAt=when;',
            'onSeek:locateTimelineBar',
            'startLoopAudio(which,layer,when)',
            '▶ PLAY',
            'Click a bar number or song section on the ruler',
        ):
            self.assertIn(marker, page)
        status, timeline = self.call("GET", "/toaster/performance-timeline.js")
        self.assertEqual(status, 200)
        for marker in (
            'this.onAction=onAction;this.onSeek=onSeek;',
            'ruler.onpointerdown=e=>this.seekFromPointer(e,ruler);',
            'ruler.onkeydown=e=>{',
            'this.onSeek(index);',
            'this.seek(bar);',
            'aria-valuenow',
        ):
            self.assertIn(marker, timeline)

    def test_five_actual_magenta_prompts_are_available_with_native_blend_controls(self):
        status, page = self.call("GET", "/toaster/live")
        self.assertEqual(status, 200)
        for marker in ('id="promptPyramid"', 'id="promptFishes"',
                       'id="promptViolin"', 'id="promptGuitar"', 'id="promptJazzDrums"', 'id="aiDrumMix"',
                       'id="aiLeadMix-pyramid"', 'id="aiLeadMix-fishes"',
                       'id="aiChords-pyramid"', 'id="aiChords-fishes"',
                       'id="aiLead-pyramid"', 'id="aiLead-fishes"',
                       'function setNativeLeadMix(which,percent)',
                       'await aiFetch("lead-mix",{scene:which,value:value/100})',
                       'const native=nativeInstrumentEnabled(scene);',
                       'CHORDS 100% · LEAD 0%',
                       'One MRT2 Small model, five genuine Google AU sound prompts'):
            self.assertIn(marker, page)
        self.assertIn('["promptPyramid","promptFishes","promptViolin","promptGuitar","promptJazzDrums"]', page)
        self.assertIn('Enter five AI prompts', page)
        self.assertIn('await aiFetch("drum-mix",{value:value/100})', page)
        self.assertIn('JAZZ DRUM AI BLEND', page)

    def test_visible_jazz_drums_and_independent_native_instrument_routing(self):
        status, page = self.call("GET", "/toaster/live")
        self.assertEqual(status, 200)
        for marker in ('id="jazzDrumDeck"', 'id="aiDrumMix"',
                       'id="promptJazzDrums"', 'id="applyJazzDrumsPrompt"',
                       'id="rhythmAudio"', 'id="instrumentSource-pyramid"',
                       'id="instrumentSource-fishes"',
                       'function localInstrumentAudible(which)',
                       'function nativeInstrumentEnabled(which)',
                       'function toggleRhythmAudio()',
                       'if(native)h.aiChordToken=aiNote(which,index);',
                       'if(!rhythmCanSound())return;'):
            self.assertIn(marker, page)
        self.assertIn('instrumentSource:"ai"', page)
        self.assertNotIn('midi(which,index);aiNote(which,index);', page)
        # #116's arrangement routing is preserved, but its release now owns
        # a specific chord instead of allowing a stale timer to kill a new one.
        self.assertIn('if(nativeInstrumentEnabled(c.scene)){', page)
        self.assertIn('const token=aiNote(c.scene,c.chord,{legato:true});', page)
        self.assertIn('if(!heldKeys.size)aiRelease(token);', page)
        self.assertNotIn('if(aiNativeReady){\\n   aiNote(c.scene,c.chord);', page)
        self.assertLess(page.index('id="jazzDrumDeck"'), page.index('id="deck-pyramid"'))

    def test_authorized_pads_work_without_physical_input(self):
        self.assertIsNone(self.bridge.source)
        self.assertEqual(self.call("POST", "/api/perform/chord", {"index":0}, token=False)[0],403)
        self.assertEqual(self.call("POST", "/api/perform/chord", {"index":0},origin="https://attacker.example")[0],403)
        code, data = self.call("POST", "/api/perform/chord", {"index":0})
        self.assertEqual(code, 200)
        self.assertEqual(data["chord_index"], 0)
        self.assertFalse(data["magenta_audio_confirmed"])
        self.assertIn([0x90, 54, 56], self.bridge.output.messages)
        self.assertEqual(self.call("POST", "/api/perform/scene", {"scene":"fishes"})[1]["scene"],"fishes")
        self.assertEqual(self.call("POST", "/api/perform/chord", {"index":0})[1]["chords"][0],"Em7")

    def test_direct_collider_route_is_explicit_token_guarded_and_audio_unverified(self):
        self.assertEqual(self.call("POST", "/api/collider/connect", token=False)[0], 403)
        self.assertEqual(self.call("POST", "/api/collider/connect",
                                   origin="https://other.example")[0], 403)
        self.assertEqual(self.call("POST", "/api/collider/connect", {"ignored": True})[0], 400)
        status, body = self.call("POST", "/api/collider/connect")
        self.assertEqual(status, 200)
        self.assertTrue(body["collider_direct_ready"])
        self.assertEqual(body["collider_direct_output"], "MRT2 - Collider Input")
        self.assertFalse(body["magenta_audio_confirmed"])
        self.assertEqual(self.call("POST", "/api/perform/chord", {"index":0})[0],200)
        self.assertIn([0x90, 54, 56],self.bridge.collider_out.messages)
        self.assertEqual(self.call("POST", "/api/collider/disconnect")[1]["collider_direct_ready"],False)
        self.assertFalse(self.perf.status()["collider_direct_ready"])

    def test_releasing_computer_key_sends_midi_note_off(self):
        self.assertEqual(self.call("POST", "/api/perform/chord", {"index":0})[0], 200)
        self.assertEqual(self.call("POST", "/api/perform/release-chord", token=False)[0], 403)
        self.assertEqual(self.call("POST", "/api/perform/release-chord", {"index":0})[0], 400)
        code, data = self.call("POST", "/api/perform/release-chord", {})
        self.assertEqual(code, 200)
        self.assertIsNone(data["chord_index"])
        self.assertIn([0x80, 54, 0], self.bridge.output.messages)

    def test_rhythm_and_release_do_not_claim_audio_mute(self):
        self.call("POST", "/api/perform/chord", {"index":0})
        self.assertEqual(self.call("POST", "/api/perform/settings", {"bpm":132,"rhythm":"pulse","intensity":75})[0],200)
        self.assertEqual(self.call("POST", "/api/perform/start")[1]["running"],True)
        code, status = self.call("POST", "/api/release")
        self.assertEqual(code, 200)
        self.assertEqual(self.perf.status()["running"],False)
        self.assertEqual(status["ai_audio_muted"],"not_observed")
        self.assertEqual(self.call("POST", "/api/perform/chord", {"index":True})[0],400)
        self.assertEqual(self.call("POST", "/api/perform/settings", {"bpm":0,"rhythm":"pulse","intensity":50})[0],400)


if __name__=="__main__":
    unittest.main()

    def test_phrase_defined_vocals_song_mutes_and_native_mix_persist(self):
        status, page = self.call("GET", "/toaster/live")
        self.assertEqual(status, 200)
        for literal in (
            'id="vocalRecordPyramid"', 'id="vocalRecordFishes"',
            'id="songEnabled-pyramid"', 'id="songEnabled-fishes"',
            'id="performanceMaster"', 'function effectiveSongMix()',
            'function setSongEnabled(which)', 'function queueNativeSongMix()',
            'take.actualSteps=endStep-take.firstStep',
            'processor.port.postMessage({type:"finish"',
            'loopOriginStep:d.anchorStep', 'await findDevices();',
        ):
            self.assertIn(literal, page)
        self.assertIn('class="song-lead-panel" aria-label="pyramid optional local fallback instrument" hidden', page)
        self.assertIn('class="voice-ai-follow" aria-label="Experimental voice controlled AI accompaniment" hidden', page)
        self.assertNotIn('const bars=d.locked?d.lengthSteps/8:d.initialBars;', page)
        self.assertNotIn('if(scene!==which&&!blendBoth){$("mix").value=', page)
        status, rack = self.call("GET", "/toaster/track-view.js")
        self.assertEqual(status, 200)
        self.assertNotIn('track-first-size', rack)
        self.assertIn('DONE VOICE → LOOP', rack)
