// SUZY//TOAST · native MRT2 prompt host (macOS only).
// One real AVAudioUnit instance; line-delimited JSON protocol on stdin/stdout.
// No UI web automation and no fake neural audio. The AU may take time to load
// its local MLX model; "audio engine started" is not proof of generated sound.
import Foundation
import AVFoundation
import AudioToolbox
import CoreAudioKit // AUv3's custom-view controller API is exposed by CoreAudioKit.
import Synchronization // Lock-free state read on the real-time render callback.
import AppKit

final class MRT2Host {
    private var engine: AVAudioEngine?
    private var generator: AVAudioUnit?
    private var reverbUnit: AVAudioUnitReverb?
    private var auUIWindow: NSWindow?
    private var auUIRequestPending = false
    private var auUIError = ""
    private var auUIRequestCount = 0
    // Set at server launch; never starts a second model instance.
    private let selectModelInGoogleUI = ProcessInfo.processInfo.environment["SUZY_MRT2_MODEL_VIA_UI"] == "1"
    private var held: [UInt8] = []
    private var melodyHeld = Set<UInt8>()
    // A browser pointer tap can last less than the MRT2 neural control latency.
    // Native chord notes should outlive a click; a new chord still wins instantly.
    private var chordStartedAt: TimeInterval = 0
    private var pendingChordRelease: DispatchWorkItem?
    private let minimumChordHoldSeconds: TimeInterval = {
        let value = Double(ProcessInfo.processInfo.environment["SUZY_MRT2_CHORD_HOLD_MS"] ?? "") ?? 480
        return max(200, min(1200, value)) / 1000.0
    }()
    // Google plays when its own UI says PLAY OR the AU host says transport MOVING.
    // Atomic avoids a lock/data race on the audio-render thread. Default stays
    // auto-playing for existing live sessions. Set AUTOPLAY=0 to start paused.
    private let transportPlaying = Atomic<Bool>(
        ProcessInfo.processInfo.environment["SUZY_MRT2_TRANSPORT_AUTOPLAY"] != "0")
    private var tempoBpm: Double = 105.0
    private var tempoStart = ProcessInfo.processInfo.systemUptime
    private var active = false
    private var loading = false
    private var modelRequested = false
    private var errorMessage = ""
    private var modelPath = ""
    private var scene = "pyramid"
    private var blend: Float = 0
    private var leadMix: [String: Float] = ["pyramid":0, "fishes":0]
    private var level: Float = 0.28
    private var reverbAmount: Float = 0.18
    private var muted = false
    private var outputSignalDetected = false
    // Diagnostic override. Default unchanged; set SUZY_MRT2_MIDI_GATE=0
    // BEFORE starting the stage server to test prompt-only native audio.
    private let midiGateEnabled = ProcessInfo.processInfo.environment["SUZY_MRT2_MIDI_GATE"] != "0"
    private var auComponentName = ""
    private var assetPath = ""
    private var bookmarkScopeVerified = false
    private var bookmarkSelfResolutionVerified = false
    // Apple recommends ordinary implicit-scope bookmarks for IPC. Google AU's
    // current upstream resolver uses WithSecurityScope, so whether it accepts
    // this cross-process form MUST be tested on the installed extension.
    private let bookmarkFormat = ProcessInfo.processInfo.environment["SUZY_MRT2_BOOKMARK_MODE"] == "implicit"
        ? "implicit_cross_process" : "explicit_app_scoped"
    private var modelFileBytes: Int64 = 0
    private var outputRate: Double = 0
    private var hostTransportSupplied = false
    private var prompts = [
        "Intimate warm piano chords, fragile orchestral strings, sparse melancholic experimental art rock, slow floating asymmetric pulse, soft bass, subtle ambient textures, restrained percussion, no vocals",
        "Interlocking clean guitar arpeggios, shimmering echoes, hypnotic experimental art rock, flowing bass, understated drums, glassy synthesizers, gradually building ethereal atmosphere, no vocals",
        "Expressive solo bowed violin, rich warm acoustic strings, intimate chamber texture, lyrical sustained legato phrases, delicate vibrato, subtle bow noise, suspended melancholy, no piano, no guitar, no vocals",
        "Expressive nylon-string classical guitar, intricate fingerpicked melodic arpeggios, warm wooden resonance, soft plucked string attacks, interlocking counterpoint, clear intimate acoustic guitar, no piano, no violin, no vocals",
    ]
    private let chords: [String: [[UInt8]]] = [
        "pyramid": [[54, 58, 61, 66], [55, 59, 62, 66], [57, 61, 64, 66], [54, 58, 61, 66]],
        "fishes": [[52, 55, 59, 62], [54, 57, 61, 64], [57, 61, 64, 69], [55, 59, 62, 66]],
    ]

