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
