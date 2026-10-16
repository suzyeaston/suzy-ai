import SwiftUI
import AppKit

@main struct SuzyLiveApp: App {
    @StateObject private var performance = Performance()
    init() { NSApplication.shared.setActivationPolicy(.regular) }
    var body: some Scene {
        WindowGroup("SUZY // LIVE") {
            CompanionView(model: performance)
                .onReceive(NotificationCenter.default.publisher(for: NSApplication.willTerminateNotification)) { _ in
                    performance.shutdown()
                }
                .onAppear { NSApplication.shared.activate(ignoringOtherApps: true) }
        }
        .windowStyle(.titleBar)
        .commands { CommandGroup(replacing: .newItem) {} }
    }
}

private struct CompanionView: View {
    @ObservedObject var model: Performance
    @State private var confirmReset = false
    @FocusState private var editing: Bool
    var body: some View {
        ScrollView {
        VStack(alignment: .leading, spacing: 18) {
            HStack {
                VStack(alignment: .leading) {
                    Text("SUZY // LIVE").font(.system(size: 32, weight: .black, design: .monospaced))
                    Text("EVOLVE WITH ME · experimental Mac companion").foregroundStyle(.secondary)
                }
                Spacer()
                Button("Connect", action: model.connect)
                Circle().fill(model.connected ? Color.green : Color.gray).frame(width: 10, height: 10)
            }
            LocalLoopView(model: model, loop: model.looper)
            Divider()
            Toggle("AI works in the background", isOn: $model.backgroundAI)
            Button("Request variation of current loop", action: model.requestBackgroundResponse).disabled(!model.connected || model.actionBusy || model.phase == "processing")
            Text("AI: \(model.phase.uppercased())\(model.loopPlaying ? " · RESPONSE LOOP PLAYING" : "")")
                .font(.system(.headline, design: .monospaced)).foregroundStyle(.mint)
            HStack {
                Picker("Response", selection: $model.mode) {
                    Text("Mirror").tag("mirror"); Text("Augment").tag("augment"); Text("Evolve").tag("evolve")
                }
                Picker("Decisions", selection: $model.provider) {
                    Text("Deterministic DSP").tag("deterministic")
                    Text("Local model").tag("model")
                }
            }.disabled(!model.canCapture)
            HStack {
                TextField("Section (e.g. opening)", text: $model.section).focused($editing)
                TextField("Key, if known", text: $model.musicalKey).focused($editing).frame(width: 130)
                Button("Clear musical history", action: model.resetMusicalContext)
            }.disabled(!model.canCapture)
            TextField("Direction (e.g. sparse, leave room for my voice)", text: $model.direction).focused($editing).disabled(!model.canCapture)
            Toggle("I understand audition uses the SAME output as the audience (no private cue)", isOn: $model.auditionAcknowledged)
                .font(.caption).foregroundStyle(.orange)
            HStack(spacing: 12) {
                Button("Audition (shared)", action: model.audition).disabled(!model.canRespond)
                Button("Add AI layer", action: model.accept).disabled(!model.canRespond)
                Button("Discard AI", action: model.discard).disabled(model.phase == "idle" || model.phase == "stopping")
                Button("Remove AI layer", action: model.removeAILayer).disabled(!model.loopPlaying)
                Button("Save AI WAV", action: model.saveResponse).disabled(!model.canSave)
                Spacer()
                Button("STOP ALL", action: model.stopAll).keyboardShortcut(.escape, modifiers: []).tint(.red)
            }.controlSize(.large)
            HStack {
                Text("Response level")
                Slider(value: $model.volume, in: 0...1)
                Text("\(Int(model.volume*100))%").monospacedDigit().frame(width: 45)
            }
            Divider()
            HStack {
                Picker("MIDI controller", selection: $model.midiSource) {
                    Text("Off").tag(UInt32(0))
                    ForEach(model.midiSources) { source in Text(source.name).tag(source.id) }
                }
                Button("Refresh", action: model.refreshMIDI)
                Stepper("Channel \(model.midiChannel)", value: $model.midiChannel, in: 1...16).frame(width: 160)
            }
            Text("36 record/finish · 37 audition AI · 38 add AI · 39 stop all · 40 discard AI · 41 overdub · 42 undo · 43 mute original · 44 clear · 45 play · 46 remove AI layer")
                .font(.caption).foregroundStyle(.secondary)
            Text(model.message).frame(maxWidth: .infinity, minHeight: 48, alignment: .leading)
                .padding(12).background(.quaternary).cornerRadius(8)
            HStack(alignment: .top) {
                Text("Dry system input → source-audio response. Playback uses system output.\nFree or experimental MIDI-clock launch. Not inserted into Logic Live Loops.")
                    .font(.caption).foregroundStyle(.secondary)
                Spacer()
                Button("Reset bridge…") { confirmReset = true }
            }
        }
        .padding(24)
        }.frame(minWidth: 1000, minHeight: 650)
        .preferredColorScheme(.dark)
        .alert("Discard the bridge's current phrase?", isPresented: $confirmReset) {
            Button("Cancel", role: .cancel) {}
            Button("Reset", role: .destructive, action: model.resetBridge)
        } message: { Text("Use one companion at a time. Reset discards any bridge phrase, including one left by another client. Logic is unaffected.") }
    }
}


