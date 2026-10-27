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
    private let prompts = [
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
            "held_notes": held.map(Int.init),
            "text_prompts": prompts,
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
        for note in held { rawMIDI([0x80, note, 0]) }
        held.removeAll()
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
        loading = true
        let desc = AudioComponentDescription(componentType: kAudioUnitType_MusicDevice,
            componentSubType: 0, componentManufacturer: 0,
            componentFlags: 0, componentFlagsMask: 0)
        guard let item = AVAudioUnitComponentManager.shared()
            .components(matching: desc)
            .first(where: { c in
                let name = c.name.lowercased()
                return name.contains("magenta") || name.contains("mrt2")
            }) else {
                loading = false
                errorMessage = "MRT2 native Audio Unit not registered. Open the installed MRT2 (AU) app once, or keep TOASTER browser synth."
                return
            }
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
                    let bookmark: Data
                    do {
                        bookmark = try modelURL.bookmarkData(options: [.withSecurityScope],
                            includingResourceValuesForKeys: nil, relativeTo: nil)
                    } catch {
                        bookmark = try modelURL.bookmarkData(options: [],
                            includingResourceValuesForKeys: nil, relativeTo: nil)
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
        noteOff()
        parameter(6, 1)
        engine?.stop()
        engine = nil
        generator = nil
        reverbUnit = nil
        active = false
        loading = false
        modelRequested = false
        outputSignalDetected = false
    }
    func command(_ request: [String: Any]) -> [String: Any] {
        let type = request["op"] as? String ?? ""
        switch type {
        case "status": break
        case "start": start()
        case "stop": stop()
        case "scene":
            guard let x = request["scene"] as? String, chords[x] != nil else {
                return ["error":"scene must be pyramid or fishes"]
            }
            noteOff();scene = x;blend = x == "pyramid" ? 0 : 1;configure()
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
        case "chord":
            guard active, let i = request["index"] as? Int,
                  let notes = chords[scene], (0..<4).contains(i) else {
                return ["error":"AI host not ready or invalid chord index"]
            }
            noteOff()
            held = notes[i]
            for note in held { rawMIDI([0x90, note, 77]) }
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
