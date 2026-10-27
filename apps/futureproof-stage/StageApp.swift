import SwiftUI
import AppKit
import AVFoundation
import AudioToolbox
import CoreMIDI

// A genuinely standalone AUDIO UNIT HOST for the *already installed* Google
// Magenta MRT2 Small instrument, with the existing native SUZY Toast effect.
// No Qwen, Python process, browser, second neural model, or internet needed.
struct ShowScene {
    let name: String
    let caption: String
    let chords: [(String, [UInt8])]
    let bpm: Int
    let warmth: Float
    let destruction: Float
    let live: Float
    let loop: Float
    let hint: String
}
private let showScenes: [ShowScene] = [
    .init(name: "PYRAMID", caption: "Pyramid Song · opening", chords: [
        ("F♯", [54,58,61]), ("Gmaj7", [55,59,62,66]),
        ("A6", [57,61,64,66]), ("Gmaj7", [55,59,62,66]),
        ("F♯", [54,58,61])
    ], bpm:105, warmth:0.48, destruction:0.02, live:0.18, loop:0.24,
       hint:"Quiet. Floating piano and voice lead. AI becomes a distant instrument."),
    .init(name: "EVOLVE", caption: "Appliance Latent Space · improvisation", chords: [
        ("Em7",[52,55,59,62]), ("A6",[57,61,64,66]),
        ("Gmaj7",[55,59,62,66]), ("F♯m7",[54,57,61,64])
    ], bpm:120, warmth:0.23, destruction:0.24, live:0.65, loop:0.54,
       hint:"The loop is a captured AI phrase, not a backing-track obligation."),
    .init(name: "FISHES", caption: "Weird Fishes/Arpeggi · closing", chords: [
        ("Em7",[52,55,59,62]), ("F♯m7",[54,57,61,64]),
        ("A",[57,61,64]), ("Gmaj7",[55,59,62,66])
    ], bpm:153, warmth:0.30, destruction:0.05, live:0.22, loop:0.36,
       hint:"Your arpeggio/pulse leads. The generated AI stays in the background.")
]

// Audio callback lives off the UI thread. We forward only short MIDI voice
// events; neither Logic nor a virtual MIDI device is needed for this host.
private final class PhysicalKeyboard {
    private var client = MIDIClientRef()
    private var port = MIDIPortRef()
    private var endpoint = MIDIEndpointRef()
    var receive: (([UInt8]) -> Void)?
    private(set) var name = "NO MIDI KEYBOARD"
    init() {
        MIDIClientCreateWithBlock("SUZY TOAST STAGE" as CFString, &client) { _ in }
        MIDIInputPortCreateWithBlock(client, "Keystation input" as CFString, &port) { [weak self] packets, _ in
            guard let self else { return }
            var p = UnsafeRawPointer(packets)
                .advanced(by: MemoryLayout<MIDIPacketList>.offset(of: \.packet)!)
                .assumingMemoryBound(to: MIDIPacket.self)
            for _ in 0..<packets.pointee.numPackets {
                let count = Int(p.pointee.length)
                if count > 0 && count <= 256 {
                    let bytes = UnsafeRawPointer(p)
                        .advanced(by: MemoryLayout<MIDIPacket>.offset(of: \.data)!)
                        .assumingMemoryBound(to: UInt8.self)
                    self.receive?(Array(UnsafeBufferPointer(start: bytes, count: count)))
                }
                p = UnsafePointer(MIDIPacketNext(p))
            }
        }
    }
    func autoConnect() -> String {
        if endpoint != 0 { MIDIPortDisconnectSource(port, endpoint); endpoint = 0 }
        let count = MIDIGetNumberOfSources()
        guard count > 0 else { name = "NO MIDI DEVICE"; return name }
        var preferred: (MIDIEndpointRef, String, Int)?
        for i in 0..<count {
            let ep = MIDIGetSource(i)
            var cf: Unmanaged<CFString>?
            MIDIObjectGetStringProperty(ep, kMIDIPropertyDisplayName, &cf)
            let name = cf?.takeRetainedValue() as String? ?? "MIDI (i + 1)"
            let lower = name.lowercased()
            let score = lower.contains("keystation") ? 3 :
              (lower.contains("keyboard") || lower.contains("m-audio")) ? 2 :
              (lower.contains("network") || lower.contains("suzy ai midi") || lower.contains("iac")) ? 0 : 1
            if preferred == nil || score > preferred!.2 { preferred = (ep, name, score) }
        }
        guard let choice = preferred, choice.2 > 0 else {
            name = "NO PHYSICAL MIDI SOURCE"; return name
        }
        endpoint = choice.0
        MIDIPortConnectSource(port, endpoint, nil)
        name = choice.1
        return name
    }
    deinit {
        if endpoint != 0 { MIDIPortDisconnectSource(port, endpoint) }
        MIDIPortDispose(port); MIDIClientDispose(client)
    }
}