    func report() -> [String: Any] {
        return [
            "phase": active ? "host-running" : loading ? "initializing" : "inactive",
            "native_au": generator != nil,
            "audio_engine_running": engine?.isRunning ?? false,
            "model_load_requested": modelRequested,
            "model_loading_source": selectModelInGoogleUI ? "native_google_au_ui" : "bookmarked_state_request",
            "native_au_ui_requested": auUIRequestPending,
            "native_au_ui_error": auUIError,
            "native_au_ui_request_count": auUIRequestCount,
            "native_au_ui_visible": auUIWindow?.isVisible ?? false,
            "native_model_selection_required": selectModelInGoogleUI,
            // Google's AU doesn't expose a public loaded/model-audible getter.
            // This only confirms a nonzero PCM signal at the native host mixer,
            // never the physical headphones or correct Magenta semantics.
            "model_audio_confirmed": outputSignalDetected,
            "output_signal_detected": outputSignalDetected,
            "midi_gate_enabled": midiGateEnabled,
            "midi_gate_parameter_readback": Double(generator?.auAudioUnit.parameterTree?.parameter(withAddress: 45)?.value ?? -1),
            "model_path": modelPath,
            "error": errorMessage,
            "scene": scene,
            "blend": Double(blend),
            "volume": Double(level),
            "reverb": Double(reverbAmount),
            "muted": muted,
            "held_notes": (held + Array(melodyHeld)).map(Int.init),
            "chord_min_hold_ms": Int(minimumChordHoldSeconds * 1000),
            "chord_release_pending": pendingChordRelease != nil,
            "tempo_bpm": tempoBpm,
            "tempo_context_supplied": generator != nil,
            "transport_context_supplied": hostTransportSupplied,
            "transport_moving": hostTransportSupplied && (engine?.isRunning ?? false)
                && transportPlaying.load(ordering: .relaxed),
            "transport_playing": transportPlaying.load(ordering: .relaxed),
            "native_loop_capture_supported": false, // Browser's current recorder cannot capture this AU's PCM.
            "text_prompts": prompts,
            "prompt_slot_count": prompts.count,
            "prompt_weights": (10...13).map { Double(generator?.auAudioUnit.parameterTree?.parameter(withAddress: AUParameterAddress($0))?.value ?? 0) },
            "lead_mix": ["pyramid": Double(leadMix["pyramid"] ?? 0),
                         "fishes": Double(leadMix["fishes"] ?? 0)],
            "au_component": auComponentName,
            "musiccoca_assets_path": assetPath,
            "bookmark_scope_verified": bookmarkScopeVerified,
            "bookmark_self_resolution_verified": bookmarkSelfResolutionVerified,
            "bookmark_format": bookmarkFormat,
            "bookmark_recipient_verified": false, // Native Google AU exposes no status response.
            "host_model_loaded": false,
            "host_model_load_state": selectModelInGoogleUI
                ? "select_in_google_AU_ui_model_loaded_not_confirmed"
                : modelRequested ? "requested_asynchronously_by_google_AU_not_confirmed" : "not_requested",
            "native_output_sample_rate": outputRate,
            "model_file_exists": FileManager.default.fileExists(atPath: modelPath),
            "model_file_bytes": ((try? FileManager.default.attributesOfItem(atPath: modelPath)[.size]) as? NSNumber)?.int64Value ?? 0,
            "midi_input": "TOASTER direct AU, not CoreMIDI",
            "output": "macOS system default, separate from browser audio",
        ]
    }
    private func parameter(_ address: AUParameterAddress, _ value: Float) {
        guard let au = generator?.auAudioUnit,
              let p = au.parameterTree?.parameter(withAddress: address) else { return }
        p.value = AUValue(value)
    }
    private func configure() {
        // Four REAL AU prompt slots, blended within one shared Small model.
        // 0=Pyramid chords, 1=Fishes chords, 2=violin, 3=nylon guitar.
        let p = max(0, min(1, leadMix["pyramid"] ?? 0))
        let f = max(0, min(1, leadMix["fishes"] ?? 0))
        parameter(10, (1.0 - blend) * (1.0 - p))
        parameter(11, blend * (1.0 - f))
        parameter(12, (1.0 - blend) * p)
        parameter(13, blend * f)
        parameter(14, 0)
        parameter(15, 0)
        parameter(39, 1.0) // Google "Filter Drums"
        parameter(4, 5.0)  // Note Adherence; human notes have priority.
        parameter(3, 2.5)  // Prompt Adherence
        parameter(45, midiGateEnabled ? 1.0 : 0.0) // Diagnostic: gate off permits prompt-only audition.
        // AU volume is measured in dB (-60…+12). Convert the user's
        // 0–100% linear fader into a logarithmic dB level, with no boost > 0dB.
        // 28% is about -11dB instead of the barely audible old -26dB.
        let db = level <= 0.0001 ? -60 : max(-60, min(0, 20 * log10(level)))
        parameter(5, db)
        reverbUnit?.wetDryMix = max(0, min(60, reverbAmount * 60))
        parameter(6, muted || level <= 0 ? 1 : 0)
    }
    private func rawMIDI(_ bytes: [UInt8]) {
        guard active, let cb = generator?.auAudioUnit.scheduleMIDIEventBlock else { return }
        bytes.withUnsafeBufferPointer { pointer in
            guard let base = pointer.baseAddress else { return }
            cb(AUEventSampleTimeImmediate, 0, bytes.count, base)
        }
    }
    private func cancelPendingChordRelease() {
        pendingChordRelease?.cancel()
        pendingChordRelease = nil
    }
    private func noteOff() {
        cancelPendingChordRelease()
        for note in held where !melodyHeld.contains(note) { rawMIDI([0x80, note, 0]) }
        held.removeAll()
        chordStartedAt = 0
    }
    private func releaseChordAfterMinimumHold() {
        cancelPendingChordRelease()
        guard !held.isEmpty else { return }
        let elapsed = ProcessInfo.processInfo.systemUptime - chordStartedAt
        let remaining = max(0, minimumChordHoldSeconds - elapsed)
        if remaining <= 0 {
            noteOff()
            return
        }
        let work = DispatchWorkItem { [weak self] in
            guard let self = self else { return }
            self.pendingChordRelease = nil
            self.noteOff()
        }
        pendingChordRelease = work
        // The AU MIDI keyboard remains responsive; only a brief note-off
        // is deferred. A newer chord cancels this pending release immediately.
        DispatchQueue.main.asyncAfter(deadline: .now() + remaining, execute: work)
    }
    private func allNotesOff() {
        for note in melodyHeld { rawMIDI([0x80, note, 0]) }
        melodyHeld.removeAll()
        noteOff()
    }
    private func findModel() -> String? {
        let fm = FileManager.default
        let home = fm.homeDirectoryForCurrentUser
        if let explicit = ProcessInfo.processInfo.environment["SUZY_MRT2_MODEL"], !explicit.isEmpty {
            let path = (explicit as NSString).expandingTildeInPath
            if fm.fileExists(atPath: path) {
                var dir: ObjCBool = false
                fm.fileExists(atPath: path, isDirectory: &dir)
                if !dir.boolValue && path.hasSuffix(".mlxfn") { return path }
                if dir.boolValue {
                    let contents = (try? fm.contentsOfDirectory(atPath: path)) ?? []
                    if let name = contents.first(where: { $0.hasSuffix(".mlxfn") && !$0.lowercased().contains("spectrostream") }) {
                        return (path as NSString).appendingPathComponent(name)
                    }
                }
            }
            errorMessage = "SUZY_MRT2_MODEL points to no usable .mlxfn file: \(path)"
            return nil
        }
        let roots = [
            home.appendingPathComponent("Library/Application Support/MagentaRT/models"),
            home.appendingPathComponent("Library/Application Support/MagentaRT"),
            home.appendingPathComponent("Documents/Magenta"),
            home.appendingPathComponent("Downloads"),
        ]
        var found: [String] = []
        for root in roots {
            guard fm.fileExists(atPath: root.path),
                let enumeration = fm.enumerator(at: root, includingPropertiesForKeys: [.isDirectoryKey],
                                                options: [.skipsHiddenFiles, .skipsPackageDescendants]) else { continue }
            var visited = 0
            for case let candidate as URL in enumeration {
                visited += 1
                if visited > 10000 { break }
                if candidate.pathExtension.lowercased() == "mlxfn" &&
                   !candidate.lastPathComponent.lowercased().contains("spectrostream") {
                    found.append(candidate.path)
                    if found.count >= 40 { break }
                }
            }
        }
        return found.sorted { a,b in
            let av = a.lowercased().contains("small") ? 0 : 1
            let bv = b.lowercased().contains("small") ? 0 : 1
            return av == bv ? a < b : av < bv
        }.first
    }
    private func findResources() -> String? {
        let home = FileManager.default.homeDirectoryForCurrentUser
        let roots = [
            "Documents/Magenta/magenta-rt-v2/resources",
            "Documents/Magenta/resources",
            "Library/Application Support/MagentaRT/resources",
        ]
        for root in roots {
            let path = home.appendingPathComponent(root)
            let encoder = path.appendingPathComponent("musiccoca/text_encoder.tflite")
            let quantizer = path.appendingPathComponent("musiccoca/pretrained_vector_quantizer.tflite")
            if FileManager.default.fileExists(atPath: encoder.path)
                && FileManager.default.fileExists(atPath: quantizer.path) {
                return path.path
            }
        }
        return nil
    }
    func start() {
        if active || loading { return }
        errorMessage = ""
        guard let path = findModel() else {
            if errorMessage.isEmpty {
                errorMessage = "MRT2 Small model not found. Set SUZY_MRT2_MODEL to the installed .mlxfn file; no model will be downloaded."
            }
            return
        }
        modelPath = path
        let attributes = try? FileManager.default.attributesOfItem(atPath: path)
        modelFileBytes = (attributes?[.size] as? NSNumber)?.int64Value ?? 0
        if modelFileBytes < 10_000_000 {
            errorMessage = "Found an unusually small MRT2 model file: \(modelFileBytes) bytes. Check model installation."
            return
        }
        // Google loads its text encoder *before* restoring our saved prompt
        // state. The default SDK path does not necessarily point to the v2
        // resources that `mrt models init` actually installed.
        if let resources = findResources() {
            assetPath = resources
            UserDefaults.standard.set(resources, forKey: "MagentaRT_CustomResourcesPath")
        } else {
            assetPath = ""
            // Plugin may have bundled resources, so do not reject blindly.
            errorMessage = "MusicCoCa assets not found in default MRT2 folders; plugin bundle may provide them."
        }
        loading = true
        // Google's current AUv3 Info.plist advertises aumu/MGR2/Goog
        // (0x4D475232). Earlier AU source also mentioned MGRT
        // (0x4D475254). Query registered components, not a single stale ID.
        let googleMusicDevice = AudioComponentDescription(
            componentType: kAudioUnitType_MusicDevice,
            componentSubType: 0, componentManufacturer: 0x476F6F67,
            componentFlags: 0, componentFlagsMask: 0)
        let available = AVAudioUnitComponentManager.shared()
            .components(matching: googleMusicDevice)
        let currentMRT2: OSType = 0x4D475232 // 'MGR2'
        let legacyMRT2: OSType = 0x4D475254 // 'MGRT'
        let item = available.first(where: { $0.audioComponentDescription.componentSubType == currentMRT2 })
            ?? available.first(where: { $0.audioComponentDescription.componentSubType == legacyMRT2 })
            ?? available.first(where: { $0.name.lowercased().contains("mrt2") })
        guard let item else {
            loading = false
            errorMessage = "MRT2 (AU).app may be registered with pluginkit, but AVAudioUnitComponentManager still does not expose Google MRT2 (aumu/MGR2/Goog). Open MRT2 (AU).app once, quit and restart TOASTER. If it persists, reboot macOS to refresh Audio Unit discovery."
            return
        }
        auComponentName = item.name
        AVAudioUnit.instantiate(with: item.audioComponentDescription, options: []) { [weak self] unit,error in
            DispatchQueue.main.async {
                guard let self = self else { return }
                self.loading = false
                guard let unit = unit else {
                    self.errorMessage = error?.localizedDescription ?? "MRT2 AU instantiation failed"
                    return
                }
                self.generator = unit
                do {
                    let audio = AVAudioEngine()
                    audio.attach(unit)
                    // IMPORTANT: Google's MagentaRT_AudioUnit internalRenderBlock
                    // writes ONLY SILENCE while both UI playback and host
                    // transport are stopped. Since TOASTER has no plugin UI,
                    // supplying BPM alone never moved the native transport.
                    // Give the performer control over the HOST transport.
                    // UI pause alone cannot stop MRT2 while host transport moves.
                    // This is the native clock, distinct from browser loop clock.
                    let transportOrigin = ProcessInfo.processInfo.systemUptime
                    unit.auAudioUnit.transportStateBlock = { [weak self] flags, samplePosition, cycleStart, cycleEnd in
                        guard let self = self else { return false }
                        flags?.pointee = self.transportPlaying.load(ordering: .relaxed) ? .moving : []
                        let seconds = max(0, ProcessInfo.processInfo.systemUptime - transportOrigin)
                        samplePosition?.pointee = seconds * 48000.0
                        cycleStart?.pointee = 0
                        cycleEnd?.pointee = 0
                        return true
                    }
                    self.hostTransportSupplied = true
                    // This supplies real AU host musical context (tempo/beat).
                    // Google MRT2 reads beat position but does not provide a
                    // public hard tempo-lock guarantee. MIDI note timing remains
                    // the stronger conditioning signal.
                    unit.auAudioUnit.musicalContextBlock = { [weak self] tempo, numerator, denominator, beat, nextBeat, downbeat in
                        guard let self = self else { return false }
                        let bpm = self.tempoBpm
                        tempo?.pointee = bpm
                        numerator?.pointee = 4
                        denominator?.pointee = 4
                        let elapsed = max(0, ProcessInfo.processInfo.systemUptime - self.tempoStart)
                        let pos = 0.001 + elapsed * bpm / 60
                        beat?.pointee = pos
                        nextBeat?.pointee = 0
                        downbeat?.pointee = floor(pos / 4) * 4
                        return true
                    }
                    let reverb = AVAudioUnitReverb()
                    reverb.loadFactoryPreset(.largeHall)
                    reverb.wetDryMix = self.reverbAmount * 60
                    audio.attach(reverb)
                    // Genuine native audio processing, not a UI-only reverb label.
                    audio.connect(unit, to: reverb, format: nil)
                    audio.connect(reverb, to: audio.mainMixerNode, format: nil)
                    self.reverbUnit = reverb
                    audio.mainMixerNode.installTap(onBus: 0, bufferSize: 2048, format: nil) { [weak self] buffer, _ in
                        guard let samples = buffer.floatChannelData else { return }
                        let strideLength = max(1, Int(buffer.frameLength) / 128)
                        let count = min(Int(buffer.format.channelCount), 2)
                        for channel in 0..<count {
                            for frame in stride(from: 0, to: Int(buffer.frameLength), by: strideLength) {
                                if abs(samples[channel][frame]) > 0.001 {
                                    DispatchQueue.main.async { self?.outputSignalDetected = true }
                                    return
                                }
                            }
                        }
                    }
                    // Google AU rejects our cross-identity bookmark with
                    // NSCocoaErrorDomain 259. When using Google's own UI,
                    // deliberately OMIT it, and let the installed AU select
                    // the model from its own sandbox and code-signing identity.
                    let modelURL = URL(fileURLWithPath: path)
                    var state = unit.auAudioUnit.fullState ?? [:]
                    let weighted = self.prompts.enumerated().map { (i,text) in
                        ["text": text, "weight": i == 0 ? 1.0 : 0.0] as [String: Any]
                    }
                    state["MGRT_Prompts"] = weighted + (0..<2).map { _ in
                        ["text":"","weight":0.0] as [String:Any]
                    }
                    if self.selectModelInGoogleUI {
                        state.removeValue(forKey: "MGRT_ModelBookmark")
                        state.removeValue(forKey: "MGRT_ModelName")
                        self.modelRequested = false
                        self.bookmarkScopeVerified = false
                        self.bookmarkSelfResolutionVerified = false
                    } else {
                        let implicit = self.bookmarkFormat == "implicit_cross_process"
                        let bookmark = try modelURL.bookmarkData(
                            options: implicit ? [] : [.withSecurityScope],
                            includingResourceValuesForKeys: nil, relativeTo: nil)
                        var stale = false
                        let checkedURL = try URL(
                            resolvingBookmarkData: bookmark,
                            options: implicit ? [.withoutUI] : [.withSecurityScope, .withoutUI],
                            relativeTo: nil, bookmarkDataIsStale: &stale)
                        self.bookmarkSelfResolutionVerified = !stale &&
                            checkedURL.standardizedFileURL == modelURL.standardizedFileURL
                        guard self.bookmarkSelfResolutionVerified else {
                            throw NSError(domain: "SUZY.TOAST.MRT2", code: 11,
                                userInfo: [NSLocalizedDescriptionKey:
                                    "Model bookmark does not resolve locally to the expected file."])
                        }
                        if !implicit {
                            let scoped = checkedURL.startAccessingSecurityScopedResource()
                            self.bookmarkScopeVerified = scoped
                            if scoped { checkedURL.stopAccessingSecurityScopedResource() }
                            guard scoped else {
                                throw NSError(domain: "SUZY.TOAST.MRT2", code: 11,
                                    userInfo: [NSLocalizedDescriptionKey:
                                        "App-scoped model bookmark access failed in Swift host."])
                            }
                        } else {
                            self.bookmarkScopeVerified = false
                        }
                        state["MGRT_ModelBookmark"] = bookmark
                        state["MGRT_ModelName"] = "mrt2_small"
                        self.modelRequested = true
                    }
                    unit.auAudioUnit.fullState = state
                    try audio.start()
                    self.outputRate = audio.outputNode.outputFormat(forBus: 0).sampleRate
                    self.engine = audio
                    self.active = true
                    self.configure()
                } catch {
                    self.active = false
                    self.errorMessage = "Native AU startup: \(error.localizedDescription)"
                    self.generator = nil
                    self.reverbUnit = nil
                    self.engine = nil
                }
            }
        }
    }
    private func showGoogleAUInterface() {
        guard active, let unit = generator else {
            auUIError = "Start the native Magenta Audio Unit before opening its model selector."
            return
        }
        guard selectModelInGoogleUI else {
            auUIError = "TOASTER was launched in bookmark mode. Stop the server and restart with SUZY_MRT2_MODEL_VIA_UI=1."
            return
        }
        auUIError = ""
        if let window = auUIWindow {
            window.makeKeyAndOrderFront(nil)
            NSApplication.shared.activate(ignoringOtherApps: true)
            return
        }
        if auUIRequestPending { return }
        auUIRequestPending = true
        auUIRequestCount += 1
        // Request the official UI for the SAME running AU, never a second AU.
        unit.auAudioUnit.requestViewController { [weak self] controller in
            DispatchQueue.main.async {
                guard let self = self else { return }
                self.auUIRequestPending = false
                guard let controller = controller else {
                    self.auUIError = "Google MRT2 AU did not return a model-selection view. The AU may not expose its UI to this host."
                    return
                }
                let preferred = controller.preferredContentSize
                let width = preferred.width > 0 ? max(520, min(1060, preferred.width)) : 900
                let height = preferred.height > 0 ? max(400, min(800, preferred.height)) : 640
                let window = NSWindow(
                    contentRect: NSRect(x: 0, y: 0, width: width, height: height),
                    styleMask: [.titled, .closable, .resizable],
                    backing: .buffered, defer: false)
                window.title = "Google MRT2 · Select Local Model"
                window.isReleasedWhenClosed = false
                window.contentViewController = controller
                window.center()
                self.auUIWindow = window
                window.makeKeyAndOrderFront(nil)
                NSApplication.shared.activate(ignoringOtherApps: true)
            }
        }
    }
    func stop() {
        allNotesOff()
        auUIWindow?.close()
        auUIWindow = nil
        auUIRequestPending = false
        auUIError = ""
        parameter(6, 1)
        engine?.stop()
        engine = nil
        generator = nil
        reverbUnit = nil
        active = false
        loading = false
        modelRequested = false
        outputSignalDetected = false
        bookmarkScopeVerified = false
        bookmarkSelfResolutionVerified = false
        hostTransportSupplied = false
    }
    func command(_ request: [String: Any]) -> [String: Any] {
        let type = request["op"] as? String ?? ""
        switch type {
        case "status": break
        case "start": start()
        case "stop": stop()
        case "show-au-ui": showGoogleAUInterface()
        case "transport-play":
            guard active else { return ["error":"AI host not ready"] }
            transportPlaying.store(true, ordering: .relaxed)
        case "transport-pause":
            guard active else { return ["error":"AI host not ready"] }
            transportPlaying.store(false, ordering: .relaxed)
        case "configure-prompts":
            // Google's AU reads the text strings while loading the model.
            // Changing fullState AFTER it is loaded doesn't update embeddings;
            // require a new ENABLE instead of pretending to hot-swap sound.
            guard !active && !loading,
                  let list = request["prompts"] as? [String],
                  list.count == 4,
                  list.allSatisfy({ !$0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty && $0.count <= 500 }) else {
                return ["error":"Stop Magenta before saving four prompts (maximum 500 characters each)"]
            }
            prompts = list
        case "scene":
            guard let x = request["scene"] as? String, chords[x] != nil else {
                return ["error":"scene must be pyramid or fishes"]
            }
            // Re-selecting the same scene must not turn off notes currently
            // held by a browser click or the Google AU's built-in keyboard.
            if x != scene {
                allNotesOff()
                scene = x
                blend = x == "pyramid" ? 0 : 1
                configure()
            }
        case "mix":
            guard let x = request["value"] as? Double, x.isFinite, x >= 0, x <= 1 else {
                return ["error":"blend must be 0..1"]
            }
            blend = Float(x);configure()
        case "lead-mix":
            guard let which = request["scene"] as? String, chords[which] != nil,
                  let x = request["value"] as? Double, x.isFinite, x >= 0, x <= 1 else {
                return ["error":"lead-mix requires pyramid/fishes scene and a 0..1 mix"]
            }
            leadMix[which] = Float(x);configure()
        case "volume":
            guard let x = request["value"] as? Double, x.isFinite, x >= 0, x <= 1 else {
                return ["error":"volume must be 0..1"]
            }
            level = Float(x);configure()
        case "reverb":
            guard let x = request["value"] as? Double, x.isFinite, x >= 0, x <= 1 else {
                return ["error":"reverb must be 0..1"]
            }
            reverbAmount = Float(x);configure()
        case "mute":
            guard let x = request["value"] as? Bool else {
                return ["error":"mute requires boolean"]
            }
            muted = x;configure()
        case "tempo":
            guard let x = request["bpm"] as? Double, x.isFinite, x >= 60, x <= 190 else {
                return ["error":"tempo must be 60..190 BPM"]
            }
            tempoBpm = x
            // Re-anchor to avoid a 0-beat reset event after tempo edits.
            tempoStart = ProcessInfo.processInfo.systemUptime - 60 / x
        case "note":
            guard active, let n = request["note"] as? Int, (0...127).contains(n) else {
                return ["error":"AI host not ready or invalid MIDI note"]
            }
            let midiNote = UInt8(n)
            if !melodyHeld.contains(midiNote) {
                melodyHeld.insert(midiNote)
                rawMIDI([0x90, midiNote, 82])
            }
        case "note-off":
            guard let n = request["note"] as? Int, (0...127).contains(n) else {
                return ["error":"invalid MIDI note"]
            }
            let midiNote = UInt8(n)
            if melodyHeld.contains(midiNote) {
                melodyHeld.remove(midiNote)
                if !held.contains(midiNote) { rawMIDI([0x80, midiNote, 0]) }
            }
        case "chord":
            guard active, let i = request["index"] as? Int,
                  let notes = chords[scene], (0..<4).contains(i) else {
                return ["error":"AI host not ready or invalid chord index"]
            }
            noteOff()
            held = notes[i]
            chordStartedAt = ProcessInfo.processInfo.systemUptime
            for note in held where !melodyHeld.contains(note) { rawMIDI([0x90, note, 77]) }
        case "release":
            releaseChordAfterMinimumHold()
        default: return ["error":"unknown operation"]
        }
        return report()
    }
}

let host = MRT2Host()
// The reader must not block AVAudioUnit.instantiate callbacks on the main queue.
// Keep all AU graph/state operations on main; stdin IO happens off-thread.
DispatchQueue.global(qos: .userInitiated).async {
    while let line = readLine(strippingNewline: true) {
        guard let data = line.data(using: .utf8),
              let json = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any] else {
            FileHandle.standardOutput.write(Data("{\"error\":\"invalid JSON\"}\n".utf8))
            continue
        }
        DispatchQueue.main.async {
            let value = host.command(json)
            let output = (try? JSONSerialization.data(withJSONObject: value, options: [.sortedKeys]))
                ?? Data("{\"error\":\"serialization failed\"}".utf8)
            FileHandle.standardOutput.write(output + Data([10]))
        }
    }
    DispatchQueue.main.async { host.stop();exit(0) }
}
// AppKit's event loop is needed for interactive controls in the official
// remote AUv3 view controller. The stdin IPC reader still runs separately.
let app = NSApplication.shared
app.setActivationPolicy(.accessory)
app.run()
