"use strict";
const test=require("node:test"),assert=require("node:assert/strict");
const fs=require("node:fs"),path=require("node:path"),vm=require("node:vm");
const source=fs.readFileSync(path.join(__dirname,"..","performance","film-club-2026","film-club.js"),"utf8");
const names=["promptPyramid","promptFishes","promptViolin","promptGuitar","promptJazzDrums"];
const desired=["film piano","film cello","film violin","film glass","film breakbeat"];
const defaults=()=>Array.from({length:5},(_,i)=>"Futureproof "+i);

function harness({active=defaults(),auActive,phase="host-running",engine,
   googleMode=true,loops=0,legacy=false,failStatus=false,failStart=false,
   failEditor=false}={}){
  const calls=[],events={scrolls:0,confirms:0,legacyFired:0};
  let requests=0,copied="",bank=active.slice();
  let actual=Array.isArray(auActive)?auActive.slice():active.slice();
  let currentPhase=phase, audioEngine=engine??phase==="host-running";
  const el=(value="")=>({
    value,textContent:"",disabled:false,dataset:{},handlers:{},
    focus(){this.focused=true},select(){this.selected=true},
    scrollIntoView(){events.scrolls++},
    setAttribute(){},
    addEventListener(name,callback,capture=false){
      (this.handlers[name]??=[]).push({callback,capture:!!capture});
    },
    async click(){
      let stopped=false;
      const event={preventDefault(){this.defaultPrevented=true},
        stopImmediatePropagation(){stopped=true}};
      const handlers=this.handlers.click||[];
      for(const item of [...handlers].sort((a,b)=>Number(b.capture)-Number(a.capture))){
        if(stopped)break;
        await item.callback(event);
      }
    }
  });
  const dom=new Map();
  for(const [index,id] of names.entries())dom.set(id,el(desired[index]));
  for(const id of ["filmExportCues","filmPromptStatus","filmSyncNativePrompts",
    "filmNativePromptStatus","filmCopyStatus","filmManualBridge",
    "filmOpenGooglePrompts","filmGoogleEditorStatus","applyPrompts",
    "applyJazzDrumsPrompt"]){dom.set(id,el());}
  const buttons=names.map((id,i)=>{
    const button=el();
    button.dataset.promptCopy=id;
    button.textContent="COPY "+(i+1);
    return button;
  });
  const document={
    getElementById:id=>dom.get(id)||null,
    querySelectorAll:selector=>selector==="[data-prompt-copy]"?buttons:[],
    body:{appendChild(){}}
  };
  const window={
    setTimeout:fn=>{fn();return 1},
    setInterval:()=>1,
    confirm(){events.confirms++;return true}
  };
  const sandbox={
    document,window,Promise,console,URL,Blob,
    navigator:{clipboard:{writeText:async value=>{copied=value}}},
    stageStarted:false,setDrumGroove(){},
    fetch:async url=>{
      assert.equal(url,"/api/ai/status");
      requests++;
      if(failStatus)throw Error("Native host unavailable");
      const state={phase:currentPhase,audio_engine_running:audioEngine,
        native_model_selection_required:googleMode,
        native_memory_loop_count:loops,text_prompts:bank.slice()};
      if(!legacy)Object.assign(state,{
        au_prompt_readback_available:audioEngine,
        au_prompt_texts:audioEngine?actual.slice():[],
        au_prompt_bank_matches_host:JSON.stringify(actual)===JSON.stringify(bank),
        au_prompt_embeddings_verified:false
      });
      return {ok:true,json:async()=>state};
    },
    aiFetch:async(action,data={})=>{
      calls.push(action);
      if(action==="stop")throw Error("REGRESSION: Film Club stopped a running AU");
      if(action==="show-au-ui-safe"){
        if(failEditor)throw Error("Native safe editor unavailable");
        if(!googleMode||!audioEngine)throw Error("Opening editor would restart current audio");
        return {phase:currentPhase,native_au_ui_visible:true};
      }
      if(action!=="start")throw Error("Unexpected native action: "+action);
      if(audioEngine)throw Error("REGRESSION: start attempted while AU was running");
      if(failStart)throw Error("MRT2 model could not initialize");
      bank=Array.from(data.prompts);
      currentPhase="initializing";
      return {phase:"initializing",audio_engine_running:false};
    },
    aiDisplay(){},syncAIMix(){}
  };
  vm.runInNewContext(source,sandbox,{filename:"film-club.js"});
  return {dom,buttons,calls,events,settle:()=>new Promise(resolve=>setImmediate(resolve)),
    async apply(){await dom.get("filmSyncNativePrompts").click()},
    async openEditor(){await dom.get("filmOpenGooglePrompts").click()},
    get bank(){return bank},get actual(){return actual},get copied(){return copied},
    get requests(){return requests}};
}

test("startup detects older host prompts without touching the live audio engine",async()=>{
 const h=harness({googleMode:true});await h.settle();
 assert.equal(h.calls.length,0);
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/MRT2 IS RUNNING/);
 assert.ok(h.requests>0);
});

