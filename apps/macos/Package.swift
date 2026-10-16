// swift-tools-version: 5.9
import PackageDescription
let package = Package(
    name: "SuzyLive",
    platforms: [.macOS(.v13)],
    products: [.executable(name: "SuzyLive", targets: ["SuzyLive"])],
    targets: [
        .target(name: "CompanionCore"),
        .executableTarget(name: "SuzyLive", dependencies: ["CompanionCore"]),
        .testTarget(name: "CompanionCoreTests", dependencies: ["CompanionCore"])
    ]
)
