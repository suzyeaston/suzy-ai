import Foundation
import CoreMIDI
import CompanionCore

final class MIDIController {
    struct Source: Identifiable { let id: MIDIEndpointRef; let name: String }
    private var client = MIDIClientRef()
    private var port = MIDIPortRef()
    private var source = MIDIEndpointRef()
    private let queue = DispatchQueue(label: "ca.suzyeaston.suzylive.midi")
    private var parser = MIDIParser()
    private let pending = DispatchSemaphore(value: 1)
    var onNote: ((Int, Int) -> Void)?

    init() {
        MIDIClientCreateWithBlock("SUZY Live" as CFString, &client, nil)
        MIDIInputPortCreateWithBlock(client, "Performance controls" as CFString, &port) { [weak self] list, context in
            guard let self, self.pending.wait(timeout: .now()) == .success else { return }
            let pending = self.pending
            let endpoint = UInt32(UInt(bitPattern: context))
            // Copy packet bytes before CoreMIDI releases the list. Parsing/UI work is off its thread.
            let first = UnsafeRawPointer(list).advanced(by: MemoryLayout<MIDIPacketList>.offset(of: \.packet)!)
                .assumingMemoryBound(to: MIDIPacket.self)
            var packet = first
            var data: [UInt8] = []
            for _ in 0..<list.pointee.numPackets {
                let bytes = UnsafeRawPointer(packet).advanced(by: MemoryLayout<MIDIPacket>.offset(of: \.data)!)
                    .assumingMemoryBound(to: UInt8.self)
                let count = Int(packet.pointee.length)
                // A pathological controller burst is dropped, never allowed to grow without bound.
                if data.count + count > 4096 { pending.signal(); return }
                data.append(contentsOf: UnsafeBufferPointer(start: bytes, count: count))
                packet = UnsafePointer(MIDIPacketNext(packet))
            }
            let packetData = data
            self.queue.async { [weak self] in
                guard let self else { pending.signal(); return }
                let notes = Array(self.parser.feed(packetData).filter { (36...40).contains($0.note) }.prefix(16))
                DispatchQueue.main.async { [weak self] in
                    defer { pending.signal() }
                    guard let self, self.source == endpoint else { return }
                    for note in notes { self.onNote?(note.channel, note.note) }
                }
            }
        }
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
        source = endpoint
        queue.sync { parser = MIDIParser() }
        if endpoint != 0 { MIDIPortConnectSource(port, endpoint, UnsafeMutableRawPointer(bitPattern: UInt(endpoint))) }
    }
    deinit { MIDIPortDispose(port); MIDIClientDispose(client) }
}
