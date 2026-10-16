import AppKit
import AVFoundation
import SwiftUI
import CompanionCore

private final class RecorderDelegate: NSObject, AVAudioRecorderDelegate {
    var finished: ((Bool) -> Void)?
    func audioRecorderDidFinishRecording(_ recorder: AVAudioRecorder, successfully flag: Bool) {
        finished?(flag)
    }
    func audioRecorderEncodeErrorDidOccur(_ recorder: AVAudioRecorder, error: Error?) {
        finished?(false)
    }
}

@MainActor final class Performance: ObservableObject {
    @Published var phase = "idle"
    @Published var message = "Select Focusrite as macOS Sound input/output, then Connect. Logic keeps its own audio settings."
    @Published var bpm = 120.0
    @Published var duration = 4.0
    @Published var mode = "mirror"
    @Published var provider = "deterministic"
    @Published var channel = 0
    @Published var volume: Float = 0.35 { didSet { preview?.volume = volume; loop?.volume = volume } }
    @Published var meter: Float = -60
    @Published var elapsed = 0.0
    @Published var midiSource: UInt32 = 0 { didSet { midi.select(midiSource) } }
    @Published var midiChannel = 16
    @Published var midiSources: [MIDIController.Source] = []
    @Published var connected = false
    @Published var loopPlaying = false
    @Published var actionBusy = false
    private let bridge = Bridge()
    private let midi = MIDIController()
    private var recorder: AVAudioRecorder?
    private let recorderDelegate = RecorderDelegate()
    private var preview: AVAudioPlayer?
    private var loop: AVAudioPlayer?
    private var responseAudio: Data?
    private var captureID: String?
    private var file: URL?
    private var folder: URL?
    private var epoch = 0
    private var timer: Timer?

    var canCapture: Bool { connected && !actionBusy && ["idle", "accepted", "failed"].contains(phase) }
    var canRespond: Bool { !actionBusy && ["ready", "auditioning"].contains(phase) }

