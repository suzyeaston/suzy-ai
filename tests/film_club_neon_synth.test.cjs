"use strict";
const test=require("node:test"),assert=require("node:assert/strict"),
  fs=require("node:fs"),path=require("node:path"),vm=require("node:vm");
const file=fs.readFileSync(path.join(__dirname,"..","performance","film-club-2026","neon-synth.js"),"utf8");

function harness({stageStarted=false}={}){
  let sourceChanges=[],audioStarts=0,originalNotes=[],extraNotes=[],oldReleases=0,stopCount=0;
  const keys=["keys","pad","pluck","bass","violin","nylon"];
  const presets=Object.fromEntries(keys.map(k=>[k,{name:k,wave:"sine"}]));
  const decks={pyramid:{instrumentSource:"ai",instrument:"keys",transpose:0}};
  const button={disabled:false,attrs:{},textContent:"",handlers:{},
    setAttribute(k,v){this.attrs[k]=v},addEventListener(k,fn){this.handlers[k]=fn}};
  const status={textContent:""};
  const document={getElementById:id=>({filmSynthKeys:button,filmSynthKeysStatus:status})[id]};
  const makeOsc=()=>({frequency:{value:440,setValueAtTime(){}},detune:{value:0},
    connect(){},start(){},stop(){stopCount++}});
  const ctx={currentTime:10,createOscillator:makeOsc,
    createGain(){return {gain:{setValueAtTime(){},exponentialRampToValueAtTime(){}},
      connect(){}}}};
  const sandbox={
    window:{},document,INSTRUMENTS:presets,stageStarted,
    ctx,decks,bpm:100,
    SCENES:{pyramid:{notes:[[52,55,59,64],[52,56,59,62]]}},
    openAudio:async()=>{audioStarts++},
    setInstrumentSource:(which,source)=>{decks[which].instrumentSource=source;sourceChanges.push(source)},
    localInstrumentAudible:which=>decks[which].instrumentSource==="local",
    makeVoice:(...args)=>{
      extraNotes.push(args);
      return {osc:makeOsc(),soft:makeOsc(),release:.17};
    },
    releaseVoice:()=>{oldReleases++},
    synth:(...args)=>{originalNotes.push(args)}
  };
  vm.runInNewContext(file,sandbox,{filename:"neon-synth.js"});
  return {sandbox,button,status,decks,presets,sourceChanges,
    get audioStarts(){return audioStarts},
    get originalNotes(){return originalNotes},
    get extraNotes(){return extraNotes},
    get oldReleases(){return oldReleases},
    get stopCount(){return stopCount}};
}

test("Film Club defaults to a real local FM synth even with a stale or silent Google AU",()=>{
 const h=harness();
 assert.equal(h.decks.pyramid.instrumentSource,"local");
 assert.deepEqual(h.sourceChanges,["local"]);
 assert.equal(h.presets.keys.name,"NEON FM SYNTH PIANO");
 assert.equal(h.presets.keys.wave,"sawtooth");
 assert.match(h.status.textContent,/NO GOOGLE PROMPTS REQUIRED/);
 assert.equal(h.button.attrs["aria-pressed"],"true");
});
test("NEON synth preserves original chord clock, but adds four rhythmic arpeggio notes",()=>{
 const h=harness();
 h.sandbox.synth("pyramid",0,20,false,.85,"keys");
 assert.equal(h.originalNotes.length,1);
 assert.equal(h.extraNotes.length,4);
 const scheduled=h.extraNotes.map(args=>args[2]);
 assert.deepEqual(scheduled,[20,20.15,20.30,20.45]);
 assert.ok(h.oldReleases>=4);
 assert.equal(h.extraNotes[0][3],"keys");
});
test("FM modulation oscillators stop at note release, preventing audio node leaks",()=>{
 const h=harness();
 const voice=h.sandbox.makeVoice("pyramid",52,20,"keys",.08,false);
 assert.ok(voice.filmMod,"FM transient oscillator created");
 assert.equal(h.stopCount,0);
 h.sandbox.releaseVoice(voice,20.4);
 assert.equal(h.stopCount,1,"modulator is scheduled to stop on release");
});
test("toggle retains the original native mode as optional, without invoking prompt restarts",async()=>{
 const h=harness();
 await h.button.handlers.click();
 assert.equal(h.decks.pyramid.instrumentSource,"ai");
 assert.match(h.status.textContent,/GOOGLE MRT2 SELECTED/);
 await h.button.handlers.click();
 assert.equal(h.decks.pyramid.instrumentSource,"local");
 assert.equal(h.audioStarts,2);
 assert.deepEqual(h.sourceChanges,["local","ai","local"]);
});
test("starting mid-session does not silently change the currently selected source",()=>{
 const h=harness({stageStarted:true});
 assert.deepEqual(h.sourceChanges,[]);
 assert.equal(h.decks.pyramid.instrumentSource,"ai");
 assert.equal(h.button.attrs["aria-pressed"],"false");
});
