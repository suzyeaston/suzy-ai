#include "PluginEditor.h"
#include <algorithm>

namespace {
const auto cream = juce::Colour::fromRGB(255, 245, 231);
const auto mauve = juce::Colour::fromRGB(244, 161, 182);
const auto charcoal = juce::Colour::fromRGB(24, 19, 32);
const auto mint = juce::Colour::fromRGB(201, 240, 193);
void decorate(juce::TextButton& button, juce::Colour c) {
    button.setColour(juce::TextButton::buttonColourId, c);
    button.setColour(juce::TextButton::textColourOffId, charcoal);
}
}

SuzyToastAudioProcessorEditor::SuzyToastAudioProcessorEditor(SuzyToastAudioProcessor& p)
: AudioProcessorEditor(&p), processor_(p) {
    setSize(890, 800);
    heading_.setText("SUZY//TOAST", juce::dontSendNotification);
    heading_.setFont(juce::Font(32.0f, juce::Font::bold));
    heading_.setColour(juce::Label::textColourId, cream);
    addAndMakeVisible(heading_);
    subtitle_.setText("THE APPLIANCE LATENT SPACE · LOCAL AI-AUDIO LOOP EFFECT",
                      juce::dontSendNotification);
    subtitle_.setColour(juce::Label::textColourId, mint);
    addAndMakeVisible(subtitle_);

    const char* ids[] = {"browning", "destruction", "live", "loop", "gain"};
    for (size_t n = 0; n < dials_.size(); ++n) {
        auto& slider = *dials_[n];
        slider.setSliderStyle(juce::Slider::RotaryHorizontalVerticalDrag);
        slider.setTextBoxStyle(juce::Slider::TextBoxBelow, false, 70, 20);
        slider.setColour(juce::Slider::rotarySliderFillColourId, mauve);
        slider.setColour(juce::Slider::thumbColourId, cream);
        addAndMakeVisible(slider);
        sliders_[n] = std::make_unique<SliderAttachment>(p.parameters, ids[n], slider);
    }

    for(auto* slider : {&bpm_, &beats_}) {
        slider->setSliderStyle(juce::Slider::LinearHorizontal);
        slider->setTextBoxStyle(juce::Slider::TextBoxRight, false, 54, 21);
        slider->setColour(juce::Slider::trackColourId, mint);
        addAndMakeVisible(*slider);
    }
    sliders_[5] = std::make_unique<SliderAttachment>(p.parameters, "bpm", bpm_);
    sliders_[6] = std::make_unique<SliderAttachment>(p.parameters, "beats", beats_);

    bars_.addItem("1 bar", 1);
    bars_.addItem("2 bars", 2);
    bars_.addItem("4 bars", 3);
    addAndMakeVisible(bars_);
    barsAttachment_ = std::make_unique<ComboAttachment>(p.parameters, "bars", bars_);

    space_.setClickingTogglesState(true);
    decorate(space_, juce::Colour::fromRGB(248, 185, 148));
    addAndMakeVisible(space_);
    muteAttachment_ = std::make_unique<ButtonAttachment>(p.parameters, "space", space_);

    for(auto* button : {&record_, &overdub_, &play_, &stop_, &clear_}) {
        decorate(*button, juce::Colour::fromRGB(255, 215, 169));
        addAndMakeVisible(*button);
    }
    record_.onClick = [this] { processor_.requestLoop(suzytoast::LoopCommand::record); };
    overdub_.onClick = [this] { processor_.requestLoop(suzytoast::LoopCommand::overdub); };
    play_.onClick = [this] { processor_.requestLoop(suzytoast::LoopCommand::play); };
    stop_.onClick = [this] { processor_.requestLoop(suzytoast::LoopCommand::stop); };
    clear_.onClick = [this] { processor_.requestLoop(suzytoast::LoopCommand::clear); };

    loopStatus_.setColour(juce::Label::textColourId, mint);
    loopStatus_.setFont(juce::Font(16.0f, juce::Font::bold));
    addAndMakeVisible(loopStatus_);
    caveat_.setText("REC captures AI audio on this track, not your VE-22 mic. "
       "Free-running loop length (not Logic bar-aligned). "
       "Loops are temporary: print to an audio track in Logic to keep them.",
       juce::dontSendNotification);
    caveat_.setColour(juce::Label::textColourId, cream.withAlpha(0.75f));
    caveat_.setJustificationType(juce::Justification::centred);
    addAndMakeVisible(caveat_);
    // These three big buttons are the main live-performance interface.
    // Scene recall changes native AU audio parameters; physical Keystation
    // remains the real MIDI/harmony input to Google's preceding MRT2 AU.
    for (auto* button : {&scenePyramid_, &sceneEvolve_, &sceneFishes_}) {
        decorate(*button, juce::Colour::fromRGB(247, 197, 159));
        button->setColour(juce::TextButton::buttonOnColourId, mint);
        button->setClickingTogglesState(false);
        addAndMakeVisible(*button);
    }
    scenePyramid_.onClick = [this] { processor_.applyPerformanceScene(0); cueIndex_ = 0; updateShowCues(); };
    sceneEvolve_.onClick = [this] { processor_.applyPerformanceScene(1); cueIndex_ = 0; updateShowCues(); };
    sceneFishes_.onClick = [this] { processor_.applyPerformanceScene(2); cueIndex_ = 0; updateShowCues(); };
    for (auto* button : {&previousCue_, &nextCue_}) {
        decorate(*button, juce::Colour::fromRGB(187, 206, 185));
        addAndMakeVisible(*button);
    }
    previousCue_.onClick = [this] {
        const auto count = static_cast<int>(
            suzytoast::sceneAt(processor_.performanceSceneIndex()).chordCount);
        cueIndex_ = (cueIndex_ + count - 1) % count;
        updateShowCues();
    };
    nextCue_.onClick = [this] {
        const auto count = static_cast<int>(
            suzytoast::sceneAt(processor_.performanceSceneIndex()).chordCount);
        cueIndex_ = (cueIndex_ + 1) % count;
        updateShowCues();
    };
    for(auto* label : {&sceneTitle_, &chordCues_, &sceneNotice_, &sceneStyle_}) {
        label->setColour(juce::Label::textColourId, cream);
        addAndMakeVisible(*label);
    }
    sceneTitle_.setFont(juce::Font(15.0f, juce::Font::bold));
    chordCues_.setFont(juce::Font(14.0f, juce::Font::bold));
    sceneNotice_.setColour(juce::Label::textColourId, mint);
    sceneNotice_.setFont(juce::Font(11.0f));
    sceneStyle_.setColour(juce::Label::textColourId, cream.withAlpha(0.72f));
    sceneStyle_.setFont(juce::Font(11.0f));
    startTimerHz(8);
    updateShowCues();
    timerCallback();
}

