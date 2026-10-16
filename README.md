# SUZY//AI

**A local musical collaborator. You keep playing; AI works in the background.**

SUZY//AI is an open-source project by [Suzy Easton](https://www.suzyeaston.ca/),
built around live music, memory, cultural references and creative interaction.
The current focus is **EVOLVE WITH ME**: performing with prepared loops, live
nylon-string guitar and layered vocals while AI develops variations of the
musician's own sounds.

This work is being developed for **The Appliance Latent Space**, a 15-minute
performance at Futureproof Festival in Vancouver on October 29, 2026.
Logic Pro handles the prepared Live Loops backing, beats and instruments. The
native Mac companion adds an experimental local looper and optional background
responses from SUZY//AI.

> The technology was always meant to serve the art, not the other way around.

## Play first. Let AI evolve alongside you.

1. **Record and loop your own phrase.** Original playback starts locally without
   waiting for a model or server.
2. **Keep playing.** Overdub, undo the last overdub, mute, stop, resume and save
   your loop using the app or a MIDI controller.
3. **Let AI work on a copy.** When enabled and connected, the background response
   service receives a snapshot of the loop. Your original keeps playing.
4. **Choose what enters the performance.** Audition a variation or add it as a
   separate layer at the next original-loop boundary. Ignoring it changes nothing.

The local looper remains usable with the AI bridge disconnected. Changing the
original invalidates stale proposals. A slow or failed AI request does not need
to interrupt recording or playback.

Audio is the musical material: the Godin guitar and microphone feed the audio
interface. MIDI is optional for controller actions and experimental clock sync;
it is not required to capture or transform the sound.

## What is implemented

| Component | Current capabilities |
| --- | --- |
| **Mac looper** | One loop up to eight seconds, one-cycle overdubs, one-level undo, mute, stop/resume, clear and WAV saving |
| **Background responses** | One bounded capture/proposal at a time, optional local-model decisions, audition, discard and an optional response layer |
| **Musical analysis and context** | Onset estimates, uncertain monophonic pitch hints, section/key/direction inputs and the last four accepted decisions in RAM |
| **Performance controls** | MIDI note mappings, local Stop All and experimental Logic/IAC clock scheduling |
| **Local AI core** | Text inference, explicitly approved private memory, bounded recall, teaching APIs, JSON events and timelines |

The response modes are **MIRROR**, **AUGMENT** and **EVOLVE**. Today they operate
on the source audio through slice order, gain, reversal and a delayed layer.
Deterministic mode uses fixed processing rules. Local-model mode uses neural text
inference to choose a validated arrangement from measured features and musical
context; rendering still uses deterministic audio processing. The model does not
hear the waveform directly, generate neural audio or synthesize inferred harmonies.

**This is an experimental instrument.** The first repeat can have a recording
finalization/startup gap, and an overdub can take another cycle to enter. Timing
is not yet sample-accurate, and there is no continuous drift correction or input/output
latency compensation. Audition shares the audience output; there is no private
cue bus. The companion runs alongside Logic and does not yet provide an Audio Unit
or insert Live Loops cells automatically.

See the [local looper guide](docs/local-looper.md) for controls and listening tests,
the [Mac companion guide](docs/mac-companion.md) for routing and clock setup, and
the [response protocol](docs/live-response.md) for the backend.

## Run on a Mac

The companion requires macOS 13+ and Xcode Command Line Tools with Swift 5.9+.
The response bridge also requires Python 3.11+. Start with local looping:

```bash
git clone https://github.com/suzyeaston/suzy-ai.git
cd suzy-ai
bash scripts/start-mac-companion.sh --looper-only
```

This builds and opens the native app without starting Python or downloading a
model. Select your interface as the macOS sound input/output; Logic has its own
audio settings. Begin with headphones and verify the input channel.

For the companion plus the background response bridge, quit the app and run:

```bash
bash scripts/start-mac-companion.sh
```

The bridge uses port **7333**. In the app, Connect and choose deterministic DSP or
local-model decisions. Deterministic responses require no model. For model mode,
start the existing SUZY//AI core in another terminal on **7332**:

```bash
bash scripts/start-mac.sh --api-port 7332 --model-port 8082
```

The local inference setup uses Qwen3 1.7B through llama.cpp. If you have not set
it up before, follow [Mac setup](docs/mac-setup.md); `scripts/setup-mac.sh` installs
tools and downloads the model. Existing installations can reuse their verified
weights. The companion launcher does not download or start a model itself.

To update an existing checkout, quit the app and old services, then run
`git pull --ff-only` and relaunch. A running process does not pick up new code.
If you are in the core's `you >` chat prompt, use `/quit` before running shell commands.

For the Python core alone, install with `pip install -e .` in a virtual environment,
then use `suzy-ai init`, `suzy-ai doctor` and `suzy-ai serve`. Its default API port is
7331; the musical setup above uses 7332. See the [chat and memory API guide](docs/local-chat.md).

