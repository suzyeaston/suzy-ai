import AppKit
import AVFoundation
import SwiftUI
import CompanionCore
import UniformTypeIdentifiers

private final class AudioLoop: LoopPlayer {
    let player: AVAudioPlayer
    init(_ player: AVAudioPlayer) { self.player = player }
    func start(at time: Double?) -> Bool { time.map { player.play(atTime: $0) } ?? player.play() }
    func stop() { player.stop() }
}

@MainActor final class Performance: ObservableObject {
    let looper = LocalLooper()
    @Published var backgroundAI = true { didSet { if !backgroundAI { sourceChanged(nil) } } }
    @Published var phase = "idle"
    @Published var message = "Select Focusrite as macOS input/output, then Connect. Audition shares the audience output."
    @Published var bpm = 120.0
    @Published var duration = 4.0
    @Published var mode = "mirror"
    @Published var provider = "deterministic"
    @Published var section = ""
    @Published var musicalKey = ""
    @Published var direction = ""
    @Published var channel = 0
    @Published var volume: Float = 0.35 { didSet {
        preview?.volume = volume
        (slot.current as? AudioLoop)?.player.volume = volume
        (slot.pending as? AudioLoop)?.player.volume = volume
    } }
    @Published var meter: Float = -60
    @Published var elapsed = 0.0
    @Published var midiSource: UInt32 = 0 { didSet { midi.select(midiSource) } }
    @Published var midiChannel = 16
    @Published var midiSources: [MIDIController.Source] = []
    @Published var clockSource: UInt32 = 0 { didSet { clockInput.select(clockSource); invalidateClock() } }
    @Published var syncEnabled = false { didSet { invalidateClock() } }
    @Published var beatsPerBar = 4
    @Published var captureBeats = 4
    @Published var clockLabel = "Clock off"
    @Published var connected = false
    @Published var loopPlaying = false
    @Published var actionBusy = false
    @Published var auditionAcknowledged = false
    @Published var savePanelOpen = false
    private let bridge = Bridge()
    private let midi = MIDIController()
    private let clockInput = MIDIController()
    private var clock = MIDIClock()
    private var preview: AVAudioPlayer?
    private let slot = PlaybackSlot()
    private var responseAudio: Data?
    private var acceptedAudio: Data?
    private var captureID: String?
    private var epoch = 0
    private var timer: Timer?
    private var ticks = 0
    private var captureTempo: Double?
    private var loopTempo: Double?
    private var pendingBoundary: Double?
    private var pendingRevision: Int?
    private var pendingAudio: Data?
    private var pendingTempo: Double?

    var canCapture: Bool { connected && !actionBusy && ["idle", "accepted", "failed"].contains(phase) }
    var canRespond: Bool { !actionBusy && ["ready", "auditioning"].contains(phase) }
    var canSave: Bool { !savePanelOpen && !actionBusy && (canRespond || responseAudio != nil || acceptedAudio != nil) }

