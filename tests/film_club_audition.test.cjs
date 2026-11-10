"use strict";
const test=require("node:test"),assert=require("node:assert/strict");
const fs=require("node:fs"),path=require("node:path"),vm=require("node:vm");
const source=fs.readFileSync(path.join(__dirname,"..","performance","film-club-2026","audition.js"),"utf8");
function harness({ready=true,recording=false,weights=[1,0,0,0,0]}={}){
 let values=weights.slice(),changes=[],calls=[],statusReads=0;
 let mix=0,leadP=0,leadF=0,drum=.0;
 const node=(id)=>{
   const el={id,textContent:"",value:"",disabled:false,dataset:{},attrs:{},callbacks:{},
     addEventListener(event,handler){this.callbacks[event]=handler},
     setAttribute(name,value){this.attrs[name]=value},
     getAttribute(name){return this.attrs[name]},
     async click(){return await this.callbacks.click?.()},
   };
   return el;
 };
 const buttons=["piano","cello","violin","glass","drums"].map(name=>{
   const b=node(name);b.dataset.filmAudition=name;return b;
 });
 const output=node("filmAuditionStatus"),blend=node("filmAuditionBlend");
 const hold=node("filmNoteHold");hold.value="2400";
 const holdValue=node("filmNoteHoldValue");
 const elements=new Map([[output.id,output],[blend.id,blend],
   [hold.id,hold],[holdValue.id,holdValue]]);
 for(const id of ["mix","aiLeadMix-pyramid","aiLeadMix-fishes","aiDrumMix",
                  "aiLeadMixValue-pyramid","aiLeadMixValue-fishes","aiDrumMixValue"])
   elements.set(id,node(id));
 const document={
   getElementById:id=>elements.get(id)||null,
   querySelectorAll:selector=>selector==="[data-film-audition]"?buttons:[]
 };
 const setWeights=()=>{
  values=[(1-drum)*(1-mix)*(1-leadP),
          (1-drum)*mix*(1-leadF),
          (1-drum)*(1-mix)*leadP,
          (1-drum)*mix*leadF,
          drum];
 };
 const sandbox={
   document,console,Promise,
   aiNativeReady:ready,
   nativeTake:recording?{role:"chords"}:null,
   nativeTakeArming:null,
   activePyramidTextureRole:null,
   chordAuditionScene:null,
   aiDrumsAllowed:false,
   aiCommandQueue:Promise.resolve(),
   fetch:async url=>{
     assert.equal(url,"/api/ai/status");statusReads++;
     return {ok:true,json:async()=>({phase:"host-running",prompt_weights:values.slice()})};
   },
   selectNativeLane:async(which,role)=>{
     calls.push({which,role});
     const roleToIndex={chords:0,textureLow:1,lead:2,textureHigh:3,drums:4};
     values=values.map((_,i)=>i===roleToIndex[role]?1:0);
   },
   aiFetch:async(action,payload)=>{
     changes.push({action,payload});
     if(action==="chord-hold")return {chord_min_hold_ms:Math.round(payload.seconds*1000)};
     if(action==="mix"){mix=payload.value;setWeights();}
     else if(action==="lead-mix"&&payload.scene==="pyramid"){leadP=payload.value;setWeights();}
     else if(action==="lead-mix"&&payload.scene==="fishes"){leadF=payload.value;setWeights();}
     else if(action==="drum-mix"){drum=payload.value;setWeights();}
     return {prompt_weights:values.slice()};
   }
 };
 vm.runInNewContext(source,sandbox,{filename:"audition.js"});
 const settle=()=>new Promise(resolve=>setImmediate(resolve));
 return {buttons,blend,output,elements,calls,changes,settle,
   get weights(){return values.slice()},get statusReads(){return statusReads}};
}
test("page load only reads native weights and shows why the piano is alone",async()=>{
 const h=harness();await h.settle();
 assert.equal(h.calls.length,0);assert.equal(h.changes.length,0);
 assert.match(h.output.textContent,/ONLY PIANO IS WEIGHTED/);
 assert.match(h.output.textContent,/CELLO 0%/);
 assert.ok(h.statusReads>=1);
});
test("piano/cello/violin/glass/drums buttons each select one real model prompt weight",async()=>{
 const map={piano:["pyramid","chords"],cello:["pyramid","textureLow"],
   violin:["pyramid","lead"],glass:["pyramid","textureHigh"],drums:["drums","drums"]};
 const h=harness();await h.settle();
 for(const [i,name] of Object.keys(map).entries()){
   await h.buttons[i].click();
   assert.equal(h.calls[i].which,map[name][0]);
   assert.equal(h.calls[i].role,map[name][1]);
   assert.ok(h.weights[i]>.8);
   assert.equal(h.buttons[i].getAttribute("aria-pressed"),"true");
   assert.match(h.output.textContent,new RegExp("SELECTED "+name.toUpperCase()));
   assert.match(h.output.textContent,/NOW PLAY Z\/X\/C/);
 }
 const actions=h.changes.map(x=>x.action);
 assert.equal(actions.filter(a=>a==="chord-hold").length,5);
 assert.equal(actions.filter(a=>a==="chord").length,5);
 assert.equal(actions.filter(a=>a==="release").length,5);
 assert.deepEqual(h.changes.filter(x=>x.action==="chord")
   .map(x=>x.payload.harmony),Array(5).fill("pyramid"));
 assert.match(h.output.textContent,/AUDITION CHORD SENT/);
 assert.equal(h.elements.get("filmNoteHoldValue").textContent,"2.4 seconds");
});
test("Blend All Five submits one-AU weighted mix and verifies all weights nonzero",async()=>{
 const h=harness();await h.settle();await h.blend.click();
 const ops=h.changes.map(x=>x.action);
 assert.deepEqual(ops,["mix","lead-mix","lead-mix","drums","drum-mix",
   "chord-hold","chord","release"]);
 assert.ok(h.weights.every(v=>v>.05),"all five must actually be audible in one mixed generator");
 assert.match(h.output.textContent,/FIVE PROMPTS WEIGHTED IN ONE GENERATOR/);
 assert.match(h.output.textContent,/SUSTAINED AUDITION CHORD SENT/);
 assert.equal(h.blend.getAttribute("aria-pressed"),"true");
 assert.equal(h.elements.get("aiDrumMix").value,"15");
 assert.equal(h.elements.get("aiLeadMix-pyramid").value,"38");
 assert.equal(h.elements.get("aiLeadMix-fishes").value,"45");
});
test("film sustain slider configures 3.8-second native holds without replacing model or audio loops",async()=>{
 const h=harness();await h.settle();
 const slider=h.elements.get("filmNoteHold");
 slider.value="3800";
 slider.callbacks.input();
 assert.equal(h.elements.get("filmNoteHoldValue").textContent,"3.8 seconds");
 await slider.callbacks.change();
 assert.deepEqual(h.changes.map(x=>x.action),["chord-hold"]);
 assert.equal(h.changes[0].payload.seconds,3.8);
 assert.match(h.output.textContent,/3.8s/);
 assert.equal(h.calls.length,0,"sustain does not select any other model voice");
});

test("do not switch native prompts while a take is recording",async()=>{
 const h=harness({recording:true});await h.settle();
 await h.buttons[2].click();await h.blend.click();
 assert.equal(h.calls.length,0);assert.equal(h.changes.length,0);
 assert.match(h.output.textContent,/FINISH THE ACTIVE RECORDING/);
});
test("do not start a stopped model or erase loops from an audition click",async()=>{
 const h=harness({ready:false});await h.settle();
 await h.buttons[3].click();await h.blend.click();
 assert.equal(h.calls.length,0);assert.equal(h.changes.length,0);
 assert.match(h.output.textContent,/START GOOGLE MRT2 FIRST/);
});
test("an unconfirmed native weight is flagged, not falsely shown as audible",async()=>{
 const h=harness({weights:[.18,0,0,0,0]});await h.settle();
 await h.blend.click();
 assert.match(h.output.textContent,/FIVE PROMPTS WEIGHTED/);
 // Instrument validation works on actual state, never simply on requested role.
 const h2=harness();await h2.settle();
 h2.buttons[0].dataset.filmAudition="unknown";
 await h2.buttons[0].click();
 assert.equal(h2.calls.length,0);
});
