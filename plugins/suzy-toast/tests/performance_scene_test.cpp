// Pure C++ performance scene test; no Mac or JUCE needed.
#include "../Source/PerformanceScenes.h"
#include <cassert>
#include <cmath>
#include <cstring>
#include <iostream>

int main() {
    using namespace suzytoast;
    static_assert(performanceScenes.size() == 3, "3 show sections");
    const auto& opening = sceneAt(0);
    const auto& middle = sceneAt(1);
    const auto& closing = sceneAt(2);
    assert(std::strcmp(opening.shortName, "PYRAMID") == 0);
    assert(std::strcmp(middle.shortName, "EVOLVE") == 0);
    assert(std::strcmp(closing.shortName, "FISHES") == 0);
    assert(opening.chordCount == 5 && closing.chordCount == 4);
    assert(std::strcmp(opening.chords[0], "F#") == 0);
    assert(std::strcmp(closing.chords[0], "Em7") == 0);
    assert(std::strcmp(closing.chords[3], "Gmaj7") == 0);
    assert(opening.rehearsalBpm == 105 && closing.rehearsalBpm == 153);
    for (const auto& scene : performanceScenes) {
        assert(scene.chordCount > 0 && scene.chordCount <= scene.chords.size());
        assert(scene.bars == 1 || scene.bars == 2 || scene.bars == 4);
        assert(scene.rehearsalBpm >= 40 && scene.rehearsalBpm <= 240);
        assert(scene.browning >= 0 && scene.browning <= 1);
        assert(scene.destruction >= 0 && scene.destruction <= 1);
        assert(scene.liveMix >= 0 && scene.liveMix <= 1);
        assert(scene.loopMix >= 0 && scene.loopMix <= 1);
        for (size_t i = 0; i < scene.chordCount; ++i)
            assert(std::strlen(scene.chords[i]) > 0);
    }
    assert(std::strcmp(sceneAt(-1).shortName, "PYRAMID") == 0);
    assert(std::strcmp(sceneAt(99).shortName, "PYRAMID") == 0);
    std::cout << "SUZY//TOAST performance scenes: three validated presets PASS\\n";
}
