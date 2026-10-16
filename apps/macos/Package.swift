// swift-tools-version: 5.9
import PackageDescription
let package = Package(
    name: "SuzyLive",
    platforms: [.macOS(.v13)],
    products: [.executable(name: "SuzyLive", targets: ["SuzyLive"])],
    targets: [
        .target(name: "CompanionCore"),
        .target(name: "NativeLoop", linkerSettings: [.linkedFramework("CoreAudio"), .linkedFramework("AudioToolbox")]),
        .executableTarget(name: "SuzyLive", dependencies: ["CompanionCore", "NativeLoop"]),
        .testTarget(name: "CompanionCoreTests", dependencies: ["CompanionCore", "NativeLoop"])
    ]
)
