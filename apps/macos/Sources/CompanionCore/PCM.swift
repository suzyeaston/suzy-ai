import Foundation

public enum CompanionError: Error, LocalizedError {
    case invalid(String)
    public var errorDescription: String? {
        switch self { case .invalid(let text): return text }
    }
}

public struct PCM: Sendable {
    public let data: Data
    public let rate: Int
    public let channels: Int
    public var seconds: Double { Double(data.count) / Double(rate * channels * 2) }

    /// RIFF chunk parsing, not an assumed 44-byte WAV header. PCM16 only.
    public init(wav: Data, channel: Int? = nil, targetFrames: Int? = nil) throws {
        guard wav.count <= 2_000_000, wav.count >= 44 else {
            throw CompanionError.invalid("Recording is empty or too large.")
        }
        let b = [UInt8](wav)
        func u16(_ p: Int) -> Int { Int(b[p]) | Int(b[p+1]) << 8 }
        func u32(_ p: Int) -> Int { u16(p) | u16(p+2) << 16 }
        func tag(_ p: Int) -> String { String(bytes: b[p..<p+4], encoding: .ascii) ?? "" }
        guard tag(0) == "RIFF", tag(8) == "WAVE", u32(4) + 8 == b.count else {
            throw CompanionError.invalid("Expected a complete RIFF WAV recording.")
        }
        var p = 12
        var format: (Int, Int)?
        var body: Range<Int>?
        while p + 8 <= b.count {
            let size = u32(p+4), start = p+8
            guard size <= b.count - start else { throw CompanionError.invalid("Truncated WAV chunk.") }
            if tag(p) == "fmt " {
                guard format == nil, size >= 16, u16(start) == 1, u16(start+14) == 16 else {
                    throw CompanionError.invalid("Use uncompressed 16-bit PCM WAV.")
                }
                let c = u16(start+2), r = u32(start+4)
                guard [1,2].contains(c), [44100,48000].contains(r), u16(start+12) == c*2,
                      u32(start+8) == r*c*2 else { throw CompanionError.invalid("Unsupported WAV format.") }
                format = (r,c)
            }
            if tag(p) == "data" {
                guard body == nil else { throw CompanionError.invalid("Duplicate WAV audio chunk.") }
                body = start..<start+size
            }
            p = start + size + size % 2
        }
        guard let (rate, channels) = format, let body, body.count % (channels*2) == 0,
              body.count >= rate*channels/2, body.count <= rate*channels*2*(targetFrames == nil ? 8 : 9) else {
            throw CompanionError.invalid("Capture must contain 0.25–8 seconds of PCM audio.")
        }
        if let targetFrames {
            guard targetFrames >= rate/4, targetFrames <= rate*8,
                  abs(body.count/(channels*2)-targetFrames) <= rate/10 else {
                throw CompanionError.invalid("Capture length differed from the musical grid by more than 100 ms.")
            }
        }
        func fitted(_ data: Data, channels: Int) -> Data {
            guard let targetFrames else { return data }
            let count = targetFrames * channels * 2
            if data.count >= count { return Data(data.prefix(count)) }
            return data + Data(repeating: 0, count: count-data.count)
        }
        self.rate = rate
        if let channel {
            guard (0..<channels).contains(channel) else { throw CompanionError.invalid("Input channel is unavailable.") }
            var mono = Data(capacity: body.count/channels)
            for frame in stride(from: body.lowerBound, to: body.upperBound, by: channels*2) {
                mono.append(b[frame+channel*2]); mono.append(b[frame+channel*2+1])
            }
            self.data = fitted(mono, channels: 1); self.channels = 1
        } else {
            self.data = fitted(Data(b[body]), channels: channels); self.channels = channels
        }
    }
}
