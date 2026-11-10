"use strict";
const test=require("node:test"),assert=require("node:assert/strict");
const fs=require("node:fs"),path=require("node:path"),vm=require("node:vm");
const file=fs.readFileSync(path.join(__dirname,"..","performance","film-club-2026","film-club.js"),"utf8");

test("Film Club compact dual rhythms share 100 BPM clock; voice FX default is filtered and moderate",async()=>{
 let bpm=105,energy=.62,groove=[],statusReads=0,fxUpdated=0;
 const node=(id,value="")=>({
   id,value,textContent:"",handlers:{},
   addEventListener(name,fn){this.handlers[name]=fn},
   setAttribute(){},click(){return this.handlers.click?.()},
 });
 const defaults={
   filmGrooveEnergy:"58",filmCounterRhythm:"62",tempo:"105",
   vocalEchoMode:"quarter",vocalEchoLevel:"0",vocalEchoFeedback:"22",
   vocalAir:"75",monitorReverb:"28",rhythmLevel:"35"
 };
 const ids=["filmExportCues","filmPromptStatus","filmGrooveEnergy",
   "filmGrooveReadout","filmCounterRhythm","filmCounterReadout","tempo",
   "rhythmLevel","rhythmLevelNumber","filmNativePromptStatus",
   "vocalEchoMode","vocalEchoLevel","vocalEchoFeedback","vocalAir","monitorReverb"];
 const elements=new Map(ids.map(id=>[id,node(id,defaults[id]||"")]));
 const document={
   getElementById:id=>elements.get(id)||null,
   querySelectorAll:()=>[],
   body:{appendChild(){}}
 };
 const window={setInterval:()=>1,setTimeout:()=>1};
 const sandbox={
   document,window,console,Promise,URL,Blob,
   get drumEnergy(){return energy},
   set drumEnergy(v){energy=v},
   stageStarted:false,
   changeTempo(n){bpm=n},
   setDrumGroove(meter,style){groove.push({meter,style})},
   updateVoiceEcho(){fxUpdated++},
   fetch:async()=>{statusReads++;return {ok:true,json:async()=>({
     phase:"host-running",text_prompts:[],au_prompt_readback_available:false
   })}}
 };
 vm.runInNewContext(file,sandbox,{filename:"film-club.js"});
 await new Promise(resolve=>setImmediate(resolve));
 assert.equal(bpm,100,"Film Club clock must remain at 100 BPM");
 assert.equal(groove.length,1,"only one master scheduler is configured");
 assert.equal(groove[0].meter,"4/4");
 assert.equal(groove[0].style,"house");
 assert.equal(window.suzyFilmClubVocalClean,true);
 assert.equal(window.suzyFilmClubLowCello,true);
 assert.equal(window.suzyFilmCounterRhythm,.62);
 assert.equal(energy,.58);
 assert.equal(elements.get("filmCounterReadout").textContent,"62%");
 assert.equal(elements.get("vocalEchoMode").value,"dotted");
 assert.equal(elements.get("vocalEchoLevel").value,"15");
 assert.equal(elements.get("vocalEchoFeedback").value,"15");
 assert.equal(elements.get("vocalAir").value,"44");
 assert.equal(elements.get("monitorReverb").value,"20");
 assert.equal(fxUpdated,1);
 // The two intensity faders are independent, not two competing clocks.
 elements.get("filmCounterRhythm").value="75";
 elements.get("filmCounterRhythm").handlers.input();
 assert.equal(window.suzyFilmCounterRhythm,.75);
 assert.equal(energy,.58);
 elements.get("filmGrooveEnergy").value="22";
 elements.get("filmGrooveEnergy").handlers.input();
 assert.equal(energy,.22);
 assert.equal(window.suzyFilmCounterRhythm,.75);
 assert.equal(bpm,100);
 assert.equal(groove.length,1);
 assert.ok(statusReads>=1);
});
