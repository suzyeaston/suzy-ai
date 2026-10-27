#pragma once
#include <JuceHeader.h>
#include "LoopBuffer.h"
#include "PerformanceScenes.h"
#include <atomic>

class SuzyToastAudioProcessor final : public juce::AudioProcessor {
public:
    SuzyToastAudioProcessor();
    ~SuzyToastAudioProcessor() override = default;

    void prepareToPlay(double sampleRate, int samplesPerBlock) override;
    void releaseResources() override {}
    bool isBusesLayoutSupported(const BusesLayout& layouts) const override;
    void processBlock(juce::AudioBuffer<float>&, juce::MidiBuffer&) override;
    juce::AudioProcessorEditor* createEditor() override;
    bool hasEditor() const override { return true; }
    const juce::String getName() const override { return JucePlugin_Name; }
    bool acceptsMidi() const override { return false; }
    bool producesMidi() const override { return false; }
    bool isMidiEffect() const override { return false; }
    double getTailLengthSeconds() const override { return 0.0; }
    int getNumPrograms() override { return 1; }
    int getCurrentProgram() override { return 0; }
    void setCurrentProgram(int) override {}
    const juce::String getProgramName(int) override { return {}; }
    void changeProgramName(int, const juce::String&) override {}
    void getStateInformation(juce::MemoryBlock&) override;
    void setStateInformation(const void*, int) override;

    // Message-thread scene recall changes the AU's *actual* post-AI sound
    // parameters. It never sends MIDI, alters Magenta style, mutes vocals,
    // switches Logic tracks, or starts/stops the host transport.
    void applyPerformanceScene(int index);
    int performanceSceneIndex() const noexcept;

    void requestLoop(suzytoast::LoopCommand cmd) noexcept { pending_.store(cmd); }
    suzytoast::LoopState loopState() const noexcept {
        return static_cast<suzytoast::LoopState>(publishedState_.load());
    }
    bool lastRecordRejected() const noexcept { return recordRejected_.load(); }
    double actualSampleRate() const noexcept { return hostRate_.load(); }
    double logicHostBpm() const noexcept { return hostBpm_.load(); }
    int actualChannels() const noexcept { return hostChannels_.load(); }

    static juce::AudioProcessorValueTreeState::ParameterLayout createParameters();
    juce::AudioProcessorValueTreeState parameters;

private:
    suzytoast::LoopBuffer loop_;
    std::atomic<suzytoast::LoopCommand> pending_{suzytoast::LoopCommand::none};
    std::atomic<int> publishedState_{static_cast<int>(suzytoast::LoopState::empty)};
    std::atomic<bool> recordRejected_{false};
    std::atomic<double> hostRate_{0.0};
    std::atomic<double> hostBpm_{0.0};
    std::atomic<int> hostChannels_{0};
    float lpState_[2] = {0.0f, 0.0f};
    juce::SmoothedValue<float, juce::ValueSmoothingTypes::Linear> outputGain_;
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(SuzyToastAudioProcessor)
};
