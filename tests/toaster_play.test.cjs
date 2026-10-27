"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const file = fs.readFileSync(path.join(__dirname,"..","suzy_ai/music/toaster_play.html"),"utf8");
const javascript = file.match(/<script>([\s\S]*?)<\/script>/)[1];
function rig(){
 const nodes=new Map(),listeners=new Map(),calls={midi:[],output:null,download:null};
 const klass=()=>({add(){},remove(){},toggle(){}});
 const el=(v="")=>({
   value:v,textContent:"",style:{},dataset:{},children:[],options:[],
   classList:klass(),disabled:false,selectedOptions:[{textContent:"Automatic"}],
   setAttribute(){},addEventListener(){},append(...x){this.children.push(...x);},replaceChildren(){this.children=[];},
   add(x){this.options.push(x);},remove(){},click(){},
   closest(){return null;},
 });
 function get(id){if(!nodes.has(id)){let defaults={rhythmLevel:"35",master:"75",mix:"0",tempo:"105",reverb:"30",aiVolume:"28",aiReverb:"18","level-pyramid":"100","level-fishes":"100","voice-pyramid":"65","voice-fishes":"65"};nodes.set(id,el(defaults[id]??""));}return nodes.get(id)}
 const deckElements=["pyramid","fishes"].map(scene=>Object.assign(el(),{dataset:{scene}}));
 const pads=["pyramid","fishes"].flatMap(scene=>[0,1,2,3].map(chord=>Object.assign(el(),{dataset:{scene,chord:String(chord)}})));
 const notePads=Array.from({length:13},(_,i)=>Object.assign(el(),{dataset:{note:String(i+60)}}));
 const doc={getElementById:get,createElement:()=>el(),body:el(),addEventListener(type,fn){if(!listeners.has(type))listeners.set(type,[]);listeners.get(type).push(fn);},
  querySelectorAll(css){return css===".deck"?deckElements:css===".pad"?pads:css===".note-pad"?notePads:[]}};
 class Param{constructor(){this.value=0}setValueAtTime(v){this.value=v}linearRampToValueAtTime(v){this.value=v}exponentialRampToValueAtTime(v){this.value=v}setTargetAtTime(v){this.value=v}cancelScheduledValues(){}}
 class AudioNode{constructor(){this.gain=new Param();this.frequency=new Param();this.buffer=null;this.type=""}connect(){return this}disconnect(){}start(){}stop(){}}
 class AudioBuffer{
   constructor(ch,length,sr){this.numberOfChannels=ch;this.length=length;this.sampleRate=sr;this.duration=length/sr;this.buf=Array.from({length:ch},()=>new Float32Array(length));}
   getChannelData(k){return this.buf[k]}
 }
 class AudioContext{
  constructor(){this.state="running";this.currentTime=0;this.sampleRate=48000;this.destination={};}
  createGain(){return new AudioNode()}createConvolver(){return new AudioNode()}createOscillator(){return new AudioNode()}
  createMediaStreamSource(){return new AudioNode()}
  createScriptProcessor(){const n=new AudioNode(); n.onaudioprocess=null;calls.processor=n;return n;}
  createBuffer(ch,len,sr){return new AudioBuffer(ch,len,sr)}
  async resume(){this.state="running";}
  async setSinkId(id){calls.output=id;}
  async decodeAudioData(){return new AudioBuffer(1,48000,48000)}
 }
 class OfflineAudioContext extends AudioContext{
  constructor(ch,len,sr){super();this.ch=ch;this.len=len;this.sampleRate=sr;}
  createBufferSource(){return new AudioNode()}
  async startRendering(){return new AudioBuffer(this.ch,this.len,this.sampleRate)}
 }
 const io=[
  {kind:"audioinput",deviceId:"mic1",label:"Scarlett Solo USB"},
  {kind:"audiooutput",deviceId:"out1",label:"Scarlett Solo USB"},
  {kind:"audiooutput",deviceId:"out2",label:"External Headphones (Built-in)"}
 ];
 const env={
  document:doc,console,
  AudioContext,OfflineAudioContext,Blob,crypto:{randomUUID:()=>String(Math.random())},
  fetch:async (url,opts)=>{calls.midi.push({url,opts});return {ok:true,json:async()=>({})}},
  navigator:{mediaDevices:{enumerateDevices:async()=>io,getUserMedia:async()=>({active:true,getTracks:()=>[{stop(){}}]})}},
  addEventListener(type,fn){if(!listeners.has('window:'+type))listeners.set('window:'+type,[]);listeners.get('window:'+type).push(fn)},
  setInterval:()=>1,clearInterval(){},setTimeout(){},clearTimeout(){},
  URL:{createObjectURL(){return "blob:test"},revokeObjectURL(){}},
  MediaRecorder:class{constructor(){this.state="inactive";this.mimeType="audio/webm";}start(){this.state="recording"}stop(){this.state="inactive";this.ondataavailable?.({data:new Blob(["capture"])});this.onstop?.();}}
 };
 env.window=env;
 vm.createContext(env);
 vm.runInContext(javascript,env,{filename:"toaster_play.html"});
 const emit=(name,key,target="BUTTON",repeat=false)=>{
  const event={key,repeat,target:{tagName:target,isContentEditable:false,closest(){return null}},preventDefault(){}};
  for(const fn of listeners.get(name)||[])fn(event);
 };
 return {env,get,calls,run:(js)=>vm.runInContext(js,env),emit};
}
test("the musician sees the toaster, one-click beat, two decks and hidden setup",()=>{
 assert.match(file,/Smiling pink toaster/);
 assert.match(file,/PLAY RHYTHM/);
 assert.match(file,/13-note|CHROMATIC/);
 assert.match(file,/id="tempo"/);
 assert.match(file,/TRACK 01/);
 assert.match(file,/TRACK 02/);
 assert.match(file,/LOOP MY CHORDS/);
 assert.match(file,/LOOP VOICE/);
 assert.match(file,/auto Scarlett/);
 assert.match(file,/MRT2 prompt/);
 assert.match(file,/ENABLE MAGENTA/);
 assert.match(file,/Native Google Magenta AU is optional/);
 assert.match(javascript,/await aiFetch\("chord",\{index\}\)/);
 assert.match(javascript,/await aiFetch\("mix",\{value:Number\(\$\("mix"\)\.value\)\/100\}\)/);
 assert.ok(file.indexOf('id="rhythm"')<file.indexOf('id="deck-pyramid"'));
 assert.ok(file.indexOf('id="deck-pyramid"')<file.indexOf('id="deck-fishes"'));
 assert.ok(file.indexOf('id="deck-fishes"')<file.indexOf('id="micInput"'));
 assert.doesNotMatch(file,/CONNECT COLLIDER DIRECT/);
 const ids=[...file.matchAll(/id="([^"]+)"/g)].map(m=>m[1]);
 assert.equal(ids.length,new Set(ids).size);
});
test("one click starts audible browser beat and prefers Scarlett, not built-in headphones",async()=>{
 const {get,calls,run}=rig();
 await run("startStop()");
 assert.equal(run("stageStarted"),true);
 assert.equal(calls.output,"out1");
 assert.match(get("outputStatus").textContent,/Scarlett/);
 assert.equal(get("rhythm").value,"");
 assert.match(get("rhythm").textContent,/PAUSE RHYTHM/);
 assert.equal(run("stepNumber")>0,true);
});
test("record chord events at cycle boundary and switch to track 2 without losing track 1",async()=>{
 const {get,run}=rig();await run("startStop()");
 run('record("pyramid")');
 assert.equal(run("recording.kind"),"chords");
 run("ctx.currentTime=5;scheduler()");
 run('beginChord("pyramid",0,"key:1")');
 run("ctx.currentTime+=.50");
 run('endChord("key:1")');
 run('beginChord("pyramid",2,"key:3")');
 run("ctx.currentTime+=.75");
 run('endChord("key:3")');
 run("ctx.currentTime=9.5;scheduler()");
 assert.equal(run("decks.pyramid.layers.length"),1);
 assert.equal(run("decks.pyramid.layers[0].kind"),"chords");
 assert.equal(run("decks.pyramid.layers[0].events.length"),2);
 assert.ok(run("decks.pyramid.layers[0].events[0].holdSteps")>=1);
 assert.ok(run("decks.pyramid.layers[0].events[1].holdSteps")>1);
 run('choose("fishes")');
 assert.equal(get("mix").value,100);
 assert.equal(run("decks.pyramid.layers.length"),1);
 assert.equal(run("decks.fishes.bus.gain.value"),1);
 assert.equal(run("decks.pyramid.bus.gain.value"),0);
 assert.match(get("clips-pyramid").children[0].children[0].textContent,/Loop/);
});
test("export has genuine two-cycle offline audio rendering and WAV header",async()=>{
 const {run,env,calls}=rig();await run("startStop()");
 run("decks.pyramid.layers.push({kind:'chords',muted:false,events:[{index:0,step:0}]})");
 // The real renderer renders two passes, then writes the second one to carry tails.
 assert.match(javascript,/oneCycle\*2/);
 assert.match(javascript,/left\[i\+oneCycle\]/);
 assert.match(javascript,/tag\(0,"RIFF"\)/);
 await run("readAndExport()");
 assert.match(run('$("message").textContent'),/Mix exported/);
});

