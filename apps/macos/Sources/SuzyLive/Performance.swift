import AppKit
import AVFoundation
import SwiftUI
import CompanionCore
import UniformTypeIdentifiers

private final class RecorderDelegate: NSObject, AVAudioRecorderDelegate {
    var finished: ((Bool) -> Void)?
    func audioRecorderDidFinishRecording(_ recorder: AVAudioRecorder, successfully flag: Bool) { finished?(flag) }
    func audioRecorderEncodeErrorDidOccur(_ recorder: AVAudioRecorder, error: Error?) { finished?(false) }
}
private final class AudioLoop: LoopPlayer {
    let player: AVAudioPlayer
    init(_ player: AVAudioPlayer) { self.player = player }
    func start(at time: Double?) -> Bool { time.map { player.play(atTime: $0) } ?? player.play() }
    func stop() { player.stop() }
}

@MainActor final class Performance: ObservableObject {
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
    private var recorder: AVAudioRecorder?
    private let recorderDelegate = RecorderDelegate()
    private var preview: AVAudioPlayer?
    private let slot = PlaybackSlot()
    private var responseAudio: Data?
    private var acceptedAudio: Data?
    private var captureID: String?
    private var folder: URL?
    private var epoch = 0
    private var timer: Timer?
    private var ticks = 0
    private var captureTempo: Double?
    private var loopTempo: Double?
    private var pendingBoundary: Double?
    private var pendingRevision: Int?
    private var pendingAudio: Data?
    private var pendingTempo: Double?
    private var recorderStart: Double?

    var canCapture: Bool { connected && !actionBusy && ["idle", "accepted", "failed"].contains(phase) }
    var canRespond: Bool { !actionBusy && ["ready", "auditioning"].contains(phase) }
    var canSave: Bool { !savePanelOpen && !actionBusy && (canRespond || responseAudio != nil || acceptedAudio != nil) }

