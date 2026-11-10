/* PYRAMID / SOFT RESET: film-specific enhancement ONLY.
 * The actual live loop, audio, mic, Magenta and transport code come from
 * suzy_ai/music/toaster_play.html. Do not build a second loop scheduler here.
 */
(() => {
  "use strict";
  const button = document.getElementById("filmExportCues");
  const status = document.getElementById("filmPromptStatus");
  if (!button || !status) return;

  // Film Club is a new page, with its own browser loop memory. Choose a
  // denser original local groove without modifying Futureproof defaults or
  // restarting the shared native Magenta model. The drum metre stays 4/4.
  if(typeof setDrumGroove==="function" && typeof stageStarted!=="undefined" && !stageStarted){
    setDrumGroove("4/4","drive");
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
      composition:"Pyramid / Soft Reset (Film Club continuation)",
      duration_sec:60,
      harmony_reference:["F♯","Gmaj7","A6","F♯"],
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
  function reportNative(message,verified=false) {
    if(nativeState)nativeState.textContent=message;
    if(status)status.textContent=verified?
      "HOST REPORTS FILM PROMPTS · GOOGLE UI STILL NEEDS VISUAL CHECK":
      "FILM TEXT READY · NATIVE HOST NOT VERIFIED";
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
      if(matchesHost(state)) {
        if(state.phase==="host-running" && state.audio_engine_running===true){
          reportNative("✓ NATIVE HOST REPORTS ALL FIVE FILM PROMPTS. CLOSE/REOPEN GOOGLE AU WINDOW IF IT STILL SHOWS OLD TEXT.",true);
        }else{
          reportNative("FILM PROMPTS CONFIGURED IN HOST · model still starting. Verify Google window after loading.",false);
        }
      }else if(Array.isArray(state.text_prompts)) {
        reportNative("OLD OR EDITED SOUND BANK ACTIVE IN MRT2 · CLICK APPLY FILM CLUB SOUNDS TO MRT2.",false);
      }else{
        reportNative("NATIVE HOST NOT READY · NO PROMPT READBACK YET. APPLY WHEN READY.",false);
      }
    }catch(err){
      reportNative("CANNOT VERIFY MRT2 BANK · "+(err?.message||err),false);
    }
  }
  nativeApply?.addEventListener("click",async()=>{
    if(syncing)return;
    const desired=textBank();
    if(desired.some(p=>!p||p.length>500)){
      reportNative("ALL FIVE SOUND PROMPTS MUST BE NONEMPTY AND UNDER 500 CHARACTERS.",false);
      return;
    }
    let old;
    try{old=await getNativeState();lastState=old;}catch{old=null;}
    if(old?.phase==="host-running"&&matchesHost(old,desired)){
      reportNative("✓ THE HOST ALREADY REPORTS THESE FIVE PROMPTS · NO RESTART NEEDED. REFRESH THE GOOGLE UI IF ITS DISPLAY IS STALE.",true);
      return;
    }
    const loopCount=Number(old?.native_memory_loop_count||0);
    const safety=loopCount>0?
      "The shared native host reports "+loopCount+" active in-memory loop(s). This restart can stop them. EXPORT your recordings first.\n\n":
      "This can stop native in-memory audio loops. EXPORT important takes first.\n\n";
    if(!window.confirm(safety+
      "Apply all FIVE Film Club prompts to the shared Google MRT2 Audio Unit now?")){
      reportNative("APPLY CANCELLED · NATIVE MODEL LEFT UNCHANGED.",false);
      return;
    }
    syncing=true;nativeApply.disabled=true;
    reportNative("RESTARTING SHARED MRT2 AND SENDING FIVE FILM PROMPTS…",false);
    try{
      // Use the existing, tested TOASTER stop/start path, which configures
      // prompts before the Swift host's AU model initialization.
      if(typeof applyPrompts!=="function")throw Error("Original TOASTER prompt control unavailable");
      await applyPrompts();
      let result=null;
      for(let attempt=0;attempt<15;attempt++){
        result=await getNativeState();
        lastState=result;
        if(matchesHost(result,desired))break;
        await new Promise(resolve=>window.setTimeout(resolve,400));
      }
      if(matchesHost(result,desired)){
        reportNative(result.phase==="host-running" && result.audio_engine_running===true?
          "✓ NATIVE HOST VERIFIED: FIVE FILM CLUB PROMPTS. GOOGLE'S POPUP MAY BE STALE; CLOSE/REOPEN IT TO CHECK.":
          "✓ FIVE FILM PROMPTS RECEIVED BY HOST; MRT2 STILL LOADING. VERIFY IN GOOGLE WINDOW WHEN READY.",
          result.phase==="host-running" && result.audio_engine_running===true);
      }else{
        reportNative("NOT VERIFIED · NATIVE HOST DID NOT REPORT THE NEW BANK. CHECK THE AI HOST STATUS BEFORE RECORDING.",false);
      }
    }catch(error){
      reportNative("PROMPT SYNC FAILED · "+(error?.message||error),false);
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

  // Applying Film Club text needs the existing native host stop/start, which
  // can erase its in-RAM AU loops. Require explicit approval every time.
  // Browser loops are not moved to this Film Club tab from a previous tab.
  const warnBeforeApply = event => {
    if (!window.confirm(
      "Changing these five Film Club Magenta prompts will restart the shared native AU and may stop unsaved native audio loops. Export important takes first. Continue?"
    )) {
      event.preventDefault();
      event.stopImmediatePropagation();
      status.textContent="PROMPT APPLY CANCELLED · native host left unchanged";
      return;
    }
    status.textContent="APPLYING TO SHARED MAGENTA HOST · original source presets remain in Futureproof page";
  };
  for(const id of ["applyPrompts","applyJazzDrumsPrompt"]){
    const target=document.getElementById(id);
    if(target)target.addEventListener("click",warnBeforeApply,true);
  }
  // Do not call any AI or MIDI route from this script. Native sounds are
  // changed only through the musician's existing TOASTER button workflows.
})();
