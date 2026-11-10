"use strict";
const test=require("node:test"),assert=require("node:assert/strict");
const fs=require("node:fs"),path=require("node:path"),vm=require("node:vm");
const source=fs.readFileSync(path.join(__dirname,"..","performance","film-club-2026","film-club.js"),"utf8");
const names=["promptPyramid","promptFishes","promptViolin","promptGuitar","promptJazzDrums"];
const desired=["film piano","film cello","film violin","film glass","film breakbeat"];
const defaults=()=>Array.from({length:5},(_,i)=>"Futureproof "+i);

function harness({active=defaults(),auActive,confirm=true,applied=true,applyAu=true,
   phase="host-running",loops=0,legacy=false,startFails=false}={}){
  let calls=0,confirmText="",requests=0,copied="";
  let bank=active.slice(),actual=Array.isArray(auActive)?auActive.slice():active.slice();
  const el=(value="")=>({
    value,textContent:"",disabled:false,callbacks:{},dataset:{},
    focus(){this.focused=true},select(){this.selected=true},
    addEventListener(name,callback){this.callbacks[name]=callback;},
    async click(){return await this.callbacks.click?.({preventDefault(){},stopImmediatePropagation(){}});}
  });
  const dom=new Map();
  for(const [index,id] of names.entries())dom.set(id,el(desired[index]));
  for(const id of ["filmExportCues","filmPromptStatus","filmSyncNativePrompts",
                   "filmNativePromptStatus","filmCopyStatus"])dom.set(id,el());
  const buttons=names.map((id,i)=>{
    const b=el();b.dataset.promptCopy=id;b.textContent="COPY "+(i+1);return b;
  });
  const document={
    getElementById:id=>dom.get(id)||null,
    querySelectorAll:sel=>sel==="[data-prompt-copy]"?buttons:[],
    body:{appendChild(){}}
  };
  const window={
    confirm(msg){confirmText=msg;return confirm;},
    setTimeout(fn){fn();return 1;},
    setInterval(){return 1;}
  };
  const sandbox={
    window,document,console,Promise,URL,Blob,
    navigator:{clipboard:{writeText:async text=>{copied=text;}}},
    fetch:async url=>{
      requests++;assert.equal(url,"/api/ai/status");
      const state={phase,audio_engine_running:phase==="host-running",
        native_memory_loop_count:loops,text_prompts:bank.slice()};
      if(!legacy)Object.assign(state,{
        au_prompt_readback_available:true,au_prompt_texts:actual.slice(),
        au_prompt_bank_matches_host:JSON.stringify(actual)===JSON.stringify(bank),
        au_prompt_embeddings_verified:false
      });
      return {ok:true,json:async()=>state};
    },
    aiFetch:async(action,data={})=>{
      if(action==="stop")return {phase:"inactive"};
      if(action!=="start")throw Error("Unexpected native operation "+action);
      calls++;
      if(startFails)throw Error("MRT2 model could not initialize");
      if(applied){bank=Array.from(data.prompts);if(applyAu)actual=bank.slice();}
      return {phase, audio_engine_running:phase==="host-running"};
    },
    aiDisplay:()=>{},syncAIMix:async()=>{},
    setDrumGroove(){},stageStarted:false
  };
  vm.runInNewContext(source,sandbox,{filename:"film-club.js"});
  const settle=()=>new Promise(resolve=>setImmediate(resolve));
  return {dom,buttons,window,settle,
    async click(){await dom.get("filmSyncNativePrompts").click();},
    get calls(){return calls},get requests(){return requests},
    get bank(){return bank},get actual(){return actual},
    get copied(){return copied},get confirmText(){return confirmText}};
}
test("read-only startup detects original host prompts without updating the AU",async()=>{
 const h=harness({loops:2});await h.settle();
 assert.equal(h.calls,0);assert.ok(h.requests>=1);
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/HOST STILL HAS OLDER PROMPTS/);
 assert.match(h.dom.get("filmPromptStatus").textContent,/GOOGLE AU SOUND BANK NOT CONFIRMED/);
});
test("real AU serialized readback is distinct from requested Swift host strings",async()=>{
 const h=harness({active:desired,auActive:defaults()});await h.settle();
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/AU STILL REPORTS OLD TEXT/);
 assert.doesNotMatch(h.dom.get("filmNativePromptStatus").textContent,/PROMPTS MATCH/);
});
test("explicit apply checks AU's own MGRT_Prompts, but does not claim actual embeddings are verified",async()=>{
 const h=harness({loops:3});await h.settle();await h.click();
 assert.equal(h.calls,1);assert.match(h.confirmText,/3 active in-memory loop/);
 assert.deepEqual(h.bank,desired);assert.deepEqual(h.actual,desired);
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/AU SERIALIZED PROMPTS MATCH/);
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/DOES NOT PROVE GOOGLE'S MODEL/);
 assert.equal(h.dom.get("filmSyncNativePrompts").disabled,false);
});
test("cancellation does not replace a running native bank",async()=>{
 const h=harness({confirm:false});await h.settle();await h.click();
 assert.equal(h.calls,0);assert.match(h.dom.get("filmNativePromptStatus").textContent,/APPLY CANCELLED/);
 assert.deepEqual(h.actual,defaults());
});
test("fully matching AU state does not trigger a needless restart",async()=>{
 const h=harness({active:desired});await h.settle();await h.click();
 assert.equal(h.calls,0);assert.match(h.dom.get("filmNativePromptStatus").textContent,/NO RESTART/);
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/GOOGLE'S VISIBLE SOUND BANK MAY STILL BE OLD/);
});
test("host text match but AU mismatch does not skip the explicit apply attempt",async()=>{
 const h=harness({active:desired,auActive:defaults()});await h.settle();await h.click();
 assert.equal(h.calls,1);assert.deepEqual(h.actual,desired);
});
test("host accepts new text but AU rejects it: no false verification",async()=>{
 const h=harness({applyAu:false});await h.settle();await h.click();
 assert.equal(h.calls,1);assert.deepEqual(h.bank,desired);assert.deepEqual(h.actual,defaults());
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/AU STILL REPORTS OLD TEXT/);
 assert.doesNotMatch(h.dom.get("filmNativePromptStatus").textContent,/AU SERIALIZED PROMPTS MATCH/);
});
test("legacy native executable without AU readback is flagged for rebuild",async()=>{
 const h=harness({active:desired,legacy:true});await h.settle();
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/OLD SWIFT HOST BINARY/);
});
test("copy button transfers exact edited prompt into Google without native API calls",async()=>{
 const h=harness();await h.settle();
 h.dom.get("promptViolin").value="new original expressive modal violin";
 await h.buttons[2].click();
 assert.equal(h.copied,"new original expressive modal violin");
 assert.equal(h.calls,0);
 assert.match(h.dom.get("filmCopyStatus").textContent,/PASTE INTO MATCHING ROW/);
});
test("editing visible prompt invalidates apparent match until applied again",async()=>{
 const h=harness({active:desired});await h.settle();
 const piano=h.dom.get("promptPyramid");
 piano.value="completely different film piano";piano.callbacks.input();
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/FILM SOUND TEXT EDITED/);
 assert.match(h.dom.get("filmPromptStatus").textContent,/GOOGLE AU SOUND BANK NOT CONFIRMED/);
 await h.click();assert.equal(h.calls,1);assert.equal(h.bank[0],"completely different film piano");
});

test("native apply errors are shown instead of swallowed as success",async()=>{
 const h=harness({startFails:true});await h.settle();await h.click();
 assert.equal(h.calls,1);
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/PROMPT SYNC FAILED/);
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/could not initialize/);
 assert.deepEqual(h.bank,defaults(),"failed native apply does not change host bank");
});
test("starting Google host is not mislabelled as an old sound bank",async()=>{
 const h=harness({phase:"initializing"});await h.settle();
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/HOST IS STARTING/);
 assert.doesNotMatch(h.dom.get("filmNativePromptStatus").textContent,/OLDER PROMPTS/);
});