test("reported old Google prompts + running music: Update preserves current model and loops",async()=>{
 const h=harness({loops:3,googleMode:true});await h.settle();await h.apply();
 assert.deepEqual(h.calls,[],"no stop/start/show UI during safe prompt update");
 assert.deepEqual(h.bank,defaults());
 assert.deepEqual(h.actual,defaults());
 assert.equal(h.events.confirms,0);
 assert.equal(h.events.scrolls,1);
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/MRT2 STILL PLAYING/);
 assert.match(h.dom.get("filmCopyStatus").textContent,/COPY 01–05/);
});

test("Google AU matching edited Film text outranks the older host bank",async()=>{
 const h=harness({active:defaults(),auActive:desired,googleMode:true});
 await h.settle();
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/AU SAVED TEXT MATCHES/);
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/HOST LABEL IS OLDER/);
 await h.apply();
 assert.deepEqual(h.calls,[]);
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/NO RESTART/);
});

test("native host text matching does not hide different text in Google AU",async()=>{
 const h=harness({active:desired,auActive:defaults()});await h.settle();
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/MRT2 IS RUNNING/);
 await h.apply();
 assert.deepEqual(h.calls,[]);
 assert.equal(h.events.scrolls,1);
});

test("the real five copy buttons work without any native commands",async()=>{
 const h=harness();await h.settle();
 h.dom.get("promptViolin").value="ethereal original violin sound";
 await h.buttons[2].click();
 assert.equal(h.copied,"ethereal original violin sound");
 assert.deepEqual(h.calls,[]);
 assert.match(h.dom.get("filmCopyStatus").textContent,/PASTE INTO MATCHING ROW/);
});

test("safe Google editor opens existing model-picker session without restarting",async()=>{
 const h=harness({googleMode:true});await h.settle();await h.openEditor();
 assert.deepEqual(h.calls,["show-au-ui-safe"]);
 assert.match(h.dom.get("filmGoogleEditorStatus").textContent,/NO RESTART/);
});

test("safe editor refuses non-picker mode rather than restarting audio",async()=>{
 const h=harness({googleMode:false});await h.settle();await h.openEditor();
 assert.deepEqual(h.calls,[]);
 assert.match(h.dom.get("filmGoogleEditorStatus").textContent,/NOT IN GOOGLE PICKER MODE/);
});

test("safe editor command errors are surfaced and never trigger a restart fallback",async()=>{
 const h=harness({googleMode:true,failEditor:true});await h.settle();await h.openEditor();
 assert.deepEqual(h.calls,["show-au-ui-safe"]);
 assert.match(h.dom.get("filmGoogleEditorStatus").textContent,/NO RESTART ATTEMPTED/);
});

test("idle host starts with all five Film prompts without a stop command",async()=>{
 const h=harness({phase:"inactive",engine:false});await h.settle();await h.apply();
 assert.deepEqual(h.calls,["start"]);
 assert.deepEqual(h.bank,desired);
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/IDLE HOST START REQUESTED/);
 assert.equal(h.events.confirms,0);
});

test("native startup failures do not claim any sound is ready",async()=>{
 const h=harness({phase:"inactive",engine:false,failStart:true});
 await h.settle();await h.apply();
 assert.deepEqual(h.calls,["start"]);
 assert.deepEqual(h.bank,defaults());
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/SAFE START FAILED/);
});

test("initializing host is not restarted while a model is loading",async()=>{
 const h=harness({phase:"initializing",engine:false});await h.settle();await h.apply();
 assert.deepEqual(h.calls,[]);
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/ALREADY INITIALIZING/);
});

test("unavailable host status must never cause a blind native stop/start",async()=>{
 const h=harness({failStatus:true});await h.settle();await h.apply();
 assert.deepEqual(h.calls,[]);
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/NO STOP OR RESTART ATTEMPTED/);
});

test("legacy full-size apply buttons in Film Club cannot invoke destructive shared callback",async()=>{
 const h=harness({googleMode:true});await h.settle();
 h.dom.get("applyPrompts").addEventListener("click",()=>{h.events.legacyFired++});
 h.dom.get("applyJazzDrumsPrompt").addEventListener("click",()=>{h.events.legacyFired++});
 await h.dom.get("applyPrompts").click();
 await h.dom.get("applyJazzDrumsPrompt").click();
 assert.equal(h.events.legacyFired,0);
 assert.deepEqual(h.calls,[]);
 assert.equal(h.events.scrolls,2);
});

test("edited text invalidates the displayed verification until user copies it to Google",async()=>{
 const h=harness({active:desired,auActive:desired});await h.settle();
 const piano=h.dom.get("promptPyramid");
 piano.value="new lively sound";piano.handlers.input[0].callback();
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/TEXT EDITED/);
 await h.apply();
 assert.deepEqual(h.calls,[]);
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/MRT2 STILL PLAYING/);
});

test("old native host lacking AU readback is not treated as proof of sound",async()=>{
 const h=harness({active:desired,legacy:true,phase:"inactive",engine:false});
 await h.settle();
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/OLD SWIFT HOST BINARY/);
});