    init() {
        looper.onSnapshot = { [weak self] wav in self?.sourceChanged(wav) }
        refreshMIDI()
        midi.onEvents = { [weak self] events, overflow in
            guard let self else { return }
            if overflow { self.stopAll(); self.message = "MIDI overflow: companion stopped. Reduce controller traffic."; return }
            for event in events {
                guard case let .note(channel, note) = event.event, channel == self.midiChannel else { continue }
                switch note {
                case 36: self.captureOrFinish()
                case 37: self.audition()
                case 38: self.accept()
                case 39: self.stopAll()
                case 40: self.discard()
                case 41: self.looper.overdub()
                case 42: self.looper.undo()
                case 43: self.looper.muted.toggle()
                case 44: self.looper.clear()
                case 45: self.looper.play()
                default: break
                }
            }
        }
        clockInput.onEvents = { [weak self] events, overflow in
            guard let self else { return }
            if overflow { self.invalidateClock(); self.message = "Clock overflow: synchronized audio stopped."; return }
            for event in events {
                let revision = self.clock.revision
                self.clock.receive(event.event, at: event.time)
                if self.syncEnabled && self.clock.revision != revision { self.cancelSynchronized("Logic transport changed; synchronized capture/playback stopped.") }
            }
        }
        timer = Timer.scheduledTimer(withTimeInterval: 0.02, repeats: true) { [weak self] _ in
            Task { @MainActor [weak self] in self?.tick() }
        }
    }
    private func tick() {
        midi.drain(); clockInput.drain()
        let now = MIDIController.now
        ticks += 1
        if syncEnabled {
            let locked = clock.locked(at: now)
            if ticks % 5 == 0 { clockLabel = locked ? String(format: "Logic clock %.1f BPM", clock.bpm ?? 0) : "Waiting for Logic Start + clock" }
            if !locked { cancelSynchronized("Logic clock lost: synchronized capture/playback stopped.") }
            if let tempo = pendingTempo ?? loopTempo ?? looper.tempo, let current = clock.bpm, abs(current-tempo)/tempo > 0.01 {
                cancelSynchronized("Tempo changed. Capture a new phrase at the new tempo.")
            }
        } else if ticks % 5 == 0 { clockLabel = "Free timing" }
        if let boundary = pendingBoundary, now >= boundary {
            guard !syncEnabled || (clock.locked(at: now) && clock.revision == pendingRevision) else {
                cancelSynchronized("Clock changed before launch."); return
            }
            slot.commit(); loopTempo = pendingTempo; pendingTempo = nil; acceptedAudio = pendingAudio; pendingAudio = nil; pendingBoundary = nil
            loopPlaying = true; phase = "accepted"; actionBusy = false
            message = "Response looping. Capture another phrase when ready."
        }
    }

