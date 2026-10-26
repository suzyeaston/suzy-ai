#pragma once
// JUCE-free, allocation-free-in-render single-loop audio buffer.
// This module intentionally cannot read Logic transport, microphone, or MIDI.
// All allocation happens in prepare() on the host's non-realtime setup thread.
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <vector>

namespace suzytoast {

enum class LoopState { empty, recording, playing, overdubbing, stopped };
enum class LoopCommand { none, record, play, overdub, stop, clear };

class LoopBuffer {
public:
    static constexpr double maxSeconds = 36.0;
    void prepare(double sampleRate, int channels) {
        sampleRate_ = sampleRate;
        channels_ = std::clamp(channels, 1, 2);
        const auto capacity = static_cast<size_t>(std::ceil(sampleRate * maxSeconds));
        for (int ch = 0; ch < 2; ++ch)
            audio_[ch].assign(ch < channels_ ? capacity : 0, 0.0f);
        capacityFrames_ = capacity;
        clear();
    }

    bool record(double bpm, int beatsPerBar, int bars) noexcept {
        if (sampleRate_ <= 0.0 || !std::isfinite(bpm) || bpm < 40.0 ||
            bpm > 240.0 || beatsPerBar < 3 || beatsPerBar > 6 ||
            (bars != 1 && bars != 2 && bars != 4)) return false;

        const auto length = static_cast<size_t>(std::llround(
            sampleRate_ * 60.0 * static_cast<double>(beatsPerBar * bars) / bpm));
        if (length == 0 || length > capacityFrames_) return false;

        length_ = length;
        cursor_ = 0;
        state_ = LoopState::recording;
        // No clearing or allocation on this audio callback. Every recorded frame is
        // overwritten before playback can ever read it.
        return true;
    }

    void play() noexcept {
        if (length_ == 0 || state_ == LoopState::recording) return;
        cursor_ = 0;
        state_ = LoopState::playing;
    }
    void overdub() noexcept {
        if (length_ == 0 || (state_ != LoopState::playing &&
                              state_ != LoopState::stopped)) return;
        cursor_ = 0;
        state_ = LoopState::overdubbing;
    }
    void stop() noexcept {
        if (state_ == LoopState::empty) return;
        // A cancelled partial recording is not playable or retained.
        if (state_ == LoopState::recording) { clear(); return; }
        state_ = LoopState::stopped;
    }
    void clear() noexcept {
        length_ = cursor_ = 0;
        state_ = LoopState::empty;
    }

    // Called once per channel for the current sample frame, then advanceFrame().
    // Only stores processed source samples; does not call external APIs or allocate.
    float sample(int channel, float source, float loopLevel) noexcept {
        if (channel < 0 || channel >= channels_) return source;
        if (state_ == LoopState::recording) {
            audio_[channel][cursor_] = source;
            return source;
        }
        if (state_ != LoopState::playing && state_ != LoopState::overdubbing)
            return source;
        const float previous = audio_[channel][cursor_];
        if (state_ == LoopState::overdubbing) {
            // Conservative feedback/overdub mix. This is not Undo: the old
            // buffer is modified for good, until Clear or a fresh Record.
            audio_[channel][cursor_] = std::clamp(previous * 0.75f + source * 0.35f,
                                                   -1.0f, 1.0f);
        }
        // Dry generator continues behind the independently controllable loop.
        return source + previous * std::clamp(loopLevel, 0.0f, 1.0f) * 0.5f;
    }
    void advanceFrame() noexcept {
        if (state_ != LoopState::recording && state_ != LoopState::playing &&
            state_ != LoopState::overdubbing) return;
        ++cursor_;
        if (cursor_ >= length_) {
            cursor_ = 0;
            if (state_ == LoopState::recording || state_ == LoopState::overdubbing)
                state_ = LoopState::playing;
        }
    }

    LoopState state() const noexcept { return state_; }
    size_t lengthFrames() const noexcept { return length_; }
    size_t cursor() const noexcept { return cursor_; }
    int channels() const noexcept { return channels_; }
private:
    std::vector<float> audio_[2];
    size_t capacityFrames_ = 0, length_ = 0, cursor_ = 0;
    double sampleRate_ = 0.0;
    int channels_ = 1;
    LoopState state_ = LoopState::empty;
};
} // namespace suzytoast
