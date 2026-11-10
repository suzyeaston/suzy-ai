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
    # Film-only original sound design. Synth-led, high-energy and no
    # artist recording, copied melody, stems, or voice identity.
    "Glittering futuristic synth piano, not acoustic piano. Glassy FM "
    "electric keys, detuned saw layers, short rubbery pluck attacks, "
    "shimmering stereo chorus and sequenced sixteenth-note arpeggios. "
    "Minor-key synth-pop over Em E7 Am E, 100 BPM four-four with double-time "
    "bounce, bright offbeat stabs and huge sparkling release. Tight gated "
    "delay, glossy icy highs, elastic electro pulse, dramatic filter sweeps. "
    "No grand piano, jazz, orchestra or vocals.",
    "Dark analog synth bass with saturated sub and sidechain pump. Detuned "
    "pulse-wave midbass, warm E2 and A2, syncopated octave jumps, 3+3+2 "
    "rubbery bass riff answering a straight four-on-floor kick. Acidic "
    "resonant filter slides, brief metallic clicks and distorted tape edges, "
    "ominous then euphoric. Em E7 Am E at 100 BPM, perceived double-time "
    "momentum. No bowed cello, harmonium, acoustic bass or vocals.",
    "High soaring synthetic lead, icy formant-free synth voice texture, "
    "supersaw harmonies and crystalline portamento. Nimble arpeggiated "
    "sixteenths alternate with huge sustained minor-key melody notes over Em "
    "E7 Am E. Subtle pitch glide, metallic FM sparkle, high stereo shimmer "
    "and tight gated reverb. Surreal neon dream-pop energy, urgent "
    "double-time feel on 100 BPM clock. No acoustic violin, string quartet "
    "or sampled singer.",
    "Alien glass synth and digital fairy-dust percussion: bright FM bells, "
    "pixelated granular droplets, ring-modulated chimes, glitchy offbeat "
    "plucks and spectral delay trails. Tiny syncopated sixteenth-note loops "
    "climb over Em E7 Am E. Translucent high-end shimmer above deep "
    "electronic bass, rhythmic and luminous, with a sudden spacious "
    "half-time break. No vibraphone, harp, guitar, acoustic mallets or "
    "vocals.",
    "Hyperkinetic electronic club drums at 100 BPM four-four: huge tight sub "
    "kick, crunchy clap on 2 and 4, shimmering metallic closed hats, fast "
    "sixteenth glitches, syncopated rim and distorted tom fills. Second "
    "interlocking 3+3+2 percussion rhythm against the straight kick; "
    "pumping, ecstatic double-time sensation and dramatic half-time dropout. "
    "Neon electro-pop with a dark futuristic edge. Dry controlled "
    "transients, no acoustic jazz drums, piano or vocals.",
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
            "One Google MRT2 Small model with five Film Club AI sound directions: neon FM synth piano, pumping analog bass, supersaw lead, granular digital glass, and hyperkinetic electronic drums. Original MIDI chords and loop pedals are preserved.",
        "✦ EDIT FIVE MAGENTA SOUND PROMPTS":
            "✦ FILM CLUB ONLY · FIVE MAGENTA SOUND PROMPTS",
        "01 · PYRAMID · intimate piano":
            "01 · NEON FM · shimmering synth piano",
        "02 · PYRAMID ORBIT · low cello / harmonium drone":
            "02 · SUB ENGINE · pumping analog bass",
        "03 · PYRAMID · MAGENTA VIOLIN LEAD":
            "03 · SUPERSAW · soaring electronic lead",
        "04 · PYRAMID ORBIT · glass harmonics / harp":
            "04 · PIXEL DUST · granular FM sparkle",
        "DRUM SOUND PROMPT · EDITABLE":
            "05 · ELECTRO PULSE · glitch club drums",
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
/* Film-only compact controls. Original TOASTER content and capture remain. */
.film-control-bar{display:flex;flex-wrap:wrap;align-items:center;gap:10px;
  padding:11px 13px;margin:9px 0 11px;border:1px solid #8d837f;
  border-radius:11px;background:#292735;color:#f9eced}
.film-control-bar strong{font:900 12px ui-monospace,monospace;color:#b9f1d6}
.film-control-bar label{display:flex;align-items:center;gap:8px;
  font:750 11px ui-monospace,monospace}
.film-control-bar input[type=range]{width:110px;accent-color:#b9efda}
.film-control-bar output{font:800 11px ui-monospace,monospace;color:#d0f5df}
.film-record-small{border:1px solid #786477;border-radius:10px;
  background:#25212d;padding:10px 12px;margin:8px 0 14px}
.film-record-small>summary{font-size:12px;color:#e9d5df;font-weight:800}
.film-tools{margin:9px 0;border:1px solid #665772;border-radius:9px;
  padding:10px 12px;background:#231e2d}
.film-tools>summary{cursor:pointer;font:850 12px ui-monospace,monospace;color:#c6f1dd}
.film-tools .film-audition-grid{display:flex;gap:7px;flex-wrap:wrap;margin:10px 0}
.film-tools .film-audition-grid button{padding:7px 9px;font-size:11px;background:#d8c5e3;color:#30243a}
.film-tools .film-audition-grid button[aria-pressed=true]{background:#aee2c7;color:#1c3329}
.film-tools output{display:block;font:750 11px/1.5 ui-monospace,monospace;color:#b6eed3;margin-top:8px}
.film-sustain{display:flex;flex-wrap:wrap;align-items:center;gap:9px;margin:9px 0}
.film-sustain label{font:800 11px ui-monospace,monospace}
.film-sustain input{max-width:240px;accent-color:#c3efdc}
.film-native-sync{border:1px solid #b5f1d6;background:#233c38;
  border-radius:12px;padding:15px;margin:15px 0;display:grid;gap:8px}
.film-native-sync p{font-size:13px;line-height:1.5;margin:0;color:#f8f0ec}
.film-native-sync button{background:#b8edcf;color:#18352b;border:1px solid #b8edcf;
  padding:11px 15px;max-width:420px;border-radius:9px;font-weight:800;cursor:pointer}
.film-native-sync button:disabled{opacity:.65;cursor:progress}
.film-native-sync output{font:800 12px/1.5 ui-monospace,monospace;color:#fff4e6}
.film-native-sync small{font-size:11px;color:#f6e1d4}
.film-manual-bridge{margin:12px 0 18px;border:1px solid #e1b6c4;border-radius:13px;
  padding:16px;background:#271e2d;color:#fff4e8;scroll-margin-top:170px}
.film-manual-bridge h3{font-size:19px;margin:3px 0 6px}
.film-manual-bridge p{font-size:13px;line-height:1.55;margin:4px 0 12px}
.film-manual-list{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:7px}
.film-copy-slot{padding:9px 4px;background:#efd3bb;color:#291c30;
  font-weight:800;font-size:11px;cursor:pointer;border:0;border-radius:8px}
.film-copy-slot:focus-visible{outline:2px solid #9ce1c2;outline-offset:2px}
.film-manual-bridge small{display:block;margin-top:9px;font-size:11px;color:#ead8d1}
@media(max-width:700px){.film-manual-list{grid-template-columns:repeat(2,minmax(0,1fr))}}
"""
    page = page.replace("</style>", style + "</style>", 1)
    # The native Google AU is a different process/UI. Do not imply that
    # changed textarea text automatically changes the running model.
    # Give the performer a prominent, deliberate, verifiable sync action
    # immediately beside the original prompt editor.
    # The official Google AU model-selector UI is not a browser DOM we can
    # automate or attest to from TOASTER. Offer an honest, reliable
    # clipboard-assisted route if its own window still shows old prompts.
    bridge = """<details class="film-manual-bridge" id="filmManualBridge">
<summary>OPTIONAL TROUBLESHOOTING · COPY PROMPTS ONLY IF AUTOMATIC MODEL RELOAD IS UNAVAILABLE</summary>
<div class="film-tag">ALTERNATE GOOGLE AU EDITOR</div>
<h3>Manual fallback for an unsupported Google plugin build</h3>
<p>Choose COPY 01–05 below, paste each prompt into the corresponding
row of the <strong>existing</strong> Google MRT2 window, then press Enter
to confirm. Editing in Google avoids restarting its selected model.
SUZY cannot write into Google's separate plugin window automatically;
the buttons only copy text and do not interrupt your live loops.</p>
<button type="button" id="filmOpenGooglePrompts">↗ OPEN CURRENT GOOGLE PROMPT WINDOW · NO RESTART</button>
<output role="status" aria-live="polite" id="filmGoogleEditorStatus">OPEN ONLY THE EXISTING GOOGLE AU · NO MODEL RESTART</output>
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
</details>"""
    editor = '<details class="prompt-editor" id="promptEditor">'
    sync_panel = """<section class="film-native-sync" aria-label="Native MRT2 prompt synchronization">
<div class="film-tag">GOOGLE MRT2 · ACTIVE SOUND BANK</div>
<p>Replace Google's original Futureproof sound bank with these five new
electronic Film Club prompts <strong>inside the real MRT2 model</strong>.
The app reuses the model bookmark granted by Google's own window so the
new Audio Unit can load the new prompt embeddings without losing the
selected model. No browser synthesizer or manual text copying required.</p>
<button type="button" id="filmSyncNativePrompts">✦ LOAD FIVE NEON SOUNDS INTO GOOGLE MRT2</button>
<output id="filmNativePromptStatus" role="status" aria-live="polite">CHECKING NATIVE HOST…</output>
<small>First select the existing local mrt2_small model in Google's window
once, if prompted, to grant the model bookmark. Applying replaces the AI
instance and briefly interrupts playback. Finish and export native takes
first; this control refuses to erase active native loops. The host verifies
serialized prompt text, but only listening can verify generated audio.</small></section>"""
    if editor not in page:
        raise ValueError("Original TOASTER prompt editor anchor changed")
    page = page.replace(editor, sync_panel + bridge + editor, 1)
    # Remove the photographed full-size recording, soundtrack audition
    # and 60s-storyboard surfaces. Keep the REAL native selectors and
    # recorder inside short collapsed tools, not by deleting their engines.
    banner = """
<div class="film-control-bar" id="filmControlBar" role="group" aria-label="Accelerando performance controls">
  <strong>ACCELERANDO · Em → E7 → Am → E · 100 BPM</strong>
  <label for="filmGrooveEnergy">PULSE
    <input id="filmGrooveEnergy" type="range" min="0" max="100" value="58" aria-label="Main electro pulse density">
    <output id="filmGrooveReadout" for="filmGrooveEnergy">58%</output>
  </label>
  <label for="filmCounterRhythm">SHADOW BEAT
    <input id="filmCounterRhythm" type="range" min="0" max="100" value="62" aria-label="Layered syncopated counter-rhythm volume">
    <output id="filmCounterReadout" for="filmCounterRhythm">62%</output>
  </label>
  <span style="font-size:11px">Two interlocking grooves, one 4/4 clock.</span>
  <button type="button" id="filmAIOutputCheck">🎧 CHECK REAL MRT2 AUDIO · HOLD Z</button>
  <output id="filmAIOutputStatus" role="status" aria-live="polite">Audio Unit output not yet checked.</output>
</div>
<details class="film-tools" id="filmInstrumentTools">
  <summary>✦ INSTRUMENT AUDITION · FIVE NATIVE SOUNDS / NOTE SUSTAIN</summary>
  <p style="font-size:12px">One MRT2 generator: audition a sound, then
  record a separate PCM layer with the existing pedals below.</p>
  <p style="font-size:12px">NEON GROOVE: use short Z/X/C/V synth-piano chord
  pickups, then record an offbeat analog bass answer and faster digital lead
  phrase. The held low notes can stay underneath. This changes phrasing,
  not the 100 BPM loop clock.</p>
  <div class="film-sustain">
    <label for="filmNoteHold">MIDI HOLD <span id="filmNoteHoldValue">2.4 seconds</span></label>
    <input type="range" id="filmNoteHold" min="400" max="4800" step="200" value="2400">
  </div>
  <div class="film-audition-grid">
    <button type="button" data-film-audition="piano">01 · HEAR FM SYNTH PIANO</button>
    <button type="button" data-film-audition="cello">02 · HEAR ANALOG SUB BASS</button>
    <button type="button" data-film-audition="violin">03 · HEAR SUPERSAW LEAD</button>
    <button type="button" data-film-audition="glass">04 · HEAR GRANULAR GLASS</button>
    <button type="button" data-film-audition="drums">05 · HEAR DRUMS</button>
    <button type="button" id="filmAuditionBlend" aria-pressed="false">BLEND FIVE · ONE GENERATOR</button>
  </div>
  <output id="filmAuditionStatus" role="status" aria-live="polite">READING MRT2 WEIGHTS…</output>
</details>
<details class="film-tools" id="filmCueTools">
  <summary>↳ ADVANCED · GASTOWN EDIT CUES / PROMPT STATUS</summary>
  <button type="button" id="filmExportCues">↓ EXPORT 60S CUE JSON</button>
  <output id="filmPromptStatus" role="status">FILM PROMPTS READY · NATIVE BANK UNVERIFIED</output>
</details>

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
        '<details class="advanced-session film-record-small" '
        'id="filmRecordStudio"><summary>'
        '● RECORD SYSTEM AUDIO · LOGIC / OPTIONAL SCARLETT</summary>',
        1
    )
    page = page.replace("</header>", "</header>" + banner + recorder, 1)
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
    if page.count('id="filmControlBar"') != 1:
        raise ValueError("Compact Film Club controls were not installed")
    if 'id="filmClubCues"' in page or 'id="filmAuditionPanel"' in page:
        raise ValueError("Legacy oversized film panels must not render")
    return page
