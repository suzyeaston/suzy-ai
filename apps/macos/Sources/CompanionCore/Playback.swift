/// No networking in the playback transaction. A failed start preserves the old loop.
public protocol LoopPlayer: AnyObject {
    func start(at time: Double?) -> Bool
    func stop()
}
public final class PlaybackSlot {
    public private(set) var current: LoopPlayer?
    public private(set) var pending: LoopPlayer?
    public init() {}
    @discardableResult public func stage(_ candidate: LoopPlayer, at time: Double?) -> Bool {
        guard candidate.start(at: time) else { candidate.stop(); return false }
        pending?.stop(); pending = candidate
        return true
    }
    public func commit() {
        guard let pending else { return }
        current?.stop(); current = pending; self.pending = nil
    }
    public func cancelPending() { pending?.stop(); pending = nil }
    @discardableResult public func replace(with candidate: LoopPlayer) -> Bool {
        guard stage(candidate, at: nil) else { return false }
        commit(); return true
    }
    public func stop() { cancelPending(); current?.stop(); current = nil }
}