test("1–4 keyboard works while a button has focus; hold sustains and key-up releases",async()=>{
 const {get,run,emit}=rig();await run("startStop()");
 emit("keydown","1","BUTTON",false);
 assert.equal(run("heldKeys.size"),1);
 assert.equal(run('heldKeys.has("key:1")'),true);
 assert.equal(run("heldKeys.get('key:1').voices.length"),4);
 emit("keydown","1","BUTTON",true);
 assert.equal(run("heldKeys.size"),1,"OS auto-repeat must not retrigger chord");
 run("ctx.currentTime+=1.8");
 emit("keyup","1","BUTTON");
 assert.equal(run("heldKeys.size"),0,"key-up must stop held oscillators");
 emit("keydown","4","BODY");
 assert.equal(run("heldKeys.get('key:4').index"),3);
 emit("keyup","4","BODY");
 assert.equal(run("heldKeys.size"),0);
});
test("typing in editable controls never triggers chord keydown",async()=>{
 const {run,emit}=rig();await run("startStop()");
 emit("keydown","2","INPUT");
 assert.equal(run("heldKeys.size"),0);
 emit("keydown","2","TEXTAREA");
 assert.equal(run("heldKeys.size"),0);
 emit("keydown","2","SELECT");
 assert.equal(run("heldKeys.size"),0);
 emit("keydown","2","BUTTON");
 assert.equal(run("heldKeys.size"),1);
 emit("keyup","2","BUTTON");
});
test("manual hold length is retained by event loops and renders sustained chord envelopes",async()=>{
 const {run,emit}=rig();await run("startStop()");
 run('record("pyramid")');
 run("ctx.currentTime=5;scheduler()");
 emit("keydown","1","BUTTON");
 run("ctx.currentTime+=1.2");
 emit("keyup","1","BUTTON");
 run("ctx.currentTime=9.5;scheduler()");
 assert.equal(run("decks.pyramid.layers.length"),1);
 assert.ok(run("decks.pyramid.layers[0].events[0].holdSteps")>2);
 assert.match(javascript,/Math\.max\(\.12,\(e\.holdSteps\|\|1\)\*tickSeconds\(\)\)/);
 assert.match(javascript,/Math\.max\(\.12,\(event\.holdSteps\|\|1\)\*tickSeconds\(\)\)/);
});

