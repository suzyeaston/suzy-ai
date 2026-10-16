import Foundation

public struct LiveStatus: Decodable, Sendable {
    public let protocol_version: Int?
    public let id: String?
    public let state: String
    public let busy: Bool
    public let error: String?
    public let response: Response?
    public struct Response: Decodable, Sendable {
        public let provider: String
        public let model: String?
        public let elapsed_seconds: Double
    }
}

public final class Bridge: @unchecked Sendable {
    private let session: URLSession
    private let base = URL(string: "http://127.0.0.1:7333")!
    public init() {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.timeoutIntervalForRequest = 5
        configuration.timeoutIntervalForResource = 10
        configuration.connectionProxyDictionary = [:]
        session = URLSession(configuration: configuration, delegate: NoRedirect(), delegateQueue: nil)
    }
    private func request(_ path: String, body: Data? = nil, type: String = "application/json", limit: Int = 65536) async throws -> Data {
        var request = URLRequest(url: base.appendingPathComponent(path))
        if let body {
            request.httpMethod = "POST"; request.httpBody = body
            request.setValue(type, forHTTPHeaderField: "Content-Type")
        }
        let (stream, response) = try await session.bytes(for: request)
        guard let http = response as? HTTPURLResponse else { throw CompanionError.invalid("Invalid bridge response.") }
        guard http.statusCode >= 200 && http.statusCode < 300 else {
            throw CompanionError.invalid("Bridge returned HTTP \(http.statusCode). Discard/reset before retrying; check the service terminal.")
        }
        guard response.expectedContentLength <= limit else { throw CompanionError.invalid("Bridge response exceeds limit.") }
        var data = Data()
        for try await byte in stream {
            guard data.count < limit else { throw CompanionError.invalid("Bridge response exceeds limit.") }
            data.append(byte)
        }
        return data
    }
    public func status() async throws -> LiveStatus {
        let status = try JSONDecoder().decode(LiveStatus.self, from: await request("v1/live"))
        guard status.protocol_version == 2 else {
            throw CompanionError.invalid("Bridge version mismatch. Quit the previous companion/bridge and restart from this checkout.")
        }
        return status
    }
    public func arm(rate: Int, channels: Int, bpm: Double, mode: String, provider: String, section: String = "", key: String = "", instruction: String = "") async throws -> String {
        let body = try JSONSerialization.data(withJSONObject: ["sample_rate":rate, "channels":channels,
                        "bpm":bpm, "mode":mode, "provider":provider, "section":section, "key":key, "instruction":instruction])
        let status = try JSONDecoder().decode(LiveStatus.self, from: await request("v1/live/capture", body: body))
        guard let id = status.id, id.count == 32, id.allSatisfy({ $0.isHexDigit }) else {
            throw CompanionError.invalid("Invalid capture identifier.")
        }
        return id
    }
    public func chunk(id: String, sequence: Int, data: Data) async throws {
        _ = try await request("v1/live/\(id)/chunks/\(sequence)", body: data, type: "application/octet-stream")
    }
    public func action(id: String, name: String) async throws {
        _ = try await request("v1/live/\(id)/\(name)", body: Data("{}".utf8))
    }
    public func resetContext() async throws {
        _ = try await request("v1/live/context/reset", body: Data("{}".utf8))
    }
    public func audio(id: String) async throws -> Data {
        try await request("v1/live/\(id)/audio.wav", limit: 1_600_000)
    }
}

private final class NoRedirect: NSObject, URLSessionTaskDelegate {
    func urlSession(_ session: URLSession, task: URLSessionTask,
                    willPerformHTTPRedirection response: HTTPURLResponse,
                    newRequest request: URLRequest, completionHandler: @escaping (URLRequest?) -> Void) {
        completionHandler(nil)
    }
}
