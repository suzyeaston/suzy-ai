/// MIDI 1 byte stream parser: handles packet splits, running status and realtime bytes.
public struct MIDIParser {
    private var status: UInt8 = 0
    private var bytes: [UInt8] = []
    public init() {}
    public mutating func feed(_ input: [UInt8]) -> [(channel: Int, note: Int)] {
        var notes: [(Int,Int)] = []
        for byte in input {
            if byte >= 0xF8 { continue }
            if byte >= 0x80 {
                status = byte < 0xF0 ? byte : 0
                bytes.removeAll(keepingCapacity: true)
                continue
            }
            guard status >= 0x80 else { continue }
            bytes.append(byte)
            let kind = status & 0xF0
            let needed = (kind == 0xC0 || kind == 0xD0) ? 1 : 2
            if bytes.count == needed {
                if kind == 0x90 && bytes[1] > 0 { notes.append((Int(status & 0x0F)+1, Int(bytes[0]))) }
                bytes.removeAll(keepingCapacity: true)
            }
        }
        return notes
    }
}