test("real Magenta is opt-in: page load plays no second neural model",()=>{
 const {calls,run}=rig();
 assert.equal(calls.midi.length,0);
 assert.equal(run("aiNativeReady"),false);
 assert.equal(run("aiNativeStarting"),false);
 assert.match(file,/AI OFF · local chords work without it/);
});
test("native bridge playback sends real MIDI note-on and MIDI note-off only when ready",async()=>{
 const {calls,run}=rig();await run("startStop()");
 run("aiNativeReady=true;aiScene='pyramid'");
 run('beginChord("pyramid",0,"key:1")');
 await new Promise(resolve=>setImmediate(resolve));
 assert.ok(calls.midi.some(v=>v.url==="/api/ai/chord"),"Google AU MIDI note-on sent");
 run('endChord("key:1")');
 await new Promise(resolve=>setImmediate(resolve));
 assert.ok(calls.midi.some(v=>v.url==="/api/ai/release"),"Google AU MIDI note-off sent");
});

test("AI faders use actual native endpoints, not browser-only gain",async()=>{
 const {run,get,calls}=rig();
 run("aiNativeReady=true");
 get("aiVolume").value="21";
 get("aiReverb").value="35";
 await run("syncAIMix()");
 const native = calls.midi.filter(x=>x.url.startsWith("/api/ai/"));
 const actions = native.map(x=>x.url);
 assert.ok(actions.includes("/api/ai/volume"));
 assert.ok(actions.includes("/api/ai/reverb"));
 assert.ok(actions.includes("/api/ai/mute"));
 const vol = JSON.parse(native.find(x=>x.url==="/api/ai/volume").opts.body);
 const rev = JSON.parse(native.find(x=>x.url==="/api/ai/reverb").opts.body);
 assert.equal(vol.value,.21);
 assert.equal(rev.value,.35);
});
test("AI mute does not turn off the browser instrument or rhythm",async()=>{
 const {run,calls}=rig();
 await run("startStop()");
 run("aiNativeReady=true");
 await run("toggleAIMute()");
 assert.equal(run("aiMuted"),true);
 assert.equal(run("stageStarted"),true);
 assert.equal(run("ctx.state"),"running");
 assert.ok(calls.midi.find(x=>x.url==="/api/ai/mute"));
 await run("toggleAIMute()");
 assert.equal(run("aiMuted"),false);
});