    private func invalidateClock() {
        cancelSynchronized("Clock source/mode changed; synchronized audio stopped.")
        clock = MIDIClock()
    }
    private func cancelSynchronized(_ reason: String) {
        let recording = captureTempo != nil && ["arming", "queued capture", "capturing", "finalizing"].contains(phase)
        if recording || pendingBoundary != nil || loopTempo != nil || (looper.isSynchronized && (looper.playing || looper.busy)) {
            stopAll(); message = reason
        }
    }
    func refreshMIDI() { midiSources = midi.sources() }
    func connect() {
        guard !actionBusy, !["arming", "queued capture", "capturing", "processing"].contains(phase) else { return }
        Task {
            do {
                let status = try await bridge.status(); connected = true
                message = ["idle", "discarded"].contains(status.state) ? "Bridge connected." : "Bridge has a \(status.state) phrase. Reset if it belongs to this session."
            } catch { connected = false; message = "Start bridge on 7333, then Connect. \(error.localizedDescription)" }
        }
    }
    func captureOrFinish() {
        if looper.state == "recording" {
            looper.record(channel: channel, duration: duration, tempo: nil, start: nil); return
        }
        let now = MIDIController.now
        if syncEnabled && !clock.locked(at: now) { looper.message = "Start Logic and wait for its clock before recording."; return }
        let tempo = syncEnabled ? clock.bpm : nil
        let seconds = tempo.map { Double(captureBeats)*60/$0 } ?? duration
        looper.record(channel: channel, duration: seconds, tempo: tempo,
                      start: syncEnabled ? clock.nextBoundary(at: now, beats: beatsPerBar, lead: 0.3) : nil)
    }
    func requestBackgroundResponse() { sourceChanged(looper.history.current) }
    private func sourceChanged(_ wav: Data?) {
        // Only AI state is invalidated. The local looper never waits for this task.
        epoch += 1; let token = epoch; let oldID = captureID
        captureID = nil; responseAudio = nil; preview?.stop(); preview = nil
        slot.stop(); pendingBoundary = nil; pendingAudio = nil; pendingTempo = nil; loopTempo = nil
        loopPlaying = false; phase = "idle"; actionBusy = false
        captureTempo = looper.tempo
        let selectedBPM = looper.tempo ?? bpm
        let selectedMode = mode, selectedProvider = provider
        let selectedSection = String(section.prefix(64)), key = String(musicalKey.prefix(24)), instruction = String(direction.prefix(500))
        let enabled = backgroundAI && connected && wav != nil
        message = enabled ? "Original loop playing; preparing a background variation." : "Local looper is independent. Connect/enable AI and request a variation when wanted."
        if enabled { phase = "processing" }
        Task {
            if let oldID { try? await bridge.action(id: oldID, name: "discard") }
            guard token == epoch, enabled, let wav else { return }
            do {
                let pcm = try PCM(wav: wav)
                await sendCapture(pcm, mode: selectedMode, provider: selectedProvider, bpm: selectedBPM,
                                  section: selectedSection, key: key, instruction: instruction, token: token)
            } catch { if token == epoch { fail(error.localizedDescription) } }
        }
    }
    private func sendCapture(_ pcm: PCM, mode: String, provider: String, bpm: Double, section: String, key: String, instruction: String, token: Int) async {
        do {
            let id = try await bridge.arm(rate: pcm.rate, channels: pcm.channels, bpm: bpm, mode: mode, provider: provider, section: section, key: key, instruction: instruction)
            guard token == epoch else { try? await bridge.action(id: id, name: "discard"); return }
            captureID = id
            for (sequence, offset) in stride(from: 0, to: pcm.data.count, by: 32768).enumerated() {
                guard token == epoch else { return }
                try await bridge.chunk(id: id, sequence: sequence, data: pcm.data.subdata(in: offset..<min(offset+32768, pcm.data.count)))
            }
            guard token == epoch else { return }
            try await bridge.action(id: id, name: "finish")
            let deadline = Date().addingTimeInterval(20)
            while token == epoch && Date() < deadline {
                let status = try await bridge.status()
                guard token == epoch else { return }
                guard status.id == id else { throw CompanionError.invalid("Bridge phrase changed in another client.") }
                if status.state == "ready" {
                    phase = "ready"; message = "Original loop continues. Response ready · \(status.response?.provider ?? "unknown"). Save, audition on shared output, or bring in."; return
                }
                if status.state == "failed" { throw CompanionError.invalid(status.error ?? "Response failed.") }
                try await Task.sleep(nanoseconds: 200_000_000)
            }
            if token == epoch { throw CompanionError.invalid("Response deadline reached.") }
        } catch {
            if token == epoch {
                if let id = captureID { try? await bridge.action(id: id, name: "discard") }
                guard token == epoch else { return }; captureID = nil; fail(error.localizedDescription)
            }
        }
    }
    private func candidate(id: String, token: Int) async throws -> Data {
        if let responseAudio { return responseAudio }
        // Backend 'audition' authorizes download; it never starts a device itself.
        try await bridge.action(id: id, name: "audition")
        guard token == epoch else { throw CancellationError() }
        phase = "auditioning"
        let data = try await bridge.audio(id: id)
        guard token == epoch else { throw CancellationError() }
        _ = try PCM(wav: data); responseAudio = data; return data
    }
    func audition() {
        guard canRespond, let id = captureID else { return }
        guard auditionAcknowledged else { message = "Audition is audible on the audience output. Acknowledge shared-output audition first."; return }
        actionBusy = true; let token = epoch
        Task {
            do {
                let data = try await candidate(id: id, token: token)
                guard token == epoch else { return }
                let player = try AVAudioPlayer(data: data); player.volume = volume
                guard player.prepareToPlay(), player.play() else { throw CompanionError.invalid("Could not play audition.") }
                preview?.stop(); preview = player; message = "Audition playing once on the SHARED output."
            } catch { if token == epoch { message = error.localizedDescription } }
            if token == epoch { actionBusy = false }
        }
    }
    func accept() {
        guard canRespond, let id = captureID else { return }
        actionBusy = true; let token = epoch
        Task {
            do {
                let data = try await candidate(id: id, token: token)
                guard token == epoch else { return }
                let player = try AVAudioPlayer(data: data); player.volume = volume; player.numberOfLoops = -1
                guard player.prepareToPlay() else { throw CompanionError.invalid("Could not prepare response. Existing loop preserved.") }
                if syncEnabled {
                    guard let tempo = captureTempo, let current = clock.bpm, abs(current-tempo)/tempo <= 0.01,
                          clock.locked(at: MIDIController.now) else { throw CompanionError.invalid("Capture a musical-length phrase at the current Logic tempo before synchronized launch.") }
                }
                // Idempotent: retry works if the acknowledgment was lost or playback subsequently failed.
                try await bridge.action(id: id, name: "accept")
                guard token == epoch else { return }
                let wrapped = AudioLoop(player)
                let now = MIDIController.now
                guard let target = looper.nextBoundary(lead: 0.15) else {
                    throw CompanionError.invalid("Play the original loop before bringing in its variation.")
                }
                guard slot.stage(wrapped, at: player.deviceCurrentTime + target-now) else {
                    throw CompanionError.invalid("Scheduling failed; original loop is unchanged.")
                }
                pendingBoundary = target; pendingRevision = clock.revision; pendingAudio = data
                pendingTempo = syncEnabled ? captureTempo : nil
                phase = "queued launch"; message = "AI layer queued at the next original-loop boundary."
                preview?.stop(); preview = nil
            } catch { if token == epoch { phase = "auditioning"; message = error.localizedDescription } }
            if token == epoch && pendingBoundary == nil { actionBusy = false }
        }
    }
    func saveResponse() {
        guard canSave else { return }
        actionBusy = true; let token = epoch
        Task {
            do {
                let data: Data
                if let responseAudio { data = responseAudio }
                else if canRespond || ["ready", "auditioning"].contains(phase), let id = captureID { data = try await candidate(id: id, token: token) }
                else if let acceptedAudio { data = acceptedAudio }
                else { throw CompanionError.invalid("No response to save.") }
                guard token == epoch else { return }
                let panel = NSSavePanel(); panel.nameFieldStringValue = "Suzy-response-\(Int(Date().timeIntervalSince1970)).wav"
                panel.title = "Save response WAV"; panel.allowedContentTypes = [.wav]
                savePanelOpen = true
                panel.begin { [weak self] result in
                    self?.savePanelOpen = false
                    guard result == .OK, let url = panel.url else { return }
                    do { try data.write(to: url, options: .atomic); self?.message = "Saved response WAV." }
                    catch { self?.message = "Save failed: \(error.localizedDescription)" }
                }
            } catch { if token == epoch { message = error.localizedDescription } }
            if token == epoch { actionBusy = false }
        }
    }
    func resetMusicalContext() {
        guard canCapture else { return }
        actionBusy = true
        Task {
            do { try await bridge.resetContext(); message = "Accepted musical history cleared. Personal memory unchanged." }
            catch { message = error.localizedDescription }
            actionBusy = false
        }
    }
    func discard() { clear(stopLoop: false, resetRemote: false) }
    func stopAll() { looper.stop(); clear(stopLoop: true, resetRemote: false) }
    func resetBridge() { clear(stopLoop: true, resetRemote: true) }
    private func clear(stopLoop: Bool, resetRemote: Bool) {
        epoch += 1; let token = epoch
        preview?.stop(); preview = nil; responseAudio = nil
        slot.cancelPending(); pendingBoundary = nil; pendingAudio = nil; pendingTempo = nil; pendingRevision = nil
        if stopLoop { slot.stop(); loopPlaying = false; loopTempo = nil }
        captureTempo = nil
        let oldID = captureID; captureID = nil; phase = "stopping"; actionBusy = true
        Task {
            do {
                var id = oldID
                if resetRemote { let status = try await bridge.status(); id = ["idle", "discarded"].contains(status.state) ? nil : status.id }
                if let id { try await bridge.action(id: id, name: "discard") }
                guard token == epoch else { return }
                message = stopLoop ? "Companion stopped. Logic continues independently." : "Candidate discarded; existing loop preserved."
            } catch { if token == epoch { message = "Local action completed; bridge cleanup failed. Reset bridge before retrying." } }
            if token == epoch { phase = "idle"; actionBusy = false }
        }
    }
    private func fail(_ text: String) {
        phase = "failed"; actionBusy = false
        message = "AI response unavailable; local loop unchanged. " + text
    }
    func shutdown() {
        epoch += 1; preview?.stop(); slot.stop(); looper.shutdown(); timer?.invalidate()
    }
}
