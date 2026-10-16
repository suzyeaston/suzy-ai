public enum MIDIEvent: Equatable, Sendable {
    case note(channel: Int, note: Int)
    case clock, start, resume, stop
    case position(Int)
}
/// MIDI 1 byte stream, including realtime interleaved inside other messages.
public struct MIDIParser {
    private var status: UInt8 = 0
    private var bytes: [UInt8] = []
    public init() {}
    public mutating func feedEvents(_ input: [UInt8]) -> [MIDIEvent] {
        var events: [MIDIEvent] = []
        for byte in input {
            if byte >= 0xF8 {
                switch byte {
                case 0xF8: events.append(.clock)
                case 0xFA: events.append(.start)
                case 0xFB: events.append(.resume)
                case 0xFC, 0xFF: events.append(.stop)
                default: break
                }
                continue
            }
            if byte >= 0x80 {
                status = byte < 0xF0 || byte == 0xF2 ? byte : 0
                bytes.removeAll(keepingCapacity: true)
                continue
            }
            guard status >= 0x80 else { continue }
            bytes.append(byte)
            let kind = status & 0xF0
            let needed = (kind == 0xC0 || kind == 0xD0) ? 1 : 2
            if bytes.count == needed {
                if status == 0xF2 {
                    events.append(.position(Int(bytes[0]) | Int(bytes[1]) << 7)); status = 0
                } else if kind == 0x90 && bytes[1] > 0 {
                    events.append(.note(channel: Int(status & 0x0F)+1, note: Int(bytes[0])))
                }
                bytes.removeAll(keepingCapacity: true)
            }
        }
        return events
    }
    public mutating func feed(_ input: [UInt8]) -> [(channel: Int, note: Int)] {
        feedEvents(input).compactMap { if case let .note(channel, note) = $0 { return (channel, note) }; return nil }
    }
}

public struct TimedMIDIEvent: Sendable {
    public let event: MIDIEvent
    public let time: Double
    public init(_ event: MIDIEvent, at time: Double) { self.event = event; self.time = time }
}
/// Caller serializes access. Overflow explicitly invalidates parser and tells the UI to stop.
public struct MIDIInbox {
    private var parser = MIDIParser()
    private var events: [TimedMIDIEvent] = []
    private var overflow = false
    public init() {}
    public mutating func push(_ bytes: [UInt8], at time: Double) {
        guard bytes.count <= 4096 else { invalidate(); return }
        let decoded = parser.feedEvents(bytes)
        guard events.count + decoded.count <= 256 else { invalidate(); return }
        events.append(contentsOf: decoded.map { TimedMIDIEvent($0, at: time) })
    }
    public mutating func invalidate() { parser = MIDIParser(); events.removeAll(keepingCapacity: true); overflow = true }
    public mutating func drain() -> (events: [TimedMIDIEvent], overflow: Bool) {
        let result = (events, overflow)
        events.removeAll(keepingCapacity: true); overflow = false
        return result
    }
}