@MainActor final class Stage: ObservableObject {
    @Published var message = "STANDBY · Press START STANDALONE to host Magenta."
    @Published var ready = false
    @Published var starting = false
    @Published var hasToast = false
    @Published var micOn = false
    @Published var backingOn = true
    @Published var keyboardName = "CONNECTING…"
    @Published var selectedScene = 0
    @Published var chordIndex = 0
    @Published var liveGain = 0.2
    @Published var loopGain = 0.4
    @Published var loopState = "IDLE"
    private var engine: AVAudioEngine?
    private var generator: AVAudioUnit?
    private var toaster: AVAudioUnit?
    private var micMixer: AVAudioMixerNode?
    private var backingPlayer: AVAudioPlayerNode?
    private var backingBuffer: AVAudioPCMBuffer?
    private var keyboard: PhysicalKeyboard?
    private var heldChord: [UInt8] = []
    private var commandSequence = 0
    private var meterTimer: Timer?

    init() {
        let kb = PhysicalKeyboard()
        keyboard = kb
        keyboardName = kb.autoConnect()
    }

    private func component(_ type: OSType, nameTerms: [String]) -> AVAudioUnitComponent? {
        let desc = AudioComponentDescription(componentType: type,
            componentSubType: 0, componentManufacturer: 0,
            componentFlags: 0, componentFlagsMask: 0)
        return AVAudioUnitComponentManager.shared()
            .components(matching: desc)
            .first { item in nameTerms.contains { item.name.lowercased().contains($0) } }
    }

    private func instantiate(_ desc: AudioComponentDescription) async throws -> AVAudioUnit {
        try await withCheckedThrowingContinuation { continuation in
            AVAudioUnit.instantiate(with: desc, options: []) { unit, error in
                if let unit { continuation.resume(returning: unit) }
                else { continuation.resume(throwing: error ?? NSError(domain: "SUZY", code: 1,
                     userInfo:[NSLocalizedDescriptionKey:"Audio Unit could not be instantiated"])) }
            }
        }
    }

    // The AU parameter's address/identifier is exposed by the AU host.
    // We set only known POST-AI processor parameters, never Google style/PCA.
    private func param(_ id: String, _ number: Float) {
        // AUv2 hosts sometimes expose a numeric parameter ID rather than
        // JUCE's text key. Match the real, unambiguous display name too.
        let names: [String: String] = [
            "browning":"Browning", "destruction":"Destruction",
            "live":"AI Live", "loop":"Loop Mix", "bpm":"Manual loop BPM",
            "beats":"Beats per bar", "bars":"Record bars",
            "scene":"Live set scene", "control":"External loop command"
        ]
        guard let parameters = toaster?.auAudioUnit.parameterTree?.allParameters else { return }
        let p = parameters.first { $0.identifier.caseInsensitiveCompare(id) == .orderedSame }
            ?? parameters.first {
                $0.displayName.caseInsensitiveCompare(names[id] ?? id) == .orderedSame
            }
        p?.value = number
    }

    private func midi(_ notes: [UInt8]) {
        guard let callback = generator?.auAudioUnit.scheduleMIDIEventBlock else { return }
        notes.withUnsafeBufferPointer { pointer in
            guard let base = pointer.baseAddress, !notes.isEmpty else { return }
            callback(AUEventSampleTimeImmediate, 0, notes.count, base)
        }
    }

    private func releaseCue() {
        for n in heldChord { midi([0x80, n, 0]) }
        heldChord.removeAll()
    }

    private func sendCue() {
        guard ready else { return }
        releaseCue()
        let cues = showScenes[selectedScene].chords
        let notes = cues[chordIndex % cues.count].1
        heldChord = notes
        for n in notes { midi([0x90, n, 77]) }
    }

    func nextChord() {
        let count = showScenes[selectedScene].chords.count
        chordIndex = (chordIndex + 1) % count
        sendCue()
    }

    func previousChord() {
        let count = showScenes[selectedScene].chords.count
        chordIndex = (chordIndex - 1 + count) % count
        sendCue()
    }


