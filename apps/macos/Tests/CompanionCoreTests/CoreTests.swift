import XCTest
@testable import CompanionCore

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
final class CoreTests: XCTestCase {
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

final class PerformanceSafetyTests: XCTestCase {
    final class Player: LoopPlayer {
        var succeeds = true
        var stopped = false
        var startTime: Double?
        func start(at time: Double?) -> Bool { startTime = time; return succeeds }
        func stop() { stopped = true }
    }
    func testFailedReplacementKeepsExistingLoopAndRetryWorks() {
        let slot = PlaybackSlot(), old = Player(), next = Player()
        XCTAssertTrue(slot.replace(with: old))
        next.succeeds = false
        XCTAssertFalse(slot.replace(with: next))
        XCTAssertFalse(old.stopped)
        XCTAssertTrue(slot.current === old)
        next.succeeds = true
        XCTAssertTrue(slot.replace(with: next))
        XCTAssertTrue(old.stopped)
        XCTAssertTrue(slot.current === next)
    }
    func testScheduledReplacementCanBeCancelledWithoutStoppingOldLoop() {
        let slot = PlaybackSlot(), old = Player(), next = Player()
        XCTAssertTrue(slot.replace(with: old))
        XCTAssertTrue(slot.stage(next, at: 10))
        XCTAssertEqual(next.startTime,10)
        XCTAssertFalse(old.stopped)
        slot.cancelPending()
        XCTAssertTrue(next.stopped)
        XCTAssertFalse(old.stopped)
        let retry = Player()
        XCTAssertTrue(slot.stage(retry, at: 20)); slot.commit()
        XCTAssertTrue(old.stopped); XCTAssertTrue(slot.current === retry)
        slot.stop(); XCTAssertTrue(retry.stopped)
    }
    func testInboxPreservesFragmentsAndStopAcrossQueuedBatches() {
        var inbox = MIDIInbox()
        inbox.push([0x9F,36], at: 1)
        inbox.push([100,0xFC], at: 2)
        let batch = inbox.drain()
        XCTAssertFalse(batch.overflow)
        XCTAssertEqual(batch.events.map(\.event), [.note(channel:16,note:36),.stop])
    }
    func testInboxOverflowExplicitlyInvalidatesRunningStatus() {
        var inbox = MIDIInbox()
        inbox.push([0x9F,36], at: 1)
        inbox.push(Array(repeating: 0xF8, count: 257), at: 2)
        let batch = inbox.drain()
        XCTAssertTrue(batch.overflow); XCTAssertTrue(batch.events.isEmpty)
        inbox.push([100,39,127], at: 3)
        XCTAssertTrue(inbox.drain().events.isEmpty)
        inbox.push([0x9F,39,127], at: 4)
        XCTAssertEqual(inbox.drain().events.map(\.event), [.note(channel:16,note:39)])
    }
    func testClockTracksPositionBarBoundaryAndLoss() throws {
        var clock = MIDIClock()
        clock.receive(.start, at: 10)
        for tick in 0...48 { clock.receive(.clock, at: 10+Double(tick)/48) }
        XCTAssertEqual(try XCTUnwrap(clock.bpm),120,accuracy:0.001)
        XCTAssertTrue(clock.locked(at:11))
        XCTAssertEqual(try XCTUnwrap(clock.nextBoundary(at:11,beats:4)),12,accuracy:0.001)
        XCTAssertFalse(clock.locked(at:11.6))
        XCTAssertNil(clock.nextBoundary(at:11.6,beats:4))
        let revision = clock.revision
        clock.receive(.position(32),at:12)
        XCTAssertGreaterThan(clock.revision,revision)
        clock.receive(.resume,at:12)
        for tick in 0...24 { clock.receive(.clock,at:12+Double(tick)/48) }
        XCTAssertEqual(try XCTUnwrap(clock.nextBoundary(at:12.5,beats:4)),14,accuracy:0.001)
        clock.receive(.stop,at:13)
        XCTAssertNil(clock.nextBoundary(at:13,beats:4))
    }
    func testRealtimeDoesNotBreakSongPositionMessage() {
        var parser = MIDIParser()
        XCTAssertEqual(parser.feedEvents([0xF2,8,0xF8,1,0xFB]), [.clock,.position(136),.resume])
    }
    func testMusicalLengthTrimsRecorderTailButRejectsBadLength() throws {
        let pcm = try PCM(wav: wav(frames: 48010), targetFrames: 48000)
        XCTAssertEqual(pcm.seconds,1)
        let padded = try PCM(wav: wav(frames: 47990), targetFrames: 48000)
        XCTAssertEqual(padded.seconds,1)
        XCTAssertThrowsError(try PCM(wav: wav(frames: 40000), targetFrames: 48000))
        XCTAssertThrowsError(try PCM(wav: wav(frames: 48000), targetFrames: 0))
    }
}
