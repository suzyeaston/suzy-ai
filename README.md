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
original invalidates stale proposals while accepted AI layers keep playing. A slow or failed AI request does not need
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

**This is an experimental instrument.** Original-loop capture, repeat, overdub and
undo now run in a continuous CoreAudio callback with timestamp-based overdub alignment.
It requires the same stereo 44.1/48 kHz interface for macOS input/output. Actual hardware
alignment still needs measurement; there is no continuous Logic clock drift correction.
AI-layer replacement still uses the separate player and UI-timer path. Audition shares the audience output; there is no private
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

### From threads to Top Ten countdowns

The next comedy direction is original AI parodies of David Letterman’s Top Ten
list format: a dry setup, ten musical punchlines, and a countdown to number one.
These first curated drafts adapt Suzy’s threads and add new jokes; the original
threads remain available as source material.

#### Top Ten Acts on the Mormon Music Festival Lineup

The lineup is subject to revelation.

**10.** Latter Day Gaga.

**9.** The Tabernacle of Sound.

**8.** The Book of More Bass.

**7.** Salt Lake, Emerson & Palmer.

**6.** Mission of Burma. They took the assignment literally.

**5.** Better Than Ezra. Just ask him.

**4.** Mennonite at Work. Booked by the interfaith committee.

**3.** Detroit Salt City.

**2.** The (latter day) Saints.

**1.** The Joseph Smiths. The Mormonissey years, of course.


#### Top Ten Songs to Take a Crap To

Tonight’s playlist comes with its own listening booth.

**10.** Carly Simon — Anticipation. We have all been here before.

**9.** The Kinks — Tired of Waiting for You. So is everyone outside.

**8.** U2 — Stuck in a Moment You Can’t Get Out Of. A concept album, apparently.

**7.** The House at Pooh Corner. Location, location, location.

**6.** Buzzcocks — Oh Shit. Finally, an honest review.

**5.** Spinal Tap — Big Bottom. Turn the fan up to eleven.

**4.** The Clash — Cut the Crap. Management has requested a shorter set.

**3.** Salt-N-Pepa — Push It. No further notes.

**2.** Snoop Dogg — Drop It Like It’s Hot. Please remain seated.

**1.** Screamin’ Jay Hawkins — Constipation Blues. The residency has been extended.


The [Top Ten workflow](docs/top-ten.md) supports curated lists and new local-model
drafts. Generation is separate from live audio and never automatically saves a
parody as an original thread or private memory.

More threads, album reviews and musical examples will join the collection as the
project develops.

## Local data

Approved memory and world state are stored locally under `~/.suzy-ai/` by default.
The public examples are separate from that private store and are not automatically
ingested by a fresh clone. Chat history and musical session context stay in process.

Loop audio is held in bounded memory buffers; recording no longer creates temporary WAV files.
Use the save controls to keep a WAV; unsaved loops are lost on exit. Model weights
are managed separately from the public source code.

## Next priorities

1. Rehearse with real guitar and vocals; measure the first-repeat gap, overdub
   alignment and sustained timing alongside Logic.
2. Calibrate hardware alignment, improve loop seams and move AI-layer replacement
   off its remaining UI timer while keeping inference outside the audio callback.
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
