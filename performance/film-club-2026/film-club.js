/* PYRAMID / SOFT RESET: film-specific enhancement ONLY.
 * The actual live loop, audio, mic, Magenta and transport code come from
 * suzy_ai/music/toaster_play.html. Do not build a second loop scheduler here.
 */
(() => {
  "use strict";
  const button = document.getElementById("filmExportCues");
  const status = document.getElementById("filmPromptStatus");
  if (!button || !status) return;

  // Film-only orchestration and vocal processing. A second 3+3+2 pattern
  // runs inside the original eighth-note scheduler; no second clock.
  // Original Futureproof behavior is unchanged when this page isn't open.
  window.suzyFilmClubLowCello=true;
  window.suzyFilmClubVocalClean=true;
  const shadow=document.getElementById("filmCounterRhythm");
  const shadowLabel=document.getElementById("filmCounterReadout");
  if(shadow){
    const setShadow=()=>{
      window.suzyFilmCounterRhythm=Math.max(0,Math.min(1,Number(shadow.value)/100));
      if(shadowLabel)shadowLabel.textContent=shadow.value+"%";
    };
    shadow.addEventListener("input",setShadow);
    setShadow();
  }
  // Noise-safe airy vocal starting point: modest wet-only delay, gentle
  // feedback and lowpass, rather than an amplified constant noise wash.
  // The source mic and recorded PCM remain completely dry.
  for(const [id,value] of [
    ["vocalEchoMode","dotted"],["vocalEchoLevel","15"],
    ["vocalEchoFeedback","15"],["vocalAir","44"],
    ["monitorReverb","20"]]){
    const field=document.getElementById(id);
    if(field)field.value=value;
  }
  if(typeof updateVoiceEcho==="function")updateVoiceEcho();

  // Film Club is a new page, with its own browser loop memory. Choose a
  // denser original local groove without modifying Futureproof defaults or
  // restarting the shared native Magenta model. The drum metre stays 4/4.
  if(typeof stageStarted!=="undefined" && !stageStarted){
    // Film-only preset: the original Futureproof page still opens at 105 BPM.
    // Set these BEFORE the first recording; changing an existing PCM loop
    // would shift its pitch and the shared looper correctly blocks that.
    const tempo=document.getElementById("tempo");
    if(tempo)tempo.value="100";
    if(typeof changeTempo==="function")changeTempo(100);
    if(typeof setDrumGroove==="function")setDrumGroove("4/4","house");
    const rhythmLevel=document.getElementById("rhythmLevel");
    if(rhythmLevel){
      rhythmLevel.value="52";
      const readout=document.getElementById("rhythmLevelNumber");
      if(readout)readout.textContent="52%";
    }
  }
  const energy = document.getElementById("filmGrooveEnergy");
  const energyReadout = document.getElementById("filmGrooveReadout");
  if(energy&&energyReadout){
    const update=()=>{
      if(typeof drumEnergy!=="undefined")drumEnergy=Number(energy.value)/100;
      energyReadout.textContent=energy.value+"%";
    };
    energy.addEventListener("input",update);
    update();
  }

  // Performance macros: accelerate density, not the audio-clock tempo.
  // These are live performer buttons, not a game sync/autoplay mechanism.
  const sceneDynamics=Object.freeze({
    float:{energy:24,level:34},
    awaken:{energy:49,level:39},
    tension:{energy:88,level:52},
    human:{energy:8,level:20},
    release:{energy:45,level:35}
  });
  const densityStatus=document.getElementById("filmDensityStatus");
  const densityButtons=[...document.querySelectorAll("[data-film-density]")];
  for(const b of densityButtons){
    b.setAttribute("aria-pressed","false");
    b.addEventListener("click",()=>{
      const key=b.dataset.filmDensity;
      const plan=sceneDynamics[key];
      if(!plan)return;
      if(energy){
        energy.value=String(plan.energy);
        if(typeof drumEnergy!=="undefined")drumEnergy=plan.energy/100;
        if(energyReadout)energyReadout.textContent=String(plan.energy)+"%";
      }
      const rhythmLevel=document.getElementById("rhythmLevel");
      if(rhythmLevel){
        rhythmLevel.value=String(plan.level);
        const meter=document.getElementById("rhythmLevelNumber");
        if(meter)meter.textContent=String(plan.level)+"%";
        if(typeof updateRhythmAudio==="function")updateRhythmAudio();
      }
      densityButtons.forEach(other=>other.setAttribute("aria-pressed",
        String(other===b)));
      if(densityStatus)densityStatus.textContent=
        key.toUpperCase()+" · "+plan.energy+"% PERCUSSION ENERGY · "+
        "BPM UNCHANGED · LOOPS UNTOUCHED";
    });
  }

  const scenes = Object.freeze([
    {id:"float",start:0,end:10,hint:"Harbour and reflective pavement. Begin with the Pyramid piano loop and space.",visual_event:"gastown_harbour",instruments:["piano","glass"]},
    {id:"awaken",start:10,end:24,hint:"Accumulate cello, glass and bow motion; movement grows without a compulsory tempo change.",visual_event:"city_awakes",instruments:["piano","cello","glass"]},
    {id:"tension",start:24,end:38,hint:"Bring in brushed/driven percussion and denser layering; Gastown lights repeat.",visual_event:"machine_tension",instruments:["cello","drums","glass"]},
    {id:"human",start:38,end:48,hint:"Drop the rhythmic density and let violin, voice and live melody interrupt.",visual_event:"human_intervention",instruments:["violin","voice"]},
    {id:"release",start:48,end:60,hint:"Return to piano and open the harmony; the same city becomes art.",visual_event:"make_art_not_war",instruments:["piano","voice","glass"]}
  ]);

  button.addEventListener("click", () => {
    const payload = {
      schema_version:"suzy-film-cues/v2",
      composition:"Pyramid / Accelerando Afterimage (Film Club four-chord adaptation)",
      duration_sec:60,
      harmony_reference:["Em","E7","Am","E"],
      chord_basis:"Four main chords reported in Mazmazika; rehearsal adaptation of Accelerando, not its full timeline",
      harmonic_colour:"E Phrygian Dominant verses/chorus, E minor bridge (Hooktheory); contrasting G-natural/G-sharp and occasional F-natural",
      reference_tempo_bpm:124,
      performance_tempo_bpm:100,
      instrument_prompts:"film-view-specific, locally editable; no audio included",
      source_instrument:"SUZY//TOAST Pyramid live loop system",
      visual_project:"Gastown Simulator",
      timing:"Editorial guide in absolute seconds; DOES NOT control or sync the looping transport",
      scenes:scenes.map(scene=>({...scene, start_sec:scene.start,end_sec:scene.end})),
      safety:"Keep the film WAV and any browser/native PCM exports separately; loops are not in JSON"
    };
    const url = URL.createObjectURL(new Blob([JSON.stringify(payload,null,2)+"\n"],{type:"application/json"}));
    const anchor=document.createElement("a");
    anchor.href=url;
    anchor.download="pyramid-soft-reset-gastown-cues.json";
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.setTimeout(()=>URL.revokeObjectURL(url),10000);
    status.textContent="GASTOWN CUES SAVED · manual edit guide, not synced playback";
  });

  // The Google AU popup is native host state, NOT a reflection of the
  // page's textarea values. Show verified status from /api/ai/status rather
  // than pretending the new page automatically changes the active model.
  const nativeApply = document.getElementById("filmSyncNativePrompts");
  const nativeState = document.getElementById("filmNativePromptStatus");
  const promptIds = ["promptPyramid","promptFishes","promptViolin","promptGuitar","promptJazzDrums"];
  let syncing = false;
  let lastState = null;
  function textBank() {
    return promptIds.map(id => document.getElementById(id)?.value.trim() ?? "");
  }
  function matchesHost(state,bank=textBank()) {
    return Array.isArray(state?.text_prompts) &&
      state.text_prompts.length === bank.length &&
      state.text_prompts.every((value,index)=>value===bank[index]);
  }
  function matchesAU(state, bank=textBank()) {
    return state?.au_prompt_readback_available===true &&
      Array.isArray(state.au_prompt_texts) &&
      state.au_prompt_texts.length===bank.length &&
      state.au_prompt_texts.every((value,index)=>value===bank[index]);
  }
  function reportNative(message, serialized=false) {
    if(nativeState)nativeState.textContent=message;
    if(status)status.textContent=serialized?
      "AU SAVED TEXT MATCHES · ACTUAL GOOGLE SOUND/POPUP UNVERIFIED":
      "FILM TEXT READY · GOOGLE AU SOUND BANK NOT CONFIRMED";
  }
  function explainState(state, bank=textBank()) {
    if(state?.phase==="starting" || state?.phase==="initializing")
      return "GOOGLE MRT2 STARTING · KEEP THE MODEL WINDOW OPEN; CHECK AGAIN AFTER INITIALIZATION.";
    // Google's actual AU fullState matters more than the Swift host's
    // desired strings. Manual edits in Google's window may legitimately
    // make AU state match while the host-side strings remain older.
    if(matchesAU(state,bank))
      return matchesHost(state,bank)?
        "GOOGLE AU SAVED TEXT MATCHES FILM CLUB. MODEL EMBEDDINGS AND AUDIBLE SOUND STILL REQUIRE LISTENING.":
        "GOOGLE AU SAVED TEXT MATCHES FILM CLUB · HOST LABEL IS OLDER, BUT NO RESTART IS NECESSARY. LISTEN TO VERIFY.";
    // NEVER suggest restarting a currently audible AU just to change
    // prompts. The Google model picker resets on a host stop/start.
    if(state?.phase==="host-running" || state?.audio_engine_running===true)
      return "MRT2 IS RUNNING WITH DIFFERENT PROMPTS · USE THE SAFE COPY 01–05 WORKFLOW IN GOOGLE; KEEP THE AUDIO UNIT RUNNING.";
    if(!matchesHost(state,bank))
      return "HOST DOES NOT HAVE FILM CLUB PROMPTS · SAFE UPDATE CAN START AN IDLE HOST ONLY.";
    if(!Object.prototype.hasOwnProperty.call(state||{},"au_prompt_readback_available"))
      return "OLD SWIFT HOST BINARY · REBUILD NATIVE HOST TO CHECK GOOGLE PROMPTS; NO AUTOMATIC RESTART.";
    if(state.au_prompt_readback_available!==true)
      return "HOST HAS FILM TEXT · GOOGLE AU READBACK UNAVAILABLE; COPY INTO GOOGLE'S EXISTING PROMPT ROWS.";
    return "GOOGLE AU REPORTS DIFFERENT SAVED TEXT · USE COPY 01–05; SOUND NOT VERIFIED.";
  }
  // Manual bridge edits Google's own prompt rows. No app-to-AU automation
  // is claimed, and nothing is transmitted or restarted when copying text.
  const copyState=document.getElementById("filmCopyStatus");
  for(const button of document.querySelectorAll("[data-prompt-copy]")){
    button.addEventListener("click",async()=>{
      const id=button.dataset.promptCopy;
      if(!promptIds.includes(id))return;
      const field=document.getElementById(id);
      const value=field?.value.trim();
      if(!value){if(copyState)copyState.textContent="PROMPT IS EMPTY";return;}
      try{
        if(!navigator.clipboard?.writeText)throw Error("Clipboard API unavailable");
        await navigator.clipboard.writeText(value);
        if(copyState)copyState.textContent=button.textContent.trim()+
          " COPIED · PASTE INTO MATCHING ROW IN GOOGLE MRT2 (CMD+V)";
      }catch{
        field?.focus();
        field?.select();
        if(copyState)copyState.textContent="SELECTED PROMPT TEXT · PRESS CMD+C, THEN PASTE INTO GOOGLE.";
      }
    });
  }
  async function getNativeState() {
    const response=await fetch("/api/ai/status",{cache:"no-store"});
    if(!response.ok)throw Error("Native host status unavailable");
    return await response.json();
  }
  async function refreshPromptState() {
    if(syncing || !nativeState)return;
    try{
      const state=await getNativeState();
      lastState=state;
      reportNative(explainState(state),matchesAU(state));
    }catch(err){
      reportNative("CANNOT VERIFY MRT2 BANK · "+(err?.message||err),false);
    }
  }
  const manualBridge=document.getElementById("filmManualBridge");
  function showSafeManualGuide(message) {
    reportNative(message,false);
    if(copyState)copyState.textContent=
      "KEEP MRT2 PLAYING · COPY 01–05, PASTE INTO GOOGLE'S PROMPT ROWS AND PRESS ENTER.";
    manualBridge?.scrollIntoView?.({behavior:"smooth",block:"start"});
  }

  // This new native action only opens the CURRENT Google AU editor.
  // Unlike the original "show-au-ui" command it refuses to switch modes
  // (which stops the generator and closes its prompt window).
  const safeGoogleEditor=document.getElementById("filmOpenGooglePrompts");
  const safeGoogleStatus=document.getElementById("filmGoogleEditorStatus");
  safeGoogleEditor?.addEventListener("click",async()=>{
    try{
      const current=await getNativeState();
      if(current?.phase!=="host-running" ||
         current?.audio_engine_running!==true ||
         current?.native_model_selection_required!==true){
        if(safeGoogleStatus)safeGoogleStatus.textContent=
          "NO SAFE EDITOR OPEN · THE CURRENT AU IS NOT IN GOOGLE PICKER MODE. DO NOT RESTART A PLAYING SESSION.";
        return;
      }
      if(typeof aiFetch!=="function")throw Error("Native host control unavailable");
      const result=await aiFetch("show-au-ui-safe");
      if(result?.error)throw Error(result.error);
      if(safeGoogleStatus)safeGoogleStatus.textContent=
        "EXISTING GOOGLE WINDOW REQUESTED · PASTE EACH COPIED PROMPT INTO ITS ROW. NO RESTART.";
    }catch(error){
      if(safeGoogleStatus)safeGoogleStatus.textContent=
        "SAFE WINDOW UNAVAILABLE · "+(error?.message||error)+" · NO RESTART ATTEMPTED.";
    }
  });

  nativeApply?.addEventListener("click",async()=>{
    if(syncing)return;
    const desired=textBank();
    if(desired.some(p=>!p||p.length>500)){
      reportNative("ALL FIVE SOUND PROMPTS MUST BE NONEMPTY AND UNDER 500 CHARACTERS.",false);
      return;
    }
    // Fail closed if current native state is unknown. A previous version
    // sent STOP before learning whether its restart would work.
    let current;
    try{
      current=await getNativeState();
      lastState=current;
    }catch(error){
      showSafeManualGuide("CANNOT CHECK GOOGLE HOST · NO STOP OR RESTART ATTEMPTED. "+(error?.message||error));
      return;
    }
    if(matchesAU(current,desired)){
      reportNative("GOOGLE AU SAVED PROMPTS ALREADY MATCH · NO RESTART. LISTEN TO VERIFY THE ACTUAL SOUND.",true);
      return;
    }
    // Most importantly: a running Google AU may already have a selected
    // mrt2_small model. Its selected model does not survive blindly
    // stopping/restarting in native model-picker mode. Keep playback,
    // captured native loops, and the Google prompt editor intact.
    if(current?.phase==="host-running" ||
       current?.audio_engine_running===true){
      showSafeManualGuide("MRT2 STILL PLAYING · NO RESTART. COPY 01–05 INTO THE CURRENT GOOGLE WINDOW; PRESS ENTER IN EACH ROW.");
      return;
    }
    if(current?.phase==="starting" || current?.phase==="initializing"){
      reportNative("MRT2 IS ALREADY INITIALIZING · NO SECOND START. CHECK AGAIN WHEN THE HOST SETTLES.",false);
      return;
    }
    if(!["inactive","failed","not-running"].includes(current?.phase)){
      showSafeManualGuide("NATIVE STATUS IS UNKNOWN · NO START/STOP ATTEMPTED. KEEP YOUR CURRENT AUDIO.");
      return;
    }
    if(Number(current?.native_memory_loop_count||0)>0){
      showSafeManualGuide("NATIVE LOOPS STILL REPORTED · NO AUTOMATIC RECONFIGURATION. EXPORT FIRST.");
      return;
    }
    // Only an IDLE host may be started with new Film prompts. There is no
    // destructive stop call anywhere in this Film-only path.
    syncing=true;
    nativeApply.disabled=true;
    reportNative("STARTING AN IDLE MRT2 HOST WITH FIVE FILM PROMPTS · NEVER STOPPING ACTIVE AUDIO…",false);
    try{
      if(typeof aiFetch!=="function")throw Error("Native TOASTER control unavailable");
      const result=await aiFetch("start",{prompts:desired});
      if(typeof aiDisplay==="function")aiDisplay(result);
      reportNative("IDLE HOST START REQUESTED · WAIT FOR GOOGLE MODEL INITIALIZATION, THEN VERIFY ITS PROMPT ROWS. AUDIO UNVERIFIED.",false);
    }catch(error){
      reportNative("SAFE START FAILED · "+(error?.message||error)+" · NO ACTIVE AUDIO WAS STOPPED.",false);
    }finally{
      syncing=false;
      nativeApply.disabled=false;
    }
  });
  for(const id of promptIds){
    document.getElementById(id)?.addEventListener("input",()=>{
      if(syncing)return;
      reportNative("FILM SOUND TEXT EDITED · APPLY TO UPDATE THE NATIVE GOOGLE HOST.",false);
    });
  }
  // Read-only verification on load: never restart the AU on page navigation.
  void refreshPromptState();
  window.setInterval?.(()=>void refreshPromptState(),5000);

  // The original full-size TOASTER prompt buttons are still present in the
  // shared DOM. In Film Club they must follow the same non-destructive path,
  // not invoke their old stop() / start() listener behind the new button.
  // Capture-phase interception keeps Futureproof /toaster/live unchanged.
  const routeLegacyApplySafely = event => {
    event.preventDefault();
    event.stopImmediatePropagation();
    return nativeApply?.click();
  };
  for(const id of ["applyPrompts","applyJazzDrumsPrompt"]){
    document.getElementById(id)?.addEventListener("click",routeLegacyApplySafely,true);
  }
  // Do not call any AI or MIDI route from this script. Native sounds are
  // changed only through the musician's existing TOASTER button workflows.
})();
