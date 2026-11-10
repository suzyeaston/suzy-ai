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
      return "GOOGLE MRT2 STARTING · WAIT FOR MODEL INITIALIZATION.";
    if(matchesAU(state,bank))
      return "GOOGLE AU SAVED THE FILM SOUND BANK · PLAY A CHORD TO VERIFY AUDIO.";
    if(!Object.prototype.hasOwnProperty.call(state||{},"google_model_bookmark_available"))
      return "OLD SWIFT HOST · REBUILD THE MAC COMPANION TO ENABLE AUTO PROMPT RELOAD.";
    if(state?.phase==="host-running" || state?.audio_engine_running===true){
      if(state?.google_model_bookmark_available===true)
        return "GOOGLE MODEL GRANTED · READY TO APPLY FILM SOUNDS AUTOMATICALLY.";
      return "ORIGINAL GOOGLE SOUNDS STILL LOADED · SELECT mrt2_small ONCE IN THE GOOGLE MODEL WINDOW, THEN APPLY.";
    }
    return "FILM SOUND BANK NOT LOADED · PRESS APPLY WHEN MRT2 IS READY.";
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
         (current?.native_model_selection_required!==true &&
          current?.model_loading_source!=="google_au_granted_bookmark")){
        if(safeGoogleStatus)safeGoogleStatus.textContent=
          "NO SAFE EDITOR · SELECT GOOGLE mrt2_small FIRST. CURRENT AUDIO WAS NOT STOPPED.";
        return;
      }
      if(typeof aiFetch!=="function")throw Error("Native host control unavailable");
      const result=await aiFetch("show-au-ui-safe");
      if(result?.error)throw Error(result.error);
      if(safeGoogleStatus)safeGoogleStatus.textContent=
        "GOOGLE MODEL WINDOW REQUESTED · VIEW ACTIVE SOUNDS WITHOUT ANOTHER RESTART.";
    }catch(error){
      if(safeGoogleStatus)safeGoogleStatus.textContent=
        "SAFE WINDOW UNAVAILABLE · "+(error?.message||error)+" · NO RESTART ATTEMPTED.";
    }
  });

  nativeApply?.addEventListener("click",async()=>{
    if(syncing)return;
    const desired=textBank();
    if(desired.some(p=>!p||p.length>500)){
      reportNative("FIVE NONEMPTY SOUND PROMPTS REQUIRED, EACH UP TO 500 CHARACTERS.",false);
      return;
    }
    let current;
    try{current=await getNativeState();lastState=current;}
    catch(error){
      reportNative("CANNOT VERIFY GOOGLE MODEL · NOTHING WAS STOPPED. "+(error?.message||error),false);
      return;
    }
    const loopCount=Number(current?.native_memory_loop_count||0);
    if(loopCount>0){
      reportNative("NATIVE AUDIO LOOPS ARE ACTIVE ("+loopCount+
        ") · EXPORT AND CLEAR THEM BEFORE RELOADING THE MODEL. NOTHING STOPPED.",false);
      return;
    }
    const running=current?.phase==="host-running"&&
      current?.audio_engine_running===true;
    const idle=["inactive","not-running","failed"].includes(current?.phase);
    if(!running&&!idle){
      reportNative("GOOGLE MRT2 IS STILL STARTING OR UNAVAILABLE · NO RESTART ATTEMPTED.",false);
      return;
    }
    if(running && current?.google_model_bookmark_available!==true){
      reportNative("GOOGLE'S MODEL BOOKMARK IS MISSING · SELECT mrt2_small ONCE IN THE ORIGINAL GOOGLE WINDOW, THEN CLICK APPLY AGAIN. NO AUDIO WAS STOPPED.",false);
      return;
    }
    // The Swift companion requires a model-granted security bookmark
    // BEFORE stopping any playing AU. It then loads a NEW instance with
    // that bookmark AND all five Film prompt texts at model initialization.
    // This is Google MRT2 output, not a browser oscillator substitute.
    if(running&&!window.confirm(
      "Replace Google's selected MRT2 model instance with the FIVE Film Club sounds? "+
      "This briefly interrupts AI playback. Export unsaved audio takes first. Continue?"
    )){
      reportNative("RELOAD CANCELLED · THE ORIGINAL GOOGLE AUDIO KEEPS PLAYING.",false);
      return;
    }
    syncing=true;nativeApply.disabled=true;
    reportNative(running?
      "RELOADING GOOGLE MRT2 WITH ITS OWN GRANTED MODEL BOOKMARK AND FILM PROMPTS…":
      "STARTING GOOGLE MRT2 WITH FILM PROMPTS…",false);
    try{
      if(typeof aiFetch!=="function")throw Error("Original native AI bridge unavailable");
      const started=await aiFetch(running?"reload-prompts":"start",{prompts:desired});
      if(started?.error)throw Error(started.error);
      if(typeof aiDisplay==="function")aiDisplay(started);
      let result=started,verified=false;
      for(let attempt=0;attempt<40;attempt++){
        result=await getNativeState();
        lastState=result;
        if(result?.error && result?.phase!=="host-running")
          throw Error(result.error);
        if(result?.phase==="host-running"&&matchesAU(result,desired)){
          verified=true;
          break;
        }
        if(result?.phase==="failed")throw Error(result?.error||"Native AU failed to restart");
        await new Promise(resolve=>window.setTimeout(resolve,500));
      }
      if(verified){
        reportNative("FIVE FILM CLUB PROMPTS SAVED IN GOOGLE'S AU · PLAY A CHORD TO VERIFY THE NEW SOUND. EMBEDDINGS AND AUDIO NOT AUTOMATICALLY VERIFIED.",true);
      }else{
        reportNative("GOOGLE RELOAD REQUESTED BUT FULL BANK IS NOT VERIFIED YET · CHECK MODEL/OUTPUT STATUS AND TRY AGAIN ONLY AFTER STARTUP FINISHES.",false);
      }
    }catch(error){
      reportNative("GOOGLE PROMPT RELOAD FAILED · "+(error?.message||error)+
        " · CHECK MODEL STATUS; NO FALSE AUDIO SUCCESS CLAIM.",false);
    }finally{
      syncing=false;nativeApply.disabled=false;
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
  // shared DOM. In Film Club they must use the bookmark-validated reload
  // action, not the original blind stop/start listener.
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
