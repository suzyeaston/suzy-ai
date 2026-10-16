import Foundation
import CoreMIDI
import Darwin
import CompanionCore

final class MIDIController {
    struct Source: Identifiable { let id: MIDIEndpointRef; let name: String }
    private var client = MIDIClientRef()
    private var port = MIDIPortRef()
    private var source = MIDIEndpointRef()
    private let lock = NSLock()
    private var inbox = MIDIInbox()
    var onEvents: (([TimedMIDIEvent], Bool) -> Void)?

    static func seconds(_ stamp: MIDITimeStamp) -> Double {
        var info = mach_timebase_info_data_t(); mach_timebase_info(&info)
        return Double(stamp == 0 ? mach_absolute_time() : stamp) * Double(info.numer) / Double(info.denom) / 1_000_000_000
    }
    static var now: Double { seconds(mach_absolute_time()) }

    init() {
        MIDIClientCreateWithBlock("SUZY Live" as CFString, &client, nil)
        MIDIInputPortCreateWithBlock(client, "Performance input" as CFString, &port) { [weak self] list, context in
            guard let self else { return }
            let endpoint = UInt32(UInt(bitPattern: context))
            self.lock.lock(); defer { self.lock.unlock() }
            guard self.source == endpoint else { return }
            var packet = UnsafeRawPointer(list).advanced(by: MemoryLayout<MIDIPacketList>.offset(of: \.packet)!)
                .assumingMemoryBound(to: MIDIPacket.self)
            var total = 0
            for _ in 0..<list.pointee.numPackets {
                let count = Int(packet.pointee.length); total += count
                guard total <= 4096 else { self.inbox.invalidate(); return }
                let bytes = UnsafeRawPointer(packet).advanced(by: MemoryLayout<MIDIPacket>.offset(of: \.data)!)
                    .assumingMemoryBound(to: UInt8.self)
                self.inbox.push(Array(UnsafeBufferPointer(start: bytes, count: count)), at: Self.seconds(packet.pointee.timeStamp))
                packet = UnsafePointer(MIDIPacketNext(packet))
            }
        }
    }
    // Called by one UI timer. No unbounded dispatch-to-main queue or dropped packet fragments.
    func drain() {
        lock.lock(); let batch = inbox.drain(); lock.unlock()
        if !batch.events.isEmpty || batch.overflow { onEvents?(batch.events, batch.overflow) }
    }
    func sources() -> [Source] {
        (0..<MIDIGetNumberOfSources()).map { index in
            let endpoint = MIDIGetSource(index)
            var name: Unmanaged<CFString>?
            MIDIObjectGetStringProperty(endpoint, kMIDIPropertyDisplayName, &name)
            return Source(id: endpoint, name: name?.takeRetainedValue() as String? ?? "MIDI source \(index+1)")
        }
    }
    func select(_ endpoint: MIDIEndpointRef) {
        if source != 0 { MIDIPortDisconnectSource(port, source) }
        lock.lock(); source = endpoint; inbox = MIDIInbox(); lock.unlock()
        if endpoint != 0 { MIDIPortConnectSource(port, endpoint, UnsafeMutableRawPointer(bitPattern: UInt(endpoint))) }
    }
    deinit { MIDIPortDispose(port); MIDIClientDispose(client) }
}