test("live tempo changes land on a common cycle boundary, both decks keep chord loops",async()=>{
 const {run,get}=rig();await run("startStop()");
 run('decks.pyramid.layers.push({kind:"chords",muted:false,events:[{step:0,index:0,holdSteps:2}]})');
 run("changeTempo(132)");
 assert.equal(run("bpm"),105);
 assert.equal(run("pendingBpm"),132);
 assert.match(get("tempoValue").textContent,/next cycle/);
 run("ctx.currentTime=5;scheduler()");
 assert.equal(run("bpm"),132);
 assert.equal(run("pendingBpm"),null);
 assert.equal(run("cycleSeconds()"),8*60/132);
 assert.ok(run("Math.abs(nextStepAt - (transportEpoch+stepNumber*tickSeconds()))")<.0001);
});
test("polyphonic melody keyboard A W S E D F T G Y H U J K sends native MIDI per note",async()=>{
 const {run,emit,calls}=rig();await run("startStop()");
 run("aiNativeReady=true");
 emit("keydown","a","BUTTON");
 emit("keydown","w","BUTTON");
 assert.equal(run("heldNotes.size"),2);
 assert.equal(run('heldNotes.get("key-note:a").midi'),60);
 assert.equal(run('heldNotes.get("key-note:w").midi'),61);
 emit("keyup","a","BUTTON");
 assert.equal(run("heldNotes.size"),1);
 emit("keyup","w","BUTTON");
 await new Promise(resolve=>setImmediate(resolve));
 assert.equal(run("heldNotes.size"),0);
 assert.ok(calls.midi.some(x=>x.url==="/api/ai/note"));
 assert.ok(calls.midi.some(x=>x.url==="/api/ai/note-off"));
});
test("vocal recording uses AudioContext buffer timestamps and identical transport epoch",async()=>{
 const {run,calls}=rig();await run("startStop()");
 await run('voiceLoop("pyramid")');
 assert.equal(run("recording.kind"),"vocal");
 assert.ok(calls.processor?.onaudioprocess);
 const first=run("recording.start");
 const frame=run("ctx.sampleRate");
 const input={length:1024,getChannelData(){return new Float32Array(1024).fill(.4)}};
 const frameCount=run("Math.round(cycleSeconds()*ctx.sampleRate)");
 for(let position=0;position<frameCount+1024;position+=1024){
  calls.processor.onaudioprocess?.({playbackTime:first+position/frame,inputBuffer:input});
 }
 assert.equal(run("recording"),null);
 assert.equal(run("decks.pyramid.layers.length"),1);
 assert.equal(run("decks.pyramid.layers[0].buffer.length"),frameCount);
});
test("tempo stays fixed if a real audio loop exists rather than shifting its pitch",async()=>{
 const {run,get}=rig();await run("startStop()");
 run('decks.pyramid.layers.push({kind:"vocal",buffer:{},muted:false})');
 run("changeTempo(145)");
 assert.equal(run("bpm"),105);
 assert.equal(run("pendingBpm"),null);
 assert.equal(get("tempo").value,"105");
});
