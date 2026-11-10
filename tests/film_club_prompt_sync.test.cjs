"use strict";
const test=require("node:test"),assert=require("node:assert/strict");
const fs=require("node:fs"),path=require("node:path"),vm=require("node:vm");
const source=fs.readFileSync(path.join(__dirname,"..","performance","film-club-2026","film-club.js"),"utf8");
const names=["promptPyramid","promptFishes","promptViolin","promptGuitar","promptJazzDrums"];
const desired=["neon FM piano","rubbery analog bass","supersaw lead","granular glass","glitch club drums"];
const defaults=()=>Array.from({length:5},(_,i)=>"Futureproof "+i);
function harness({bank=defaults(),auBank,bookmark=true,phase="host-running",engine,
  loops=0,confirm=true,failReload=false,failStatus=false,applyAu=true,
  legacy=false,modelSource="native_google_au_ui",rejectEditor=false}={}){
  let host=Array.from(bank),actual=auBank?Array.from(auBank):Array.from(bank);
  let currentPhase=phase,currentEngine=engine??phase==="host-running";
  const calls=[],events={confirms:0,scrolls:0,legacyFired:0};
  let copied="";
  const el=(value="")=>({
    value,textContent:"",disabled:false,handlers:{},dataset:{},
    focus(){this.focused=true},select(){this.selected=true},
    scrollIntoView(){events.scrolls++},
    setAttribute(){},
    addEventListener(name,callback,capture=false){(this.handlers[name]??=[]).push({callback,capture:!!capture})},
    async click(){
      let stopped=false;
      const event={preventDefault(){this.defaultPrevented=true},stopImmediatePropagation(){stopped=true}};
      const entries=[...(this.handlers.click||[])].sort((a,b)=>Number(b.capture)-Number(a.capture));
      for(const entry of entries){if(stopped)break;await entry.callback(event)}
    }
  });
  const dom=new Map();
  names.forEach((id,i)=>dom.set(id,el(desired[i])));
  for(const id of ["filmExportCues","filmPromptStatus","filmSyncNativePrompts",
    "filmNativePromptStatus","filmCopyStatus","filmManualBridge","filmOpenGooglePrompts",
    "filmGoogleEditorStatus","applyPrompts","applyJazzDrumsPrompt"])dom.set(id,el());
  const copyButtons=names.map((id,i)=>{
    const item=el();item.dataset.promptCopy=id;item.textContent="COPY "+(i+1);return item;
  });
  const document={
    getElementById:id=>dom.get(id)||null,
    querySelectorAll:selector=>selector==="[data-prompt-copy]"?copyButtons:[],
    body:{appendChild(){}}
  };
  const window={
    setTimeout(fn){fn();return 1},setInterval(){return 1},
    confirm(){events.confirms++;return confirm}
  };
  const sandbox={
    window,document,Promise,URL,Blob,console,
    navigator:{clipboard:{async writeText(v){copied=v}}},
    stageStarted:false,setDrumGroove(){},
    async fetch(url){
      assert.equal(url,"/api/ai/status");
      if(failStatus)throw Error("Native status unavailable");
      const state={phase:currentPhase,audio_engine_running:currentEngine,
        model_loading_source:modelSource,
        google_model_bookmark_available:bookmark,
        native_model_selection_required:modelSource==="native_google_au_ui",
        native_memory_loop_count:loops,text_prompts:host.slice()};
      if(!legacy)Object.assign(state,{
        au_prompt_readback_available:currentEngine,
        au_prompt_texts:currentEngine?actual.slice():[],
        au_prompt_embeddings_verified:false
      });
      else delete state.google_model_bookmark_available;
      return {ok:true,async json(){return state}};
    },
    async aiFetch(action,data={}){
      calls.push(action);
      if(action==="stop")throw Error("BUG: blind STOP attempted");
      if(action==="reload-prompts"){
        if(!currentEngine||!bookmark||loops)throw Error("Should not invoke reload without saved model bookmark");
        if(failReload)throw Error("Google model reload failed");
        host=Array.from(data.prompts);
        if(applyAu)actual=host.slice();
        return {phase:"initializing"};
      }
      if(action==="start"){
        if(currentEngine)throw Error("BUG: duplicate model start");
        if(failReload)throw Error("Cannot start");
        host=Array.from(data.prompts);
        currentPhase="host-running";currentEngine=true;
        if(applyAu)actual=host.slice();
        return {phase:"initializing"};
      }
      if(action==="show-au-ui-safe"){
        if(rejectEditor)throw Error("Safe editor refused");
        return {native_au_ui_visible:true};
      }
      throw Error("Unexpected native operation "+action);
    },
    aiDisplay(){},syncAIMix:async()=>{}
  };
  vm.runInNewContext(source,sandbox,{filename:"film-club.js"});
  return {dom,copyButtons,calls,events,settle:()=>new Promise(resolve=>setImmediate(resolve)),
    async apply(){await dom.get("filmSyncNativePrompts").click()},
    async openEditor(){await dom.get("filmOpenGooglePrompts").click()},
    get bank(){return host},get actual(){return actual},
    get copied(){return copied}};
}
test("opening Film Club does not mutate the existing Futureproof AU",async()=>{
 const h=harness();await h.settle();
 assert.deepEqual(h.calls,[]);
 assert.deepEqual(h.actual,defaults());
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/READY TO APPLY FILM SOUNDS AUTOMATICALLY/);
});
test("apply uses Google's trusted model reload instead of blind stop/start",async()=>{
 const h=harness();await h.settle();await h.apply();
 assert.deepEqual(h.calls,["reload-prompts"]);
 assert.deepEqual(h.bank,desired);assert.deepEqual(h.actual,desired);
 assert.equal(h.events.confirms,1);
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/FIVE FILM CLUB PROMPTS SAVED/);
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/NOT AUTOMATICALLY VERIFIED/);
});
test("no Google bookmark means no destructive action or manual prompt copying",async()=>{
 const h=harness({bookmark:false});await h.settle();await h.apply();
 assert.deepEqual(h.calls,[]);
 assert.equal(h.events.confirms,0);
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/SELECT mrt2_small ONCE/);
 assert.equal(h.events.scrolls,0);
});
test("native loops block model replacement until the user exports takes",async()=>{
 const h=harness({loops:2});await h.settle();await h.apply();
 assert.deepEqual(h.calls,[]);
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/EXPORT AND CLEAR/);
});
test("user can cancel automatic model replacement without affecting audio",async()=>{
 const h=harness({confirm:false});await h.settle();await h.apply();
 assert.deepEqual(h.calls,[]);
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/RELOAD CANCELLED/);
});
test("a native model already initializing is not started again",async()=>{
 const h=harness({phase:"initializing",engine:false});await h.settle();await h.apply();
 assert.deepEqual(h.calls,[]);
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/STILL STARTING/);
});
test("inactive host may start with all five new sounds, without stop",async()=>{
 const h=harness({phase:"inactive",engine:false});await h.settle();await h.apply();
 assert.deepEqual(h.calls,["start"]);assert.deepEqual(h.bank,desired);
 assert.equal(h.events.confirms,0);
});
test("failure to contact the host does not initiate an unverified restart",async()=>{
 const h=harness({failStatus:true});await h.settle();await h.apply();
 assert.deepEqual(h.calls,[]);
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/NOTHING WAS STOPPED/);
});
test("reload command errors are visible instead of claiming new audio works",async()=>{
 const h=harness({failReload:true});await h.settle();await h.apply();
 assert.deepEqual(h.calls,["reload-prompts"]);
 assert.deepEqual(h.actual,defaults());
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/GOOGLE PROMPT RELOAD FAILED/);
});
test("new saved text with old host labels is still not claimed as audible proof",async()=>{
 const h=harness({bank:defaults(),auBank:desired});await h.settle();
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/SAVED THE FILM SOUND BANK/);
 assert.deepEqual(h.calls,[]);
});
test("Google fullState mismatch cannot falsely verify new embeddings",async()=>{
 const h=harness({applyAu:false});await h.settle();await h.apply();
 assert.deepEqual(h.calls,["reload-prompts"]);
 assert.deepEqual(h.bank,desired);assert.deepEqual(h.actual,defaults());
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/NOT VERIFIED YET/);
});
test("native editor can reopen after Google's own granted bookmark was reused",async()=>{
 const h=harness({modelSource:"google_au_granted_bookmark"});await h.settle();await h.openEditor();
 assert.deepEqual(h.calls,["show-au-ui-safe"]);
});
test("native safe editor errors do not cause a blind restart",async()=>{
 const h=harness({rejectEditor:true});await h.settle();await h.openEditor();
 assert.deepEqual(h.calls,["show-au-ui-safe"]);
 assert.match(h.dom.get("filmGoogleEditorStatus").textContent,/NO RESTART ATTEMPTED/);
});
test("legacy apply buttons delegate to the bookmark-validated operation",async()=>{
 const h=harness();await h.settle();
 for(const id of ["applyPrompts","applyJazzDrumsPrompt"]){
   h.dom.get(id).addEventListener("click",()=>h.events.legacyFired++);
 }
 await h.dom.get("applyPrompts").click();
 await h.dom.get("applyJazzDrumsPrompt").click();
 assert.equal(h.events.legacyFired,0);
 assert.deepEqual(h.calls,["reload-prompts","reload-prompts"]);
});
test("manual text copying remains an optional fallback, not a prerequisite",async()=>{
 const h=harness();await h.settle();
 h.dom.get("promptViolin").value="original digital lead";
 await h.copyButtons[2].click();
 assert.equal(h.copied,"original digital lead");
 assert.deepEqual(h.calls,[]);
});
test("legacy native binary without bookmark field must be rebuilt",async()=>{
 const h=harness({legacy:true});await h.settle();
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/OLD SWIFT HOST/);
});
