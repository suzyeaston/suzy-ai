import Foundation
import Combine
import AVFoundation
import AppKit
import UniformTypeIdentifiers
import CompanionCore
import NativeLoop

/// UI/control surface only. CoreAudio owns capture, repeat, overdub and undo timing.
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
    private var engine: OpaquePointer?
    private var timer: Timer?
    private var generation = 0
    private var exportGeneration = 0
    private var snapshotRevision: UInt32 = 0
    private var observedRevision: UInt32 = 0
    private var exportedRevision: UInt32 = 0
    private var exporting = false
    var currentSnapshot: Data? {
        guard let engine, nl_status(engine).revision == exportedRevision else { return nil }
        return history.current
    }
    private var synchronizedTempo: Double?
    var isSynchronized: Bool { synchronizedTempo != nil }
    var tempo: Double? { synchronizedTempo }
    var busy: Bool { ["arming", "recording", "overdubbing", "queued"].contains(state) }
    var playing: Bool { ["playing", "overdubbing", "queued"].contains(state) }

    init() {
        timer = Timer(timeInterval: 0.03, repeats: true) { [weak self] _ in
            Task { @MainActor [weak self] in self?.tick() }
        }
        if let timer { RunLoop.main.add(timer, forMode: .common) }
    }
    private func updateVolume() { if let engine { nl_gain(engine, muted ? 0 : volume) } }
    private func command(_ code: Int, frames: UInt32 = 0, channel: UInt32 = 0, start: Double = 0) -> Bool {
        guard let engine, nl_command(engine, UInt32(code), frames, channel, start) != 0 else {
            message = "Audio control is busy; try that control again."; return false
        }
        return true
    }
    private func tick() {
        guard let engine else { return }
        if nl_fault(engine) != 0 {
            // Stop only our IOProc, never Logic's device or stream. Preserve the latest exported take.
            nl_close(engine); self.engine = nil; synchronizedTempo = nil
            canUndo = false; onSnapshot?(nil)
            state = "stopped"; message = "Interface changed or its audio format is unsupported. Save your take, Clear, then reconnect and record."
            return
        }
        let status = nl_status(engine)
        let names = ["empty", "arming", "recording", "playing", "queued", "overdubbing", "stopped"]
        state = names[min(Int(status.state), names.count-1)]
        hasLoop = status.frames > 0; canUndo = status.undo != 0
        seconds = Double(status.frames)/Double(status.rate)
        if status.revision != observedRevision {
            observedRevision = status.revision
            onSnapshot?(nil) // invalidate proposals before asynchronous WAV encoding finishes
        }
        guard !exporting else { return }
        var frames: UInt32 = 0, revision: UInt32 = 0
        guard let samples = nl_snapshot(engine, &frames, &revision) else { return }
        // Immutable export buffer, never the render buffer. Bounded to 8 seconds.
        // Copy on control thread; encoding runs on a background task and cannot delay audio.
        let copy = Array(UnsafeBufferPointer(start: samples, count: Int(frames)*2))
        nl_release_snapshot(engine)
        guard revision == nl_status(engine).revision, revision != snapshotRevision else { return }
        snapshotRevision = revision; exporting = true
        let token = exportGeneration, rate = Int(status.rate)
        Task {
            let wav = await Task.detached(priority: .utility) { Self.encode(copy, rate: rate) }.value
            exporting = false
            guard token == exportGeneration, let engine = self.engine,
                  nl_status(engine).revision == revision else { return }
            history.commit(wav); exportedRevision = revision
            message = playing ? "Your loop is playing independently of AI." : "Loop snapshot ready to save or resume."
            onSnapshot?(playing ? wav : nil)
        }
    }
    nonisolated private static func encode(_ samples: [Float], rate: Int) -> Data {
        var data = Data(capacity: 44+samples.count*2)
        func le(_ value: Int, _ count: Int) { for byte in 0..<count { data.append(UInt8((value >> (8*byte)) & 255)) } }
        data.append(contentsOf: "RIFF".utf8); le(36+samples.count*2,4); data.append(contentsOf: "WAVEfmt ".utf8)
        le(16,4); le(1,2); le(2,2); le(rate,4); le(rate*4,4); le(4,2); le(16,2)
        data.append(contentsOf: "data".utf8); le(samples.count*2,4)
        for sample in samples { let v = Int16(clamping: Int((max(-1,min(1,sample))*32767).rounded())); le(Int(UInt16(bitPattern:v)),2) }
        return data
    }
    func record(channel: Int, duration: Double, tempo: Double?, start: Double?) {
        if state == "recording" {
            guard synchronizedTempo == nil else { message = "Beat-length capture finishes automatically. Stop cancels it."; return }
            _ = command(Int(NL_FINISH)); return
        }
        guard !busy, !hasLoop else { message = "Use Overdub to add a layer, or Clear for a new loop."; return }
        guard duration.isFinite, duration >= 0.25, duration <= 8, (0...2).contains(channel) else { message = "Loop length must be 0.25–8 seconds."; return }
        generation += 1; let token = generation; state = "arming"
        Task {
            let allowed = await AVCaptureDevice.requestAccess(for: .audio)
            guard token == generation else { return }
            guard allowed else { state = "empty"; message = "Microphone permission is required."; return }
            if engine == nil {
                var error = [CChar](repeating: 0, count: 512)
                engine = nl_open(&error, UInt32(error.count))
                guard engine != nil else { state = "empty"; message = String(cString:error); return }
                snapshotRevision = 0; updateVolume()
            }
            if let start, start-MIDIController.now < 0.05 {
                state = "empty"; message = "The capture boundary passed during setup. Press Record again."; return
            }
            let rate = nl_status(engine!).rate
            if command(Int(NL_RECORD), frames: UInt32((duration*Double(rate)).rounded()), channel: UInt32(channel), start: start ?? 0) {
                synchronizedTempo = tempo; message = "Recording will roll directly into looping."
            } else { state = "empty" }
        }
    }
    func overdub() {
        guard hasLoop, playing, !busy else { message = "Play the loop before overdubbing."; return }
        if command(Int(NL_OVERDUB)) { state = "queued"; message = "One-cycle overdub starts at the next loop boundary." }
    }
    func undo() { guard !busy, canUndo else { return }; _ = command(Int(NL_UNDO)) }
    func play() { guard !busy, !playing, hasLoop else { return }; if command(Int(NL_PLAY)) { synchronizedTempo = nil } }
    func nextBoundary(lead: Double = 0.1) -> Double? {
        guard let engine, playing, seconds > 0 else { return nil }
        var target = nl_status(engine).boundary
        guard target > 0 else { return nil }
        let earliest = MIDIController.now+lead
        if target < earliest { target += ceil((earliest-target)/seconds)*seconds }
        return target
    }
    func stop() {
        generation += 1
        if let engine { nl_stop(engine) }
        synchronizedTempo = nil; state = hasLoop ? "stopped" : "empty"
        message = "Local loop stopped. Play resumes; Clear removes it."
    }
    func clear() {
        generation += 1; exportGeneration += 1
        // Closing only our IOProc guarantees no stale command or snapshot survives Clear.
        if let engine { nl_close(engine); self.engine = nil }
        synchronizedTempo = nil; snapshotRevision = 0; observedRevision = 0; exportedRevision = 0; history.clear()
        hasLoop = false; canUndo = false; seconds = 0; state = "empty"; onSnapshot?(nil)
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
    func shutdown() { clear(); timer?.invalidate() }
}
