#include "PluginProcessor.h"
#include "PluginEditor.h"
#include <algorithm>
#include <cmath>
#include <memory>

namespace {
float value(juce::AudioProcessorValueTreeState& p, const char* id) noexcept {
    auto* raw = p.getRawParameterValue(id);
    return raw == nullptr ? 0.0f : raw->load(std::memory_order_relaxed);
}
}

SuzyToastAudioProcessor::SuzyToastAudioProcessor()
: AudioProcessor(BusesProperties()
    .withInput("Input", juce::AudioChannelSet::stereo(), true)
    .withOutput("Output", juce::AudioChannelSet::stereo(), true)),
  parameters(*this, nullptr, juce::Identifier("SUZYTOAST"), createParameters()) {}

juce::AudioProcessorValueTreeState::ParameterLayout SuzyToastAudioProcessor::createParameters() {
    juce::AudioProcessorValueTreeState::ParameterLayout layout;
    const auto f = [&layout](const char* id, const char* title, float lo, float hi, float start) {
        layout.add(std::make_unique<juce::AudioParameterFloat>(
            juce::ParameterID{id, 1}, title, juce::NormalisableRange<float>{lo, hi, 0.001f}, start));
    };
    f("browning", "Browning", 0.0f, 1.0f, 0.0f);
    f("destruction", "Destruction", 0.0f, 1.0f, 0.0f);
    f("live", "AI Live", 0.0f, 1.0f, 0.7f);
    f("loop", "Loop Mix", 0.0f, 1.0f, 0.5f);
    f("gain", "Master", 0.0f, 1.0f, 0.75f);
    layout.add(std::make_unique<juce::AudioParameterBool>(
        juce::ParameterID{"space", 1}, "SPACE (mute this effect output)", false));
    layout.add(std::make_unique<juce::AudioParameterInt>(
        juce::ParameterID{"bpm", 1}, "Manual loop BPM", 40, 240, 120));
    layout.add(std::make_unique<juce::AudioParameterInt>(
        juce::ParameterID{"beats", 1}, "Beats per bar", 3, 6, 4));
    layout.add(std::make_unique<juce::AudioParameterChoice>(
        juce::ParameterID{"bars", 1}, "Record bars", juce::StringArray{"1", "2", "4"}, 1));
    return layout;
}

bool SuzyToastAudioProcessor::isBusesLayoutSupported(const BusesLayout& layouts) const {
    auto input = layouts.getMainInputChannelSet();
    return (input == juce::AudioChannelSet::mono() || input == juce::AudioChannelSet::stereo())
       && input == layouts.getMainOutputChannelSet();
}

void SuzyToastAudioProcessor::prepareToPlay(double rate, int /*blockSize*/) {
    loop_.prepare(rate, std::clamp(getTotalNumInputChannels(), 1, 2));
    hostRate_.store(rate);
    hostChannels_.store(std::clamp(getTotalNumInputChannels(), 1, 2));
    publishedState_.store(static_cast<int>(suzytoast::LoopState::empty));
    recordRejected_.store(false);
    pending_.store(suzytoast::LoopCommand::none);
    lpState_[0] = lpState_[1] = 0.0f;
    outputGain_.reset(rate, 0.008); // Short, click-reducing level/mute ramp.
    outputGain_.setCurrentAndTargetValue(value(parameters, "gain"));
    setLatencySamples(0);
}

void SuzyToastAudioProcessor::processBlock(juce::AudioBuffer<float>& audio,
                                             juce::MidiBuffer& /*midi*/) {
    juce::ScopedNoDenormals noDenormals;
    const int channels = std::min(audio.getNumChannels(), 2);
    const int frames = audio.getNumSamples();
    for (int ch = channels; ch < audio.getNumChannels(); ++ch) audio.clear(ch, 0, frames);
    const auto action = pending_.exchange(suzytoast::LoopCommand::none);
    switch(action) {
    case suzytoast::LoopCommand::record: {
        const int chosenBars[] = {1, 2, 4};
        const auto barsIndex = std::clamp(static_cast<int>(value(parameters, "bars")), 0, 2);
        const bool ok = loop_.record(value(parameters, "bpm"),
                                     static_cast<int>(value(parameters, "beats")),
                                     chosenBars[barsIndex]);
        recordRejected_.store(!ok);
        break;
    }
    case suzytoast::LoopCommand::play: loop_.play(); break;
    case suzytoast::LoopCommand::overdub: loop_.overdub(); break;
    case suzytoast::LoopCommand::stop: loop_.stop(); break;
    case suzytoast::LoopCommand::clear: loop_.clear(); break;
    case suzytoast::LoopCommand::none: break;
    }
    const float heat = std::clamp(value(parameters, "browning"), 0.0f, 1.0f);
    const float destruction = std::clamp(value(parameters, "destruction"), 0.0f, 1.0f);
    const float dry = std::clamp(value(parameters, "live"), 0.0f, 1.0f);
    const float loopGain = std::clamp(value(parameters, "loop"), 0.0f, 1.0f);
    const bool space = value(parameters, "space") > 0.5f;
    outputGain_.setTargetValue(space ? 0.0f : std::clamp(value(parameters, "gain"), 0.0f, 1.0f));

    const double sr = std::max(8000.0, hostRate_.load());
    const double cutoff = 17500.0 - heat * 15500.0;
    const float a = static_cast<float>(std::exp(-2.0 * juce::MathConstants<double>::pi * cutoff / sr));
    const float drive = 1.0f + destruction * 5.0f;
    float* channelsOut[2] = {
        channels > 0 ? audio.getWritePointer(0) : nullptr,
        channels > 1 ? audio.getWritePointer(1) : nullptr
    };

    for (int i = 0; i < frames; ++i) {
        const float master = outputGain_.getNextValue();
        for (int ch = 0; ch < channels; ++ch) {
            const float input = channelsOut[ch][i];
            lpState_[ch] = heat < 0.001f ? input : (1.0f - a) * input + a * lpState_[ch];
            const float signal = destruction < 0.001f
                ? lpState_[ch] : std::tanh(lpState_[ch] * drive) / std::tanh(drive);
            // Record the pre-fader AI generation so its level can later be set to 0
            // while the captured loop continues. This is deliberate layering.
            const float mixed = loop_.sample(ch, signal, loopGain, dry);
            channelsOut[ch][i] = std::clamp(mixed * master, -1.0f, 1.0f);
        }
        loop_.advanceFrame();
    }
    publishedState_.store(static_cast<int>(loop_.state()));
}

juce::AudioProcessorEditor* SuzyToastAudioProcessor::createEditor() {
    return new SuzyToastAudioProcessorEditor(*this);
}

void SuzyToastAudioProcessor::getStateInformation(juce::MemoryBlock& out) {
    if (auto xml = parameters.copyState().createXml())
        juce::copyXmlToBinary(*xml, out);
    // Loop audio is intentionally NOT serialized in host presets or projects.
    // For durable AI audio, print/record the track in Logic and verify reopen.
}

void SuzyToastAudioProcessor::setStateInformation(const void* data, int size) {
    if (auto xml = juce::getXmlFromBinary(data, size)) {
        const auto tree = juce::ValueTree::fromXml(*xml);
        if (tree.isValid()) parameters.replaceState(tree);
    }
}

juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter() {
    return new SuzyToastAudioProcessor();
}
