import Foundation

/// Fixed-tempo experimental follower. Timestamps are monotonic host seconds.
/// Meter is user supplied: MIDI clock does not convey time signature.
public struct MIDIClock {
    public private(set) var running = false
    public private(set) var revision = 0
    private var tick = -1
    private var last: Double?
    private var intervals: [Double] = []
    public init() {}
    public var bpm: Double? {
        guard intervals.count >= 24 else { return nil }
        let sorted = intervals.sorted()
        return 60 / (sorted[sorted.count/2] * 24)
    }
    public mutating func receive(_ event: MIDIEvent, at time: Double) {
        switch event {
        case .start: running = true; tick = -1; last = nil; intervals = []; revision += 1
        case .resume: running = true; last = nil; intervals = []; revision += 1
        case .stop: running = false; last = nil; intervals = []; revision += 1
        case .position(let sixteenths): tick = sixteenths * 6 - 1; last = nil; intervals = []; revision += 1
        case .clock:
            guard running else { return }
            if let last {
                let gap = time - last
                if gap > 0.004 && gap < 0.08 {
                    intervals.append(gap)
                    if intervals.count > 48 { intervals.removeFirst() }
                } else { intervals = []; revision += 1 }
            }
            last = time; tick += 1
        default: break
        }
    }
    public func locked(at now: Double) -> Bool {
        guard running, let last, let bpm else { return false }
        return (40...240).contains(bpm) && now >= last && now-last < 0.5
    }
    public func nextBoundary(at now: Double, beats: Int, lead: Double = 0.15) -> Double? {
        guard locked(at: now), let last, let bpm, (1...8).contains(beats) else { return nil }
        let period = 60 / (bpm * 24), grid = beats * 24
        var target = ((tick / grid) + 1) * grid
        while last + Double(target-tick) * period < now + lead { target += grid }
        return last + Double(target-tick) * period
    }
}