    // Bundled original audio scaffolds: no samples or internet needed.
    private func playSceneBacking() {
        guard let player = backingPlayer,
            let url = Bundle.main.url(forResource:
                showScenes[selectedScene].name.lowercased(), withExtension:"wav") else { return }
        do {
            let file = try AVAudioFile(forReading: url)
            guard file.length > 0 && file.length < 48_000 * 60,
                let buffer = AVAudioPCMBuffer(pcmFormat:file.processingFormat,
                    frameCapacity:AVAudioFrameCount(file.length)) else { return }
            try file.read(into:buffer)
            player.stop()
            backingBuffer = buffer
            player.scheduleBuffer(buffer, at:nil, options:[.loops], completionHandler:nil)
            player.volume = 0.42
            if backingOn { player.play() }
        } catch { message = "Backing could not load: \(error.localizedDescription)" }
    }

    func toggleBacking() {
        backingOn.toggle()
        if backingOn { backingPlayer?.play() } else { backingPlayer?.pause() }
    }

    // First launch copies bundled SUZY Toast AU only to the user's own
    // components directory. No admin, no modifying Google's Magenta bundle.
    private func installBundledToastIfNeeded() {
        guard let embedded = Bundle.main.resourceURL?
            .appendingPathComponent("SUZY Toast.component", isDirectory:true),
            FileManager.default.fileExists(atPath:embedded.path) else { return }
        let folder = FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent("Library/Audio/Plug-Ins/Components", isDirectory:true)
        let dest = folder.appendingPathComponent("SUZY Toast.component", isDirectory:true)
        guard !FileManager.default.fileExists(atPath:dest.path) else { return }
        do {
            try FileManager.default.createDirectory(at:folder,withIntermediateDirectories:true)
            try FileManager.default.copyItem(at:embedded,to:dest)
        } catch { message = "Toast installation blocked: \(error.localizedDescription)" }
    }

    func selectScene(_ index: Int) {
        guard showScenes.indices.contains(index) else { return }
        releaseCue()
        selectedScene = index; chordIndex = 0
        let s = showScenes[index]
        liveGain = Double(s.live); loopGain = Double(s.loop)
        param("scene", Float(index))
        param("browning", s.warmth)
        param("destruction", s.destruction)
        param("live", s.live)
        param("loop", s.loop)
        param("bpm", Float(s.bpm))
        param("beats", 4); param("bars", 1)
        if ready { sendCue(); playSceneBacking() }
        message = "(s.name) · Play your keyboard; press NEXT CHORD to steer Magenta."
    }

    private func command(_ id: Int) {
        guard ready && hasToast else {
            message = "AI generates, but the SUZY Toast effect is not registered. Loop controls are unavailable."
            return
        }
        commandSequence = (commandSequence + 1) % 8191
        param("control", Float(commandSequence * 8 + id))
        switch id {
        case 1: loopState = "RECORD SENT · CHECK SOUND"
        case 2: loopState = "PLAY SENT"
        case 3: loopState = "OVERDUB SENT"
        case 4: loopState = "STOP SENT"
        case 5: loopState = "CLEAR SENT"
        default: break
        }
    }
    func record() { command(1) }
    func play() { command(2) }
    func overdub() { command(3) }
    func stopLoop() { command(4) }
    func clear() { command(5) }

    func setLive(_ val: Double) { liveGain = val; param("live", Float(val)) }
    func setLoop(_ val: Double) { loopGain = val; param("loop", Float(val)) }

    func openLogic() {
        shutdown()
        if let url = NSWorkspace.shared.urlForApplication(withBundleIdentifier: "com.apple.logic10") {
            NSWorkspace.shared.openApplication(at: url, configuration: NSWorkspace.OpenConfiguration()) { _, err in
                if let err { Task { @MainActor in self.message = "Logic could not open: (err.localizedDescription)" } }
            }
            message = "Logic is opening. Standalone audio is stopped to avoid two model instances."
        } else {
            message = "Logic Pro is not installed. START STANDALONE does not require it."
        }
    }

