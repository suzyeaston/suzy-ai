# SUZY//AI: Logic + MRT2 Small studio proof

Date: 2026-10-25. **This is a test plan, not a claim that the show Mac has passed.**

## Critical distinction: MIDI response is NOT audible AI confirmation

On October 25 the SUZY MIDI page displayed **Keystation Mini 32 MK3** with 14 incoming note events, but the musician could not hear AI audio. That means the **Keystation → SUZY** half works, *not* that **SUZY virtual MIDI → Jam/Logic → Scarlett audio** works. The browser process creates no audio stream.

### Find the missing link in standalone Jam

1. Leave SUZY running at `http://127.0.0.1:7345/`. In Magenta **MRT2 - Jam**, change the bottom **MIDI INPUT** from `Keystation Mini 32 MK3` to `SUZY AI MIDI`. If absent, reopen Jam with the bridge running.
2. Select **Jam**, press the top-right Play control, begin at low volume, and play Keystation notes or the SUZY test chord.
3. If still silent, temporarily select the physical Keystation as Jam input again. If that works, focus on virtual MIDI source selection. If not, focus on Jam transport/volume, headphones and macOS output/sample-rate settings.
4. The standalone Jam app owns its own audio output. **SUZY cannot select that audio device** merely by listing macOS devices. Set the intended macOS default output in System Settings → Sound / Audio MIDI Setup and verify **48,000 Hz**. The separately built MRT2 standalone has Settings for explicit output-device selection; don't assume Jam has an equivalent control.
5. An increased SUZY note counter does not verify Magenta audio. Document what actually comes out of the headphones.

### Move to actual Logic performance

- Close the standalone Jam test to reduce competing audio/memory use before running Logic on the 8 GB Mac.
- Put `MRT2 (AU).app` in `/Applications` **before its first launch**; open it once to register. Restart or rescan Logic if the AU isn't listed.
- Logic Pro → **Settings → Audio → Devices**: select Scarlett as both input and output, with headphones connected to Scarlett. Ensure the Logic **project** and audio device are **48 kHz**.
- Add a **software instrument** track, insert the Google/MRT2 AU, and verify it plays **first with the physical Keystation**. Only then reintroduce SUZY virtual MIDI steering, checking Logic's source/channel selection to prevent duplicate note paths.
- Add a **separate audio vocal track** fed by BOSS VE-22 → Scarlett microphone input. Audio input monitoring is enabled on the *vocal track* (or via Scarlett Direct Monitor if supported); avoid doubled monitoring.
- **Actual audible mute** is the Logic AI track mute. Test it while vocals and backing keep playing. Save and re-open a printed AI audio region before claiming the take was recorded.

The **Audio + Logic setup** section in SUZY discovers Scarlett and system device candidates without opening streams. It cannot inspect or set Logic track monitoring, DAW device selection, plugin validation or audio output. Those are manual host actions until a verified integration exists.

## Independent signal paths

- Dynamic mic → BOSS VE-22 → Scarlett Solo → Logic vocal track.
- Keystation → Logic software instrument track `AI - MRT2 SMALL` → Magenta RealTime 2 Small AUv3 → dedicated, independently mutable Logic audio channel.
- Prepared beats and synths remain in Logic. No Qwen/Python/browser dependency sits between the human music and house speakers.

