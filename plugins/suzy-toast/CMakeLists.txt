cmake_minimum_required(VERSION 3.22)
project(SuzyToast VERSION 0.2.0 LANGUAGES C CXX)

# Pin a JUCE security-patch tag; no fork and no vendored proprietary assets.
# The JUCE licence choice (GPLv3 / commercial) must be resolved before distribution.
include(FetchContent)
FetchContent_Declare(
  JUCE
  GIT_REPOSITORY https://github.com/juce-framework/JUCE.git
  GIT_TAG 8.0.16-security
  GIT_SHALLOW TRUE
)
FetchContent_MakeAvailable(JUCE)

if(NOT APPLE)
  message(FATAL_ERROR "The AU build is macOS-only. LoopBuffer tests run on other systems.")
endif()

juce_add_plugin(SuzyToast
  COMPANY_NAME "Suzy Easton"
  BUNDLE_ID "ca.suzyeaston.suzytoast"
  PLUGIN_MANUFACTURER_CODE Szye
  PLUGIN_CODE St01
  PRODUCT_NAME "SUZY Toast"
  DESCRIPTION "Lightweight audio-effects and audio-loop companion for live neural instruments"
  FORMATS AU
  IS_SYNTH FALSE
  NEEDS_MIDI_INPUT FALSE
  NEEDS_MIDI_OUTPUT FALSE
  IS_MIDI_EFFECT FALSE
  EDITOR_WANTS_KEYBOARD_FOCUS FALSE
  COPY_PLUGIN_AFTER_BUILD TRUE
)

juce_generate_juce_header(SuzyToast)
target_compile_features(SuzyToast PRIVATE cxx_std_17)
target_sources(SuzyToast PRIVATE
  Source/PluginProcessor.h
  Source/PluginProcessor.cpp
  Source/PluginEditor.h
  Source/PluginEditor.cpp
  Source/LoopBuffer.h
)
target_compile_definitions(SuzyToast PUBLIC
  JUCE_WEB_BROWSER=0
  JUCE_USE_CURL=0
  JUCE_VST3_CAN_REPLACE_VST2=0
)
target_link_libraries(SuzyToast PRIVATE
  juce::juce_audio_utils
  juce::juce_audio_processors
  juce::juce_gui_extra
  PUBLIC
  juce::juce_recommended_config_flags
  juce::juce_recommended_warning_flags
)