    func start() {
        guard !ready && !starting else { return }
        starting = true
        installBundledToastIfNeeded()
        message = "Finding the installed Google Magenta MIDI Audio Unit…"
        Task {
            defer { starting = false }
            guard let magentaComponent = component(kAudioUnitType_MusicDevice,
                 nameTerms: ["magenta realtime", "magenta real", "mrt2", "magenta"]) else {
                message = "Google Magenta MRT2 instrument not registered. This app does not download Google's model."
                return
            }
            do {
                let unit = try await instantiate(magentaComponent.audioComponentDescription)
                // Resolve the optional AU effect only after the official generator.
                let toastComponent = component(kAudioUnitType_Effect, nameTerms:["suzy toast"])
                var fx: AVAudioUnit?
                if let toastComponent {
                    fx = try? await instantiate(toastComponent.audioComponentDescription)
                }
                let e = AVAudioEngine()
                e.attach(unit)
                let backing = AVAudioPlayerNode()
                e.attach(backing)
                let backingFormat = AVAudioFormat(standardFormatWithSampleRate:48000, channels:2)!
                e.connect(backing, to:e.mainMixerNode, format:backingFormat)
                if let fx {
                    e.attach(fx)
                    e.connect(unit, to: fx, format: nil)
                    e.connect(fx, to: e.mainMixerNode, format: nil)
                } else {
                    e.connect(unit, to: e.mainMixerNode, format: nil)
                }
                // Microphone is optional but has its own mixer and kill. It
                // is NOT sent into the AI instrument or recordable toaster.
                let vm = AVAudioMixerNode()
                e.attach(vm)
                e.connect(e.inputNode, to: vm, format: e.inputNode.outputFormat(forBus: 0))
                e.connect(vm, to: e.mainMixerNode, format: nil)
                vm.outputVolume = 0.0
                try e.start()
                engine = e; generator = unit; toaster = fx; micMixer = vm
                backingPlayer = backing
                hasToast = fx != nil
                ready = true
                keyboardName = keyboard?.autoConnect() ?? "NO PHYSICAL MIDI DEVICE"
                let generatorRef = unit
                keyboard?.receive = { events in
                    // MIDI callback must not mutate SwiftUI state.
                    guard events.count >= 3,
                        events[0] >= 0x80, events[0] < 0xF0 else { return }
                    let message = [events[0], events[1], events[2]]
                    if let callback = generatorRef.auAudioUnit.scheduleMIDIEventBlock {
                        message.withUnsafeBufferPointer { p in
                            if let base = p.baseAddress {
                                callback(AUEventSampleTimeImmediate, 0, message.count, base)
                            }
                        }
                    }
                }
                selectScene(selectedScene)
                message = hasToast
                    ? "LIVE · Google Magenta → SUZY Toast → system audio output. One model."
                    : "LIVE · Magenta direct. Toast component missing; looping disabled."
                // Ask only when voice is explicitly enabled to avoid blocking
                // a MIDI-only performance on system privacy dialogs.
            } catch {
                shutdown()
                message = "Standalone host not ready: (error.localizedDescription). Open Logic for the tested fallback."
            }
        }
    }

    func toggleMicrophone() {
        guard ready else { message = "Start audio first."; return }
        if micOn {
            micMixer?.outputVolume = 0
            micOn = false
            return
        }
        AVCaptureDevice.requestAccess(for: .audio) { allowed in
            Task { @MainActor in
                self.micMixer?.outputVolume = allowed ? 0.8 : 0
                self.micOn = allowed
                if !allowed { self.message = "Microphone access declined. MIDI/AI remain usable." }
            }
        }
    }

    func shutdown() {
        releaseCue()
        keyboard?.receive = nil
        micMixer?.outputVolume = 0
        engine?.stop()
        engine = nil
        backingPlayer = nil
        backingBuffer = nil
        generator = nil
        toaster = nil
        micMixer = nil
        ready = false; micOn = false; hasToast = false; loopState = "IDLE"
    }

    var nowChord: String { showScenes[selectedScene].chords[chordIndex].0 }
    var scene: ShowScene { showScenes[selectedScene] }
}

@main struct FutureproofApp: App {
    @StateObject private var stage = Stage()
    var body: some Scene {
        WindowGroup("SUZY//TOAST · FUTUREPROOF") {
            StageView(model: stage)
                .onDisappear { stage.shutdown() }
        }
        .windowStyle(.titleBar)
        .commands { CommandGroup(replacing: .newItem) {} }
    }
}

