import Foundation

/// Bounded local PCM operations. This code never calls the bridge or model.
public enum LoopAudio {
    public static func wav(_ pcm: PCM) -> Data {
        var data = Data()
        func tag(_ text: String) { data.append(contentsOf: text.utf8) }
        func le(_ value: Int, _ count: Int) { for byte in 0..<count { data.append(UInt8((value >> (8*byte)) & 255)) } }
        tag("RIFF"); le(36+pcm.data.count,4); tag("WAVEfmt "); le(16,4); le(1,2)
        le(pcm.channels,2); le(pcm.rate,4); le(pcm.rate*pcm.channels*2,4)
        le(pcm.channels*2,2); le(16,2); tag("data"); le(pcm.data.count,4); data.append(pcm.data)
        return data
    }
    /// Same duration/rate/channels. Saturation bounds peaks; performer controls input gain.
    public static func overdub(base: PCM, take: PCM) throws -> PCM {
        guard base.rate == take.rate, base.channels == take.channels, base.data.count == take.data.count else {
            throw CompanionError.invalid("Overdub must match the loop's format and frame count.")
        }
        let a = [UInt8](base.data), b = [UInt8](take.data)
        var mixed = Data(capacity: a.count)
        let frames = a.count/(base.channels*2), fade = min(base.rate/200, frames/2)
        for i in stride(from: 0, to: a.count, by: 2) {
            let original = Int(Int16(bitPattern: UInt16(a[i]) | UInt16(a[i+1]) << 8))
            let added = Int(Int16(bitPattern: UInt16(b[i]) | UInt16(b[i+1]) << 8))
            let frame = i/(base.channels*2)
            let envelope = min(1.0, Double(frame)/Double(max(1,fade)), Double(frames-1-frame)/Double(max(1,fade)))
            let value = Int16(clamping: original + Int((Double(added)*envelope).rounded()))
            let raw = UInt16(bitPattern: value)
            mixed.append(UInt8(raw & 255)); mixed.append(UInt8(raw >> 8))
        }
        return try PCM(wav: encode(mixed, rate: base.rate, channels: base.channels))
    }
    private static func encode(_ samples: Data, rate: Int, channels: Int) -> Data {
        var data = Data()
        func tag(_ text: String) { data.append(contentsOf: text.utf8) }
        func le(_ value: Int, _ count: Int) { for byte in 0..<count { data.append(UInt8((value >> (8*byte)) & 255)) } }
        tag("RIFF"); le(36+samples.count,4); tag("WAVEfmt "); le(16,4); le(1,2)
        le(channels,2); le(rate,4); le(rate*channels*2,4); le(channels*2,2); le(16,2)
        tag("data"); le(samples.count,4); data.append(samples)
        return data
    }
}

/// One committed loop and one undo, regardless of the number of overdubs.
public struct LoopHistory {
    public private(set) var current: Data?
    public private(set) var previous: Data?
    public private(set) var revision = 0
    public init() {}
    public mutating func commit(_ wav: Data) { previous = current; current = wav; revision += 1 }
    public mutating func undo() -> Data? {
        guard let previous else { return nil }
        current = previous; self.previous = nil; revision += 1; return previous
    }
    public mutating func clear() { current = nil; previous = nil; revision += 1 }
}
