import XCTest
@testable import CompanionCore

final class CoreTests: XCTestCase {
    func wav(channels: Int = 2, frames: Int = 12000, junk: Bool = false) -> Data {
        var body = Data()
        func le(_ value: Int, _ count: Int) -> Data {
            Data((0..<count).map { UInt8((value >> ($0*8)) & 255) })
        }
        body.append(Data("WAVE".utf8))
        if junk { body.append(Data("JUNK".utf8)); body.append(le(2,4)); body.append(Data([0,0])) }
        body.append(Data("fmt ".utf8)); body.append(le(16,4)); body.append(le(1,2))
        body.append(le(channels,2)); body.append(le(48000,4)); body.append(le(48000*channels*2,4))
        body.append(le(channels*2,2)); body.append(le(16,2))
        body.append(Data("data".utf8)); body.append(le(frames*channels*2,4))
        for _ in 0..<frames { for c in 0..<channels { body.append(le(c == 0 ? 1000 : 2000,2)) } }
        var result = Data("RIFF".utf8); result.append(le(body.count,4)); result.append(body)
        return result
    }
    func testPCMChannelSelectionAndExtraChunks() throws {
        let audio = try PCM(wav: wav(junk: true), channel: 1)
        XCTAssertEqual(audio.rate,48000); XCTAssertEqual(audio.channels,1)
        XCTAssertEqual(audio.data.count,24000); XCTAssertEqual(audio.seconds,0.25)
        XCTAssertEqual(Array(audio.data.prefix(2)), [208,7])
        XCTAssertEqual(try PCM(wav: wav()).channels,2)
    }
    func testPCMRejectsTruncationAndInvalidChannel() {
        XCTAssertThrowsError(try PCM(wav: wav().dropLast()))
        XCTAssertThrowsError(try PCM(wav: wav(channels: 1), channel: 1))
        XCTAssertThrowsError(try PCM(wav: wav(frames: 10)))
        XCTAssertThrowsError(try PCM(wav: wav(frames: 384001)))
        XCTAssertThrowsError(try PCM(wav: Data(repeating: 0, count: 2_000_001)))
    }
    func testMIDIFragmentsRunningStatusAndRealtime() {
        var parser = MIDIParser()
        XCTAssertTrue(parser.feed([0x9F,36]).isEmpty)
        let first = parser.feed([0xF8,100,37,0,38,127])
        XCTAssertEqual(first.map(\.channel),[16,16])
        XCTAssertEqual(first.map(\.note),[36,38])
    }
    func testMIDISysExAndNonNoteMessages() {
        var parser = MIDIParser()
        let notes = parser.feed([0xF0,36,100,0xF7,36,100,0xBF,36,127,0xCF,40,0x90,39,100])
        XCTAssertEqual(notes.count,1); XCTAssertEqual(notes.first?.channel,1); XCTAssertEqual(notes.first?.note,39)
    }
    func testBridgeStatusContract() throws {
        let json = Data("""
        {"id":"abc","state":"ready","busy":false,"error":null,
        "response":{"provider":"model","model":"suzy-local","elapsed_seconds":0.5}}
        """.utf8)
        let status = try JSONDecoder().decode(LiveStatus.self, from: json)
        XCTAssertEqual(status.state,"ready"); XCTAssertEqual(status.response?.provider,"model")
    }
}