private struct StageView: View {
    @ObservedObject var model: Stage
    private let ink = Color(red:0.12, green:0.1, blue:0.17)
    private let peach = Color(red:1, green:0.73, blue:0.64)
    private let mint = Color(red:0.65, green:0.94, blue:0.75)
    var body: some View {
        VStack(alignment:.leading,spacing:14) {
            HStack {
                VStack(alignment:.leading,spacing:3) {
                    Text("SUZY//TOAST").font(.system(size:34,weight:.black,design:.rounded))
                    Text("THE APPLIANCE LATENT SPACE   /   FUTUREPROOF 2026")
                        .font(.system(size:12,weight:.semibold,design:.monospaced)).foregroundStyle(mint)
                }
                Spacer()
                Circle().fill(model.ready ? mint : .gray).frame(width:12,height:12)
                Text(model.ready ? "LIVE" : "STANDBY").font(.system(.caption,design:.monospaced))
            }
            HStack(spacing:10) {
                Button("▶ START STANDALONE") { model.start() }
                    .disabled(model.ready || model.starting)
                    .buttonStyle(.borderedProminent)
                Button("OPEN LOGIC") { model.openLogic() }
                Button("■ STOP AUDIO") { model.shutdown() }.disabled(!model.ready)
                Spacer()
                Text("ONE MAGENTA MODEL").font(.system(size:11,weight:.bold,design:.monospaced))
                    .foregroundStyle(mint)
            }.controlSize(.large)
            HStack(spacing:9) {
                ForEach(0..<3,id:\.self) { i in
                    Button {
                        model.selectScene(i)
                    } label: {
                        VStack(spacing:7) {
                            Text(String(format:"0%d",i+1)).font(.system(size:13,weight:.semibold,design:.monospaced))
                            Text(showScenes[i].name).font(.system(size:17,weight:.heavy,design:.rounded))
                            Text(showScenes[i].caption).font(.system(size:11)).lineLimit(2)
                        }
                        .frame(maxWidth:.infinity,minHeight:85)
                        .padding(6)
                        .background(model.selectedScene == i ? peach : ink.opacity(0.7))
                        .foregroundColor(model.selectedScene == i ? ink : .white)
                        .clipShape(RoundedRectangle(cornerRadius:14))
                    }.buttonStyle(.plain)
                }
            }
            HStack {
                VStack(alignment:.leading,spacing:9) {
                    Text("NEXT HARMONY").font(.system(size:11,weight:.bold,design:.monospaced)).foregroundStyle(.secondary)
                    Text(model.nowChord).font(.system(size:40,weight:.black,design:.rounded)).foregroundStyle(peach)
                    HStack {
                        Button("◀ PREVIOUS") { model.previousChord() }
                        Button("NEXT CHORD ▶") { model.nextChord() }
                            .buttonStyle(.borderedProminent)
                    }
                }.frame(width:230,alignment:.leading)
                Spacer()
                VStack(alignment:.leading,spacing:6) {
                    Text(model.scene.hint).font(.system(size:14)).fixedSize(horizontal:false,vertical:true)
                    Text("Keystation: (model.keyboardName)")
                        .font(.system(size:11,design:.monospaced)).foregroundStyle(mint)
                    Text("Cue buttons actually send held MIDI chords to Magenta. Play or replace them on the keyboard.")
                        .font(.system(size:11)).foregroundStyle(.secondary)
                }.frame(maxWidth:.infinity,alignment:.leading)
            }.padding(14).background(ink.opacity(0.7)).clipShape(RoundedRectangle(cornerRadius:14))
            HStack(spacing:10) {
                Button("● RECORD") { model.record() }
                Button("↻ OVERDUB") { model.overdub() }
                Button("▶ PLAY") { model.play() }
                Button("■ STOP") { model.stopLoop() }
                Button("CLEAR") { model.clear() }
            }.disabled(!model.ready || !model.hasToast).controlSize(.large)
            HStack {
                Text("LIVE AI")
                Slider(value:Binding(get:{model.liveGain},set:{model.setLive($0)}),in:0...1)
                Text("LOOP")
                Slider(value:Binding(get:{model.loopGain},set:{model.setLoop($0)}),in:0...1)
            }
            HStack {
                Button(model.backingOn ? "♫ BACKING ON · MUTE" : "♫ BACKING OFF · PLAY") {
                    model.toggleBacking()
                }.disabled(!model.ready)
                Text("Original generated piano, beat and arpeggio loops load with each section.")
                    .font(.system(size:11)).foregroundStyle(.secondary)
            }
            HStack {
                Button(model.micOn ? "🎤 MIC ON · MUTE" : "🎤 ENABLE VOCAL INPUT") {
                    model.toggleMicrophone()
                }.disabled(!model.ready)
                Text("VE-22 → system input · monitoring must be checked to prevent doubling")
                    .font(.system(size:11)).foregroundStyle(.secondary)
            }
            Text("LOOPER: (model.loopState)   |   (model.message)")
                .font(.system(size:12,weight:.medium,design:.monospaced))
                .foregroundStyle(mint)
                .lineLimit(3)
                .frame(maxWidth:.infinity,alignment:.leading)
                .padding(12).background(ink).clipShape(RoundedRectangle(cornerRadius:9))
            Text("Experimental standalone Audio Unit host · Google MRT2 and SUZY Toast must be installed · Doesn't launch Logic and standalone simultaneously.")
                .font(.system(size:10)).foregroundStyle(.secondary)
        }
        .padding(24)
        .frame(minWidth:850,minHeight:620)
        .background(Color(red:0.16,green:0.12,blue:0.19))
        .foregroundStyle(.white)
    }
}
