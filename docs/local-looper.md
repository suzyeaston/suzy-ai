# Local looper with optional background AI

The original performance loop now belongs to a native `LocalLooper`, independent
of the Python bridge and model. Start the app, leave AI disconnected or disabled,
and use Record, Overdub, Undo, Mute, Play, Stop and Clear. Logic continues its
prepared Live Loops backing. No file export/import is required during playing.

## Playing

- Record captures the selected dry input, up to the configured maximum (8 seconds).
  Press again to finish in free mode. The captured phrase starts repeating locally
  before the AI snapshot callback runs. A short file-finalization/playback-start gap
  remains: this is not yet a sample-accurate, gapless pedal looper.
- Overdub schedules one complete cycle against the original player's phase. Existing
  playback continues while the dry input is captured. The take is mixed into the
  original and queued for a later loop boundary. There can be one extra cycle before
  the completed overdub becomes audible. Monitor the live input through Logic or the
  interface; do not route the looper's output back into its own input.
- Undo removes the last committed overdub, at a loop boundary if playing. Only one
  undo is kept. Mute changes output level without resetting the loop's phase.
- Stop silences local and AI playback immediately, before HTTP cleanup. Original audio
  remains available for Play or Save original. Play resumes with free timing; Clear
  removes the loop and undo. A cancelled/failed overdub preserves the original.
- Save original preserves the current local mix; Save AI WAV preserves the optional
  response. Unsaved loops and the undo buffer are lost when the app exits.

Local looping keeps at most the current mix, one undo and a bounded take/pending mix.
Each is at most eight seconds, mono/stereo PCM16 at 48 kHz. More overdubs do not add
unbounded tracks. Summing saturates at PCM16 limits; leave input headroom and listen
for clipping. This is one loop with overdubs, not a bank of independently editable tracks.

## Background AI

Enable AI, Connect the bridge, and select deterministic DSP or local model decisions.
After a committed recording, overdub or undo, an immutable WAV snapshot is offered to
AI. The original loop keeps playing and all local controls remain available. The AI
state is displayed separately. Background AI off means no new inference request.

Only one proposal is active. Changing/clearing the local loop invalidates old results
and stops any previous AI layer, without stopping the original. The worker is not
forcibly killed; if it is still occupied, the new proposal can fail visibly instead
of accumulating queued jobs. Press Request variation after it becomes available.
No automatic AI fallback is relabelled as a model result.

Add AI layer schedules the selected variation at the next original-loop boundary.
It adds a separately controlled layer; it does not overwrite the original or its undo.
Ignoring a ready proposal has no effect on the original loop. Audition remains shared
with the audience output and requires acknowledgment; there is no private cue bus.

## Controller mapping

| Note (channel 16 by default) | Action |
| --- | --- |
| 36 | Record / finish original |
| 37 | Audition AI on shared output |
| 38 | Add AI layer |
| 39 | Stop all |
| 40 | Discard AI candidate |
| 41 | One-cycle overdub |
| 42 | Undo last overdub |
| 43 | Mute/unmute original |
| 44 | Clear original and invalidate AI |
| 45 | Play stopped original |

Letter shortcuts are removed to avoid interfering with musical direction fields.
Escape remains Stop All. Mouse controls and MIDI work without a bridge connection.

## Timing and QA gate

The existing experimental Logic/IAC clock option can schedule the first recording;
beat lengths and transport handling remain available. However, AVAudioRecorder file
finalization and AVAudioPlayer startup add an unmeasured gap before the first repeat.
Subsequent overdubs and AI entries follow the actual original-loop phase, not a claim
of sample-accurate Logic synchronization. There is no input/output latency compensation
or continuous drift correction. Replacements stop the old player on a 10 ms UI timer,
so overlap can be longer if the UI stalls. Hardware listening QA is mandatory.

1. **No bridge/model:** record, loop, overdub twice, undo, mute/unmute, stop/play, save.
2. **Slow/offline AI:** repeat all local controls while a request stalls or fails.
3. **Stale result:** change or clear the source while AI works; no old response may play.
4. **Failure:** deny mic access or stop mid-overdub; existing audio/undo must survive.
5. **Timing:** record a click/guitar phrase against Logic, measure first-repeat gap,
   overdub alignment and 15-minute drift. Test at performance tempo with Focusrite.
6. **Levels:** repeated overdubs and original+AI layers must not clip the final mix.

If timing is not musically acceptable, keep Logic's own recording/loop playback as
the stage looper while improving the native audio engine. Passing CI does not establish
pedal-quality timing. Do not merge automatically or describe this as hardware-tested.