void SuzyToastAudioProcessorEditor::updateShowCues() {
    const int index = processor_.performanceSceneIndex();
    const auto& s = suzytoast::sceneAt(index);
    if (index != displayedScene_) { cueIndex_ = 0; displayedScene_ = index; }
    cueIndex_ = std::clamp(cueIndex_, 0, static_cast<int>(s.chordCount) - 1);
    sceneTitle_.setText(juce::String(s.song) + "   |   " + s.instructions,
                        juce::dontSendNotification);
    juce::String progression;
    for (size_t i = 0; i < s.chordCount; ++i) {
        if (i) progression += "  ·  ";
        progression += s.chords[i];
    }
    chordCues_.setText("PLAY ON KEYSTATION: " +
        juce::String(s.chords[static_cast<size_t>(cueIndex_)]) +
        "     |   " + progression, juce::dontSendNotification);
    sceneNotice_.setText("NEXT/PREV = CUE DISPLAY ONLY · Chords are played on the keyboard · " +
        juce::String(s.rehearsalBpm) +
        " BPM is a loop reference, NOT Logic transport", juce::dontSendNotification);
    sceneStyle_.setText("OPTIONAL GOOGLE AU STYLE REFERENCE (not sent): " +
        juce::String(s.styleReminder), juce::dontSendNotification);
    const juce::Colour normal = juce::Colour::fromRGB(247, 197, 159);
    for(auto* b : {&scenePyramid_, &sceneEvolve_, &sceneFishes_})
        b->setColour(juce::TextButton::buttonColourId, normal);
    (index == 0 ? scenePyramid_ : (index == 1 ? sceneEvolve_ : sceneFishes_))
        .setColour(juce::TextButton::buttonColourId, mint);
}

void SuzyToastAudioProcessorEditor::timerCallback() {
    updateShowCues();
    juce::String state = "EMPTY";
    switch (processor_.loopState()) {
        case suzytoast::LoopState::empty: state = "EMPTY"; break;
        case suzytoast::LoopState::recording: state = "RECORDING AI AUDIO"; break;
        case suzytoast::LoopState::playing: state = "LOOP PLAYING"; break;
        case suzytoast::LoopState::overdubbing: state = "OVERDUBBING"; break;
        case suzytoast::LoopState::stopped: state = "STOPPED"; break;
    }
    if (processor_.lastRecordRejected()) state += " · INVALID / TOO-LONG LOOP REQUEST";
    loopStatus_.setText("LOOP  " + state, juce::dontSendNotification);
}

