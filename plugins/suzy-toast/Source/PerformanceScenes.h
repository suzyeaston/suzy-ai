#pragma once
// Performance scene metadata. Portable C++, no JUCE/GUI/ML dependencies.
// Chord strings are human-readable cues. This module never sends MIDI,
// changes the official Magenta AU prompt or controls Logic transport.
#include <array>
#include <cstddef>
#include <string_view>

namespace suzytoast {

struct PerformanceScene {
    const char* shortName;
    const char* song;
    const char* instructions;
    const char* styleReminder;  // Manual AU prompting advice, NOT applied by this plugin.
    std::array<const char*, 5> chords;
    size_t chordCount;
    int rehearsalBpm;
    float browning;
    float destruction;
    float liveMix;
    float loopMix;
    int bars;
};

inline constexpr std::array<PerformanceScene, 3> performanceScenes{{
    {"PYRAMID", "Pyramid Song / OPEN",
     "Piano and voice lead. Let the floating rhythm settle; AI enters quietly.",
     "If available in Google's AU: sparse strings, glassy harmonics, soft transients.",
     {"F#", "Gmaj7", "A6", "Gmaj7", "F#"}, 5, 105,
     0.48f, 0.02f, 0.18f, 0.24f, 2},
    {"EVOLVE", "The Appliance Latent Space / MIDDLE",
     "Your own beat, vocal and synth lead. Catch only the AI phrases you choose.",
     "If available in Google's AU: warm spacious jazz-rap, airy keys, restrained rhythm.",
     {"Em7", "A6", "Gmaj7", "F#m7", "Em7"}, 5, 120,
     0.23f, 0.24f, 0.65f, 0.54f, 2},
    {"FISHES", "Weird Fishes/Arpeggi / CLOSE",
     "Keep repeating arpeggios in Logic. AI is soft counterpoint, not the riff.",
     "If available in Google's AU: translucent picked textures, distant harmonics.",
     {"Em7", "F#m7", "A", "Gmaj7", ""}, 4, 153,
     0.30f, 0.05f, 0.22f, 0.36f, 2}
}};

inline const PerformanceScene& sceneAt(int index) noexcept {
    return performanceScenes[static_cast<size_t>(
        index >= 0 && index < static_cast<int>(performanceScenes.size()) ? index : 0)];
}
}  // namespace suzytoast
