"use strict";
const test=require("node:test"),assert=require("node:assert/strict");
const fs=require("node:fs"),path=require("node:path"),vm=require("node:vm");
const file=fs.readFileSync(path.join(__dirname,"..","performance","film-club-2026","film-club.js"),"utf8");

test("live five-cue accelerando changes percussion density, never tempo or recorded PCM",async()=>{
 let bpm=105,started=false,energy=.62,groove=[],updates=0,apiCalls=0;
 const el=(id,value="")=>({
   id,value,textContent:"",callbacks:{},attrs:{},dataset:{},
   addEventListener(type,cb){this.callbacks[type]=cb},
   setAttribute(k,v){this.attrs[k]=v},
   async click(){return this.callbacks.click?.()},
 });
 const ids=["filmExportCues","filmPromptStatus","filmGrooveEnergy",
            "filmGrooveReadout","filmDensityStatus","tempo",
            "rhythmLevel","rhythmLevelNumber","filmNativePromptStatus"];
 const items=new Map(ids.map(id=>[id,el(id,id==="filmGrooveEnergy"?"24":"")]));
 const cues=["float","awaken","tension","human","release"].map(id=>{
   const b=el("cue-"+id);b.dataset.filmDensity=id;return b;
 });
 const document={
   getElementById:id=>items.get(id)||null,
   querySelectorAll:selector=>
     selector==="[data-film-density]"?cues:[],
   body:{appendChild(){}}
 };
 const window={setInterval:()=>0,setTimeout:()=>0};
 const sandbox={
   document,window,console,Promise,URL,Blob,
   get drumEnergy(){return energy},
   set drumEnergy(v){energy=v},
   stageStarted:started,
   changeTempo(n){bpm=n},
   setDrumGroove(meter,style){groove.push({meter,style})},
   updateRhythmAudio(){updates++},
   fetch:async()=>{apiCalls++;return {ok:true,json:async()=>({
     phase:"host-running",text_prompts:[],au_prompt_readback_available:false
   })}}
 };
 vm.runInNewContext(file,sandbox,{filename:"film-club.js"});
 await new Promise(resolve=>setImmediate(resolve));
 assert.equal(bpm,100,"Film Club starts at 100, not old 105");
 assert.equal(groove[0].meter,"4/4");
 assert.equal(groove[0].style,"house");
 const expected=[[24,34],[49,39],[88,52],[8,20],[45,35]];
 for(let i=0;i<cues.length;i++){
   await cues[i].click();
   assert.equal(Math.round(energy*100),expected[i][0]);
   assert.equal(Number(items.get("filmGrooveEnergy").value),expected[i][0]);
   assert.equal(Number(items.get("rhythmLevel").value),expected[i][1]);
   assert.equal(cues[i].attrs["aria-pressed"],"true");
   assert.match(items.get("filmDensityStatus").textContent,/BPM UNCHANGED/);
   assert.equal(bpm,100,"live density must never alter the clock");
 }
 assert.equal(updates,5,"update existing browser rhythm bus, no new engine");
 assert.ok(apiCalls>=1,"the existing read-only native status still runs");
 assert.equal(groove.length,1,"live cue never resets meter or groove");
});
