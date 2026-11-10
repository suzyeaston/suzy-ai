"""Film Club continuation of Pyramid Orbit using the existing TOASTER loop UI.

No second copy of the 270 KB performance page and no changes to its loop
engine. Film sound prompts live only in this view until the musician explicitly
chooses APPLY or starts a stopped Magenta host.
"""
from __future__ import annotations

from html import escape
import re

from .magenta_native_host import PROMPTS


TITLE = "PYRAMID / SOFT RESET · Film Club"
FILM_PROMPTS = (
    # Four-chord Film Club adaptation; the original Futureproof F-sharp bank
    # remains unchanged. Instrument roles are independent timbral prompts.
    "Natural acoustic jazz grand piano: felt hammer attacks, real resonant "
    "piano strings, warm wooden soundboard, long overlapping chord decay. "
    "Play the four sustained harmonies E minor, E dominant seventh, A minor "
    "and E major, with gentle ninth extensions and slightly swung rubato. "
    "Let G-natural resolve to G-sharp in E7. Dark spacious piano at "
    "100 BPM 4/4, no electric piano, organ, bell synthesizer or drums",
    "Low warm bowed cello doubled by a softly breathing pump harmonium "
    "reed-organ bass drone. The bass moves E2 to E2 to A2 to E2 beneath "
    "E minor, E dominant seventh, A minor, E major harmony. Deep woody "
    "resonance and round low-frequency fundamentals, long legato arco "
    "strokes, subtle vibrato and slow warm reed swells; modal F-natural "
    "passing colour for tension. 100 BPM 4/4, no bright synth or drums",
    "Expressive lyrical jazz violin in long bowed legato tones, gliding "
    "portamento and human imperfect vibrato over E minor to E dominant "
    "seventh, A minor and E major. Dark minor phrasing contrasts with "
    "G-sharp dominant tension and occasional F-natural Phrygian colour. "
    "Gradually increase tremolo and granular electronic resonance, then "
    "return to a fragile long release; 100 BPM 4/4, no drums",
    "Sustained glass harmonica, bowed vibraphone and harp harmonics. "
    "Long ringing overtones and spacious granular delays surround "
    "E minor, E7, A minor and E major chords; occasional F-natural "
    "Phrygian colour, shifting major-minor tension and open jazz ninths. "
    "Sparse spectral textures bloom into motion, then disappear. "
    "100 BPM cinematic electronica, no piano, voice or drums",
    "Organic 100 BPM four-four jazz-electronica rhythm: rounded electronic "
    "kick, brushed backbeat and ghost snare, shuffling cymbal shimmer, "
    "low toms and sub-bass pressure beneath E minor, E7, A minor, E major. "
    "Darker modal F-natural ornaments, increasing rhythmic density and "
    "distortion with an abrupt half-time feeling in the bridge, no lead "
    "melody, sampled vocals or continuous aggressive house fills",
)
PROMPT_IDS = (
    "promptPyramid", "promptFishes", "promptViolin",
    "promptGuitar", "promptJazzDrums",
)
ORIGINAL_PROMPTS = tuple(PROMPTS[key] for key in (
    "pyramid", "fishes", "pyramid_violin", "fishes_guitar", "jazz_drums"
))
assert len(FILM_PROMPTS) == len(PROMPT_IDS) == 5
assert all(0 < len(prompt) <= 500 for prompt in FILM_PROMPTS)


