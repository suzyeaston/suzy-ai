# SUZY//AI live control panel: Focusrite → Qwen → headphones

**New experimental rehearsal interface.** This adds a **real local graphical
control surface** for the existing Focusrite Scarlett microphone input and
local Qwen note composer. There is **no WAV export**, no browser mic recording
and no upload or cloud processing. The browser sends only controls to a
local Python audio process. Logic's playback remains independent.

**Important distinction:** This is *phrase-turn* interaction (sing for 4/8/12/16
beats, wait for the local model, then audition). It is not continuous streaming
inference, not DAW synchronized and not ready to be a required stage signal.
The audio is currently a basic synthesized note response, **not** R&B singing
or a Rhodes instrument. Real Mac/Focusrite operation must still be tested.

## Start in Terminal (Mac)

From the repository after merging the PR:

```bash
cd ~/Projects/suzy-ai
git pull --ff-only

# Already installed if you used the live probe:
.venv-mac/bin/python -m pip install -e ".[live]"

# Run Qwen using your existing SUZY//AI Mac startup path first.
# It must answer on http://127.0.0.1:7332/v1/chat.

.venv-mac/bin/python -m suzy_ai.music.stage_panel
```

Open **http://127.0.0.1:7344/** in a local browser on the same Mac.

### What the panel controls

1. **Audio input:** select **Scarlett Solo USB** (or your Focusrite name),
   then choose physical XLR input **1** (or channel 2 if intentionally used).
   The mic may travel through Boss VE-22 before the Scarlett. Dry vocal
   initially helps our approximate pitch extraction.
2. **Listening output:** select headphones/interface or Mac output. Press
   **Connect audio**, then **Test output** at LOW speaker/headphone volume.
   The test tone does not capture your microphone. If you don't hear it,
   switch output or check permissions. Use headphones to prevent feedback.
3. **Tempo / phrase:** enter the ACTUAL Logic BPM and choose 4/8/12/16
   beats for a legal 1.5-8-second capture. The 3-second countdown gives
   you time to put your hands back on the MIDI keys.
4. **Musical direction:** enter a brief instruction and optional known
   chord symbol. Enable the research checkbox to send up to two reviewed,
   attributed era cards to the localhost model. Disable it to test baseline.
5. **Capture my phrase:** record from Scarlett into preallocated RAM.
   An off-callback thread extracts approximate monophonic note events,
   calls Qwen and renders any validated generated notes as low-level PCM.
   The panel shows **the actual note event array** or an explicit failure.
6. **Hear AI answer:** the AI phrase is played 2x to the chosen listening
   output. The Qwen answer cannot alter original Logic music.
7. **STOP AI:** immediately silence AI playback, abort any capture and
   invalidate late inference output. Logic continues independently.
   Esc is STOP, Space is Capture when the focus is not in a text field.

The panel displays capture progress, selected mic peak (after capture),
model inference time, note count, actual output pitches/velocity and research
card IDs. Reference ID acceptance proves only a cited card reached the
model; it does not prove musical understanding.

## Sound routing for this first version

```
Your voice → (VE-22 optional) → Focusrite Scarlett input 1
                              → local stage_panel Python capture
                              → approximate pitch notes
                              → Qwen3 1.7B on localhost:7332
                              → validated new MIDI note events
                              → low-gain synthesized AI response
                              → selected headphone/audio output

Your Logic Pro beats + synths ------------------------------------> Logic audio output
```

**Not connected yet:** Logic's internal stereo audio bus, drum onset
classification, MIDI clock, IAC/CoreMIDI instrument track, song key detection,
multivoice R&B harmony, vocal synthesis, beat-aligned AI scheduling.
The audio capture measures your **selected mic channel only**.
If the beat is audible in the room it can contaminate vocal pitch extraction.

### Devices and interference

- macOS may ask for **Terminal microphone access**. Grant only if intended.
- Scarlett Solo physical mic is usually input **1**. The device can expose
  multiple input channels with one silent channel.
- 48 kHz and stereo output are required for this proof of concept.
- Some pairs of independent CoreAudio input/output devices cannot open
  a single duplex stream. If your chosen pair fails, first try Scarlett
  input + Scarlett headphone output; leave Logic routing unchanged.
- If both Logic and our panel own the same device, CoreAudio behavior may
  differ depending on interface/driver. Inspect audio settings and avoid
  routing AI output back into its own microphone.
- This is a low-complexity Python PortAudio callback, NOT hard realtime.
  UI processing, inference and musical rendering happen elsewhere, but
  some Python buffer copies remain in the callback. It is safe as an
  experimental tool, not guaranteed glitch-free at a live event.

## Security and privacy

The local panel listens only on **127.0.0.1:7344**, serves one static HTML
file, sends audio neither to browser nor to disk, and uses an in-memory
random token and browser-origin checks on API writes. Qwen and research
remain local. The port is configurable via `--port`; close with Ctrl-C.

## Hardware-free QA

```bash
.venv-mac/bin/python -m unittest discover -s tests -p 'test_stage_panel.py' -v
```

The tests use a fake PortAudio stream and fake Qwen, verifying capture,
response notes, preview output, selected mic channel, STOP during a late
model call and local API request protection. These are not a proof of
audible operation on Suzy's Scarlett, nor a groove-quality result.

## Next PRs (after hardware check)

1. Add **true Logic beat/MIDI input** via a safe loopback or CoreMIDI/IAC
   bridge. Make the model aware of actual drum/bass/chord context, not just
   BPM + optional chord.
2. Add a **Logic instrument-track AI MIDI audition** rather than a sine
   waveform. A note from Qwen should sound like a part in the song.
3. Add musical-bar quantized scheduling, phrase buffering and optional
   repeating responses, bounded by an immediate hard mute.
4. Introduce rehearsed original examples/feedback from Suzy; compare
   responses from informed versus uninformed Qwen, *on the same material*.

Don't train on unlicensed Nas, Badu or Rascalz recordings. Historical
knowledge is separate from actual human-approved musical examples.
