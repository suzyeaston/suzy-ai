# SUZY//AI → Magenta: first playable MIDI control path

**Experimental physical QA required.** On October 25 the performer confirmed `mrt2_small` in **MRT2 - Jam** responded to the Keystation Mini 32 MK3 when the keyboard was selected directly. This PR preserves that known-good fallback and adds a separate virtual-MIDI bridge/UI. It has not yet been heard or tested with the real Mac device.

## What you get (and what you don't)

```text
Keystation Mini 32 MK3  ─USB MIDI─► SUZY//AI MIDI bridge (local Python)
                                        │
                                  DIRECT / DOWN / UP
                                  PAUSE / RELEASE
                                        │ virtual CoreMIDI source
                                        ▼
                                  "SUZY AI MIDI"
                                        │ select as Jam MIDI INPUT
                                        ▼
                           MRT2 - Jam  /  mrt2_small
                                        │
                                  generated AUDIO
```

SUZY//AI does **NOT** process MIDI in Qwen or generate the sound. Magenta stays open separately and produces neural audio. The bridge doesn't capture the microphone, intercept the Logic backing, record any audio, control Magenta's text/style/chaos/volume, or confirm the virtual source is selected in Jam. A MIDI-only release/pause cannot guarantee Magenta audio silence.

## Mac setup, step by step

1. **Keep a known-good baseline.** In Jam, choose the physical `Keystation Mini 32 MK3` and verify you can still hear a chord. Stop Jam playback and turn its volume down before rerouting.
2. With this PR checked out and the repo's Python environment active, install the existing optional dependency set once:
   ```sh
   cd ~/Projects/suzy-ai
   .venv-mac/bin/python -m pip install -e '.[live-midi]'
   ```
   This does not download any model and does not start Qwen or Logic.
3. In another terminal, start the **independent** MIDI panel:
   ```sh
   .venv-mac/bin/python -m suzy_ai.music.magenta_stage
   ```
   Open the printed local address: **http://127.0.0.1:7345/**.
4. Open **MIDI setup** on SUZY//AI, choose the *exact* `Keystation Mini 32 MK3`, and click **Connect**.
5. In Jam, switch the bottom **MIDI INPUT** away from `Keystation Mini 32 MK3` to **SUZY AI MIDI**. This is a virtual **source** created by the SUZY bridge. If Jam doesn't list it, relaunch Jam **after** starting the bridge, check Audio MIDI Setup, or close/reopen Jam's input menu. Do not assume the Magenta standalone's separately named `Magenta RT Input` is available in Jam.
6. Select **Jam** mode, lower the volume, press Play and click **TEST CHORD** in SUZY//AI. Listen for an actual change in the model's generated sound.
7. Play your Keystation while switching **DIRECT**, **OCTAVE DOWN**, **OCTAVE UP**. Notice how the conditioning notes change. **PAUSE MIDI** releases existing notes and ignores new ones until **RESUME MIDI**; Magenta audio may keep generating.
8. Press **RELEASE MIDI** and verify the keyboard-driven notes release. **Use Jam's own playback/volume for actual audio stop**, never confuse MIDI RELEASE with an emergency stage audio kill.

Keep the SUZY terminal running. Closing only the browser does not stop the bridge. `Ctrl-C` in the terminal releases tracked MIDI notes, sends channel panic events, and removes the virtual port.

## User-facing controls

| UI | Actual result |
|---|---|
| DIRECT | Physical MIDI notes forwarded unchanged |
| OCTAVE DOWN / UP | Physical notes shifted by -/+ 12 semitones |
| PAUSE MIDI | Release tracked notes and block further Note On until RESUME |
| TEST CHORD | 800 ms original Am7 MIDI test notes, automatically released |
| RELEASE MIDI | Send note-offs, sustain off, All Notes Off and All Sound Off on 16 MIDI channels |
| CONNECT / DISCONNECT | Start/stop only Keystation input receiving |

Keyboard shortcuts: Shift+1/2/3 (down/direct/up), Shift+G (pause/resume), Esc (release). Bare Space/Enter are intentionally not captured globally.

## Audition QA scorecard

- [ ] SUZY AI MIDI **appears** in Jam's MIDI INPUT menu with bridge running
- [ ] Direct physical Keystation no longer selected in Jam: only SUZY input is selected
- [ ] SUZY **TEST CHORD** produces audible Magenta reaction
- [ ] Held note + mode change releases prior pitch before sending a new note
- [ ] Direct/down/up sound meaningfully different on the same keyboard phrase
- [ ] Pause MIDI suppresses new MIDI but does not claim to mute continuous audio
- [ ] Browser closed / reopened retains bridge without blocking MIDI
- [ ] Keyboard unplug/replug and a new Connect restore routing safely
- [ ] Exit bridge, return Jam to direct Keystation; original sound still works
- [ ] CPU/memory remain acceptable on the 8 GB Mac

Run no-hardware tests:
```sh
.venv-mac/bin/python -m unittest tests.test_magenta_midi tests.test_magenta_stage
```

## Next PRs: sound control is not MIDI control

- [#46](https://github.com/suzyeaston/suzy-ai/issues/46) Host MRT2 Small AUv3 on its own **Logic** instrument track. Verify actual 48kHz audio, separate recording/commit, offline recovery.
- [#47](https://github.com/suzyeaston/suzy-ai/issues/47) Real **AI audio mute** in Logic, from tested host control (not a fake "STOP AI" button).
- [#50](https://github.com/suzyeaston/suzy-ai/issues/50) After we have a reproducible MIDI→MRT2 passage, replace simple octave steering with meaningful, **audible** SPACE/ANSWER/TEXTURE behaviours using controlled timing and artist approval.
- [#51](https://github.com/suzyeaston/suzy-ai/issues/51) Unify the legacy Qwen audition and Magenta control entrypoints only when audio/engine status can be stated truthfully.

If this experimental MIDI adapter fails, quit its terminal and switch Jam MIDI INPUT back to Keystation. No DAW project, preset or recorded file needs changing.

Sources: [python-rtmidi virtual ports](https://spotlightkid.github.io/python-rtmidi/classes.html), [Magenta apps](https://magenta.withgoogle.com/mrt2), [Magenta standalone MIDI port (different app)](https://github.com/magenta/magenta-realtime/blob/main/docs/apps/standalone_app.md).
