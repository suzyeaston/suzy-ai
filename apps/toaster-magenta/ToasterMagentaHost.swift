// SUZY//TOAST · native MRT2 prompt host (macOS only).
// One real AVAudioUnit instance; line-delimited JSON protocol on stdin/stdout.
// No UI web automation and no fake neural audio. The AU may take time to load
// its local MLX model; "audio engine started" is not proof of generated sound.
import Foundation
import AVFoundation
import AudioToolbox

final class MRT2Host {
    private var engine: AVAudioEngine?
    private var generator: AVAudioUnit?
    private var reverbUnit: AVAudioUnitReverb?
    private var held: [UInt8] = []
    private var melodyHeld = Set<UInt8>()
    private var tempoBpm: Double = 105.0
    private var tempoStart = ProcessInfo.processInfo.systemUptime
    private var active = false
    private var loading = false
    private var modelRequested = false
    private var errorMessage = ""
    private var modelPath = ""
    private var scene = "pyramid"
    private var blend: Float = 0
    private var level: Float = 0.28
    private var reverbAmount: Float = 0.18
    private var muted = false
    private var outputSignalDetected = false
    private var auComponentName = ""
    private var assetPath = ""
    private var bookmarkScopeVerified = false
    private var modelFileBytes: Int64 = 0
    private var outputRate: Double = 0
    private var prompts = [
        "Intimate warm piano chords, fragile orchestral strings, sparse melancholic experimental art rock, slow floating asymmetric pulse, soft bass, subtle ambient textures, restrained percussion, no vocals",
        "Interlocking clean guitar arpeggios, shimmering echoes, hypnotic experimental art rock, flowing bass, understated drums, glassy synthesizers, gradually building ethereal atmosphere, no vocals",
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
            // Google's AU doesn't expose a public loaded/model-audible getter.
            // This only confirms a nonzero PCM signal at the native host mixer,
            // never the physical headphones or correct Magenta semantics.
            "model_audio_confirmed": outputSignalDetected,
            "output_signal_detected": outputSignalDetected,
            "model_path": modelPath,
            "error": errorMessage,
            "scene": scene,
            "blend": Double(blend),
            "volume": Double(level),
            "reverb": Double(reverbAmount),
            "muted": muted,
            "held_notes": (held + Array(melodyHeld)).map(Int.init),
            "tempo_bpm": tempoBpm,
            "tempo_context_supplied": generator != nil,
            "text_prompts": prompts,
            "au_component": auComponentName,
            "musiccoca_assets_path": assetPath,
            "bookmark_scope_verified": bookmarkScopeVerified,
            "host_model_loaded": false,
            "host_model_load_state": modelRequested ? "requested_asynchronously_by_google_AU_not_confirmed" : "not_requested",
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
        // Weights 0/1 are real native AU text-prompt weights, not browser presets.
        parameter(10, 1.0 - blend)
        parameter(11, blend)
        parameter(39, 1.0) // Google "Filter Drums"
        parameter(4, 5.0)  // Note Adherence; human notes have priority.
        parameter(3, 2.5)  // Prompt Adherence
        parameter(45, 1.0) // MIDI gate: cease AI when notes released.
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
    private func noteOff() {
        for note in held where !melodyHeld.contains(note) { rawMIDI([0x80, note, 0]) }
        held.removeAll()
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
                    // Bookmark + text prompts are consumed by Google's AU's
                    // applyCustomState and set_text_prompts during model load.
                    let modelURL = URL(fileURLWithPath: path)
                    // A plain unscoped fallback bookmark cannot satisfy Google's
                    // exact AU loader, which requires startAccessingSecurityScopedResource.
                    // Reject it explicitly instead of reporting a running but silent AU.
                    let bookmark = try modelURL.bookmarkData(options: [.withSecurityScope],
                        includingResourceValuesForKeys: nil, relativeTo: nil)
                    var stale = false
                    let checkedURL = try URL(resolvingBookmarkData: bookmark,
                        options: [.withSecurityScope, .withoutUI], relativeTo: nil,
                        bookmarkDataIsStale: &stale)
                    let scoped = checkedURL.startAccessingSecurityScopedResource()
                    self.bookmarkScopeVerified = scoped
                    if scoped { checkedURL.stopAccessingSecurityScopedResource() }
                    guard scoped, !stale else {
                        throw NSError(domain: "SUZY.TOAST.MRT2", code: 11,
                            userInfo: [NSLocalizedDescriptionKey:
                                "Google AU needs a usable security-scoped model bookmark. Bookmark scope could not be verified."])
                    }
                    var state = unit.auAudioUnit.fullState ?? [:]
                    let weighted = self.prompts.enumerated().map { (i,text) in
                        ["text": text, "weight": i == 0 ? 1.0 : 0.0] as [String: Any]
                    }
                    state["MGRT_Prompts"] = weighted + (0..<4).map { _ in ["text":"","weight":0.0] as [String:Any] }
                    state["MGRT_ModelBookmark"] = bookmark
                    state["MGRT_ModelName"] = "mrt2_small"
                    unit.auAudioUnit.fullState = state
                    self.modelRequested = true
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
    func stop() {
        allNotesOff()
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
    }
    func command(_ request: [String: Any]) -> [String: Any] {
        let type = request["op"] as? String ?? ""
        switch type {
        case "status": break
        case "start": start()
        case "stop": stop()
        case "configure-prompts":
            // Google's AU reads the text strings while loading the model.
            // Changing fullState AFTER it is loaded doesn't update embeddings;
            // require a new ENABLE instead of pretending to hot-swap sound.
            guard !active && !loading,
                  let list = request["prompts"] as? [String],
                  list.count == 2,
                  list.allSatisfy({ !$0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty && $0.count <= 500 }) else {
                return ["error":"Stop Magenta before saving two prompts (maximum 500 characters each)"]
            }
            prompts = list
        case "scene":
            guard let x = request["scene"] as? String, chords[x] != nil else {
                return ["error":"scene must be pyramid or fishes"]
            }
            allNotesOff();scene = x;blend = x == "pyramid" ? 0 : 1;configure()
        case "mix":
            guard let x = request["value"] as? Double, x.isFinite, x >= 0, x <= 1 else {
                return ["error":"blend must be 0..1"]
            }
            blend = Float(x);configure()
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
            for note in held where !melodyHeld.contains(note) { rawMIDI([0x90, note, 77]) }
        case "release":
            noteOff()
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
RunLoop.main.run()
