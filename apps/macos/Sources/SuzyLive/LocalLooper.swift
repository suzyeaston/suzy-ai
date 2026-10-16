import Foundation
import Combine
import AVFoundation
import AppKit
import UniformTypeIdentifiers
import CompanionCore

private final class LoopRecorderDelegate: NSObject, AVAudioRecorderDelegate {
    var finished: ((Bool) -> Void)?
    func audioRecorderDidFinishRecording(_ recorder: AVAudioRecorder, successfully flag: Bool) { finished?(flag) }
    func audioRecorderEncodeErrorDidOccur(_ recorder: AVAudioRecorder, error: Error?) { finished?(false) }
}

/// Local instrument: no HTTP, inference or model state is needed for any control.
@MainActor final class LocalLooper: ObservableObject {
    @Published var state = "empty"
    @Published var message = "Record a phrase. It loops locally before AI does any work."
    @Published var muted = false { didSet { updateVolume() } }
    @Published var volume: Float = 0.6 { didSet { updateVolume() } }
    @Published var hasLoop = false
    @Published var canUndo = false
    @Published var seconds = 0.0
    @Published var saveOpen = false
    private(set) var history = LoopHistory()
    var onSnapshot: ((Data?) -> Void)?
    private var player: AVAudioPlayer?
    private var pendingPlayer: AVAudioPlayer?
    private var recorder: AVAudioRecorder?
    private let delegate = LoopRecorderDelegate()
    private var folder: URL?
    private var generation = 0
    private var pendingWAV: Data?
    private var pendingUndo = false
    private var boundary: Double?
    private var timer: Timer?
    private var loopChannel = 0
    private var synchronizedTempo: Double?
    var isSynchronized: Bool { synchronizedTempo != nil }
    var tempo: Double? { synchronizedTempo }
    var busy: Bool { ["arming", "recording", "overdubbing", "queued", "finalizing"].contains(state) }
    var playing: Bool { player?.isPlaying == true }