Sources: [Official MRT2 apps](https://magenta.withgoogle.com/mrt2), [AUv3 install instructions](https://github.com/magenta/magenta-realtime/blob/main/examples/mrt2/auv3/INSTALL.md), [Logic Bounce in Place](https://support.apple.com/en-ca/guide/logicpro/lgcpe2a9f868/mac).

## First practical proof on the actual 8 GB Apple Silicon Mac

1. Duplicate your current Logic project. Confirm the new project and Scarlett run at **48,000 Hz**. Keep the original prepared set independent and recoverable.
2. While connected to the internet, download the official MRT2 bundle and **mrt2_small** (230M) assets. Finish the model download before attempting the offline rehearsal. Avoid 2.4B Base on this show machine.
3. With Logic and Qwen stopped, open Magenta Jam or the official MRT2 standalone, select the Keystation, and test chords, silence and single-note variations. Is the sound demonstrably new, continuous neural audio? The separately built MRT2 standalone exposes `Magenta RT Input`; **do not assume Jam has that virtual port**.
4. Install the **official** MRT2 AU host app in its permanent Applications location and launch once for AU registration. Restart/rescan Logic if required. On a NEW Logic software instrument track choose the Google/MRT2 AU; keep the level very low initially.
5. Play Keystation notes with one of your own original beats. Verify the sounds are coming from MRT2, not a hidden conventional Logic synthesizer. Check rests and melodic changes.
6. Physically mute the Logic AI track. AI output must disappear while prepared backing, VE-22 vocal and headphones carry on. MIDI All Notes Off is not enough to guarantee silence from a streaming audio synthesizer.
7. Record a short human vocal take **and** the Keystation MIDI region in Logic. Confirm they survive Stop/Play.
8. Try Logic **Bounce in Place** for the AI software-instrument region to a new audio track called `AI - COMMIT`. Disable the original AI instrument and *listen to the result*. Neural generators may behave differently under offline bounce, so neither a visible bounce command nor a WAV filename proves the recorded sound is correct. If bounce fails, first engineer a tested real-time bus print inside Logic.
9. Save, quit, reopen, and audibly verify the recorded vocal plus the committed AI track.
10. Disable Wi-Fi and cold-open the set. Run the complete 15-minute show with one intentional AI mute/recovery and observe audio dropouts, CPU/memory pressure and recoverability.

### Acceptance checklist

- [ ] Small model audibly generates on the show Mac
- [ ] Logic and Scarlett at 48 kHz
- [ ] AI isolated to a muteable track; backing/vocal unaffected by AI failure
- [ ] Vocal and MIDI recording confirmed
- [ ] AI audio committed to a durable, *audible* audio region
- [ ] Save, reopen, and playback confirmed
- [ ] Offline cold-start passed
- [ ] 15-minute rehearsal passed
- [ ] Logic-only fallback rehearsed

## Local read-only diagnostics

```sh
python -m suzy_ai.music.studio_doctor
python -m suzy_ai.music.studio_doctor --json
```

Optional hardware enumeration dependencies are installed with `pip install -e '.[live-midi]'`. Missing optional packages produce CHECK status, not false confidence. The checker inspects OS, audio/MIDI device names, registered AU extensions and probable llama.cpp processes. It never changes CoreAudio settings, starts/stops processes, touches Logic, or marks the performance ready.

## SUZY//AI performance UI contract after the Mac proof

The current browser panel is **Legacy Qwen Audition**, not an MRT2 or Logic controller. It must not display “AI RECORDED” or “LOGIC RECORDING” based on in-memory mic capture. Incorporate PR #43's honest “LISTEN TO PHRASE” wording in the later UI refactor.

- **SPACE:** musician-driven real audio silence or an explicitly proven entry gate. A text prompt asking Qwen to pause isn't enough.
- **ANSWER:** a deliberate musician-triggered cue for a response after a vocal phrase, optionally quantized when Logic synchronization is actually proven. Do not claim continuous mic/beat listening.
- **TEXTURE:** steer the model with available MIDI conditioning and approved own-material style prompts, with independent gain/mute.
- **STOP AI:** must cause an observable AI-channel *audio mute*. Until native/DAW integration has been physically verified, the authoritative control is the Logic track mute, not the browser button or a MIDI panic event.

Show view: large mode selection, readable human/AI status, obvious mute, no prompt typing. Setup/Diagnostics view: sound devices, AU registration, sample rate, proof checkboxes and error details. No decorative “connected” indicator should masquerade as a verified recording or house-audio route.