void SuzyToastAudioProcessorEditor::paint(juce::Graphics& g) {
    const auto bg = juce::Colour::fromRGB(31, 25, 39);
    g.fillAll(bg);
    g.setColour(juce::Colour::fromRGB(59, 47, 66));
    g.fillRoundedRectangle(16.0f, 587.0f, 855.0f, 188.0f, 19.0f);
    g.setColour(mint);
    g.setFont(juce::Font(12.0f, juce::Font::bold));
    g.drawText("LIVE SET / THREE SCENES · ACTUAL AU DSP PRESETS", 28, 591, 800, 17,
               juce::Justification::left);
    g.setColour(juce::Colour::fromRGB(60, 44, 66));
    g.fillRoundedRectangle(16.0f, 99.0f, 855.0f, 405.0f, 22.0f);
    g.setColour(cream.withAlpha(0.07f));
    g.fillRoundedRectangle(26.0f, 107.0f, 282.0f, 382.0f, 18.0f);

    // A cheap, native vector toaster. No browser, image download, animation or GPU engine.
    g.setColour(juce::Colour::fromRGB(117, 73, 81));
    g.fillRoundedRectangle(73.0f, 148.0f, 190.0f, 34.0f, 15.0f);
    g.setColour(juce::Colour::fromRGB(247, 205, 157));
    g.fillRoundedRectangle(112.0f, 118.0f, 118.0f, 83.0f, 22.0f);
    g.setColour(juce::Colour::fromRGB(204, 124, 87));
    g.drawRoundedRectangle(112.0f, 118.0f, 118.0f, 83.0f, 22.0f, 7.0f);

    juce::ColourGradient gradient(cream, 63.0f, 199.0f, mauve, 272.0f, 410.0f, false);
    gradient.addColour(0.55, juce::Colour::fromRGB(246, 183, 178));
    g.setGradientFill(gradient);
    g.fillRoundedRectangle(54.0f, 190.0f, 236.0f, 220.0f, 40.0f);
    g.setColour(cream);
    g.drawRoundedRectangle(54.0f, 190.0f, 236.0f, 220.0f, 40.0f, 6.0f);
    g.setColour(charcoal);
    g.fillEllipse(113.0f, 254.0f, 14.0f, 22.0f);
    g.fillEllipse(214.0f, 254.0f, 14.0f, 22.0f);
    g.fillRoundedRectangle(157.0f, 298.0f, 31.0f, 16.0f, 8.0f);
    g.setFont(juce::Font(16.0f, juce::Font::bold));
    g.setColour(juce::Colour::fromRGB(106, 58, 79));
    g.drawText("SUZY//AI", 100, 356, 152, 24, juce::Justification::centred);
    g.setColour(mint);
    g.fillEllipse(249.0f, 355.0f, 11.0f, 11.0f);

    g.setColour(cream);
    g.setFont(juce::Font(12.0f, juce::Font::bold));
    const char* labels[] = {"BROWNING", "DESTRUCTION", "AI LIVE", "LOOP MIX", "MASTER"};
    for (int i = 0; i < 5; ++i)
        g.drawText(labels[i], 328 + i * 108, 137, 108, 22, juce::Justification::centred);
    g.drawText("TEMPO (MANUAL)", 349, 309, 153, 22, juce::Justification::left);
    g.drawText("BEATS/BAR", 525, 309, 132, 22, juce::Justification::left);
    g.drawText("LOOP LENGTH", 712, 309, 144, 22, juce::Justification::left);
    g.drawText("No model runs in this plugin. Google MRT2 stays in the preceding Logic instrument.",
               18, 515, 855, 18, juce::Justification::centred);
}

void SuzyToastAudioProcessorEditor::resized() {
    heading_.setBounds(25, 14, 460, 43);
    subtitle_.setBounds(29, 63, 775, 22);
    for (size_t i = 0; i < dials_.size(); ++i)
        dials_[i]->setBounds(329 + static_cast<int>(i) * 108, 174, 104, 110);

    bpm_.setBounds(345, 332, 175, 32);
    beats_.setBounds(521, 332, 155, 32);
    bars_.setBounds(714, 336, 128, 25);

    record_.setBounds(330, 381, 95, 35);
    overdub_.setBounds(430, 381, 106, 35);
    play_.setBounds(541, 381, 73, 35);
    stop_.setBounds(619, 381, 73, 35);
    clear_.setBounds(697, 381, 76, 35);
    space_.setBounds(777, 381, 82, 35);

    loopStatus_.setBounds(333, 435, 510, 29);
    caveat_.setBounds(23, 538, 844, 32);
    scenePyramid_.setBounds(28, 615, 222, 42);
    sceneEvolve_.setBounds(257, 615, 212, 42);
    sceneFishes_.setBounds(476, 615, 221, 42);
    previousCue_.setBounds(708, 615, 72, 42);
    nextCue_.setBounds(787, 615, 72, 42);
    sceneTitle_.setBounds(30, 663, 828, 25);
    chordCues_.setBounds(30, 688, 828, 26);
    sceneNotice_.setBounds(30, 715, 828, 20);
    sceneStyle_.setBounds(30, 738, 828, 26);
}
