#pragma once
#include "PluginProcessor.h"
#include <array>
#include <memory>

class SuzyToastAudioProcessorEditor final : public juce::AudioProcessorEditor,
                                            private juce::Timer {
public:
    explicit SuzyToastAudioProcessorEditor(SuzyToastAudioProcessor&);
    ~SuzyToastAudioProcessorEditor() override = default;
    void paint(juce::Graphics&) override;
    void resized() override;

private:
    void timerCallback() override;
    SuzyToastAudioProcessor& processor_;
    juce::Label heading_, subtitle_, loopStatus_, caveat_;
    juce::Label sceneTitle_, chordCues_, sceneNotice_, sceneStyle_;
    juce::TextButton scenePyramid_{"01 · PYRAMID"}, sceneEvolve_{"02 · EVOLVE"},
                     sceneFishes_{"03 · FISHES"}, previousCue_{"◀ CUE"},
                     nextCue_{"CUE ▶"};
    int cueIndex_ = 0;
    int displayedScene_ = -1;
    void updateShowCues();
    juce::TextButton record_{"RECORD"}, overdub_{"OVERDUB"}, play_{"PLAY"},
                     stop_{"STOP"}, clear_{"CLEAR"}, space_{"SPACE · MUTE"};
    juce::Slider browning_, destruction_, live_, loopMix_, gain_, bpm_, beats_;
    juce::ComboBox bars_;
    std::array<juce::Slider*, 5> dials_{{&browning_, &destruction_, &live_, &loopMix_, &gain_}};
    using SliderAttachment = juce::AudioProcessorValueTreeState::SliderAttachment;
    using ComboAttachment = juce::AudioProcessorValueTreeState::ComboBoxAttachment;
    using ButtonAttachment = juce::AudioProcessorValueTreeState::ButtonAttachment;
    std::array<std::unique_ptr<SliderAttachment>, 7> sliders_;
    std::unique_ptr<ComboAttachment> barsAttachment_;
    std::unique_ptr<ButtonAttachment> muteAttachment_;
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(SuzyToastAudioProcessorEditor)
};