    init() {
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
            if let tempo = pendingTempo ?? loopTempo ?? (recorder != nil ? captureTempo : nil), let current = clock.bpm, abs(current-tempo)/tempo > 0.01 {
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
        if let start = recorderStart, now >= start, phase == "queued capture" { phase = "capturing"; recorderStart = nil }
        if ticks % 5 == 0, let recorder, recorder.isRecording {
            recorder.updateMeters(); meter = recorder.averagePower(forChannel: channel == 1 ? 1 : 0)
            elapsed = recorder.currentTime
        }
    }
    private func invalidateClock() {
        cancelSynchronized("Clock source/mode changed; synchronized audio stopped.")
        clock = MIDIClock()
    }
    private func cancelSynchronized(_ reason: String) {
        let recording = captureTempo != nil && ["arming", "queued capture", "capturing", "finalizing"].contains(phase)
        if recording || pendingBoundary != nil || loopTempo != nil {
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
        if phase == "capturing" {
            if captureTempo != nil { message = "Musical capture finishes at its selected beat length. Stop cancels it."; return }
            phase = "finalizing"; recorder?.stop(); return
        }
        guard canCapture else { return }
        let now = MIDIController.now
        if syncEnabled && !clock.locked(at: now) { message = "Select Logic's IAC clock source, then start Logic and wait for clock lock."; return }
        let selectedBPM = syncEnabled ? (clock.bpm ?? bpm) : bpm
        guard selectedBPM.isFinite, (40...240).contains(selectedBPM) else { message = "Use 40–240 BPM."; return }
        let selectedDuration = syncEnabled ? Double(captureBeats)*60/selectedBPM : duration
        guard selectedDuration >= 0.25, selectedDuration <= 8 else { message = "Choose fewer beats: each phrase must fit within eight seconds."; return }
        epoch += 1; let token = epoch
        captureTempo = syncEnabled ? selectedBPM : nil
        let synchronized = syncEnabled
        phase = "arming"; elapsed = 0; meter = -60
        preview?.stop(); preview = nil; responseAudio = nil
        let selectedChannel = channel, selectedMode = mode, selectedProvider = provider
        let selectedSection = String(section.prefix(64)), selectedKey = String(musicalKey.prefix(24)), instruction = String(direction.prefix(500))
        Task {
            let allowed = await AVCaptureDevice.requestAccess(for: .audio)
            guard token == epoch else { return }
            guard allowed else { fail("Allow microphone access in System Settings → Privacy & Security."); return }
            do {
                let root = FileManager.default.temporaryDirectory.appendingPathComponent("suzy-live-\(UUID().uuidString)", isDirectory: true)
                try FileManager.default.createDirectory(at: root, withIntermediateDirectories: false, attributes: [.posixPermissions: 0o700])
                folder = root; let url = root.appendingPathComponent("capture.wav")
                let settings: [String: Any] = [AVFormatIDKey:kAudioFormatLinearPCM, AVSampleRateKey:48000, AVNumberOfChannelsKey:2,
                    AVLinearPCMBitDepthKey:16, AVLinearPCMIsFloatKey:false, AVLinearPCMIsBigEndianKey:false, AVLinearPCMIsNonInterleaved:false]
                let rec = try AVAudioRecorder(url: url, settings: settings)
                rec.delegate = recorderDelegate; rec.isMeteringEnabled = true
                recorderDelegate.finished = { [weak self] success in
                    Task { @MainActor [weak self] in
                        guard let self, token == self.epoch, ["queued capture", "capturing", "finalizing"].contains(self.phase) else { return }
                        self.recorder = nil; self.recorderStart = nil
                        guard success else { self.fail("Audio capture failed."); return }
                        self.phase = "processing"
                        await self.sendCapture(url, channel: selectedChannel, mode: selectedMode, provider: selectedProvider,
                            bpm: selectedBPM, frames: synchronized ? Int((selectedDuration*48000).rounded()) : nil,
                            section: selectedSection, key: selectedKey, instruction: instruction, token: token)
                    }
                }
                recorder = rec
                if synchronized {
                    guard rec.prepareToRecord() else { throw CompanionError.invalid("Input could not prepare.") }
                    let now = MIDIController.now
                    guard let target = clock.nextBoundary(at: now, beats: beatsPerBar) else { throw CompanionError.invalid("Clock unavailable or input could not prepare.") }
                    guard rec.record(atTime: rec.deviceCurrentTime + target-now, forDuration: selectedDuration) else { throw CompanionError.invalid("Could not schedule capture.") }
                    recorderStart = target; phase = "queued capture"
                    message = "Capture queued for next bar; \(captureBeats) beats."
                } else {
                    guard rec.record(forDuration: selectedDuration) else { throw CompanionError.invalid("Could not start recorder.") }
                    phase = "capturing"; message = "Capturing dry input. Press Capture to finish."
                }
            } catch { if token == epoch { fail(error.localizedDescription) } }
        }
    }
    private func sendCapture(_ url: URL, channel: Int, mode: String, provider: String, bpm: Double, frames: Int?, section: String, key: String, instruction: String, token: Int) async {
        do {
            let size = try url.resourceValues(forKeys: [.fileSizeKey]).fileSize ?? 0
            guard size <= 2_000_000 else { throw CompanionError.invalid("Recording exceeds capture limit.") }
            let pcm = try PCM(wav: Data(contentsOf: url), channel: channel == 2 ? nil : channel, targetFrames: frames)
            cleanupRecording()
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
                    phase = "ready"; message = "Response ready · \(status.response?.provider ?? "unknown"). Save, audition on shared output, or bring in."; return
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
                if syncEnabled {
                    let now = MIDIController.now
                    guard let target = clock.nextBoundary(at: now, beats: beatsPerBar) else { throw CompanionError.invalid("Clock lost before launch. Retry when locked.") }
                    guard slot.stage(wrapped, at: player.deviceCurrentTime + target-now) else { throw CompanionError.invalid("Scheduling failed; old loop preserved.") }
                    pendingBoundary = target; pendingRevision = clock.revision; pendingAudio = data; pendingTempo = captureTempo
                    phase = "queued launch"; message = "Response queued for next bar. Stop cancels it."
                } else {
                    guard slot.replace(with: wrapped) else { throw CompanionError.invalid("Playback failed; old loop preserved. Retry Bring in.") }
                    acceptedAudio = data; loopTempo = nil; loopPlaying = true; phase = "accepted"
                    message = "Response looping with free timing."
                }
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
    func stopAll() { clear(stopLoop: true, resetRemote: false) }
    func resetBridge() { clear(stopLoop: true, resetRemote: true) }
    private func clear(stopLoop: Bool, resetRemote: Bool) {
        epoch += 1; let token = epoch
        recorderDelegate.finished = nil; recorder?.stop(); recorder = nil; recorderStart = nil
        preview?.stop(); preview = nil; responseAudio = nil
        slot.cancelPending(); pendingBoundary = nil; pendingAudio = nil; pendingTempo = nil; pendingRevision = nil
        if stopLoop { slot.stop(); loopPlaying = false; loopTempo = nil }
        cleanupRecording(); captureTempo = nil
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
    private func cleanupRecording() {
        if let folder { try? FileManager.default.removeItem(at: folder) }; folder = nil
    }
    private func fail(_ text: String) {
        recorderDelegate.finished = nil; recorder?.stop(); recorder = nil; recorderStart = nil
        cleanupRecording(); phase = "failed"; actionBusy = false; message = text
    }
    func shutdown() {
        epoch += 1; recorderDelegate.finished = nil; recorder?.stop(); preview?.stop(); slot.stop()
        cleanupRecording(); timer?.invalidate()
    }
}