    init() {
        refreshMIDI()
        midi.onNote = { [weak self] channel, note in
            guard let self, channel == self.midiChannel else { return }
            switch note {
            case 36: self.captureOrFinish()
            case 37: self.audition()
            case 38: self.accept()
            case 39: self.stopAll()
            case 40: self.discard()
            default: break
            }
        }
        timer = Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { [weak self] _ in
            Task { @MainActor [weak self] in
                guard let self, let recorder = self.recorder, recorder.isRecording else { return }
                recorder.updateMeters()
                self.meter = recorder.averagePower(forChannel: self.channel == 1 ? 1 : 0)
                self.elapsed = recorder.currentTime
            }
        }
    }
    func refreshMIDI() { midiSources = midi.sources() }
    func connect() {
        guard !actionBusy, phase != "capturing", phase != "processing" else { return }
        Task {
            do {
                let status = try await bridge.status()
                connected = true
                message = status.state == "idle" || status.state == "discarded"
                    ? "Bridge connected. Ready for dry input capture."
                    : "Bridge has an existing \(status.state) phrase. Use Reset bridge if it belongs to this session."
            } catch { connected = false; message = "Start the bridge on port 7333, then Connect. \(error.localizedDescription)" }
        }
    }
    func captureOrFinish() {
        if phase == "capturing" { phase = "finalizing"; recorder?.stop(); return }
        guard canCapture else { return }
        epoch += 1
        let token = epoch
        phase = "arming"; elapsed = 0; meter = -60
        preview?.stop(); preview = nil; responseAudio = nil
        let selectedChannel = channel, selectedMode = mode, selectedProvider = provider
        let selectedBPM = bpm, selectedDuration = duration
        Task {
            let allowed = await AVCaptureDevice.requestAccess(for: .audio)
            guard token == epoch else { return }
            guard allowed else { phase = "failed"; message = "Allow microphone access in System Settings → Privacy & Security."; return }
            do {
                let root = FileManager.default.temporaryDirectory.appendingPathComponent("suzy-live-\(UUID().uuidString)", isDirectory: true)
                try FileManager.default.createDirectory(at: root, withIntermediateDirectories: false,
                    attributes: [.posixPermissions: 0o700])
                folder = root
                let url = root.appendingPathComponent("capture.wav"); file = url
                let settings: [String: Any] = [AVFormatIDKey: kAudioFormatLinearPCM,
                    AVSampleRateKey: 48000, AVNumberOfChannelsKey: 2,
                    AVLinearPCMBitDepthKey: 16, AVLinearPCMIsFloatKey: false,
                    AVLinearPCMIsBigEndianKey: false, AVLinearPCMIsNonInterleaved: false]
                let rec = try AVAudioRecorder(url: url, settings: settings)
                rec.delegate = recorderDelegate; rec.isMeteringEnabled = true
                recorderDelegate.finished = { [weak self] success in
                    Task { @MainActor [weak self] in
                        guard let self, token == self.epoch, ["capturing", "finalizing"].contains(self.phase) else { return }
                        self.recorder = nil
                        guard success else { self.fail("Audio capture failed."); return }
                        self.phase = "processing"
                        await self.sendCapture(url, channel: selectedChannel, mode: selectedMode,
                                               provider: selectedProvider, bpm: selectedBPM, token: token)
                    }
                }
                recorder = rec
                guard rec.record(forDuration: selectedDuration) else { throw CompanionError.invalid("Could not start the audio recorder.") }
                phase = "capturing"
                message = "Capturing dry input. Press Capture again to finish; backing playback is unchanged."
            } catch { fail(error.localizedDescription) }
        }
    }
    private func sendCapture(_ url: URL, channel: Int, mode: String, provider: String, bpm: Double, token: Int) async {
        do {
            let size = try url.resourceValues(forKeys: [.fileSizeKey]).fileSize ?? 0
            guard size <= 2_000_000 else { throw CompanionError.invalid("Recording exceeds capture limit.") }
            let pcm = try PCM(wav: Data(contentsOf: url), channel: channel == 2 ? nil : channel)
            cleanupRecording()
            let id = try await bridge.arm(rate: pcm.rate, channels: pcm.channels, bpm: bpm, mode: mode, provider: provider)
            guard token == epoch else { try? await bridge.action(id: id, name: "discard"); return }
            captureID = id
            for (sequence, offset) in stride(from: 0, to: pcm.data.count, by: 32768).enumerated() {
                guard token == epoch else { return }
                try await bridge.chunk(id: id, sequence: sequence, data: pcm.data.subdata(in: offset..<min(offset+32768, pcm.data.count)))
            }
            try await bridge.action(id: id, name: "finish")
            let deadline = Date().addingTimeInterval(20)
            while token == epoch && Date() < deadline {
                let status = try await bridge.status()
                guard token == epoch else { return }
                guard status.id == id else { throw CompanionError.invalid("Bridge phrase changed in another client.") }
                if status.state == "ready" {
                    phase = "ready"
                    let label = status.response?.provider ?? "unknown"
                    message = "Response ready · \(label) · \(String(format: "%.1f", status.response?.elapsed_seconds ?? 0)) seconds. Audition or Bring in."
                    return
                }
                if status.state == "failed" { throw CompanionError.invalid(status.error ?? "Response failed.") }
                try await Task.sleep(nanoseconds: 200_000_000)
            }
            if token == epoch { throw CompanionError.invalid("Response deadline reached. Discard/reset before retrying.") }
        } catch {
            if token == epoch {
                if let id = captureID { try? await bridge.action(id: id, name: "discard") }
                guard token == epoch else { return }
                captureID = nil
                fail(error.localizedDescription)
            }
        }
    }
    func audition() {
        guard canRespond, let id = captureID else { return }
        actionBusy = true
        let token = epoch
        Task {
            do {
                if phase == "ready" { try await bridge.action(id: id, name: "audition") }
                guard token == epoch else { return }
                phase = "auditioning"
                let data = try await bridge.audio(id: id)
                guard token == epoch else { return }
                _ = try PCM(wav: data)
                let player = try AVAudioPlayer(data: data)
                preview?.stop(); preview = player; responseAudio = data
                player.volume = volume; player.numberOfLoops = 0
                guard player.play() else { throw CompanionError.invalid("Could not play the response.") }
                message = "Auditioning once. Bring in loops it immediately; Stop silences all companion audio."
            } catch { if token == epoch { message = error.localizedDescription } }
            if token == epoch { actionBusy = false }
        }
    }
    func accept() {
        guard canRespond, let id = captureID else { return }
        actionBusy = true
        let token = epoch
        Task {
            do {
                try await bridge.action(id: id, name: "accept")
                guard token == epoch else { return }
                let data: Data
                if let cached = responseAudio { data = cached } else { data = try await bridge.audio(id: id) }
                guard token == epoch else { return }
                _ = try PCM(wav: data)
                let player = try AVAudioPlayer(data: data)
                player.volume = volume; player.numberOfLoops = -1
                preview?.stop(); preview = nil; loop?.stop(); loop = player
                guard player.play() else { throw CompanionError.invalid("Could not play the accepted response.") }
                loopPlaying = true; phase = "accepted"
                message = "Response looping. You can capture another phrase. Launch is manual—not synchronized to Logic."
            } catch { if token == epoch { phase = "failed"; message = error.localizedDescription } }
            if token == epoch { actionBusy = false }
        }
    }
    func discard() { clear(stopLoop: false, resetRemote: false) }
    func stopAll() { clear(stopLoop: true, resetRemote: false) }
    func resetBridge() { clear(stopLoop: true, resetRemote: true) }
    private func clear(stopLoop: Bool, resetRemote: Bool) {
        epoch += 1; let token = epoch
        // Local stop happens before any network await and works with the bridge down.
        recorderDelegate.finished = nil; recorder?.stop(); recorder = nil
        preview?.stop(); preview = nil; responseAudio = nil
        if stopLoop { loop?.stop(); loop = nil; loopPlaying = false }
        cleanupRecording()
        let oldID = captureID; captureID = nil
        phase = "stopping"; actionBusy = true
        Task {
            do {
                var id = oldID
                if resetRemote {
                    let status = try await bridge.status()
                    id = ["idle", "discarded"].contains(status.state) ? nil : status.id
                }
                if let id { try await bridge.action(id: id, name: "discard") }
                guard token == epoch else { return }
                message = stopLoop ? "Companion audio stopped. Logic was not stopped." : "Candidate discarded; accepted loop continues."
            } catch { if token == epoch { message = "Local audio stopped/cleared. Bridge cleanup failed; Connect/Reset before next capture." } }
            if token == epoch { phase = "idle"; actionBusy = false }
        }
    }
    private func cleanupRecording() {
        if let folder { try? FileManager.default.removeItem(at: folder) }
        folder = nil; file = nil
    }
    private func fail(_ text: String) {
        recorderDelegate.finished = nil; recorder?.stop(); recorder = nil
        cleanupRecording(); phase = "failed"; actionBusy = false; message = text
    }
    func shutdown() {
        epoch += 1; recorderDelegate.finished = nil; recorder?.stop(); preview?.stop(); loop?.stop()
        cleanupRecording(); timer?.invalidate()
    }
}