## How the projects fit together

| Project | Role |
| --- | --- |
| **SUZY//AI — this repository** | Local AI core, memory, music-response service and native Mac looper |
| **[The Appliance Latent Space](https://github.com/suzyeaston/appliance-latent-space-live)** | Browser instrument with sequencing, synthesis, scenes, deterministic variations and visuals |
| **[POP//CONTEXT](https://github.com/suzyeaston/pop-context)** | Audiovisual input pipeline with media windows, transcripts, frames and timestamps |
| **[SUZY//WORLD](https://github.com/suzyeaston/suzy-world)** | Published album reviews and structured cultural knowledge |
| **[suzyeaston.ca](https://www.suzyeaston.ca/)** | Public creative lab and music experiments |

These projects share a creative direction, but they are not a fully integrated
system. The Mac looper and response service live here. Connecting the browser
instrument, approved audiovisual observations and cultural knowledge to the live
workflow remains development work. The [app registry](config/apps.json) records
the related repositories; `scripts/sync-apps.sh` manages sibling checkouts.

## Musical taste, memory and humour

The wider project explores how album reviews, musical ideas, listening observations,
wordplay and cultural associations can inform a creative collaborator. Suzy's
threads are part of that collection: music knowledge with a sense of humour.

Saved examples can be retrieved into local conversations. They do not change model
weights or automatically establish a learned musical style. Live response planning
currently uses its own small musical session history, with personal-memory recall
disabled. Bringing the broader collection into musical decisions is future work.

### From the thread collection: Mormon music

> **What do you think about Mormon music?**
>
> 1. I'm partial to the The Joseph Smiths... The Mormonissey years, at least.
> 2. the (latter day) Saints
> 3. Detroit Salt City
> 4. Better Than Ezra...Just Ask Him
> 5. Mennonite At Work
> 6. Mission of Burma

A musical-wordplay thread created by Suzy.

### From the thread collection: best music to take a crap to?

> **best music to take a crap to?**
>
> 1. duh- the brown tone
>    - de-bunked on mythbusters
>      - baby got back
> 2. The House at Pooh Corner
> 3. sunn O ))) only if they are playing in the room
> 4. Big Bottom by Spinal Tap
> 5. Buzzcocks- Oh Shit
> 6. Coil: Scatology ( whole album )
> 7. The Pooh Sticks
> 8. Bathtub shitter
> 9. World of Pooh
> 10. The Fartz ( well almost )
> 11. U2- stuck in a moment you can't get out of
> 12. Stones- Can't always get what you want
> 13. Carly Simon- Anticipation
> 14. Kinks- So tired ( tired of waiting for yoooouuu)
>     - +4 for imagination, creativity, and refraining
> 15. salt n pepa- push it
> 16. Clash- Cut the crap
>     - There is NEVER a reason to listen to that
> 17. one more, got go to the bathroom now
> 18. "I Can't Get Behind That"
> 19. Every Impaled album except the new one.
> 20. screamin' jay hawkins - constipation blues
> 21. Whoomp, There It Is!
> 22. Supersuckers - She's my Bitch
> 23. This belongs in the Kink forum.
>     - Freud would have a lot to say about you then
> 24. Snoop Dogg "Drop It Like It's Hot"

A thread created by Suzy, March 2005.

More threads, album reviews and musical examples will join the collection as the
project develops.

## Local data

Approved memory and world state are stored locally under `~/.suzy-ai/` by default.
The public examples are separate from that private store and are not automatically
ingested by a fresh clone. Chat history and musical session context stay in process.

Loop audio is held in memory, with private temporary files used during recording.
Use the save controls to keep a WAV; unsaved loops are lost on exit. Model weights
are managed separately from the public source code.

## Next priorities

1. Rehearse with real guitar and vocals; measure the first-repeat gap, overdub
   alignment and sustained timing alongside Logic.
2. Improve seamless looping and latency compensation while keeping AI off the
   critical playback path.
3. Evaluate whether MIRROR, AUGMENT and EVOLVE produce useful musical responses.
4. Develop richer musical transformations and connect the wider collection and
   audiovisual tools where they serve the performance.

Development targets include an M2 MacBook Pro with 8 GB unified memory, so audio
buffers, session history and concurrent work are bounded. Actual CPU load and
memory pressure still need testing with Logic and the model running together.

## Development

Python core and backend tests:

```bash
bash scripts/test.sh
```

Native companion tests and local app build, on macOS:

```bash
(cd apps/macos && swift test)
bash scripts/build-mac-companion.sh
```

CI covers Linux and macOS. Automated tests use synthetic audio and model services;
passing them does not establish musical quality or performance-ready hardware timing.

Further reading: [architecture](docs/architecture.md), [world-model storage](docs/world-model.md),
[teaching surfaces](docs/teaching-surfaces.md) and [build notes](docs/build-in-public/).

Code is licensed under [Apache-2.0](LICENSE).
