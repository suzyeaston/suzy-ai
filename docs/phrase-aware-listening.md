# Experimental phrase-aware listening (offline / post-capture)

`suzy_ai.music.phrase.extract_phrase(pcm, rate, channels, bpm)` accepts up to eight seconds of **interleaved little-endian PCM16**. It returns bounded, approximate monophonic note events, rests, relative beat positions, intervals, contour and confidence. Tempo is supplied by Logic/the performer; the code does **not** infer a key, chords, genre, lyrics or reliable polyphonic transcription. It does not access private memory or invoke Qwen.

```python
from suzy_ai.music.phrase import extract_phrase
phrase = extract_phrase(captured_pcm16, rate=48000, channels=2, bpm=120)
print(phrase['notes'], phrase['intervals'], phrase['contour'])
```

This is an **optional research API**, not inserted into `audio.describe`, `LiveSession`, the native looper, or a Core Audio callback. The existing `pitch_hints` and note/vocal replies remain unchanged. Both 44.1 and 48 kHz are supported; a one-sided Scarlett microphone avoids dilution by the silent second channel.

The implementation uses no third-party packages. It runs windowed normalized autocorrelation only *after* capture, and may confuse harmonics, vibrato, low-level breath noise, effects, polyphonic audio, or rapid notes. Timestamps have window-level uncertainty. Results include `status: unvoiced` instead of inventing melody when pitch cannot be estimated. Limitations, audible usefulness, and CPU use require actual Mac/Logic/VE-22 tests before real-time integration.

Run the synthetic offline tests with:

```bash
python3 -m unittest discover -s tests -p 'test_phrase.py' -v
```

Next research step: a symbolic counterline generator consuming the note-event schema. No automatic performance playback or AI model decision is introduced by this PR.
