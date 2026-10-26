// Hardware-free tests for the audio core shared by AU and a possible future app.
// Compile: c++ -std=c++17 -O2 tests/loop_buffer_test.cpp -o /tmp/suzy-toast-loop-test
#include "../Source/LoopBuffer.h"
#include <cassert>
#include <cmath>
#include <iostream>

using suzytoast::LoopBuffer;
using suzytoast::LoopState;

int main() {
    constexpr double rate = 48000.0;
    LoopBuffer loop;
    loop.prepare(rate, 2);
    assert(loop.channels() == 2);
    assert(loop.state() == LoopState::empty);
    assert(!loop.record(0, 4, 1));
    assert(!loop.record(120, 4, 3));
    assert(!loop.record(30, 4, 1));
    assert(loop.record(120, 4, 1));
    assert(loop.lengthFrames() == 96000);
    assert(loop.state() == LoopState::recording);
    for (size_t i = 0; i < loop.lengthFrames(); ++i) {
        auto left = loop.sample(0, .25f, 0.5f, 1.0f);
        auto right = loop.sample(1, -.125f, 0.5f, 1.0f);
        assert(std::abs(left - .25f) < .001f);
        assert(std::abs(right + .125f) < .001f);
        loop.advanceFrame();
    }
    assert(loop.state() == LoopState::playing);
    // Captured sound remains audible even with live AI stream fader at 0.
    assert(std::abs(loop.sample(0, 0.f, 1.f, 0.f) - .25f) < .001f);
    assert(std::abs(loop.sample(1, 0.f, 1.f, 0.f) + .125f) < .001f);
    loop.advanceFrame();
    assert(loop.cursor() == 1);
    loop.stop();
    assert(loop.state() == LoopState::stopped);
    assert(std::abs(loop.sample(0, 0.f, 1.f, 0.f)) < .001f);
    loop.play();
    assert(loop.state() == LoopState::playing);
    assert(loop.cursor() == 0);

    loop.overdub();
    assert(loop.state() == LoopState::overdubbing);
    for (size_t i = 0; i < loop.lengthFrames(); ++i) {
        loop.sample(0, .5f, 0.f, 0.f);
        loop.sample(1, 0.f, 0.f, 0.f);
        loop.advanceFrame();
    }
    assert(loop.state() == LoopState::playing);
    assert(std::abs(loop.sample(0, 0.f, 1.f, 0.f) - .3625f) < .001f);
    // Fresh recording overwrites old content, and cancelling mid-take discards it.
    assert(loop.record(120, 4, 2));
    loop.sample(0, 1.f, 1.f, 0.f);
    loop.advanceFrame();
    loop.stop();
    assert(loop.state() == LoopState::empty);
    assert(loop.lengthFrames() == 0);

    loop.prepare(44100.0, 1);
    assert(loop.record(120, 4, 1));
    assert(loop.lengthFrames() == 88200);
    loop.clear();
    assert(loop.state() == LoopState::empty);
    std::cout << "SUZY TOAST loop core: stereo capture, independent mix, overdub, "
                 "record cancel, 44.1/48 kHz PASS\n";
}
