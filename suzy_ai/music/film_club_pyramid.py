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
    # Clearly separated, forceful attacks rather than soft, continuous pads.
    "Punchy close-miked piano at 100 BPM, steady 4/4 electro-house. "
    "Short staccato low-mid chord stabs, crisp percussive hammer transients, "
    "strong accents on beats 1 and 3 and syncopated offbeat answers, "
    "eighth-note repeated hooks with deliberate rests and quick note-off. "
    "F sharp suspended, Gmaj7, A6 colours; dry upfront sound, no legato wash, "
    "no drums and no vocals",
    "Strong low cello at 100 BPM, tight 4/4 electro-house ostinato. "
    "Punchy pizzicato and short accented spiccato bow attacks, low "
    "repeated F sharp pulse, offbeat octave responses, firm transient "
    "and short decay, clear silence between notes, subtle modal slides "
    "only at phrase endings. Warm sub weight but no sustained drone, "
    "no drum kit, no vocals and no soft ambient pad",
    "Expressive bowed violin with original modal turns and ornamental "
    "slides, contrasting short rhythmic answers with longer vocal-like "
    "legato phrases over the same 100 BPM four-four pulse, suspended "
    "F sharp and G major seventh colours, humane dynamics, no drums",
    "Bright glass celesta and harp harmonics with clearly plucked "
    "sixteenth-note ostinati, rhythmic metallic answers and spacious "
    "delay trails, 100 BPM in four-four, subtle modal ornamentation, "
    "F sharp suspended harmony, no percussion or vocals",
    "100 BPM electro-house in steady 4/4, powerful four-on-the-floor "
    "rounded kick, firm snare clap on beats 2 and 4, offbeat closed "
    "hi-hats and brief syncopated frame-drum inspired dum tek fills, "
    "crisp energetic club percussion with open space for piano and cello "
    "stabs, no vocals or melody",
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
            "PYRAMID · THE LIVING LOOP / FILM CLUB",
        "Your original piano, violin and voice stay exactly where they are":
            "The Futureproof harmony continues. Record NEW Film Club takes on this page.",
        "One MRT2 Small model, five genuine Google AU sound prompts: Pyramid piano, low cello/harmonium, violin, glass bells/harp, and brushed jazz drums. Live blending uses the same native engine.":
            "One MRT2 Small model, the original Pyramid chord instrument and loop pedals, with five new Film Club prompt ideas: felt piano, cello/sub shadow, expressive violin, glass/harp, and evolving percussion.",
        "✦ EDIT FIVE MAGENTA SOUND PROMPTS":
            "✦ FILM CLUB ONLY · FIVE MAGENTA SOUND PROMPTS",
        "01 · PYRAMID · intimate piano":
            "01 · PYRAMID ATTACK · punchy house piano",
        "02 · PYRAMID ORBIT · low cello / harmonium drone":
            "02 · BASS ENGINE · pizzicato cello pulse",
        "03 · PYRAMID · MAGENTA VIOLIN LEAD":
            "03 · HUMAN INTERRUPTION · modal violin",
        "04 · PYRAMID ORBIT · glass harmonics / harp":
            "04 · CITY GLASS · rhythmic celesta / harp",
        "DRUM SOUND PROMPT · EDITABLE":
            "05 · FILM CLUB PULSE · driving breaks / hand drum",
    }
    for old, new in labels.items():
        if old not in page:
            raise ValueError("TOASTER view anchor changed: " + old[:60])
        page = page.replace(old, new, 1)

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
  <h2>Same loop station. A new chapter of the same song.</h2>
  <p>F♯ → Gmaj7 → A6 is still home. Use the familiar green beat-one,
  record-first-loop, DONE → LOOP, layered cello/violin/glass/drums, microphone,
  and native PCM pedals. The film's acceleration comes from what you play and
  layer, not an automatic replacement beat. Gastown Simulator supplies the film.</p>
  <div class="film-cue-grid" aria-label="Suggested edit storyboard">
    <div class="film-cue-item"><strong>0–10s</strong> FLOAT / harbour</div>
    <div class="film-cue-item"><strong>10–24s</strong> AWAKEN / glass</div>
    <div class="film-cue-item"><strong>24–38s</strong> TENSION / percussion</div>
    <div class="film-cue-item"><strong>38–48s</strong> HUMAN / violin & voice</div>
    <div class="film-cue-item"><strong>48–60s</strong> RELEASE / soft reset</div>
  </div>
  <div class="film-cue-actions" style="margin:15px 0;gap:15px">
    <label for="filmGrooveEnergy" class="film-tag">ELECTRONIC GROOVE ENERGY</label>
    <input id="filmGrooveEnergy" type="range" min="0" max="100" value="84"
      aria-label="Film Club sub-eighth rhythmic energy"
      style="max-width:260px;flex:1;accent-color:#bdf3d9">
    <output id="filmGrooveReadout" for="filmGrooveEnergy" class="film-tag">72%</output>
    <span class="film-tag">FILM CLUB: 4/4 ELECTRO HOUSE · 100 BPM</span>
  </div>
  <p>Choose <strong>Electro house · four-on-the-floor</strong> or
  <strong>Frame-drum electro / syncopated</strong> under DRUM STYLE.
  Both add local synthesized off-grid ornaments without moving the original
  4/4 piano loop. Extra subdivisions are browser audio, not imported
  percussion recordings or part of the three-lane MIDI export.</p>
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
    page = page.replace("</header>", "</header>" + banner, 1)
    page = page.replace(
        "</body>",
        '<script src="/film-club/soft-reset/film-club.js" defer></script></body>',
        1
    )
    if page.count('id="filmClubCues"') != 1:
        raise ValueError("Film Club cue surface not installed")
    return page
