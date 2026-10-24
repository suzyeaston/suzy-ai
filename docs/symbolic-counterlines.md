# Symbolic counterlines: original note answers (experimental)

PR #31 extracts approximate monophonic note events from an already-captured phrase. This optional module uses those observed events to **compose a distinct answering line**, with a staggered entrance, contrary/oblique motion, optional sparse density, register control, and rests. The new pitches are derived from the singer's intervals; they are **not** a preselected four-note pattern, delayed copy, or neural-audio output.

This is a deterministic, small musical grammar, **not** Qwen-based improvisation, a trained music model, or chord/key recognition. The simple synthesized sound is strictly an offline audition tool. The native looper, Python live probe, Logic integration, Qwen prompting and onstage routing are untouched.

## Hearing the experiment

From the project root after pulling/checkout of this PR's branch:

```bash
python3 -m unittest discover -s tests -p 'test_counterline.py' -v
python3 -m suzy_ai.music.counterline --demo-wav counterline-demo.wav
```

The WAV contains a quiet stereo synthesized four-second answer to a **manually specified, synthetic** four-note source. It does not use the microphone or your recorded voice; you can import it into Logic to judge contour and phrasing. The file is only written when `--demo-wav` is explicitly provided.

Use the actual optional phrase observations with:

```python
from suzy_ai.music.phrase import extract_phrase
from suzy_ai.music.counterline import compose_counterline, audition_wav

phrase = extract_phrase(captured_pcm16, rate=48000, channels=1, bpm=120)
answer = compose_counterline(
    phrase, register="above", density="sparse", motion="contrary",
    harmony={"root_pc": 0, "quality": "major"},  # explicit C major, NOT inferred
)
if answer["status"] == "composed":
    wav_bytes = audition_wav(answer)
    # Write to a file only if you explicitly choose to audition it.
```

With no supplied harmony, the composer preserves contour relationships but does **not** guarantee consonance against live chords. If the melody is absent, insufficiently confident, or invalid, it returns no note events or raises a clear validation error. No silent fallback to a fabricated melody.

Controls:
- `register="above"|"below"`: approximate second-voice register.
- `density="full"|"sparse"`: play all eligible source-derived answers or alternate notes.
- `motion="contrary"|"oblique"`: move against source melodic intervals or hold a pitch.
- `harmony={"root_pc":0..11,"quality":"major"|"minor"}`: optional musician-supplied chord tones.

Boundaries: at most twelve output note events, MIDI notes 48–84, low synth gain, finite 8-second 44.1/48 kHz WAVs, no dependencies, no external calls, no private memory access, and no MIDI/Audio callback operations.

## Known limitations and next PR

The phrase tracker is still an experimental post-capture estimator: vocal effects, vibrato, noise, harmonies and quick transitions can misidentify notes. The counterline generator is intentionally rule-based and simple. Chord quality currently supports major and minor only, with no progressions or voice-leading optimization. `oblique` holds one pitch and `contrary` mirrors detected interval changes in a bounded register. The resulting counterline still needs human musical listening and arrangement decisions.

Next: model-guided **musical intention** (rather than fixed FX menus) and safe MIDI/CoreMIDI or IAC transport into a dedicated Logic instrument track. Do not turn these on in the October 29 set without timing and failure tests on the actual 8 GB Mac. A model timeout must never interrupt the existing music.