private struct LocalLoopView: View {
    @ObservedObject var model: Performance
    @ObservedObject var loop: LocalLooper
    @FocusState private var editing: Bool
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("YOUR LOOP · \(loop.state.uppercased())").font(.headline).foregroundStyle(.mint)
            Text("Record → loop → overdub → undo. Works with AI off or disconnected.").font(.caption)
            HStack {
                Toggle("Follow Logic clock (experimental)", isOn: $model.syncEnabled)
                Picker("Clock input", selection: $model.clockSource) {
                    Text("Off").tag(UInt32(0))
                    ForEach(model.midiSources) { source in Text(source.name).tag(source.id) }
                }
                Text(model.clockLabel).font(.caption)
            }.disabled(loop.busy)
            HStack {
                Stepper("\(model.beatsPerBar) quarter-note beats / bar", value: $model.beatsPerBar, in: 1...8)
                Picker("Musical capture", selection: $model.captureBeats) {
                    ForEach([1,2,4,8], id: \.self) { Text("\($0) beats").tag($0) }
                }
            }.disabled(loop.busy || !model.syncEnabled)
            HStack {
                Text("Free BPM")
                TextField("120", value: $model.bpm, format: .number).focused($editing).frame(width: 65)
                Picker("Free capture", selection: $model.duration) {
                    Text("2 sec").tag(2.0); Text("4 sec").tag(4.0)
                    Text("6 sec").tag(6.0); Text("7.5 sec").tag(7.5)
                }
                Picker("Input", selection: $model.channel) {
                    Text("Channel 1").tag(0); Text("Channel 2").tag(1); Text("Stereo 1 + 2").tag(2)
                }
            }.disabled(loop.busy)

            HStack {
                Button(loop.state == "recording" ? "Finish loop" : "Record", action: model.captureOrFinish)
                    .disabled(loop.hasLoop || (loop.busy && loop.state != "recording"))
                Button("Overdub", action: loop.overdub).disabled(!loop.hasLoop || loop.busy || !loop.playing)
                Button("Undo overdub", action: loop.undo).disabled(!loop.canUndo || loop.busy)
                Button(loop.muted ? "Unmute" : "Mute") { loop.muted.toggle() }.disabled(!loop.hasLoop)
                Button("Play", action: loop.play).disabled(!loop.hasLoop || loop.busy || loop.playing)
                Button("Stop", action: model.stopAll)
                Button("Clear", action: loop.clear).disabled(!loop.hasLoop && !loop.busy)
                Button("Save original", action: loop.save).disabled(!loop.hasLoop || loop.saveOpen)
            }.controlSize(.large)
            HStack {
                Text("Original level")
                Slider(value: $loop.volume, in: 0...1)
                Text(String(format: "%.2f sec", loop.seconds)).monospacedDigit()
            }
            Text(loop.message).font(.callout)
        }
    }
}