def render_film_club_page(original: str, token: str) -> str:
    """Return Film Club variant without editing the source Futureproof page.

    Expects the same ids, scripts and PCM loop controls as /toaster/live.
    Fail closed if an upstream HTML change removes a prompt/anchor.
    """
    if not original.startswith("<!doctype html>"):
        raise ValueError("Expected the original TOASTER HTML document")
    page = original.replace("__MAGENTA_TOKEN__", token)
    if page == original and "__MAGENTA_TOKEN__" in original:
        raise ValueError("Could not substitute stage token")

    labels = {
        "FUTUREPROOF · THE APPLIANCE LATENT SPACE":
            "FILM CLUB · PYRAMID / SOFT RESET · MAKE ART NOT WAR",
        "PYRAMID · THE LIVING LOOP":
            "PYRAMID / ACCELERANDO · THE LIVING LOOP",
        "Your original piano, violin and voice stay exactly where they are":
            "Em → E7 → Am → E · Film Club-only harmonies, original live-loop engine.",
        "One MRT2 Small model, five genuine Google AU sound prompts: Pyramid piano, low cello/harmonium, violin, glass bells/harp, and brushed jazz drums. Live blending uses the same native engine.":
            "One MRT2 Small model, the original Pyramid chord instrument and loop pedals, with five new Film Club prompt ideas: acoustic grand piano, deep cello/harmonium bass, expressive violin, glass/harp, and evolving percussion.",
        "✦ EDIT FIVE MAGENTA SOUND PROMPTS":
            "✦ FILM CLUB ONLY · FIVE MAGENTA SOUND PROMPTS",
        "01 · PYRAMID · intimate piano":
            "01 · PYRAMID JAZZ · sustained resonant piano",
        "02 · PYRAMID ORBIT · low cello / harmonium drone":
            "02 · UNDERCURRENT · warm cello + harmonium bass",
        "03 · PYRAMID · MAGENTA VIOLIN LEAD":
            "03 · HUMAN INTERRUPTION · legato jazz violin",
        "04 · PYRAMID ORBIT · glass harmonics / harp":
            "04 · CITY GLASS · ringing vibraphone / harmonics",
        "DRUM SOUND PROMPT · EDITABLE":
            "05 · PULSE · brushed jazz electronica / sub",
    }
    for old, new in labels.items():
        if old not in page:
            raise ValueError("TOASTER view anchor changed: " + old[:60])
        page = page.replace(old, new, 1)

    # Film Club performance-only chords. Keep the original /toaster/live
    # HTML and its F♯ / Gmaj7 / A6 / F♯ bank unchanged. The renderer
    # replaces exactly the source's verified anchors and fails closed on
    # drift. Four playable pads (Z X C V) are available in Film Club.
    # Mazmazika's main-chord chart is Em / E7 / Am / E; this is a
    # *rehearsal adaptation*, not a complete transcription of every section.
    substitutions = (
        ('pyramid:{names:["F♯","Gmaj7","A6","F♯"],notes:[[54,58,61,66],[55,59,62,66],[57,61,64,66],[54,58,61,66]]',
         'pyramid:{names:["Em","E7","Am","E"],notes:[[52,55,59,64],[52,56,59,62],[57,60,64,69],[52,56,59,64]]'),
        ('pyramid:["Z","X","C"],fishes:',
         'pyramid:["Z","X","C","V"],fishes:'),
        ('c:{which:"pyramid",index:2},',
         'c:{which:"pyramid",index:2},v:{which:"pyramid",index:3},'),
        ('KeyZ:"z",KeyX:"x",KeyC:"c",',
         'KeyZ:"z",KeyX:"x",KeyC:"c",KeyV:"v",'),
        ('<button class="pad" data-scene="pyramid" data-chord="0"><kbd>Z</kbd><b>F♯</b></button>',
         '<button class="pad" data-scene="pyramid" data-chord="0"><kbd>Z</kbd><b>Em</b></button>'),
        ('<button class="pad" data-scene="pyramid" data-chord="1"><kbd>X</kbd><b>Gmaj7</b></button>',
         '<button class="pad" data-scene="pyramid" data-chord="1"><kbd>X</kbd><b>E7</b></button>'),
        ('<button class="pad" data-scene="pyramid" data-chord="2"><kbd>C</kbd><b>A6</b></button>',
         '<button class="pad" data-scene="pyramid" data-chord="2"><kbd>C</kbd><b>Am</b></button>\n<button class="pad" data-scene="pyramid" data-chord="3"><kbd>V</kbd><b>E</b></button>'),
        # Rendered film-only native harmony bank: matching Swift MIDI values.
        ('const bassOctave=(window.suzyFilmClubLowCello===true &&\n     which==="pyramid"&&role==="textureLow")?-12:0;\n   await aiFetch("chord",bassOctave?{index,harmony,legato:true,octave:bassOctave}:\n     {index,harmony,legato:true});',
         'const bassOctave=(window.suzyFilmClubLowCello===true &&\n     which==="pyramid"&&role==="textureLow")?-12:0;\n   const soundBank=harmony==="pyramid"?"accelerando":harmony;\n   await aiFetch("chord",bassOctave?{index,harmony:soundBank,legato:true,octave:bassOctave}:\n     {index,harmony:soundBank,legato:true});'),
        ('await aiFetch("chord",legato?{index,legato:true}:{index});',
         'await aiFetch("chord",legato?{index,legato:true,harmony:which==="pyramid"?"accelerando":"fishes"}:\n      {index,harmony:which==="pyramid"?"accelerando":"fishes"});'),
    )
    for old, new in substitutions:
        if page.count(old) != 1:
            raise ValueError("TOASTER chord source anchor changed: " + old[:72])
        page = page.replace(old, new, 1)

    # Keep every *visible* Film Club rehearsal hint in sync with the
    # actual four-pad bank. Do not alter the original Futureproof source.
    for old, new in (
        ('Harmonic orbit: F♯ → Gmaj7 → A6 → F♯.',
         'Film Club harmony: Em → E7 → Am → E.'),
        ('Low sustained notes and breathy drones, grounded in your existing F♯ / Gmaj7 / A6 harmony.',
         'Low sustained cello and warm reed drones under Em / E7 / Am / E, an octave below piano.'),
        ('PYRAMID: Z X C · WEIRD FISHES: B N M ,',
         'FILM CLUB: Z X C V · WEIRD FISHES: B N M ,'),
        ('Press PLAY RHYTHM · Pyramid Z X C · Weird Fishes B N M ,',
         'Press PLAY RHYTHM · Accelerando Em E7 Am E (Z X C V) · Weird Fishes B N M ,'),
        ('PYRAMID Z X C · WEIRD FISHES B N M , (comma)',
         'FILM CLUB Z X C V · WEIRD FISHES B N M , (comma)'),
        ('PYRAMID · Z X C chords · Fishes B N M ,',
         'ACCELERANDO · Z X C V chords · Fishes B N M ,'),
        ('WEIRD FISHES · B N M , chords · Pyramid Z X C',
         'WEIRD FISHES · B N M , chords · Film Club Z X C V'),
        (' · PYRAMID Z X C / FISHES B N M , play this sound',
         ' · ACCELERANDO Z X C V / FISHES B N M , play this sound'),
        ('KEYBOARD RESET · PYRAMID Z X C · FISHES B N M ,',
         'KEYBOARD RESET · FILM CLUB Z X C V · FISHES B N M ,'),
    ):
        if old not in page:
            raise ValueError("Film Club visible chord hint anchor changed: " + old[:65])
        page = page.replace(old, new)

    for key, prompt in zip(PROMPT_IDS, FILM_PROMPTS):
        pattern = re.compile(
            r'(<textarea\s+id="' + re.escape(key) +
            r'"\s+maxlength="500">)(.*?)(</textarea>)',
            re.DOTALL
        )
        page, count = pattern.subn(
            lambda match: match.group(1) + escape(prompt, quote=False) + match.group(3),
            page, count=1
        )
        if count != 1:
            raise ValueError("Film Club could not locate prompt: " + key)

    if "</style>" not in page or "</header>" not in page or "</body>" not in page:
        raise ValueError("Missing required TOASTER page anchors")
    style = """
/* Film Club colorway, added on top of the unchanged performance UX */
.film-recorder-spotlight{border:2px solid #e3afc7;border-radius:16px;
  background:linear-gradient(110deg,#332337,#263844);padding:14px 16px;
  margin:16px 0 18px;box-shadow:0 0 0 1px #e9b8d120}
.film-recorder-spotlight>summary{cursor:pointer;display:block;font-size:15px;
  font-weight:900;letter-spacing:.015em;color:#ffdbdd;padding:5px 0 13px;
  list-style:none}
.film-recorder-spotlight>summary::-webkit-details-marker{display:none}
.film-recorder-spotlight:not([open])>summary{padding-bottom:5px}
.film-recorder-spotlight .set-recorder{background:#291d2d;border-color:#e9bacd}
.film-recorder-spotlight #setRecordStart{font-size:14px;min-height:46px}
.film-recorder-guide{font-size:13px;line-height:1.5;color:#f4e4e5;
  margin:0 0 12px}
.film-recorder-guide strong{color:#c3f8dc}
.film-record-logic{color:#f8cfcf;font:800 11px ui-monospace,monospace;
  letter-spacing:.08em}
.film-cue-rail{border:1px solid #d39fae;border-radius:16px;margin:15px 0 18px;
  padding:18px;background:linear-gradient(125deg,#4c283e,#253b3d);color:#fff0e9}
.film-cue-rail h2{margin:6px 0 8px;font-size:clamp(21px,3vw,30px)}
.film-cue-rail p{font-size:13px;line-height:1.55;max-width:850px}
.film-cue-rail .film-tag{font:900 11px ui-monospace,monospace;
  letter-spacing:.13em;color:#c1ffe2}
.film-cue-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:7px;margin:14px 0}
.film-cue-item{border:1px solid #ffffff40;border-radius:9px;padding:10px;
  font:800 11px/1.4 ui-monospace,monospace;background:#201a27}
.film-cue-item strong{display:block;color:#bdf3d9;font-size:12px}
.film-cue-item{color:#f5e8ee;text-align:left;cursor:pointer}
.film-cue-item[aria-pressed="true"]{border-color:#bdf3d9;background:#244b43}
.film-cue-item:focus-visible{outline:2px solid #bdf3d9;outline-offset:3px}

.film-audition{margin:16px 0;padding:16px;border:1px solid #abdcc3;border-radius:12px;background:#1e2630}
.film-audition h3{margin:3px 0 8px;font-size:20px}
.film-audition p{max-width:940px;line-height:1.5}
.film-audition-grid{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}
.film-audition-grid button{background:#e6d1ee;color:#27192e;border:1px solid #efddef;border-radius:9px;padding:10px 12px;font-weight:800;font-size:12px;cursor:pointer}
.film-audition-grid button[aria-pressed="true"]{background:#b2f0cd;color:#182f2b;border-color:#b2f0cd}
.film-audition-grid button:disabled{opacity:.6;cursor:progress}
.film-audition output{display:block;font:700 12px/1.5 ui-monospace,monospace;color:#b6f0d3;padding:7px 0;min-height:20px}
.film-sustain{display:grid;gap:7px;margin:12px 0;color:#f9e9ec}
.film-sustain label{font:800 12px ui-monospace,monospace}
.film-sustain input{width:min(100%,430px);accent-color:#b9edda}
.film-sustain small{font-size:11px;line-height:1.5;color:#ead9e7}

.film-cue-actions{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
.film-cue-actions button{padding:10px 14px;font-size:12px}
.film-native-sync{border:1px solid #b5f1d6;background:#233c38;border-radius:12px;padding:15px;margin:15px 0;display:grid;gap:8px}
.film-native-sync p{font-size:13px;line-height:1.5;margin:0;color:#f8f0ec}
.film-native-sync button{background:#b8edcf;color:#18352b;border:1px solid #b8edcf;padding:11px 15px;max-width:420px;border-radius:9px;font-weight:800;cursor:pointer}
.film-native-sync button:disabled{opacity:.65;cursor:progress}
.film-native-sync output{font:800 12px/1.5 ui-monospace,monospace;color:#fff4e6}
.film-manual-bridge{margin:12px 0 18px;border:1px solid #e1b6c4;border-radius:13px;padding:16px;background:#271e2d;color:#fff4e8}
.film-manual-bridge h3{font-size:19px;margin:3px 0 6px}
.film-manual-bridge p{font-size:13px;line-height:1.55;margin:4px 0 12px}
.film-manual-list{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:7px}
.film-copy-slot{padding:9px 4px;background:#efd3bb;color:#291c30;font-weight:800;font-size:11px;cursor:pointer;border:0;border-radius:8px}
.film-copy-slot:focus-visible{outline:2px solid #9ce1c2;outline-offset:2px}
.film-manual-bridge small{display:block;margin-top:9px;font-size:11px;color:#ead8d1}
@media(max-width:700px){.film-manual-list{grid-template-columns:repeat(2,minmax(0,1fr))}}

.film-native-sync small{font-size:11px;color:#f6e1d4}
.film-warning{padding:9px 12px;border-left:3px solid #f4d0aa;
  background:#291a24;border-radius:5px;font:12px/1.5 system-ui}
@media(max-width:700px){.film-cue-grid{grid-template-columns:repeat(2,1fr)}}
"""
    page = page.replace("</style>", style + "</style>", 1)
    # The native Google AU is a different process/UI. Do not imply that
    # changed textarea text automatically changes the running model.
    # Give the performer a prominent, deliberate, verifiable sync action
    # immediately beside the original prompt editor.
    # The official Google AU model-selector UI is not a browser DOM we can
    # automate or attest to from TOASTER. Offer an honest, reliable
    # clipboard-assisted route if its own window still shows old prompts.
    bridge = """<section class="film-manual-bridge" id="filmManualBridge"
 aria-label="Copy Film Club prompts into Google's native Audio Unit window">
<div class="film-tag">WHEN GOOGLE'S WINDOW STILL SHOWS THE OLD SOUNDS</div>
<h3>Use the native plugin's five prompt rows</h3>
<p>Google MRT2 can display or continue generating from an older sound bank
even when the SUZY host accepted updated text. Select each matching prompt
row in Google's own window, replace its text, and press Enter/confirm.
Use these copy buttons to transfer the exact Film Club prompts.
They copy text only; they do not restart or secretly modify the model.</p>
<div class="film-manual-list">
<button type="button" class="film-copy-slot" data-prompt-copy="promptPyramid">COPY 01 · PIANO</button>
<button type="button" class="film-copy-slot" data-prompt-copy="promptFishes">COPY 02 · CELLO</button>
<button type="button" class="film-copy-slot" data-prompt-copy="promptViolin">COPY 03 · VIOLIN</button>
<button type="button" class="film-copy-slot" data-prompt-copy="promptGuitar">COPY 04 · GLASS</button>
<button type="button" class="film-copy-slot" data-prompt-copy="promptJazzDrums">COPY 05 · DRUMS</button>
</div>
<output role="status" aria-live="polite" id="filmCopyStatus">READY TO COPY · NO MODEL RESTART</output>
<small>Do not confuse the Bank 1–3 memory slots with these sound-prompt rows.
Google's own prompt edits are the final authority for what the popup shows.
If you're currently recording a take, finish and export it first.</small>
</section>"""
    editor = '<details class="prompt-editor" id="promptEditor">'
    sync_panel = """<section class="film-native-sync" aria-label="Native MRT2 prompt synchronization">
<div class="film-tag">GOOGLE MRT2 · ACTIVE SOUND BANK</div>
<p>These Film Club prompts are new, but the Google Audio Unit may still be
running the original Futureproof sounds. Apply the five prompts below to
the <strong>real native MRT2 host</strong> before auditioning.</p>
<button type="button" id="filmSyncNativePrompts">↻ APPLY FILM CLUB SOUNDS TO MRT2</button>
<output id="filmNativePromptStatus" role="status" aria-live="polite">CHECKING NATIVE HOST…</output>
<small>This action restarts the shared Magenta generator and may clear native
in-memory loops. Export important takes first. Opening this page alone never
changes the host or Google's window.</small></section>"""
    if editor not in page:
        raise ValueError("Original TOASTER prompt editor anchor changed")
    page = page.replace(editor, sync_panel + bridge + editor, 1)
    banner = """
<section class="film-cue-rail" aria-label="Film Club composition and Gastown storyboard" id="filmClubCues">
  <div class="film-tag">FILM CLUB · PYRAMID AFTERIMAGE · COMPOSITION MODE</div>
  <h2>PYRAMID AFTERIMAGE · an accelerating city, a human interruption.</h2>
  <p><strong>ACCELERANDO HARMONIC REHEARSAL: Em → E7 → Am → E</strong>.
  The <strong>E7</strong> brings G♯ and D-natural against the opening
  E-minor G-natural. Hooktheory describes E Phrygian Dominant colour
  with an E-minor bridge. We adapt that tension to the warm acoustic piano,
  bowed cello and harmonium at <strong>100 BPM / 4⁄4</strong>. Press
  <strong>Z · X · C · V</strong> for the four real chords. Build rhythmic
  density, then interrupt with human violin and voice. The original
  RECORD FIRST LOOP → DONE → LOOP pedals still drive the music.</p>
  <section class="film-audition" id="filmAuditionPanel" aria-label="Audition the five actual native MRT2 sound roles">
    <div class="film-tag">WHY ONLY PIANO? THE OTHER PROMPT WEIGHTS DEFAULT TO ZERO</div>
    <h3>Hear a sustained voice · then record its own loop</h3>
    <p>Google MRT2 is one blended generator, not five audio tracks. Select
    a sound below to send a sustained audition chord automatically, or
    hold Z / X / C / V as long as you like. Press its regular
    RECORD TAKE → DONE → LOOP pedal to capture a
    real, independently repeating PCM layer. The original loop clock,
    recordings and prompts are not reset by these selectors.</p>
    <div class="film-sustain">
      <label for="filmNoteHold">NATIVE CHORD SUSTAIN · <strong id="filmNoteHoldValue">2.4 seconds</strong></label>
      <input type="range" id="filmNoteHold" min="400" max="4800" step="200" value="2400" aria-label="Minimum native MRT2 chord hold in milliseconds">
      <small>Film-only sustained audition: even a quick click rings for at least
      this long, while a physically held key stays active until released.
      Releasing an old chord never cuts off a new one.</small>
    </div>
    <div class="film-audition-grid">
      <button type="button" data-film-audition="piano">01 · HEAR PIANO</button>
      <button type="button" data-film-audition="cello">02 · HEAR CELLO + HARMONIUM</button>
      <button type="button" data-film-audition="violin">03 · HEAR VIOLIN</button>
      <button type="button" data-film-audition="glass">04 · HEAR GLASS</button>
      <button type="button" data-film-audition="drums">05 · HEAR DRUMS</button>
      <button type="button" id="filmAuditionBlend" aria-pressed="false">♫ BLEND ALL FIVE · ONE GENERATOR</button>
    </div>
    <output id="filmAuditionStatus" aria-live="polite">READING MRT2 PROMPT WEIGHTS…</output>
    <small>Blending prompts produces one texture, not separate stems. For
    a true five-instrument orchestration, record one native PCM take per
    instrument. Don't switch native roles while a take is recording.</small>
  </section>
  <div class="film-cue-grid" aria-label="Suggested edit storyboard">
    <button type="button" class="film-cue-item" data-film-density="float"><strong>0–10s</strong> SUSPEND / piano and city</button>
    <button type="button" class="film-cue-item" data-film-density="awaken"><strong>10–24s</strong> COMPOUND / cello and glass</button>
    <button type="button" class="film-cue-item" data-film-density="tension"><strong>24–38s</strong> ACCELERATE / density and sub</button>
    <button type="button" class="film-cue-item" data-film-density="human"><strong>38–48s</strong> INTERRUPT / violin and voice</button>
    <button type="button" class="film-cue-item" data-film-density="release"><strong>48–60s</strong> RELEASE / unresolved light</button>
  </div>
  <output id="filmDensityStatus" aria-live="polite" class="film-tag">LIVE DENSITY CUES · CLICK TO BUILD / DROP RHYTHM, BPM STAYS 100</output>
  <div class="film-cue-actions" style="margin:15px 0;gap:15px">
    <label for="filmGrooveEnergy" class="film-tag">ELECTRONIC GROOVE ENERGY</label>
    <input id="filmGrooveEnergy" type="range" min="0" max="100" value="24"
      aria-label="Film Club sub-eighth rhythmic energy"
      style="max-width:260px;flex:1;accent-color:#bdf3d9">
    <output id="filmGrooveReadout" for="filmGrooveEnergy" class="film-tag">24%</output>
    <span class="film-tag">FILM CLUB: 4/4 ELECTRO HOUSE · 100 BPM</span>
  </div>
  <p>Choose <strong>Electro house · four-on-the-floor</strong> or
  <strong>Frame-drum electro / syncopated</strong> under DRUM STYLE.
  The five time cards above are LIVE intensity gestures: sparse pulse,
  syncopation, increasingly dense subdivisions, dramatic half-time-feeling
  drop, and release. They adjust browser rhythm energy/level only, never
  restart Google, move the 100 BPM clock or overwrite recorded audio.
  Extra subdivisions are synthesized browser audio, not imported samples
  or notes in the three-lane MIDI export.</p>
  <div class="film-cue-actions">
    <button id="filmExportCues" type="button">↓ SAVE GASTOWN 60s CUES JSON</button>
    <a href="/toaster/live">Return to Futureproof interface</a>
    <span class="film-tag" id="filmPromptStatus" role="status">FILM TEXT READY · NATIVE PROMPT BANK NOT YET VERIFIED</span>
  </div>
  <p class="film-warning"><strong>Separate composition, shared Mac model:</strong>
  Film prompt text does not replace the Futureproof source presets.
  The native MRT2 host is shared by both browser pages. APPLY PROMPTS restarts
  that host and can stop native-memory audio loops. Finish/export any important
  takes first; avoid running both performance pages at once. The browser
  never restores unsaved recordings after a reload.</p>
</section>
"""
    # The original TOASTER recorder works, but its closed ADVANCED
    # details panel was pushed far below the long Film Club instrument
    # banner. Reuse that SAME recorder DOM and callbacks (not a second
    # capture engine) and move it directly beneath the top header, OPEN
    # by default only for the Film Club view.
    record_start = (
        '<details class="advanced-session"><summary>'
        '▸ ADVANCED · Record the entire performance</summary>'
    )
    record_end = '</section></details>'
    if page.count(record_start) != 1:
        raise ValueError("Expected exactly one original full-set recorder")
    record_begin = page.index(record_start)
    record_finish = page.find(record_end, record_begin)
    if record_finish < 0:
        raise ValueError("Could not find original recorder closing tags")
    record_finish += len(record_end)
    recorder = page[record_begin:record_finish]
    for required_id in (
        'setRecordStart', 'setRecordStop', 'setRecordMic',
        'setRecordStatus'
    ):
        if recorder.count('id="' + required_id + '"') != 1:
            raise ValueError("Recorder controls missing: " + required_id)
    page = page[:record_begin] + page[record_finish:]
    recorder = recorder.replace(
        record_start,
        '<details class="advanced-session film-recorder-spotlight" '
        'id="filmRecordStudio" open><summary>'
        '🔴 FILM CLUB RECORDING · SCREEN AUDIO + VOCALS → LOGIC</summary>',
        1
    )
    recorder = recorder.replace(
        '<section class="set-recorder" aria-label="Record entire live set as audio">',
        '<p class="film-record-logic">FULL STEREO PERFORMANCE CAPTURE</p>'
        '<p class="film-recorder-guide">Click <strong>RECORD FULL SET</strong>'
        ' to open Chrome’s screen-sharing picker. Choose '
        '<strong>Entire Screen + Share system audio</strong> to capture '
        'Google MRT2, the rhythm and existing loops. Optional Scarlett / '
        'VE-22 microphone is mixed into the same recording. Then '
        '<strong>STOP &amp; SAVE AUDIO</strong> to download for Logic Pro.</p>'
        '<section class="set-recorder" aria-label="Record entire live set as audio">',
        1
    )
    page = page.replace("</header>", "</header>" + recorder + banner, 1)
    if page.count('id="filmRecordStudio"') != 1:
        raise ValueError("Film Club recording panel was not mounted")
    if page.count('id="setRecordStart"') != 1:
        raise ValueError("Film Club recording UI has duplicated controls")

    page = page.replace(
        "</body>",
        '<script src="/film-club/soft-reset/film-club.js" defer></script>'
        '<script src="/film-club/soft-reset/audition.js" defer></script></body>',
        1
    )
    if page.count('id="filmClubCues"') != 1:
        raise ValueError("Film Club cue surface not installed")
    return page
