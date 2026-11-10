/* Film Club native AU sound auditor / performer controls.
 * Keeps the original TOASTER live-looper, prompts, beat clock and existing
 * native PCM clips untouched. There is ONE MRT2 AU, not five audio stems.
 */
(() => {
  "use strict";
  const status = document.getElementById("filmAuditionStatus");
  const blend = document.getElementById("filmAuditionBlend");
  const buttons = [...document.querySelectorAll("[data-film-audition]")];
  if(!status || !blend || buttons.length !== 5) return;

  const slots = Object.freeze({
    piano:  {which:"pyramid",role:"chords",index:0},
    cello:  {which:"pyramid",role:"textureLow",index:1},
    violin: {which:"pyramid",role:"lead",index:2},
    glass:  {which:"pyramid",role:"textureHigh",index:3},
    drums:  {which:"drums",role:"drums",index:4}
  });
  let busy = false;

  function label(weights){
    if(!Array.isArray(weights)||weights.length!==5)
      return "Google prompt weights unavailable. Open MRT2, then audition a chord.";
    const names=["PIANO","CELLO","VIOLIN","GLASS","DRUMS"];
    return names.map((n,i)=>n+" "+Math.round(Number(weights[i]||0)*100)+"%").join(" · ");
  }

  function readState(){
    return fetch("/api/ai/status",{cache:"no-store"}).then(r=>{
      if(!r.ok)throw Error("Native model status unavailable");
      return r.json();
    });
  }
  function canSwitch(){
    if(typeof aiNativeReady==="undefined"||!aiNativeReady){
      status.textContent="START GOOGLE MRT2 FIRST, SELECT mrt2_small, THEN PLAY A CHORD.";
      return false;
    }
    if((typeof nativeTake!=="undefined"&&nativeTake) ||
       (typeof nativeTakeArming!=="undefined"&&nativeTakeArming)){
      status.textContent="FINISH THE ACTIVE RECORDING BEFORE CHANGING MRT2 SOUND.";
      return false;
    }
    return true;
  }
  function setBusy(value){
    busy=value;
    for(const b of [...buttons,blend])b.disabled=value;
  }
  function mark(name){
    for(const b of buttons)b.setAttribute("aria-pressed",String(b.dataset.filmAudition===name));
    blend.setAttribute("aria-pressed",String(name==="ensemble"));
  }
  async function display(expectIndex=null,ensemble=false){
    const state=await readState();
    const weights=state.prompt_weights;
    if(!Array.isArray(weights)||weights.length!==5)
      throw Error("Native AU did not report five prompt weights");
    const values=weights.map(v=>Number(v)||0);
    const suffix=label(values);
    if(ensemble){
      if(values.every(v=>v>.05)){
        status.textContent="FIVE PROMPTS WEIGHTED IN ONE GENERATOR · "+suffix+
          " · PLAY Z/X/C TO AUDITION, RECORD SEPARATE TAKES FOR REAL LAYERS";
        return true;
      }
      status.textContent="BLEND REQUESTED BUT NOT ALL FIVE WEIGHTS WERE CONFIRMED · "+suffix;
      return false;
    }
    if(expectIndex!==null){
      if(values[expectIndex]>.80){
        status.textContent="SELECTED "+Object.keys(slots)[expectIndex].toUpperCase()+
          " · "+suffix+" · NOW PLAY Z/X/C OR RECORD ITS NATIVE TAKE";
        return true;
      }
      status.textContent="SELECTED ROLE, BUT GOOGLE AU WEIGHTS DID NOT CONFIRM IT · "+suffix;
      return false;
    }
    const on=values.map((v,i)=>v>.05?i:-1).filter(x=>x>=0);
    status.textContent=(on.length===1?
      "ONLY "+Object.keys(slots)[on[0]].toUpperCase()+" IS WEIGHTED. USE HEAR / BLEND TO CHANGE. ":
      "NATIVE PROMPT MIX: ")+suffix+
      " · NO NEW PCM STEMS UNTIL YOU RECORD THEM";
    return true;
  }

  for(const b of buttons){
    b.setAttribute("aria-pressed","false");
    b.addEventListener("click",async()=>{
      if(busy||!canSwitch())return;
      const name=b.dataset.filmAudition;
      const slot=slots[name];
      if(!slot)return;
      if(typeof selectNativeLane!=="function"){
        status.textContent="ORIGINAL TOASTER NATIVE INSTRUMENT CONTROL UNAVAILABLE.";
        return;
      }
      setBusy(true);
      status.textContent="SELECTING "+name.toUpperCase()+" IN THE SHARED MRT2 GENERATOR…";
      try{
        await selectNativeLane(slot.which,slot.role);
        const ok=await display(slot.index,false);
        mark(ok?name:"");
      }catch(e){
        mark("");
        status.textContent="FAILED TO SELECT "+name.toUpperCase()+" · "+(e?.message||e);
      }finally{setBusy(false);}
    });
  }

  blend.setAttribute("aria-pressed","false");
  blend.addEventListener("click",async()=>{
    if(busy||!canSwitch())return;
    if(typeof aiFetch!=="function"){
      status.textContent="NATIVE HOST CONTROL UNAVAILABLE.";
      return;
    }
    setBusy(true);
    status.textContent="SETTING NONZERO WEIGHTS FOR ALL FIVE GOOGLE PROMPTS…";
    try{
      if(typeof aiCommandQueue!=="undefined")await aiCommandQueue.catch(()=>{});
      // This preview adjusts MODEL PROMPT WEIGHTS. It cannot spawn independent
      // stems; recordings made via the existing native pedals are PCM layers.
      // Leave all previous saved take buffers and rhythm transport untouched.
      if(typeof activePyramidTextureRole!=="undefined")activePyramidTextureRole=null;
      if(typeof chordAuditionScene!=="undefined")chordAuditionScene=null;
      if(typeof aiDrumsAllowed!=="undefined")aiDrumsAllowed=true;
      const changes=[
        ["mix",{value:.42}],
        ["lead-mix",{scene:"pyramid",value:.38}],
        ["lead-mix",{scene:"fishes",value:.45}],
        ["drums",{value:true}],
        ["drum-mix",{value:.15}]
      ];
      for(const [action,payload] of changes)await aiFetch(action,payload);
      const ui=[
        ["aiLeadMix-pyramid","38"],
        ["aiLeadMix-fishes","45"],["aiDrumMix","15"]
      ];
      for(const [id,value] of ui){
        const field=document.getElementById(id);if(field)field.value=value;
      }
      for(const [id,value] of [
        ["aiLeadMixValue-pyramid","CHORDS 62% · LEAD 38%"],
        ["aiLeadMixValue-fishes","CHORDS 55% · LEAD 45%"],
        ["aiDrumMixValue","15%"]
      ]){
        const field=document.getElementById(id);if(field)field.textContent=value;
      }
      // The native-only blend is a temporary timbre audition: don't modify
      // the browser song crossfader, which mixes already-recorded PCM.
      // Re-select an instrument to leave this blend mode. The two lead and
      // drum controls above reflect the request, and status readback is
      // authoritative.
      const allow=document.getElementById("aiDrums");
      if(allow){
        allow.setAttribute("aria-pressed","true");
        allow.textContent="🥁 AI DRUM AUDIO ALLOWED";
      }
      // Existing syncAIMix may run again later; keep its controls truthful.
      const ok=await display(null,true);
      mark(ok?"ensemble":"");
    }catch(e){
      mark("");
      status.textContent="NATIVE ENSEMBLE BLEND FAILED · "+(e?.message||e);
    }finally{setBusy(false);}
  });

  // Reading status never mutates native weights, source clips or prompts.
  // Playback requires the performer's existing keyboard or chord-pad action.
  void display().catch(e=>{
    status.textContent="NATIVE AUDITION STATUS UNAVAILABLE · "+(e?.message||e);
  });
})();
