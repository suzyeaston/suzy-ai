"use strict";
const test=require("node:test"),assert=require("node:assert/strict");
const fs=require("node:fs"),path=require("node:path"),vm=require("node:vm");
const source=fs.readFileSync(path.join(__dirname,"..","performance","film-club-2026","film-club.js"),"utf8");
const names=["promptPyramid","promptFishes","promptViolin","promptGuitar","promptJazzDrums"];
const desired=["film piano","film cello","film violin","film glass","film breakbeat"];

function harness({active=Array.from({length:5},(_,i)=>"Futureproof "+i),confirm=true,
   applied=true,phase="host-running",loops=0}={}){
  let calls=0,confirmText="",requests=0;
  let bank=active.slice();
  const el=(value="")=>({
    value,textContent:"",disabled:false,callbacks:{},
    addEventListener(name,callback){this.callbacks[name]=callback;},
    async click(){return await this.callbacks.click?.({preventDefault(){},stopImmediatePropagation(){}});}
  });
  const dom=new Map();
  for(const [index,id] of names.entries())dom.set(id,el(desired[index]));
  for(const id of ["filmExportCues","filmPromptStatus","filmSyncNativePrompts","filmNativePromptStatus"])
    dom.set(id,el());
  const document={getElementById:id=>dom.get(id)||null,body:{appendChild(){}}};
  const window={
    confirm(msg){confirmText=msg;return confirm;},
    setTimeout(fn){fn();return 1;},
    setInterval(){return 1;}
  };
  let lastError=null;
  const sandbox={
    window,document,console,Promise,URL,Blob,
    fetch:async url=>{
      requests++;
      assert.equal(url,"/api/ai/status");
      return {ok:true,json:async()=>({
        phase,audio_engine_running:phase==="host-running",native_memory_loop_count:loops,
        text_prompts:bank.slice()
      })};
    },
    applyPrompts:async()=>{
      calls++;if(applied)bank=names.map(id=>dom.get(id).value.trim());
      else lastError="simulated native failure";
    },
    setDrumGroove(){},stageStarted:false
  };
  vm.runInNewContext(source,sandbox,{filename:"film-club.js"});
  const settle=()=>new Promise(resolve=>setImmediate(resolve));
  return {dom,window,settle,async click(){await dom.get("filmSyncNativePrompts").click();},
    get calls(){return calls},get requests(){return requests},
    get bank(){return bank},get confirmText(){return confirmText},
    get lastError(){return lastError}};
}

test("opening Film Club checks native prompts but never changes the Audio Unit",async()=>{
 const h=harness({loops:2});await h.settle();
 assert.equal(h.calls,0);
 assert.ok(h.requests>=1);
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/OLD OR EDITED SOUND BANK ACTIVE/);
 assert.match(h.dom.get("filmPromptStatus").textContent,/NATIVE HOST NOT VERIFIED/);
});

test("explicit apply confirms possible native-loop loss and checks all five actual host prompts",async()=>{
 const h=harness({loops:3});await h.settle();
 await h.click();
 assert.equal(h.calls,1);
 assert.match(h.confirmText,/3 active in-memory loop/);
 assert.deepEqual(h.bank,desired);
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/NATIVE HOST VERIFIED: FIVE FILM CLUB PROMPTS/);
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/CLOSE\/REOPEN/);
 assert.equal(h.dom.get("filmSyncNativePrompts").disabled,false);
});

test("user cancel leaves native bank unchanged",async()=>{
 const h=harness({confirm:false});await h.settle();
 await h.click();
 assert.equal(h.calls,0);
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/APPLY CANCELLED/);
 assert.deepEqual(h.bank,Array.from({length:5},(_,i)=>"Futureproof "+i));
});

test("already-configured native host needs no restart",async()=>{
 const h=harness({active:desired});await h.settle();
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/HOST REPORTS ALL FIVE/);
 await h.click();
 assert.equal(h.calls,0);
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/NO RESTART NEEDED/);
});

test("failed apply cannot produce a false success status",async()=>{
 const h=harness({applied:false});await h.settle();
 await h.click();
 assert.equal(h.calls,1);
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/NOT VERIFIED/);
 assert.doesNotMatch(h.dom.get("filmNativePromptStatus").textContent,/NATIVE HOST VERIFIED/);
});

test("editing a visible prompt invalidates displayed verification until re-applied",async()=>{
 const h=harness({active:desired});await h.settle();
 const piano=h.dom.get("promptPyramid");
 piano.value="completely different film piano";
 piano.callbacks.input();
 assert.match(h.dom.get("filmNativePromptStatus").textContent,/FILM SOUND TEXT EDITED/);
 assert.match(h.dom.get("filmPromptStatus").textContent,/NATIVE HOST NOT VERIFIED/);
 await h.click();
 assert.equal(h.calls,1);
 assert.equal(h.bank[0],"completely different film piano");
});