    init() {
        timer = Timer(timeInterval: 0.01, repeats: true) { [weak self] _ in
            Task { @MainActor [weak self] in self?.tick() }
        }
        if let timer { RunLoop.main.add(timer, forMode: .common) }
    }
    private func updateVolume() {
        player?.volume = muted ? 0 : volume; pendingPlayer?.volume = muted ? 0 : volume
    }
    private func tick() {
        if let target = boundary, MIDIController.now >= target, let pendingPlayer, let wav = pendingWAV {
            player?.stop(); player = pendingPlayer; self.pendingPlayer = nil; pendingWAV = nil; boundary = nil
            if pendingUndo { _ = history.undo() } else { history.commit(wav) }
            pendingUndo = false; state = "playing"; canUndo = history.previous != nil
            message = "Loop updated. Keep playing; AI is optional."
            onSnapshot?(wav)
        }
    }
    func record(channel: Int, duration: Double, tempo: Double?, start: Double?) {
        if state == "recording" {
            if synchronizedTempo != nil { message = "Beat-length capture finishes automatically. Stop cancels it."; return }
            state = "finalizing"; recorder?.stop(); return
        }
        guard !busy, !hasLoop else { message = "Use Overdub to add a layer, or Clear for a new loop."; return }
        guard duration >= 0.25, duration <= 8 else { message = "Loop length must be 0.25–8 seconds."; return }
        loopChannel = channel; synchronizedTempo = tempo
        startRecording(duration: duration, channel: channel, isOverdub: false, scheduled: start)
    }
    func overdub() {
        guard hasLoop, playing, !busy else { message = "Play the loop before overdubbing."; return }
        startRecording(duration: seconds, channel: loopChannel, isOverdub: true, scheduled: nil)
    }
    private func startRecording(duration: Double, channel: Int, isOverdub: Bool, scheduled: Double?) {
        generation += 1; let token = generation
        state = "arming"
        Task {
            let allowed = await AVCaptureDevice.requestAccess(for: .audio)
            guard token == generation else { return }
            guard allowed else { fail("Microphone permission is required; existing loop preserved."); return }
            do {
                let root = FileManager.default.temporaryDirectory.appendingPathComponent("suzy-loop-\(UUID().uuidString)", isDirectory: true)
                try FileManager.default.createDirectory(at: root, withIntermediateDirectories: false, attributes: [.posixPermissions:0o700])
                folder = root; let url = root.appendingPathComponent("take.wav")
                let recorder = try AVAudioRecorder(url: url, settings: [AVFormatIDKey:kAudioFormatLinearPCM,
                    AVSampleRateKey:48000, AVNumberOfChannelsKey:2, AVLinearPCMBitDepthKey:16,
                    AVLinearPCMIsFloatKey:false, AVLinearPCMIsBigEndianKey:false, AVLinearPCMIsNonInterleaved:false])
                self.recorder = recorder; recorder.delegate = delegate
                guard recorder.prepareToRecord() else { throw CompanionError.invalid("Input preparation failed.") }
                delegate.finished = { [weak self] success in
                    Task { @MainActor [weak self] in
                        guard let self, token == self.generation else { return }
                        self.recorder = nil
                        guard success else { self.fail("Recording failed; existing loop preserved."); return }
                        self.finish(url, channel: channel, duration: duration, isOverdub: isOverdub)
                    }
                }
                if isOverdub {
                    guard let target = nextBoundary() else { throw CompanionError.invalid("Loop stopped before overdub.") }
                    guard recorder.record(atTime: recorder.deviceCurrentTime + target-MIDIController.now, forDuration: duration) else {
                        throw CompanionError.invalid("Overdub could not start.")
                    }
                    state = "overdubbing"; message = "One-cycle overdub starts at the next loop boundary. Original loop keeps playing."
                } else if let scheduled {
                    let remaining = scheduled-MIDIController.now
                    guard remaining > 0.05 else { throw CompanionError.invalid("Capture boundary passed while granting permission. Press Record again.") }
                    guard recorder.record(atTime: recorder.deviceCurrentTime+remaining, forDuration: duration) else { throw CompanionError.invalid("Scheduled capture failed.") }
                    state = "recording"; message = "Capture scheduled on Logic's bar; playback follows locally."
                } else {
                    guard recorder.record(forDuration: duration) else { throw CompanionError.invalid("Recording could not start.") }
                    state = "recording"; message = "Recording. Press Record again to close the loop."
                }
            } catch { fail(error.localizedDescription) }
        }
    }
    private func finish(_ url: URL, channel: Int, duration: Double, isOverdub: Bool) {
        defer { cleanup() }
        do {
            guard (try url.resourceValues(forKeys: [.fileSizeKey]).fileSize ?? 0) <= 2_000_000 else { throw CompanionError.invalid("Take too large.") }
            let target = isOverdub || synchronizedTempo != nil ? Int((duration*48000).rounded()) : nil
            let take = try PCM(wav: Data(contentsOf: url), channel: channel == 2 ? nil : channel, targetFrames: target)
            if isOverdub {
                guard let original = history.current else { throw CompanionError.invalid("Original loop is unavailable.") }
                let mixed = try LoopAudio.overdub(base: PCM(wav: original), take: take)
                try queue(LoopAudio.wav(mixed), undo: false)
            } else {
                let wav = LoopAudio.wav(take)
                let next = try makePlayer(wav)
                // Start the original locally BEFORE invoking any AI snapshot callback.
                guard next.play() else { throw CompanionError.invalid("Local playback could not start.") }
                player = next; history.commit(wav); hasLoop = true; seconds = take.seconds
                canUndo = false; state = "playing"; message = "Your original is looping. AI can work in the background."
                onSnapshot?(wav)
            }
        } catch { fail(error.localizedDescription) }
    }
    private func makePlayer(_ wav: Data) throws -> AVAudioPlayer {
        let next = try AVAudioPlayer(data: wav); next.numberOfLoops = -1; next.volume = muted ? 0 : volume
        guard next.prepareToPlay() else { throw CompanionError.invalid("Loop preparation failed.") }
        return next
    }
    func nextBoundary(lead: Double = 0.1) -> Double? {
        guard let player, player.isPlaying, seconds > 0 else { return nil }
        var remaining = seconds - player.currentTime.truncatingRemainder(dividingBy: seconds)
        while remaining < lead { remaining += seconds }
        return MIDIController.now + remaining
    }
    private func queue(_ wav: Data, undo: Bool) throws {
        let next = try makePlayer(wav)
        guard let target = nextBoundary(), next.play(atTime: next.deviceCurrentTime + target-MIDIController.now) else {
            throw CompanionError.invalid("Loop replacement could not schedule; original preserved.")
        }
        pendingPlayer = next; pendingWAV = wav; pendingUndo = undo; boundary = target
        state = "queued"; message = undo ? "Undo queued at next loop boundary." : "Overdub queued at next loop boundary."
    }
    func undo() {
        guard !busy, let wav = history.previous else { return }
        do {
            if playing { try queue(wav, undo: true) }
            else { _ = history.undo(); canUndo = false; onSnapshot?(wav); message = "Last overdub undone." }
        } catch { message = error.localizedDescription }
    }
    func play() {
        guard !busy, !playing, let wav = history.current else { return }
        do {
            let next = try makePlayer(wav)
            guard next.play() else { throw CompanionError.invalid("Loop playback failed.") }
            player = next; state = "playing"
            // Manual resume is free timing; do not pretend it retained Logic phase.
            synchronizedTempo = nil; message = "Loop resumed with free timing."
        } catch { message = error.localizedDescription }
    }
    func stop() {
        generation += 1; delegate.finished = nil; recorder?.stop(); recorder = nil
        pendingPlayer?.stop(); pendingPlayer = nil; pendingWAV = nil; pendingUndo = false; boundary = nil
        player?.stop(); player = nil; cleanup(); synchronizedTempo = nil
        state = hasLoop ? "stopped" : "empty"; message = "Local loop stopped. Play resumes; Clear removes it."
    }
    func clear() {
        stop(); history.clear(); hasLoop = false; canUndo = false; seconds = 0; state = "empty"
        onSnapshot?(nil)
    }
    func save() {
        guard !saveOpen, let wav = history.current else { return }
        let panel = NSSavePanel(); panel.allowedContentTypes = [.wav]; panel.nameFieldStringValue = "Suzy-original-loop.wav"
        saveOpen = true
        panel.begin { [weak self] result in
            self?.saveOpen = false
            guard result == .OK, let url = panel.url else { return }
            do { try wav.write(to: url, options: .atomic); self?.message = "Original loop saved." }
            catch { self?.message = error.localizedDescription }
        }
    }
    private func cleanup() { if let folder { try? FileManager.default.removeItem(at: folder) }; folder = nil }
    private func fail(_ text: String) {
        delegate.finished = nil; recorder?.stop(); recorder = nil; cleanup()
        state = playing ? "playing" : (hasLoop ? "stopped" : "empty"); message = text
    }
    func shutdown() { stop(); timer?.invalidate() }
}
