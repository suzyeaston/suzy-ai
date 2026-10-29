"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const file = fs.readFileSync(path.join(__dirname,"..","suzy_ai/music/toaster_play.html"),"utf8");
const javascript = file.match(/<script>([\s\S]*?)<\/script>/)[1];
const arrangementJS = fs.readFileSync(path.join(__dirname,"..","suzy_ai/music/toaster_arrangement.js"),"utf8");
const tracksJS = fs.readFileSync(path.join(__dirname,"..","suzy_ai/music/toaster_track_view.js"),"utf8");
const timelineJS = fs.readFileSync(path.join(__dirname,"..","suzy_ai/music/toaster_performance_timeline.js"),"utf8");
const voiceFollowJS = fs.readFileSync(path.join(__dirname,"..","suzy_ai/music/toaster_voice_follow.js"),"utf8");
function rig(){
 const nodes=new Map(),listeners=new Map(),calls={midi:[],output:null,download:null,inputs:[],forceDeviceId:null,
 systemAudioAvailable:true,screenCaptures:0,recordingStream:null,recordingMime:null};
 const klass=()=>({add(){},remove(){},toggle(){},contains(){return false}});
 const el=(v="")=>({
   value:v,textContent:"",style:{setProperty(name,value){this[name]=value}},dataset:{},children:[],options:[],
   classList:klass(),disabled:false,selectedOptions:[{textContent:"Automatic"}],
   setAttribute(){},addEventListener(type,fn){this._events??={};(this._events[type]??=[]).push(fn);},append(...x){this.children.push(...x);},replaceChildren(){this.children=[];},
   add(x){this.options.push(x);},remove(){},click(){if(this.download)calls.download={filename:this.download,url:this.href};},
   closest(){return null;},
 });
 function get(id){if(!nodes.has(id)){let defaults={rhythmLevel:"35",master:"75",mix:"0",tempo:"105",liveLevel:"80",loopLevel:"100",vocalEchoMode:"quarter",vocalEchoLevel:"0",vocalEchoFeedback:"22",vocalAir:"75",reverb:"30",tone:"75",drumMeter:"4/4",drumStyle:"pulse",
 "leadLevel-pyramid":"72","leadLevel-fishes":"72",performanceMaster:"100","leadOctave-pyramid":"0","leadOctave-fishes":"0","lead-pyramid":"violin","lead-fishes":"nylon",promptPyramid:"piano and strings",promptFishes:"guitar arpeggios",
 promptViolin:"warm expressive violin",promptGuitar:"fingerpicked nylon guitar",promptJazzDrums:"brushed swing jazz drums",aiDrumMix:"0",
 "aiLeadMix-pyramid":"0","aiLeadMix-fishes":"0",aiVolume:"28",aiReverb:"18","level-pyramid":"100","level-fishes":"100","voice-pyramid":"65","voice-fishes":"65"};nodes.set(id,el(defaults[id]??""));}return nodes.get(id)}
 const deckElements=["pyramid","fishes"].map(scene=>Object.assign(el(),{dataset:{scene}}));
 const pads=["pyramid","fishes"].flatMap(scene=>[0,1,2,3].map(chord=>Object.assign(el(),{dataset:{scene,chord:String(chord)}})));
 const notePads=Array.from({length:13},(_,i)=>Object.assign(el(),{dataset:{note:String(i+60)}}));
 const doc={getElementById:get,createElement:()=>el(),body:el(),addEventListener(type,fn){if(!listeners.has(type))listeners.set(type,[]);listeners.get(type).push(fn);},
  querySelectorAll(css){return css===".deck"?deckElements:css===".pad"?pads:css===".note-pad"?notePads:[]}};
 class Param{constructor(){this.value=0}setValueAtTime(v){this.value=v}linearRampToValueAtTime(v){this.value=v}exponentialRampToValueAtTime(v){this.value=v}setTargetAtTime(v){this.value=v}cancelScheduledValues(){}}
 class AudioNode{constructor(){this.gain=new Param();this.frequency=new Param();this.Q=new Param();this.threshold=new Param();this.knee=new Param();this.ratio=new Param();this.attack=new Param();this.release=new Param();this.delayTime=new Param();this.buffer=null;this.type="";this.stopAt=null;this.startAt=null;this.startOffset=null}connect(){return this}disconnect(){}start(t,offset){this.startAt=t;this.startOffset=offset}stop(t){this.stopAt=t}getFloatTimeDomainData(samples){samples.fill(0)}}
 class AudioBuffer{
   constructor(ch,length,sr){this.numberOfChannels=ch;this.length=length;this.sampleRate=sr;this.duration=length/sr;this.buf=Array.from({length:ch},()=>new Float32Array(length));}
   getChannelData(k){return this.buf[k]}
 }
 class AudioContext{
  constructor(){this.state="running";this.currentTime=0;this.sampleRate=48000;this.destination={};
   this.audioWorklet={addModule:async src=>{calls.workletModule=src}};}
  createGain(){return new AudioNode()}createAnalyser(){return new AudioNode()}createConvolver(){return new AudioNode()}createOscillator(){return new AudioNode()}
   createDelay(){return new AudioNode()}
   createDynamicsCompressor(){return new AudioNode()}
  createBiquadFilter(){return new AudioNode()}
  createBufferSource(){return new AudioNode()}
  createMediaStreamSource(){return new AudioNode()}
  createMediaStreamDestination(){const n=new AudioNode();n.stream={getAudioTracks:()=>[{kind:"audio",readyState:"live"}]};return n;}
  async close(){this.state="closed";}
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
  {kind:"audioinput",deviceId:"mac0",label:"MacBook Pro Microphone"},
  {kind:"audioinput",deviceId:"mic1",label:"Scarlett Solo USB"},
  {kind:"audiooutput",deviceId:"out1",label:"Scarlett Solo USB"},
  {kind:"audiooutput",deviceId:"out2",label:"External Headphones (Built-in)"}
 ];
 class AudioWorkletNode extends AudioNode{
  constructor(context,name,opts){super();this.name=name;this.opts=opts;
   this.port={onmessage:null,postMessage(data){calls.workletMessage=data;}};calls.worklet=this;}
 }
 const env={
  document:doc,console,AudioWorkletNode,
  localStorage:{getItem(){return null},setItem(){}},
  confirm:()=>true,
  AudioContext,OfflineAudioContext,Blob,crypto:{randomUUID:()=>String(Math.random())},
  fetch:async (url,opts)=>{calls.midi.push({url,opts});return {ok:true,json:async()=>({})}},
  navigator:{mediaDevices:{enumerateDevices:async()=>io,getDisplayMedia:async constraints=>{
   calls.screenCaptures++;
   calls.displayConstraints=constraints;
   const video={kind:"video",readyState:"live",addEventListener(){},stop(){this.readyState="ended";}};
   const audio={kind:"audio",readyState:"live",stop(){this.readyState="ended";}};
   const audioTracks=calls.systemAudioAvailable?[audio]:[];
   return {active:true,getVideoTracks:()=>[video],getAudioTracks:()=>audioTracks,
    getTracks:()=>[video,...audioTracks]};
  },getUserMedia:async constraints=>{
   calls.inputs.push(constraints);
   const requested=constraints.audio===true?"mac0":constraints.audio.deviceId?.exact||constraints.audio.deviceId?.ideal||"mac0";
   const device=io.find(d=>d.kind==="audioinput"&&d.deviceId===requested);
   if(!device)throw Error("Requested audio input unavailable: "+requested);
   const opened=io.find(d=>d.kind==="audioinput"&&d.deviceId===(calls.forceDeviceId||requested))||device;
   const stream={active:true,getAudioTracks:()=>[track],getTracks:()=>[track]};
   const track={label:opened.label,getSettings:()=>({deviceId:opened.deviceId}),readyState:"live",
    stop(){this.readyState="ended";stream.active=false;}};
   return stream;
  }}},
  addEventListener(type,fn){if(!listeners.has('window:'+type))listeners.set('window:'+type,[]);listeners.get('window:'+type).push(fn)},
  setInterval:()=>1,clearInterval(){},setTimeout(){},clearTimeout(){},
  URL:{createObjectURL(){return "blob:test"},revokeObjectURL(){}},
  MediaRecorder:class{static isTypeSupported(type){return type==="audio/mp4";}
    constructor(stream,options){this.state="inactive";this.mimeType=options?.mimeType||"audio/webm";
     calls.recordingStream=stream;calls.recordingMime=this.mimeType;}
    start(){this.state="recording"}
    stop(){this.state="inactive";this.ondataavailable?.({data:new Blob(["set-audio"])});this.onstop?.();}}
 };
 env.window=env;
 vm.createContext(env);
 vm.runInContext(arrangementJS,env,{filename:"toaster_arrangement.js"});
 vm.runInContext(tracksJS,env,{filename:"toaster_track_view.js"});
 vm.runInContext(timelineJS,env,{filename:"toaster_performance_timeline.js"});
 vm.runInContext(javascript,env,{filename:"toaster_play.html"});
 const emit=(name,key,target="BUTTON",repeat=false)=>{
  const event={key,repeat,target:{tagName:target==="RANGE"?"INPUT":target,type:target==="RANGE"?"range":"text",isContentEditable:false,closest(){return null}},preventDefault(){}};
  for(const fn of listeners.get(name)||[])fn(event);
 };
 return {env,get,calls,io,pads,run:(js)=>vm.runInContext(js,env),emit};
}
test("the musician sees the toaster, one-click beat, two decks and hidden setup",()=>{
 assert.match(file,/Smiling pink toaster/);
 assert.match(file,/PLAY RHYTHM/);
 assert.match(file,/13-note|CHROMATIC/);
 assert.match(file,/id="tempo"/);
 assert.match(file,/TRACK 01/);
 assert.match(file,/TRACK 02/);
 assert.match(file,/RECORD FIRST LOOP/);
 assert.match(file,/LOOP VOICE/);
 assert.match(file,/VOICE INPUT · VE-22 THROUGH SCARLETT/);
 assert.match(file,/id="testMic"/);
 assert.match(file,/id="micMeter"/);
 assert.match(file,/MRT2 prompt/);
 assert.match(file,/ENABLE MAGENTA/);
 assert.match(file,/Native Google Magenta AU is optional/);
 assert.match(javascript,/await aiFetch\("chord",legato\?\{index,legato:true\}:\{index\}\)/);
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
 const {get,run}=rig();await run("startStop()"); run('setInstrumentSource("pyramid","local")'); run('setInstrumentSource("fishes","local")');
 run('record("pyramid")');
 assert.equal(run("recording.kind"),"chords");
 run("ctx.currentTime=5;scheduler()");
 run('beginChord("pyramid",0,"key:1")');
 run("ctx.currentTime+=.50");
 run('endChord("key:1")');
 run('beginChord("pyramid",2,"key:3")');
 run("ctx.currentTime+=.75");
 run('endChord("key:3")');
 run('record("pyramid")'); // finish first take at a bar boundary
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
 assert.match(run('$("message").textContent'),/Exported pyramid/);
});

test("Z X C V chords work from the computer keyboard, including focused buttons",async()=>{
 const {run,emit}=rig();await run("startStop()"); run('setInstrumentSource("pyramid","local")');
 for(const [i,key] of ["z","x","c","v"].entries()){
  emit("keydown",key,"BUTTON",false);
  assert.equal(run("heldKeys.size"),1);
  assert.equal(run('heldKeys.get("key:'+key+'").index'),i);
  assert.equal(run('heldKeys.get("key:'+key+'").voices.length'),4);
  emit("keydown",key,"BUTTON",true);
  assert.equal(run("heldKeys.size"),1,"OS repeat must not retrigger held chord");
  emit("keyup",key,"BUTTON");
  assert.equal(run("heldKeys.size"),0);
 }
 emit("keydown","1","BODY");
 assert.equal(run("heldKeys.size"),0,"number keys do not trigger chords");
 emit("keyup","1","BODY");
});
test("typing in editable controls never triggers chord keydown",async()=>{
 const {run,emit}=rig();await run("startStop()");
 emit("keydown","x","INPUT");
 assert.equal(run("heldKeys.size"),0);
 emit("keydown","x","TEXTAREA");
 assert.equal(run("heldKeys.size"),0);
 emit("keydown","x","SELECT");
 assert.equal(run("heldKeys.size"),0);
 emit("keydown","x","BUTTON");
 assert.equal(run("heldKeys.size"),1);
 emit("keyup","x","BUTTON");
});
test("Z X C V still plays immediately after moving a range fader",async()=>{
 const {run,emit}=rig();await run("startStop()");
 emit("keydown","x","RANGE");
 assert.equal(run('heldKeys.get("key:x").index'),1);
 emit("keyup","x","RANGE");
 assert.equal(run("heldKeys.size"),0);
 emit("keydown","z","TEXTAREA");
 assert.equal(run("heldKeys.size"),0);
});
test("rapid mouse click switches chords and each chord has an audible attack",async()=>{
 const {run,pads}=rig();await run("startStop()"); run('setInstrumentSource("pyramid","local")');
 const fire=(el,type,pointerId=1)=>{
  for(const fn of el._events?.[type]||[])fn({button:0,pointerId,preventDefault(){}});
 };
 const first=pads[0],second=pads[1];
 fire(first,"pointerdown");
 assert.equal(run("heldKeys.size"),1);
 const start=run('heldKeys.get("pad:pyramid:0").start');
 const voice=run('heldKeys.get("pad:pyramid:0").voices[0]');
 fire(first,"pointerup");
 assert.equal(run("heldKeys.size"),0);
 assert.ok(voice.osc.stopAt>=start+.105,"short tap must survive attack");
 fire(second,"pointerdown");
 assert.equal(run("heldKeys.get('pad:pyramid:1').index"),1);
 fire(second,"pointerup");
 assert.equal(run("heldKeys.size"),0);
 fire(first,"pointerdown");
 assert.equal(run("heldKeys.get('pad:pyramid:0').index"),0);
 fire(first,"pointercancel");
 assert.equal(run("heldKeys.size"),0);
});
test("second mouse pointer-down retriggers after missing pointer-up",async()=>{
 const {run,pads}=rig();await run("startStop()"); run('setInstrumentSource("pyramid","local")');
 const e={button:0,pointerId:7,preventDefault(){}};
 pads[0]._events.pointerdown[0](e);
 const before=run('heldKeys.get("pad:pyramid:0").voices[0]');
 // Simulate dropped mouse-up event. A fresh press must not be ignored.
 pads[0]._events.pointerdown[0](e);
 const after=run('heldKeys.get("pad:pyramid:0").voices[0]');
 assert.notEqual(before,after);
 assert.equal(run("heldKeys.size"),1);
 pads[0]._events.pointerup[0](e);
 assert.equal(run("heldKeys.size"),0);
});
test("short ambient-pad tap reaches its slower attack before stopping",async()=>{
 const {run,pads}=rig();await run("startStop()"); run('setInstrumentSource("pyramid","local")');
 run('setInstrument("pyramid","pad")');
 pads[2]._events.pointerdown[0]({button:0,pointerId:3,preventDefault(){}});
 const start=run('heldKeys.get("pad:pyramid:2").start');
 const voice=run('heldKeys.get("pad:pyramid:2").voices[0]');
 pads[2]._events.pointerup[0]();
 assert.ok(voice.osc.stopAt>=start+.275,"pad attack must finish on quick clicks");
});
test("manual hold length is retained by event loops and renders sustained chord envelopes",async()=>{
 const {run,emit}=rig();await run("startStop()");
 run('record("pyramid")');
 run("ctx.currentTime=5;scheduler()");
 emit("keydown","z","BUTTON");
 run("ctx.currentTime+=1.2");
 emit("keyup","z","BUTTON");
 run('record("pyramid")'); // finish first take at a bar boundary
 run("ctx.currentTime=9.5;scheduler()");
 assert.equal(run("decks.pyramid.layers.length"),1);
 assert.ok(run("decks.pyramid.layers[0].events[0].holdSteps")>2);
 assert.match(javascript,/recordedNoteHoldSeconds\(which,e\)/);
 assert.match(javascript,/Math\.max\(\.12,\(event\.holdSteps\|\|1\)\*tickSeconds\(\)\)/);
});

test("page refresh checks native Magenta status but does not spawn another model",()=>{
 const {calls,run}=rig();
 assert.ok(calls.midi.some(x=>x.url==="/api/ai/status"));
 assert.equal(calls.midi.filter(x=>x.url==="/api/ai/start").length,0);
 assert.equal(run("aiNativeReady"),false);
 assert.equal(run("aiNativeStarting"),false);
 assert.match(file,/AI OFF · local chords work without it/);
});
test("five native Magenta prompts include jazz drums in AU slot five",()=>{
 const {run,get}=rig();
 assert.equal(run("getPromptStrings().length"),5);
 assert.equal(run("getPromptStrings()[0]"),"piano and strings");
 assert.equal(run("getPromptStrings()[1]"),"guitar arpeggios");
 assert.equal(run("getPromptStrings()[2]"),"warm expressive violin");
 assert.equal(run("getPromptStrings()[3]"),"fingerpicked nylon guitar");
 assert.equal(run("getPromptStrings()[4]"),"brushed swing jazz drums");
 assert.match(file,/id="promptJazzDrums"/);
 assert.match(file,/id="aiDrumMix"/);
 assert.match(file,/id="promptViolin"/);
 assert.match(file,/id="promptGuitar"/);
 for(const which of ["pyramid","fishes"]){
  assert.match(file,new RegExp('id="aiLeadMix-'+which+'"'));
  assert.equal(get("aiLeadMix-"+which).value,"0");
 }
});
test("native lead blend uses real host endpoint and keeps original chord timbre option",async()=>{
 const {run,calls,get,emit}=rig();await run("startStop()");
 run("aiNativeReady=true;aiScene='pyramid'");
 run('setNativeLeadMix("pyramid",100)');
 for(let i=0;i<5;i++)await new Promise(resolve=>setImmediate(resolve));
 const lead=calls.midi.find(v=>v.url==="/api/ai/lead-mix");
 assert.ok(lead,"native four-prompt weights routed to host");
 assert.equal(JSON.parse(lead.opts.body).scene,"pyramid");
 assert.equal(JSON.parse(lead.opts.body).value,1);
 assert.match(get("aiLeadMixValue-pyramid").textContent,/LEAD 100%/);
 emit("keydown","a");
 assert.equal(run('heldNotes.get("key-note:a").voice'),null,"no browser lead oscillator layered over real Magenta sound");
 emit("keyup","a");
 run('setNativeLeadMix("pyramid",0)');
 assert.equal(get("aiLeadMix-pyramid").value,"0");
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

test("rapid app chord taps preserve ordered native note-on/off events",async()=>{
 const {calls,run}=rig();await run("startStop()");
 run("aiNativeReady=true;aiScene='pyramid'");
 run('beginChord("pyramid",0,"pad:pyramid:0")');
 run('endChord("pad:pyramid:0")');
 run('beginChord("pyramid",1,"pad:pyramid:1")');
 run('endChord("pad:pyramid:1")');
 // Browser HTTP commands serialize; the native Swift host now holds the
 // released notes for its minimum neural response window.
 for(let i=0;i<8;i++)await new Promise(resolve=>setImmediate(resolve));
 const native=calls.midi.filter(x=>x.url.startsWith("/api/ai/")).map(x=>x.url);
 const sequence=native.filter(x=>x==="/api/ai/chord"||x==="/api/ai/release");
 assert.deepEqual(sequence,[
  "/api/ai/chord","/api/ai/release","/api/ai/chord","/api/ai/release"
 ]);
 assert.equal(native.filter(x=>x==="/api/ai/scene").length,0,"same-scene taps must not reset held native notes");
});
test("AI faders use actual native endpoints, not browser-only gain",async()=>{
 const {run,get,calls}=rig();
 run("aiNativeReady=true");
 get("aiVolume").value="21";
 get("reverb").value="35";
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
test("vocal worklet can capture a full phrase without an arbitrary eight-bar preset",async()=>{
 const {run,calls}=rig();await run("startStop()");
 await run('voiceLoop("pyramid")');
 assert.equal(run("recording.kind"),"vocal");
 assert.equal(calls.worklet?.name,"suzy-vocal-capture");
 assert.equal(calls.workletModule,"/toaster/vocal-capture.js");
 const frames=run("Math.round(Math.min(256,Math.floor(120/tickSeconds()))*tickSeconds()*ctx.sampleRate)");
 assert.equal(calls.worklet.opts.processorOptions.frames,frames);
 calls.worklet.port.onmessage({data:{
  type:"complete",data:new Float32Array(frames).fill(.4),peak:.4,hot:0,missing:0
 }});
 assert.equal(run("recording"),null);
 assert.equal(run("decks.pyramid.layers.length"),1);
 assert.equal(run("decks.pyramid.layers[0].buffer.length"),frames);
});
test("tempo stays fixed if a real audio loop exists rather than shifting its pitch",async()=>{
 const {run,get}=rig();await run("startStop()");
 run('decks.pyramid.layers.push({kind:"vocal",buffer:{},muted:false})');
 run("changeTempo(145)");
 assert.equal(run("bpm"),105);
 assert.equal(run("pendingBpm"),null);
 assert.equal(get("tempo").value,"105");
});

test("app opens with automatic Magenta status, audible browser graph and editable native prompts",async()=>{
 const {run,get,calls}=rig();
 assert.match(file,/id="promptPyramid"/);
 assert.match(file,/id="promptFishes"/);
 assert.match(file,/id="applyPrompts"/);
 assert.match(file,/id="roomValue"/);
 assert.match(file,/id="tone"/);
 assert.ok(calls.midi.find(c=>c.url==="/api/ai/status"),"AI checked without pressing ENABLE");
 await run("startStop()");
 assert.ok(run("mixFilter")!==null);
 assert.ok(run("beatBus")!==null);
 assert.ok(run("wet")!==null);
 assert.equal(run("getPromptStrings().length"),5);
});
test("room and tone effect controls work for synth, rhythm, imported loops and native AI",async()=>{
 const {run,get,calls}=rig();await run("startStop()");
 get("reverb").value="45";
 run("updateRoomFx()");
 assert.equal(get("roomValue").textContent,"45%");
 assert.equal(get("aiReverb").value,"45");
 assert.equal(run("wet.gain.value"),.25);
 get("tone").value="20";
 get("tone").oninput();
 assert.ok(run("mixFilter.frequency.value")>220);
 run("aiNativeReady=true");
 run("updateRoomFx()");
 await new Promise(resolve=>setImmediate(resolve));
 assert.ok(calls.midi.some(x=>x.url==="/api/ai/reverb"));
});

test("AI SOLO lets musician hear real Magenta without the always-on browser chord oscillator",async()=>{
 const {run,get}=rig();
 await run("startStop()"); run('setInstrumentSource("pyramid","local")');
 assert.equal(run("aiSolo"),false);
 assert.equal(run("decks.pyramid.bus.gain.value"),1);
 run("toggleAISolo()");
 assert.equal(run("aiSolo"),true);
 assert.equal(run("decks.pyramid.bus.gain.value"),0);
 assert.equal(run("stageStarted"),true,"rhythm stays playing");
 assert.equal(run("beatBus.gain.value"),0,"diagnostic SOLO NATIVE AI mutes browser rhythm");
 assert.equal(get("aiSolo").textContent,"🎹 RESTORE BROWSER MIX");
 run("toggleAISolo()");
 assert.equal(run("decks.pyramid.bus.gain.value"),1);
});
test("each song has an independently playable lead under the Z/X/C/V chord pads",async()=>{
 const {run,emit,get}=rig();await run("startStop()"); run('setInstrumentSource("pyramid","local")'); run('setInstrumentSource("fishes","local")');
 assert.equal(run("decks.pyramid.leadInstrument"),"violin");
 assert.equal(run("decks.fishes.leadInstrument"),"nylon");
 assert.equal(run("decks.pyramid.instrument"),"keys");
 assert.equal(run("decks.fishes.instrument"),"keys");
 assert.equal(run("decks.pyramid.leadBus.gain.value"),.72);
 assert.equal(run("decks.fishes.leadBus.gain.value"),.72);
 emit("keydown","z");
 assert.equal(run('heldKeys.get("key:z").instrument'),"keys");
 emit("keyup","z");
 emit("keydown","a");
 assert.equal(run('heldNotes.get("key-note:a").instrument'),"violin");
 assert.equal(run('heldNotes.get("key-note:a").midi'),60);
 emit("keyup","a");
 run('choose("fishes")');
 emit("keydown","a");
 assert.equal(run('heldNotes.get("key-note:a").instrument'),"nylon");
 emit("keyup","a");
 assert.equal(get("lead-pyramid").value,"violin");
 await run('auditionLead("pyramid")');
 assert.equal(run("scene"),"pyramid");
});
test("per-song lead register and volume do not transpose chord pads or change prior overdubs",async()=>{
 const {run,emit,get}=rig();await run("startStop()"); run('setInstrumentSource("pyramid","local")'); run('setInstrumentSource("fishes","local")');
 run('setLeadOctave("pyramid",12)');
 run('setLeadLevel("pyramid",40)');
 assert.equal(run("decks.pyramid.leadBus.gain.value"),.4);
 assert.equal(run("decks.fishes.leadBus.gain.value"),.72);
 emit("keydown","a");
 assert.equal(run('heldNotes.get("key-note:a").midi'),72);
 emit("keyup","a");
 emit("keydown","z");
 assert.equal(run('heldKeys.get("key:z").instrument'),"keys");
 emit("keyup","z");
 run('setLead("pyramid","nylon")');
 assert.equal(run("decks.pyramid.leadInstrument"),"nylon");
 assert.equal(run("decks.fishes.leadInstrument"),"nylon");
 assert.equal(get("leadLevelValue-pyramid").textContent,"40%");
});
test("four drum styles really differ and 3/4, 6/8, 5/4 have distinct accent groupings",async()=>{
 const {run,get}=rig();await run("startStop()");
 run('setDrumGroove("3/4","brush")');
 assert.equal(run("drumPattern(0).kick"),true);
 assert.equal(run("drumPattern(3).snare"),true);
 assert.equal(run("drumPattern(6).kick"),true);
 assert.match(get("drumStatus").textContent,/4\/4 grid/);
 run('setDrumGroove("6/8","trip")');
 assert.equal(run("drumPattern(0).len"),6);
 assert.equal(run("drumPattern(3).secondary"),true);
 assert.equal(run("drumPattern(4).kick"),true);
 run('setDrumGroove("5/4","broken")');
 assert.equal(run("drumPattern(7).kick"),true);
 assert.equal(run("drumPattern(10).kick"),true);
 run('setDrumGroove("4/4","pulse")');
 assert.equal(run("drumPattern(0).kick"),true);
 assert.equal(run("drumPattern(4).kick"),true);
 assert.equal(run("drumPattern(8).kick"),true);
 assert.equal(run("bpm"),105);
 assert.equal(run("loopSteps"),16);
 // Changing percussion meter does NOT lie about the 4/4 recorded clip grid.
 assert.equal(run("songCycleSteps('pyramid')"),16);
});
test("overdubs preserve instruments and live/loop levels are independent",async()=>{
 const {get,run}=rig();await run("startStop()"); run('setInstrumentSource("pyramid","local")');
 run('setInstrument("pyramid","pad")');
 run('beginChord("pyramid",0,"live")');
 assert.equal(run('heldKeys.get("live").voices[0].osc.type'),"sine");
 run('endChord("live")');
 run('decks.pyramid.layers.push({kind:"chords",muted:false,instrument:"keys",events:[{index:1,step:0,holdSteps:2,instrument:"keys"}]})');
 get("liveLevel").value="60";get("loopLevel").value="110";
 run("updateOverdubBalance()");
 assert.equal(run("decks.pyramid.liveBus.gain.value"),.6);
 assert.equal(run("decks.pyramid.loopBus.gain.value"),1.1);
 run('setInstrument("pyramid","bass")');
 assert.equal(run('decks.pyramid.layers[0].events[0].instrument'),"keys");
});
test("key changes can return to previous and original pitch",async()=>{
 const {get,run}=rig();await run("startStop()");
 run('setKey("pyramid",2)');run('setKey("pyramid",4)');
 assert.equal(run("decks.pyramid.transpose"),4);
 run("decks.pyramid.keyHistoryIndex--;setKey('pyramid',decks.pyramid.keyHistory[decks.pyramid.keyHistoryIndex],false)");
 assert.equal(run("decks.pyramid.transpose"),2);
 run('setKey("pyramid",0)');
 assert.equal(run("decks.pyramid.transpose"),0);
 assert.equal(run("decks.fishes.transpose"),0);
 assert.equal(get("keyValue-pyramid").textContent,"ORIGINAL");
});
test("both song decks may play together while choosing a different instrument",async()=>{
 const {get,run}=rig();await run("startStop()"); run('setInstrumentSource("pyramid","local")'); run('setInstrumentSource("fishes","local")');
 get("mixBoth").onclick();
 assert.equal(run("blendBoth"),true);
 assert.equal(get("mix").value,"50");
 run('choose("fishes")');
 assert.equal(get("mix").value,"50");
 assert.equal(run("decks.pyramid.bus.gain.value"),.5);
 assert.equal(run("decks.fishes.bus.gain.value"),.5);
});
test("native status differentiates bookmark, assets and loaded model from host-running",()=>{
 const {run,get}=rig();
 run('aiDisplay({phase:"host-running",audio_engine_running:true,scene:"pyramid",native_au:true,model_file_exists:true,model_file_bytes:470000000,model_load_requested:true,host_model_load_state:"requested_asynchronously_by_google_AU_not_confirmed",bookmark_scope_verified:false,output_signal_detected:false})');
 assert.match(get("aiHostStatus").textContent,/AUDIO NOT VERIFIED/);
 assert.match(get("aiDiagnostics").textContent,/bookmark: not confirmed/);
 assert.match(get("aiDiagnostics").textContent,/not_confirmed/);
 run('aiDisplay({phase:"failed",error:"scope denied"})');
 assert.match(get("aiHostStatus").textContent,/scope denied/);
});

test("full timeline uses real MIDI/audio clips and gates source play by full-performance bars",async()=>{
 const {run}=rig();await run("startStop()");
 const beginning=run('clipActiveAt({muted:false,arrStartBar:4,arrEndBar:9},3)');
 assert.equal(beginning,false);
 assert.equal(run('clipActiveAt({muted:false,arrStartBar:4,arrEndBar:9},4)'),true);
 assert.equal(run('clipActiveAt({muted:false,arrStartBar:4,arrEndBar:9},9)'),false);
 run('decks.pyramid.layers.push({id:"demo",kind:"chords",muted:false,arrStartBar:4,arrEndBar:10,instrument:"keys",events:[{index:0,step:0,holdSteps:1}]})');
 run('fullTimeline.render()');
 const active=run('fullTimeline.totalBars()');
 assert.ok(active>=32);
 run('fullTimeline.onEdit("pyramid","demo",8,18)');
 assert.equal(run("decks.pyramid.layers[0].arrStartBar"),8);
 assert.equal(run("decks.pyramid.layers[0].arrEndBar"),18);
 assert.equal(run('clipActiveAt(decks.pyramid.layers[0],12)'),true);
});
test("voice-follow module steers existing native model but does not claim synthetic singing",()=>{
 assert.match(voiceFollowJS,/registerProcessor\("suzy-voice-follow"/);
 assert.match(voiceFollowJS,/type:"pitch"/);
 assert.match(file,/id="voiceFollow"/);
 assert.match(file,/does not create a synthetic singer/);
 assert.match(javascript,/aiMelody\(next,true\)/);
 assert.match(javascript,/aiMelody\(followedMidi,false\)/);
 assert.match(javascript,/fullTimeline=new window.SuzyPerformanceTimeline/);
 assert.match(javascript,/fullTimeline\?\.render\(\)/);
 assert.match(javascript,/songLayerAudible\(which,layer,count\/8\)/);
});

test("first sung take sets the same bar-quantized master length as keys",async()=>{
 const {run,calls}=rig();await run("startStop()");
 await run('voiceLoop("pyramid")');
 assert.equal(run("recording.first"),true);
 const original=run("recording.firstStep");
 // Press Finish at the first possible four-bar boundary.
 run("stepNumber="+(original+32));
 await run('voiceLoop("pyramid")');
 assert.equal(calls.workletMessage.type,"finish");
 const takenSteps=run("recording.actualSteps");
 assert.equal(takenSteps,32);
 const totalFrames=calls.worklet.opts.processorOptions.frames;
 const capturedFrames=calls.workletMessage.frames;
 assert.ok(capturedFrames<totalFrames);
 calls.worklet.port.onmessage({data:{type:"complete",
  data:new Float32Array(totalFrames).fill(.25),frames:capturedFrames,
  peak:.25,hot:0,missing:0}});
 assert.equal(run("recording"),null);
 assert.equal(run("decks.pyramid.lengthSteps"),32);
 assert.equal(run("decks.pyramid.layers[0].buffer.length"),capturedFrames);
 assert.equal(run("decks.pyramid.layers[0].bars"),4);
});
test("voice pitch follow recognizes A4 without an octave error",()=>{
 const events=[];
 class Base{constructor(){this.port={postMessage:message=>events.push(message),onmessage:null}}}
 let kind=null;
 const worker={AudioWorkletProcessor:Base,sampleRate:48000,Float32Array,Math,
   registerProcessor:(name,type)=>{assert.equal(name,"suzy-voice-follow");kind=type}};
 vm.runInNewContext(voiceFollowJS,worker,{filename:"toaster_voice_follow.js"});
 assert.ok(kind);
 const processor=new kind();
 let t=0;
 for(let block=0;block<145;block++){
  const buffer=new Float32Array(128);
  for(let n=0;n<128;n++)buffer[n]=.18*Math.sin(2*Math.PI*440*(t++/48000));
  processor.process([[buffer]]);
 }
 assert.ok(events.some(x=>x.type==="pitch"&&x.note===69));
});


test("lead voice monitoring is opt-in, shares Scarlett output, and does not bake reverb into vocal capture",async()=>{
 const {run,get}=rig();
 await run("startStop()");
 assert.equal(run("monitoringVoice"),false);
 get("monitorLevel").value="55";get("monitorReverb").value="28";
 await run("toggleVoiceMonitor()");
 assert.equal(run("monitoringVoice"),true);
 assert.equal(run("monitorDry.gain.value"),.55);
 assert.equal(run("monitorSend.gain.value"),.28);
 assert.equal(get("monitorVoice").textContent.includes("ON"),true);
 assert.match(file,/source.connect\(processor\);processor.connect\(silent\);silent.connect\(ctx.destination\)/);
 await run('voiceLoop("pyramid")');
 assert.equal(run("recording.kind"),"vocal");
 assert.equal(run("monitoringVoice"),true);
 await run("toggleVoiceMonitor()");
 assert.equal(run("monitoringVoice"),false);
 assert.equal(run("recording.kind"),"vocal");
});
test("a vocal overdub arms at the next BAR instead of waiting for the next 32-bar cycle",async()=>{
 const {run}=rig();await run("startStop()");
 run("decks.pyramid.locked=true;decks.pyramid.lengthSteps=256;decks.pyramid.anchorStep=0;stepNumber=23");
 await run('voiceLoop("pyramid")');
 assert.equal(run("recording.firstStep"),24);
 assert.equal(run("recording.steps"),256);
 assert.equal(run("recording.first"),false);
});
test("solo LOCAL keys isolates browser pads without mutating the underlying AI prompt",async()=>{
 const {run,get}=rig();await run("startStop()");
 const prompts=run("getPromptStrings().join('|')");
 await run("toggleLocalKeysOnly()");
 assert.equal(run("localKeysOnly"),true);
 assert.equal(run("beatBus.gain.value"),0);
 assert.equal(run("decks.pyramid.loopBus.gain.value"),0);
 assert.equal(run("decks.pyramid.voiceBus.gain.value"),0);
 assert.ok(run("decks.pyramid.liveBus.gain.value")>0);
 await run("toggleLocalKeysOnly()");
 assert.equal(run("localKeysOnly"),false);
 assert.equal(run("beatBus.gain.value"),.35);
 assert.equal(run("getPromptStrings().join('|')"),prompts);
});
test("the full timeline edits real clips with copy, cut, cross-song paste, split, and delete",async()=>{
 const {run}=rig();await run("startStop()");
 run('decks.pyramid.locked=true;decks.pyramid.lengthSteps=32;decks.pyramid.layers.push({id:"first",kind:"chords",instrument:"keys",muted:false,arrStartBar:2,arrEndBar:50,events:[{step:0,index:1,holdSteps:2}]})');
 run('fullTimeline.selected={which:"pyramid",kind:"chords",id:"first"}');
 run('fullTimeline.perform("copy")');
 assert.equal(run("fullTimeline.clipboard.layer.id"),"first");
 run('fullTimeline.target={which:"fishes",kind:"chords",bar:12}');
 run('fullTimeline.perform("paste")');
 assert.equal(run("decks.fishes.layers.length"),1);
 assert.equal(run("decks.fishes.layers[0].arrStartBar"),12);
 assert.equal(run("decks.fishes.layers[0].events[0].index"),1);
 const pasted=run("decks.fishes.layers[0].id");
 run('fullTimeline.selected={which:"fishes",kind:"chords",id:decks.fishes.layers[0].id};stepNumber=144');
 run('fullTimeline.perform("split")');
 assert.equal(run("decks.fishes.layers.length"),2);
 assert.equal(run("decks.fishes.layers[0].arrEndBar"),18);
 assert.equal(run("decks.fishes.layers[1].arrStartBar"),18);
 run('fullTimeline.selected={which:"fishes",kind:"chords",id:decks.fishes.layers[1].id}');
 run('fullTimeline.perform("delete")');
 assert.equal(run("decks.fishes.layers.length"),1);
 run('fullTimeline.selected={which:"fishes",kind:"chords",id:decks.fishes.layers[0].id}');
 run('fullTimeline.perform("cut")');
 assert.equal(run("decks.fishes.layers.length"),0);
 assert.equal(run("fullTimeline.clipboard.kind"),"chords");
});

test("filtered vocal tape echo is zero by default and follows the live BPM",async()=>{
 const {run,get}=rig();
 await run("startStop()");
 assert.equal(run("vocalEchoWet.gain.value"),0,"FX dry by default");
 assert.equal(run("vocalEchoFeedbackNode.gain.value"),.22);
 get("vocalEchoMode").value="dotted";
 get("vocalEchoLevel").value="22";
 get("vocalEchoFeedback").value="33";
 get("vocalAir").value="25";
 run("updateVoiceEcho()");
 assert.equal(run("vocalEchoWet.gain.value"),.22);
 assert.equal(run("vocalEchoFeedbackNode.gain.value"),.33);
 assert.ok(Math.abs(run("vocalEchoDelay.delayTime.value")-(45/105))<.001);
 assert.ok(run("vocalEchoTone.frequency.value")>3000);
 get("vocalEchoMode").value="off";
 run("updateVoiceEcho()");
 assert.equal(run("vocalEchoWet.gain.value"),0);
 assert.equal(run("vocalEchoFeedbackNode.gain.value"),0);
});
test("browser timeline stop and rewind preserve vocal clips while resetting bar position",async()=>{
 const {run,get}=rig();await run("startStop()");
 run('decks.pyramid.layers.push({id:"voice",kind:"vocal",muted:false,arrStartBar:0,buffer:null})');
 run("stepNumber=48");
 await run("timelineStop()");
 assert.equal(run("stageStarted"),false);
 assert.equal(run("stepNumber"),0);
 assert.equal(run("decks.pyramid.layers.length"),1);
 assert.match(get("timelineTransportStatus").textContent,/STOPPED/);
 assert.doesNotMatch(get("timelineTransportStatus").textContent,/BAR|BEAT/);
 assert.match(get("vocalLoopState").textContent,/1 VOCAL LOOP SAVED/);
 await run("startStop()");
 run("stepNumber=96");
 await run("timelineRewind()");
 assert.equal(run("stageStarted"),true);
 assert.ok(run("stepNumber")<=3);
 assert.equal(run("decks.pyramid.layers.length"),1);
});
test("return to start while playing keeps live lead monitoring engaged",async()=>{
 const {run}=rig();await run("startStop()");
 await run("toggleVoiceMonitor()");
 assert.equal(run("monitoringVoice"),true);
 run("stepNumber=96");
 await run("timelineRewind()");
 assert.equal(run("stageStarted"),true);
 assert.equal(run("monitoringVoice"),true);
 assert.ok(run("stepNumber")<=3);
});
test("live monitor and recording are separate states, vocal loop tally is explicit",async()=>{
 const {run,get}=rig();await run("startStop()");
 assert.match(get("vocalRecordState").textContent,/NOT RECORDING/);
 assert.match(get("vocalLoopState").textContent,/NO VOCAL LOOPS/);
 await run("toggleVoiceMonitor()");
 assert.equal(run("monitoringVoice"),true);
 assert.match(get("monitorStatus").textContent,/MONITOR ON/);
 assert.match(get("vocalRecordState").textContent,/NOT RECORDING/);
 await run('voiceLoop("pyramid")');
 assert.match(get("vocalRecordState").textContent,/VOCAL ARMED/);
 assert.equal(run("recording.kind"),"vocal");
});

test("clicking bar ruler locates real cursor while stopped, and Play begins from clicked Fishes section",async()=>{
 const {get,run}=rig();
 const ruler=get("fullRuler");
 ruler.getBoundingClientRect=()=>({left:0});
 assert.equal(typeof ruler.onpointerdown,"function");
 // The visible sections occupy one clock: Fishes begins after Pyramid.
 const fishesStart=run('arranger.cues.filter(c=>c.scene==="pyramid").reduce((a,c)=>a+c.bars,0)');
 const bar=fishesStart+8;
 ruler.onpointerdown({button:0,clientX:bar*6+.5});
 assert.equal(run("parkedBar"),bar);
 assert.equal(run("stepNumber"),bar*8);
 assert.equal(run("scene"),"fishes");
 assert.match(get("fullPosition").textContent,new RegExp("BAR "+(bar+1)));
 assert.equal(get("timelinePlay").textContent,"▶ PLAY");
 assert.equal(run("stageStarted"),false);
 await run("startStop()");
 assert.equal(run("stageStarted"),true);
 assert.ok(run("stepNumber")>=bar*8);
 assert.equal(run("currentTransportBar()"),bar);
});
test("click ruler during playback rephases actual vocal loops and starts matching cue without restarting native model",async()=>{
 const {get,run}=rig();
 await run("startStop()");
 run('decks.fishes.layers.push({id:"voice",kind:"vocal",muted:false,arrStartBar:0,buffer:ctx.createBuffer(1,48000,48000)})');
 run('startLoopAudio("fishes",decks.fishes.layers[0])');
 const oldSource=run('decks.fishes.layers[0].source');
 run("ctx.currentTime=1");
 const ruler=get("fullRuler");
 ruler.getBoundingClientRect=()=>({left:0});
 ruler.onpointerdown({button:0,clientX:205*6+.5});
 const newSource=run('decks.fishes.layers[0].source');
 assert.notEqual(newSource,oldSource,"audio buffer must be rescheduled at new cursor");
 assert.ok(oldSource.stopAt>=1.09,"old source stops at the new bar");
 assert.ok(newSource.startAt>=1.09,"new source starts with new bar");
 assert.equal(run("parkedBar"),205);
 assert.equal(run("currentTransportBar()"),205);
 assert.equal(run("scene"),"fishes");
 assert.equal(run("stageStarted"),true);
 assert.match(get("fullPosition").textContent,/BAR 206/);
});
test("Stop parks the playhead at its current bar; rewind returns to 1, with real clips preserved",async()=>{
 const {get,run}=rig();
 await run("startStop()");
 run("ctx.currentTime=transportEpoch+75*8*tickSeconds()+.05");
 run('decks.pyramid.layers.push({id:"take",kind:"chords",muted:false,events:[],arrStartBar:2})');
 await run("timelineStop()");
 assert.equal(run("stageStarted"),false);
 assert.equal(run("parkedBar"),75);
 assert.equal(run("stepNumber"),75*8);
 assert.equal(get("timelinePlay").textContent,"▶ PLAY");
 assert.equal(run("decks.pyramid.layers.length"),1);
 await run("timelineRewind()");
 assert.equal(run("parkedBar"),0);
 assert.equal(run("stepNumber"),0);
 assert.equal(get("timelinePlay").textContent,"▶ PLAY");
});
test("click seeking during an active recording is refused without moving clock",async()=>{
 const {run}=rig();await run("startStop()");
 await run('voiceLoop("pyramid")');
 const before=run("stepNumber");
 run("locateTimelineBar(150)");
 assert.equal(run("parkedBar"),0);
 assert.equal(run("stepNumber"),before);
});
test("ruler navigation supports arrows, Home and End without modifying recorded clips",()=>{
 const {get,run}=rig();
 const ruler=get("fullRuler");
 const key=key=>ruler.onkeydown({key,preventDefault(){},stopPropagation(){}});
 key("ArrowRight");assert.equal(run("parkedBar"),1);
 key("Home");assert.equal(run("parkedBar"),0);
 key("End");assert.equal(run("parkedBar"),run("fullTimeline.total")-1);
 key("ArrowLeft");assert.equal(run("parkedBar"),run("fullTimeline.total")-2);
});

test("all vocal paths bind to the verified Scarlett Solo, never the default Mac mic",async()=>{
 const {get,calls,run}=rig();
 await run("startStop()");
 await run("enableMic()");
 assert.equal(get("micInput").value,"mic1");
 assert.equal(run("activeMicDeviceId"),"mic1");
 assert.equal(calls.inputs.at(-1).audio.deviceId.exact,"mic1");
 assert.match(get("micStatus").textContent,/VERIFIED INPUT.*Scarlett Solo USB/);
 assert.match(get("micPeakLive").textContent,/LISTENING/);
 assert.equal(run("micStream.getAudioTracks()[0].getSettings().deviceId"),"mic1");
 await run("toggleVoiceMonitor()");
 assert.equal(run("monitoringVoice"),true);
 assert.equal(calls.inputs.length,1,"live monitoring reuses the verified mic");
});
test("without Scarlett block the browser default mic even if the MacBook mic exists",async()=>{
 const {io,get,calls,run}=rig();
 io.splice(io.findIndex(d=>d.deviceId==="mic1"),1);
 await run("startStop()");
 await assert.rejects(()=>run("enableMic()"),/Scarlett Solo USB input not found/);
 assert.equal(run("micStream"),null);
 assert.equal(calls.inputs.length,0,"do not open built-in microphone");
 assert.match(get("micStatus").textContent,/NO SCARLETT INPUT/);
});
test("a mismatched exact device must be rejected before recording or monitoring",async()=>{
 const {get,calls,run}=rig();
 calls.forceDeviceId="mac0";
 await run("startStop()");
 await assert.rejects(()=>run("enableMic()"),/different microphone/);
 assert.equal(run("micStream"),null);
 assert.equal(run("activeMicDeviceId"),null);
 assert.match(get("micStatus").textContent,/WRONG MIC/);
 assert.equal(calls.inputs.at(-1).audio.deviceId.exact,"mic1");
});
test("manual alternate mic selection can reconnect live monitoring immediately",async()=>{
 const {get,calls,run}=rig();
 await run("startStop()");
 await run("startVoiceMonitor()");
 assert.equal(run("monitoringVoice"),true);
 get("micInput").value="mac0";get("micInput").dataset.manual="true";
 await run("changeMicInput()");
 assert.equal(run("activeMicDeviceId"),"mac0");
 assert.equal(calls.inputs.at(-1).audio.deviceId.exact,"mac0");
 assert.equal(run("monitoringVoice"),true);
 assert.match(get("micStatus").textContent,/VERIFIED INPUT.*MacBook Pro Microphone/);
});
test("changing the microphone during an armed vocal take is refused",async()=>{
 const {get,calls,run}=rig();
 await run("startStop()");
 await run('voiceLoop("pyramid")');
 assert.equal(run("recording.kind"),"vocal");
 const count=calls.inputs.length;
 get("micInput").value="mac0";
 await run("changeMicInput()");
 assert.equal(calls.inputs.length,count);
 assert.equal(run("activeMicDeviceId"),"mic1");
 assert.equal(get("micInput").value,"mic1");
 assert.equal(run("recording.kind"),"vocal");
});

test("first chord take arms at next 8th-note tick and double tap cannot cancel count-in",async()=>{
 const {run,get}=rig();
 await run("startStop()");
 run('record("pyramid")');
 assert.equal(run("recording.beginAt"),1,"recording starts at the next unscheduled pulse, not a whole bar later");
 assert.equal(run("recording.active"),false);
 assert.match(get("recordHint-pyramid").textContent,/WAIT.*pulse/);
 run('record("pyramid")');
 assert.equal(run("recording.beginAt"),1);
 assert.equal(run("recording.active"),false);
 assert.match(get("recordHint-pyramid").textContent,/ARMED/);
});
test("recorded chord clip anchors to actual first captured bar, not the finish cursor",async()=>{
 const {run,get}=rig();
 await run("startStop()");
 run('record("pyramid")');
 const start=run("recording.beginAt");
 run('recording.active=true; recording.start=1; recording.endAt=recording.beginAt+16; recording.events.push({step:0,index:0,instrument:"keys",holdSteps:2}); stepNumber=96');
 run("endRecord()");
 assert.equal(run("decks.pyramid.locked"),true);
 assert.equal(run("decks.pyramid.anchorStep"),start);
 assert.equal(run("decks.pyramid.layers[0].arrStartBar"),Math.floor(start/8));
 assert.equal(run("decks.pyramid.layers[0].events[0].step"),0);
 assert.match(get("recordHint-pyramid").textContent,/LOOP PLAYING/);
});
test("next-bar overdub events rephase to existing master anchor instead of drifting",async()=>{
 const {run,get}=rig();
 await run("startStop()");
 run('decks.pyramid.locked=true;decks.pyramid.lengthSteps=16;decks.pyramid.anchorStep=8;stepNumber=14');
 run('record("pyramid")');
 assert.equal(run("recording.beginAt"),14,"overdub begins at next tick without changing original loop clock");
 run('recording.active=true;recording.start=1;recording.events.push({step:0,type:"note",midi:68,holdSteps:1,instrument:"violin"})');
 run("endRecord()");
 assert.equal(run("decks.pyramid.layers[0].events[0].step"),6,"align MIDI from overdub onset back to original master phase");
 assert.equal(run("decks.pyramid.layers[0].arrStartBar"),1);
 assert.match(get("recordHint-pyramid").textContent,/LOOP PLAYING/);
});
test("repair keeps native four-prompt design and VE-22 microphone controls unchanged",()=>{
 const {get,run}=rig();
 assert.equal(run("getPromptStrings().length"),5);
 assert.ok(file.includes('id="promptViolin"'));
 assert.ok(file.includes('id="promptGuitar"'));
 assert.ok(file.includes('id="testMic"'));
 assert.ok(file.includes('id="micMeter"'));
 assert.ok(!file.includes('id="includeLeadPrompt-pyramid"'));
});

test("Google model selector is clickable in native bookmark mode, with no server relaunch required",async()=>{
 const {get,run,calls}=rig();
 run('aiDisplay({phase:"host-running",scene:"pyramid",audio_engine_running:true,native_model_selection_required:false,native_au:true})');
 assert.equal(get("aiGoogleModel").disabled,false,"running AU can transition to picker from bookmark mode");
 assert.match(get("aiModelHelp").textContent,/Click OPEN GOOGLE MODEL SELECTOR/);
 await run("openGoogleModelSelector()");
 assert.ok(calls.midi.some(x=>x.url==="/api/ai/show-au-ui"),"the UI calls the existing same-host action");
});
test("model picker stays disabled until native AU ready and during an in-flight UI request",()=>{
 const {get,run}=rig();
 run('aiDisplay({phase:"starting",native_model_selection_required:false})');
 assert.equal(get("aiGoogleModel").disabled,true);
 run('aiDisplay({phase:"host-running",scene:"pyramid",audio_engine_running:true,native_model_selection_required:true,native_au_ui_requested:true})');
 assert.equal(get("aiGoogleModel").disabled,true);
 run('aiDisplay({phase:"host-running",scene:"pyramid",audio_engine_running:true,native_model_selection_required:true,native_au_ui_requested:false})');
 assert.equal(get("aiGoogleModel").disabled,false);
});

test("performer presses DONE and that exact phrase length becomes an immediately repeating pattern",async()=>{
 const {run,get}=rig();await run("startStop()");
 assert.doesNotMatch(file,/id="loopBars-pyramid"/);
 assert.equal(get("loopToggle-pyramid").disabled,true);
 run('record("pyramid")');
 const start=run("recording.beginAt");
 assert.equal(start,1,"first capture begins next eighth note");
 assert.equal(run("recording.endAt")-start,256,"safety maximum only; no preset length");
 run(`ctx.currentTime=transportEpoch+(${start}+1)*tickSeconds();scheduler()`);
 assert.equal(run("recording.active"),true);
 run('beginChord("pyramid",0,"key:manual")');
 run('endChord("key:manual")');
 run('var audibleLoops=[];const originalSynth=synth;synth=(...args)=>{audibleLoops.push(args);return originalSynth(...args)}');
 run(`ctx.currentTime=transportEpoch+(${start}+4.25)*tickSeconds()`);
 run('record("pyramid")');
 const close=run("recording.endAt");
 assert.equal(close-start,5,"DONE locks five eighth-note subdivisions, not 2/4/8 bars");
 assert.equal(run("recording.finishQueued"),true);
 assert.match(get("recordHint-pyramid").textContent,/DONE/);
 run(`ctx.currentTime=transportEpoch+(${close}+3)*tickSeconds();scheduler()`);
 assert.equal(run("recording"),null,"recorder closes and becomes playback on the very next scheduled clock tick");
 assert.equal(run("decks.pyramid.locked"),true);
 assert.equal(run("decks.pyramid.lengthSteps"),4,"first silent tick is removed");
 assert.equal(run("decks.pyramid.anchorStep"),start+1,"master begins on first played note");
 assert.equal(run("decks.pyramid.layers[0].events[0].step"),0);
 assert.ok(run("audibleLoops.some(args=>args[0]==='pyramid'&&args[1]===0)"),"playback starts at first loop phase during SAME scheduler pass");
 assert.match(get("record-pyramid").textContent,/OVERDUB/);
 assert.equal(get("loopToggle-pyramid").disabled,false);
});
test("DONE after a different phrase duration locks that custom length and not any preset bar",async()=>{
 const {run,get}=rig();await run("startStop()");
 run('record("fishes")');
 const begin=run("recording.beginAt");
 run(`ctx.currentTime=transportEpoch+(${begin}+1)*tickSeconds();scheduler()`);
 run('beginChord("fishes",1,"key:fishes")');
 run('endChord("key:fishes")');
 run(`ctx.currentTime=transportEpoch+(${begin}+11.25)*tickSeconds()`);
 run('record("fishes")');
 const finish=run("recording.endAt");
 assert.equal(finish-begin,12,"second phrase is 12 ticks, not restricted to 8/16/32");
 run(`ctx.currentTime=transportEpoch+(${finish}+2)*tickSeconds();scheduler()`);
 assert.equal(run("decks.fishes.lengthSteps"),11,"trim one silent tick before first chord");
 assert.equal(run("decks.fishes.anchorStep"),begin+1);
 assert.ok(!file.includes('id="loopBars-fishes"'));
 assert.match(get("recordHint-fishes").textContent,/LOOP PLAYING/);
});
test("DONE is ignored during count-in and double DONE cannot shift loop end",async()=>{
 const {run,get}=rig();await run("startStop()");
 run('record("pyramid")');
 const begin=run("recording.beginAt");
 run('record("pyramid")');
 assert.equal(run("recording.endAt"),begin+256);
 run(`ctx.currentTime=transportEpoch+(${begin}+1)*tickSeconds();scheduler()`);
 run('beginChord("pyramid",2,"key:foo")');
 run(`ctx.currentTime=transportEpoch+(${begin}+5.4)*tickSeconds()`);
 run('record("pyramid")');
 const requested=run("recording.endAt");
 run('record("pyramid")');
 assert.equal(run("recording.endAt"),requested);
 assert.match(get("recordHint-pyramid").textContent,/DONE/);
});
test("a chord held across next-pulse count-in becomes the first note, not a missing beat",async()=>{
 const {run}=rig();await run("startStop()");
 run('record("pyramid")');
 const begin=run("recording.beginAt");
 run('beginChord("pyramid",0,"key:downstroke")');
 assert.equal(run("recording.events.length"),0,"not recording before clock starts");
 run(`ctx.currentTime=transportEpoch+(${begin}+.4)*tickSeconds();scheduler()`);
 assert.equal(run("recording.events.length"),1);
 assert.equal(run("recording.events[0].step"),0);
 run(`ctx.currentTime=transportEpoch+(${begin}+4.5)*tickSeconds()`);
 run('record("pyramid")');
 const finish=run("recording.endAt");
 run(`ctx.currentTime=transportEpoch+(${finish}+2)*tickSeconds();scheduler()`);
 assert.equal(run("decks.pyramid.layers[0].events[0].step"),0);
 assert.equal(run("decks.pyramid.lengthSteps"),finish-begin);
});
test("loop pedal stop and restart quantize to next bar and preserve absolute song phase",async()=>{
 const {run,get}=rig();await run("startStop()");
 run('decks.pyramid.locked=true;decks.pyramid.lengthSteps=16;decks.pyramid.anchorStep=8;decks.pyramid.layers.push({id:"original",kind:"chords",muted:false,events:[{step:0,index:0,holdSteps:2,instrument:"keys"}],arrStartBar:1})');
 run("renderClips('pyramid')");
 const anchor=run("decks.pyramid.anchorStep");
 run('toggleLoop("pyramid")');
 assert.match(get("loopToggle-pyramid").textContent,/STOP NEXT BAR/);
 const stopStep=run("decks.pyramid.loopToggleAt");
 assert.equal(stopStep%8,0);
 run('ctx.currentTime=transportEpoch+(decks.pyramid.loopToggleAt+1)*tickSeconds();scheduler()');
 assert.equal(run("decks.pyramid.loopEnabled"),false);
 assert.equal(run("decks.pyramid.anchorStep"),anchor);
 assert.equal(run("songLayerAudible('pyramid',decks.pyramid.layers[0],Math.floor(stepNumber/8))"),false);
 assert.match(get("loopToggle-pyramid").textContent,/RESTART LOOP/);
 run('toggleLoop("pyramid")');
 const restartStep=run("decks.pyramid.loopToggleAt");
 assert.ok(restartStep>stopStep);
 run('ctx.currentTime=transportEpoch+(decks.pyramid.loopToggleAt+1)*tickSeconds();scheduler()');
 assert.equal(run("decks.pyramid.loopEnabled"),true);
 assert.equal(run("decks.pyramid.anchorStep"),anchor);
 assert.match(get("loopToggle-pyramid").textContent,/STOP LOOP/);
});
test("one loop pedal gates chord and vocal loop sources, not metronome or the other song",async()=>{
 const {run,get}=rig();await run("startStop()");
 run('decks.pyramid.locked=true;decks.pyramid.anchorStep=8;decks.pyramid.lengthSteps=16;decks.pyramid.layers.push({id:"chords",kind:"chords",events:[{step:0,index:1,holdSteps:1,instrument:"keys"}],muted:false,arrStartBar:1})');
 run('decks.pyramid.layers.push({id:"vocal",kind:"vocal",muted:false,arrStartBar:1,buffer:ctx.createBuffer(1,48000,48000)})');
 run('startLoopAudio("pyramid",decks.pyramid.layers[1])');
 run('toggleLoop("pyramid")');
 run('ctx.currentTime=transportEpoch+(decks.pyramid.loopToggleAt+1)*tickSeconds();scheduler()');
 assert.equal(run("decks.pyramid.layers[1].gain.gain.value"),0,"vocal output gated at exact song bar");
 assert.equal(run("decks.pyramid.loopEnabled"),false);
 assert.equal(run("decks.fishes.loopEnabled"),true,"other deck remains available");
 assert.equal(run("stageStarted"),true,"underlying rhythm keeps running");
 run('toggleLoop("pyramid")');
 run('ctx.currentTime=transportEpoch+(decks.pyramid.loopToggleAt+1)*tickSeconds();scheduler()');
 assert.equal(run("decks.pyramid.layers[1].gain.gain.value"),.65,"vocal gain reopens on original grid");
});
test("pausing and restarting rhythm never resets original recorded loop downbeat",async()=>{
 const {run}=rig();await run("startStop()");
 run('decks.pyramid.locked=true;decks.pyramid.lengthSteps=16;decks.pyramid.anchorStep=8');
 run('ctx.currentTime=transportEpoch+23*tickSeconds();scheduler()');
 await run("startStop()");
 const saved=run("decks.pyramid.anchorStep");
 assert.equal(saved,8);
 await run("startStop()");
 assert.equal(run("decks.pyramid.anchorStep"),saved);
 assert.equal(run("decks.pyramid.lengthSteps"),16);
});

test("local replay sustains a chord held through DONE across next loop attack",async()=>{
 const {run}=rig();await run("startStop()");
 run('record("pyramid")');
 run('recording.active=true;recording.start=0;recording.endAt=recording.beginAt+5;ctx.currentTime=.38');
 run('beginChord("pyramid",0,"key:sustain")');
 run('endRecord()');
 assert.equal(run("decks.pyramid.lengthSteps"),4,"shorter phrase after removing initial silence");
 assert.equal(run("decks.pyramid.layers[0].events[0].sustainAcrossBoundary"),true);
 const original=run("decks.pyramid.layers[0].events[0].holdSteps*tickSeconds()");
 const loopSeconds=run("songCycleSeconds('pyramid')");
 const sustained=run("recordedNoteHoldSeconds('pyramid',decks.pyramid.layers[0].events[0])");
 assert.ok(sustained>loopSeconds,"held chord overlaps the next iteration instead of going silent");
 assert.ok(sustained>original,"recorded duration is extended solely at the loop seam");
 const noTie=run("recordedNoteHoldSeconds('pyramid',{holdSteps:1})");
 assert.ok(noTie<loopSeconds,"released chord still has its original short musical phrasing");
});
test("releasing before DONE does not falsely tie a naturally short chord",async()=>{
 const {run}=rig();await run("startStop()");
 run('record("pyramid")');
 run('recording.active=true;recording.start=0;recording.endAt=recording.beginAt+6;ctx.currentTime=.4');
 run('beginChord("pyramid",0,"key:released")');
 run('ctx.currentTime+=.2;endChord("key:released")');
 run('endRecord()');
 assert.equal(run("decks.pyramid.layers[0].events[0].sustainAcrossBoundary"),undefined);
 assert.ok(run("recordedNoteHoldSeconds('pyramid',decks.pyramid.layers[0].events[0])")<
  run("songCycleSeconds('pyramid')"));
});
test("browser synth no longer forcibly truncates a held note to one loop duration",async()=>{
 const {run}=rig();await run("startStop()"); run('setInstrumentSource("pyramid","local")');
 run('decks.pyramid.lengthSteps=4;var releaseTimes=[];const releaseOriginal=releaseVoice;releaseVoice=(v,t)=>{releaseTimes.push(t);return releaseOriginal(v,t)}');
 run('synth("pyramid",0,1,true,3,"pad")');
 assert.equal(run("releaseTimes.length"),4);
 assert.ok(run("releaseTimes.every(t=>Math.abs(t-4)<.00001)"),
  "all chord notes release after the specified three-second hold, not after the 4-tick cycle");
});
test("live looper shows simple states, no beat/bar/pass counters, while tempo remains",async()=>{
 const {run,get}=rig();await run("startStop()");
 const trackJS=tracksJS;
 assert.doesNotMatch(trackJS,/track-ruler|track-bar|\\u0022BEAT |\\u0022BAR |LOOP \\u0022\\+pass/);
 assert.match(trackJS,/LOOPING/);
 assert.match(file,/id="tempo"/);
 run("trackView.draw()");
 assert.doesNotMatch(get("track-loop-label-pyramid").textContent,/BAR|BEAT|LOOP [0-9]/);
 assert.doesNotMatch(get("timelineTransportStatus").textContent,/BAR|BEAT/);
 assert.doesNotMatch(get("vocalLoopState").textContent,/BAR [0-9]/);
 assert.equal(get("tempo").value,"105","tempo input remains available");
 assert.match(file,/id="tempoValue"/,"tempo display remains present");
});
test("stopping a sustained loop fades its active oscillator bus without stopping rhythm",async()=>{
 const {run,get}=rig();await run("startStop()"); run('setInstrumentSource("pyramid","local")');
 run('decks.pyramid.locked=true;decks.pyramid.lengthSteps=5;decks.pyramid.anchorStep=0;decks.pyramid.layers.push({id:"long",kind:"chords",events:[{step:0,index:0,holdSteps:5,sustainAcrossBoundary:true}],muted:false,arrStartBar:0})');
 run('renderClips("pyramid")');
 run('toggleLoop("pyramid")');
 const end=run("decks.pyramid.loopToggleAt");
 run(`ctx.currentTime=transportEpoch+(${end}+1)*tickSeconds();scheduler()`);
 assert.equal(run("decks.pyramid.loopEnabled"),false);
 assert.equal(run("decks.pyramid.loopBus.gain.value"),0,"already playing notes fade out on STOP");
 assert.equal(run("stageStarted"),true);
 run('toggleLoop("pyramid")');
 const resume=run("decks.pyramid.loopToggleAt");
 run(`ctx.currentTime=transportEpoch+(${resume}+1)*tickSeconds();scheduler()`);
 assert.ok(run("decks.pyramid.loopBus.gain.value")>0,"audible bus is restored at bar-quantized restart");
});

test("AI ONLY hard-mutes ALL browser audio including rhythm vocals live pads and loops",async()=>{
 const {run,get}=rig();await run("startStop()");
 run('decks.pyramid.layers.push({kind:"chords",muted:false,events:[{step:0,index:0,holdSteps:4}]})');
 run('updateOverdubBalance()');
 assert.equal(run("aiSolo"),false);
 run("toggleAISolo()");
 assert.equal(run("aiSolo"),true);
 assert.equal(run("stageStarted"),true,"music clock stays running");
 assert.equal(run("master.gain.value"),0,"all browser sources including beat/voice/monitor go through browser master");
 assert.equal(run("decks.pyramid.bus.gain.value"),0);
 assert.equal(run("decks.pyramid.voiceBus.gain.value"),0);
 run('beginChord("pyramid",0,"key:AI-ONLY")');
 assert.equal(run('heldKeys.get("key:AI-ONLY").voices.length'),0,"no browser chord oscillator");
 assert.equal(run('heldKeys.get("key:AI-ONLY").index'),0,"MIDI chord steering remains active");
 run('endChord("key:AI-ONLY")');
 run('beginNote(60,"key:AI-LEAD")');
 assert.equal(run('heldNotes.get("key:AI-LEAD").voice'),null,"no browser melody oscillator");
 run('endNote("key:AI-LEAD")');
 run("ctx.currentTime+=1;scheduler()");
 assert.equal(run("master.gain.value"),0,"scheduled rhythm and loops remain silenced");
 get("master").value="100";get("master").oninput();
 assert.equal(run("master.gain.value"),0,"master fader cannot punch through isolation");
 assert.equal(run("aiSolo"),true,"diagnostic solo persists after key-release messages");
 run("toggleAISolo()");
 assert.equal(run("master.gain.value"),1,"restore user master gain");
});
test("editable drum MIDI preserves meter clock and maps to GM channel 10 notes",async()=>{
 const {run,get}=rig();await run("startStop()");
 const baseline=Array.from(run("drumMidiBytes()"));
 assert.deepEqual(baseline.slice(0,4),[77,84,104,100],"standard MThd");
 assert.deepEqual(baseline.slice(14,18),[77,84,114,107],"standard MTrk");
 assert.ok(baseline.includes(0x99),"channel ten note on is present");
 assert.ok(baseline.includes(36),"GM kick 36");
 assert.ok(baseline.includes(42),"GM closed hi-hat 42");
 assert.equal(run("editableDrumPattern().length"),16,"4/4 is two cycles of eight eighth notes");
 assert.ok(get("drumMidiGrid").children.length>0,"editable controls rendered");
 const prior=run("drumPattern(1).snare");
 run("customDrumHits=editableDrumPattern()");
 run("customDrumHits[1].snare=true");
 assert.equal(run("drumPattern(1).snare"),true);
 const modified=Array.from(run("drumMidiBytes()"));
 assert.ok(modified.length>baseline.length,"new snare note on/off is exported");
 assert.equal(run("stageStarted"),true,"editing does not restart clock");
 run('setDrumGroove("5/4","broken")');
 assert.equal(run("editableDrumPattern().length"),20);
 assert.equal(run("customDrumHits"),null);
 assert.equal(run("drumPattern(0).len"),10);
 assert.ok(run("drumMidiBytes().length")>40);
});
test("groove variation is correctly labelled algorithmic and remains exportable MIDI",async()=>{
 const {run,get}=rig();await run("startStop()");
 run("varyDrumPattern()");
 assert.match(get("drumMidiStatus").textContent,/ALGORITHMIC VARIATION/);
 assert.match(get("drumMidiStatus").textContent,/not Magenta-generated MIDI/);
 assert.equal(run("customDrumHits.length"),16);
 const bytes=Array.from(run("drumMidiBytes()"));
 assert.deepEqual(bytes.slice(0,4),[77,84,104,100]);
 const clock=run("stepNumber");
 run("varyDrumPattern()");
 assert.equal(run("stepNumber"),clock);
});
test("AI ONLY does not assert neural model produced drums or audio merely because MIDI is present",async()=>{
 const {run,get}=rig();await run("startStop()");
 run("toggleAISolo()");
 run('aiDisplay({phase:"host-running",scene:"pyramid",audio_engine_running:true,output_signal_detected:false,muted:false})');
 assert.match(get("aiHostStatus").textContent,/AUDIO NOT VERIFIED/);
 assert.equal(run("master.gain.value"),0);
 assert.equal(run("aiSolo"),true);
 assert.equal(run("drumMidiBytes()[0]"),77);
});

test("jazzy fifth native prompt blends live with no change at zero",async()=>{
 const {run,get,calls}=rig();
 run("aiNativeReady=true");
 run("setNativeDrumBlend(0)");
 for(let i=0;i<6;i++)await new Promise(resolve=>setImmediate(resolve));
 let xs=calls.midi.filter(x=>x.url==="/api/ai/drum-mix");
 assert.equal(xs.length,1);
 assert.equal(JSON.parse(xs[0].opts.body).value,0);
 assert.equal(get("aiDrumMixValue").textContent,"0%");
 run("aiNativeReady=true;setNativeDrumBlend(35)");
 for(let i=0;i<12;i++)await new Promise(resolve=>setImmediate(resolve));
 xs=calls.midi.filter(x=>x.url==="/api/ai/drum-mix");
 assert.equal(JSON.parse(xs.at(-1).opts.body).value,.35);
 assert.ok(calls.midi.some(x=>x.url==="/api/ai/drums"&&JSON.parse(x.opts.body).value===true));
 assert.equal(get("aiDrumMix").value,"35");
 assert.equal(run("aiDrumsAllowed"),true);
 assert.equal(run("getPromptStrings().length"),5);
 run("aiNativeReady=true;setNativeDrumBlend(0)");
 for(let i=0;i<10;i++)await new Promise(resolve=>setImmediate(resolve));
 assert.equal(JSON.parse(calls.midi.filter(x=>x.url==="/api/ai/drum-mix").at(-1).opts.body).value,0);
});
test("AI only is still silent from local browser with the fifth native prompt active",async()=>{
 const {run,calls}=rig();await run("startStop()");
 run("aiNativeReady=true");
 run("toggleAISolo()");
 run("setNativeDrumBlend(60)");
 for(let i=0;i<7;i++)await new Promise(resolve=>setImmediate(resolve));
 assert.equal(run("aiSolo"),true);
 assert.equal(run("master.gain.value"),0);
 assert.ok(calls.midi.some(x=>x.url==="/api/ai/drum-mix"));
 assert.equal(calls.midi.filter(x=>x.url==="/api/ai/start").length,0);
});

test("Track 03 jazzy Magenta drums is visible and independently editable",()=>{
 const {get,run}=rig();
 assert.match(file,/id="jazzDrumDeck"/);
 assert.match(file,/TRACK 03 · NATIVE GOOGLE MAGENTA · PROMPT 05/);
 assert.match(file,/id="applyJazzDrumsPrompt"/);
 assert.match(file,/id="promptJazzDrums"/);
 assert.match(file,/id="aiDrumMix"/);
 assert.ok(file.indexOf('id="jazzDrumDeck"')<file.indexOf('id="deck-pyramid"'));
 assert.match(file,/id="rhythmAudio"/);
 assert.equal(get("aiDrumMix").value,"0");
 assert.equal(run("decks.pyramid.instrumentSource"),"ai");
 assert.equal(run("decks.fishes.instrumentSource"),"ai");
});
test("native AI instruments are exclusive without diagnostic AI SOLO, while local rhythm stays on",async()=>{
 const {run,calls,get}=rig();await run("startStop()");
 run("aiNativeReady=true");
 run("updateInstrumentSource('pyramid')");
 assert.equal(run("aiSolo"),false,"pure AI solo not needed");
 assert.equal(run("rhythmCanSound()"),true);
 assert.equal(run("master.gain.value"),.75,"browser bus remains available for rhythm");
 assert.equal(run("beatBus.gain.value"),.35);
 run('beginChord("pyramid",0,"key:native")');
 assert.equal(run('heldKeys.get("key:native").voices.length'),0);
 assert.equal(run("decks.pyramid.bus.gain.value"),0);
 await new Promise(resolve=>setImmediate(resolve));
 assert.ok(calls.midi.some(q=>q.url==="/api/ai/chord"));
 assert.ok(!calls.midi.some(q=>q.url==="/api/perform/chord"),"never duplicate native pad to Logic/CoreMIDI");
 run('endChord("key:native")');
 run('beginNote(60,"key:native-melody")');
 assert.equal(run('heldNotes.get("key:native-melody").voice'),null);
 run('endNote("key:native-melody")');
 assert.equal(get("instrumentSource-pyramid").getAttribute?.("aria-pressed")||run("decks.pyramid.instrumentSource"),"ai");
});
test("local rhythm on/off never changes AI instrument source or transport clock",async()=>{
 const {run,get}=rig();await run("startStop()");
 run("aiNativeReady=true");
 assert.equal(run("rhythmAudioEnabled"),true);
 run("toggleRhythmAudio()");
 assert.equal(run("rhythmCanSound()"),false);
 assert.equal(run("beatBus.gain.value"),0);
 assert.equal(run("decks.pyramid.instrumentSource"),"ai");
 assert.equal(run("stageStarted"),true);
 assert.equal(run("master.gain.value"),.75);
 const step=run("stepNumber");
 run("toggleRhythmAudio()");
 assert.equal(run("rhythmCanSound()"),true);
 assert.equal(run("beatBus.gain.value"),.35);
 assert.equal(run("stepNumber"),step);
 assert.match(get("rhythmAudio").textContent,/ON/);
});
test("local instrument is explicit and does not also command native Magenta",async()=>{
 const {run,calls}=rig();await run("startStop()");
 run("aiNativeReady=true");
 run('setInstrumentSource("pyramid","local")');
 assert.equal(run("decks.pyramid.instrumentSource"),"local");
 assert.ok(run("decks.pyramid.bus.gain.value")>0);
 run('beginChord("pyramid",0,"key:local")');
 assert.equal(run('heldKeys.get("key:local").voices.length'),4);
 run('endChord("key:local")');
 await new Promise(resolve=>setImmediate(resolve));
 assert.ok(!calls.midi.some(q=>q.url==="/api/ai/chord"));
 assert.ok(!calls.midi.some(q=>q.url==="/api/perform/chord"));
 run('setInstrumentSource("pyramid","ai")');
 assert.equal(run("decks.pyramid.bus.gain.value"),0);
});
test("native AI instrument does not secretly fall back to local piano when model unavailable",async()=>{
 const {run,calls,get}=rig();await run("startStop()");
 assert.equal(run("aiNativeReady"),false);
 run('beginChord("pyramid",0,"key:silent")');
 assert.equal(run('heldKeys.get("key:silent").voices.length'),0);
 assert.equal(run("decks.pyramid.bus.gain.value"),0);
 assert.match(get("instrumentSourceStatus-pyramid").textContent,/WAITING/);
 await new Promise(resolve=>setImmediate(resolve));
 assert.ok(!calls.midi.some(q=>q.url==="/api/perform/chord"));
 run('endChord("key:silent")');
});

test("older loop note-off cannot release a newer native chord",async()=>{
 const {run,calls}=rig();await run("startStop()");
 run("aiNativeReady=true;aiScene='pyramid'");
 const old=run('aiNote("pyramid",0,{legato:true})');
 const next=run('aiNote("pyramid",1,{legato:true})');
 assert.ok(next>old);
 run(`aiRelease(${old})`);
 assert.equal(run("aiChordOwner.token"),next);
 for(let i=0;i<8;i++)await new Promise(resolve=>setImmediate(resolve));
 const chords=calls.midi.filter(x=>x.url==="/api/ai/chord");
 assert.equal(chords.length,2);
 assert.deepEqual(chords.map(x=>JSON.parse(x.opts.body)),[{index:0,legato:true},{index:1,legato:true}]);
 assert.equal(calls.midi.filter(x=>x.url==="/api/ai/release").length,0,"old timer must not kill newer chord");
 run(`aiRelease(${next})`);
 for(let i=0;i<5;i++)await new Promise(resolve=>setImmediate(resolve));
 assert.equal(calls.midi.filter(x=>x.url==="/api/ai/release").length,1);
 assert.equal(run("aiChordOwner"),null);
});
test("native MIDI loop tied at DONE stays held across the next repetition",async()=>{
 const {run,calls}=rig();await run("startStop()");
 run("aiNativeReady=true;aiScene='pyramid'");
 run('var loopTie={step:0,index:0,holdSteps:4,sustainAcrossBoundary:true}');
 const start=run('aiNote("pyramid",loopTie.index,{loopEvent:loopTie,legato:true})');
 const same=run('aiNote("pyramid",loopTie.index,{loopEvent:loopTie,legato:true})');
 assert.equal(same,start,"second pass reuses same held chord; no staccato reattack");
 for(let i=0;i<8;i++)await new Promise(resolve=>setImmediate(resolve));
 assert.equal(calls.midi.filter(x=>x.url==="/api/ai/chord").length,1);
 assert.equal(calls.midi.filter(x=>x.url==="/api/ai/release").length,0);
 assert.equal(run("aiChordOwner.loopEvent===loopTie"),true);
 // A genuinely new chord changes harmony without an intervening gap.
 const newChord=run('aiNote("pyramid",1,{loopEvent:{index:1},legato:true})');
 run(`aiRelease(${start})`);
 for(let i=0;i<8;i++)await new Promise(resolve=>setImmediate(resolve));
 assert.equal(calls.midi.filter(x=>x.url==="/api/ai/chord").length,2);
 assert.equal(calls.midi.filter(x=>x.url==="/api/ai/release").length,0);
 run(`aiRelease(${newChord})`);
});
test("native loop pedal STOP explicitly releases a tied chord; other song and rhythm unaffected",async()=>{
 const {run,calls}=rig();await run("startStop()");
 run("aiNativeReady=true;aiScene='pyramid'");
 run('decks.pyramid.locked=true;decks.pyramid.lengthSteps=8;decks.pyramid.anchorStep=0;decks.pyramid.layers.push({id:"tie",kind:"chords",events:[{step:0,index:0,holdSteps:8,sustainAcrossBoundary:true}],muted:false,arrStartBar:0})');
 run("renderClips('pyramid')");
 const token=run('aiNote("pyramid",0,{loopEvent:decks.pyramid.layers[0].events[0],legato:true})');
 run('toggleLoop("pyramid")');
 const stop=run("decks.pyramid.loopToggleAt");
 run(`ctx.currentTime=transportEpoch+(${stop}+1)*tickSeconds();scheduler()`);
 for(let i=0;i<6;i++)await new Promise(resolve=>setImmediate(resolve));
 assert.equal(run("decks.pyramid.loopEnabled"),false);
 assert.equal(run("aiChordOwner"),null);
 assert.ok(calls.midi.some(x=>x.url==="/api/ai/release"));
 assert.equal(run("stageStarted"),true,"shared drum clock remains running");
 assert.equal(run("decks.fishes.loopEnabled"),true);
});

test("live view replaces huge full arrangement with visible record full set controls",()=>{
 const {get}=rig();
 assert.match(file,/<section class="full-arrangement" id="fullArrangement" hidden aria-hidden="true"/);
 assert.ok(file.includes("#fullArrangement[hidden]{display:none!important}"));
 assert.doesNotMatch(file,/href="#fullArrangement"/);
 assert.match(file,/id="setRecordStart"/);
 assert.match(file,/id="setRecordStop" disabled/);
 assert.match(file,/id="setRecordMic" type="checkbox" checked/);
 assert.match(file,/id="setRecordStatus"/);
 assert.ok(file.indexOf('id="setRecordStart"')<file.indexOf('id="rhythm"'));
 assert.equal(get("setRecordStatus").textContent,"");
});
test("record full set captures genuine Mac system audio PLUS Scarlett into one audio file",async()=>{
 const {run,calls,get}=rig();
 get("setRecordMic").checked=true;
 await run("startSetRecording()");
 assert.equal(calls.screenCaptures,1);
 assert.equal(calls.displayConstraints.systemAudio,"include");
 assert.equal(calls.displayConstraints.audio,true);
 assert.equal(calls.recordingMime,"audio/mp4");
 assert.equal(run("setRecorder.recorder.state"),"recording");
 assert.equal(run("setRecorder.addedMic"),true);
 assert.equal(run("setRecorder.display.getAudioTracks().length"),1);
 assert.equal(get("setRecordStart").disabled,true);
 assert.equal(get("setRecordStop").disabled,false);
 assert.ok(calls.inputs.some(x=>x.audio?.deviceId?.exact==="mic1"),"selected Scarlett stream used");
 run("setRecorder.heardSystemAudio=true");
 run("setRecordClock()");
 assert.match(get("setRecordStatus").textContent,/MAC AUDIO VERIFIED/);
 run("stopSetRecording()");
 for(let i=0;i<5;i++)await new Promise(resolve=>setImmediate(resolve));
 assert.ok(calls.download.filename.startsWith("SUZY_TOASTER_FULL_SET_")&&calls.download.filename.endsWith(".m4a"));
 assert.match(get("setRecordStatus").textContent,/SET SAVED/);
 assert.equal(get("setRecordStart").disabled,false);
});
test("screen capture without system audio refuses to start, never produces a misleading empty set",async()=>{
 const {run,calls,get}=rig();
 calls.systemAudioAvailable=false;
 get("setRecordMic").checked=false;
 await run("startSetRecording()");
 assert.equal(run("setRecorder"),null);
 assert.equal(calls.recordingStream,null);
 assert.equal(calls.download,null);
 assert.match(get("setRecordStatus").textContent,/WITHOUT SYSTEM AUDIO/);
 assert.equal(get("setRecordStart").disabled,false);
});
test("mic monitoring must be off when recorder separately includes Scarlett",async()=>{
 const {run,calls,get}=rig();
 get("setRecordMic").checked=true;
 run("monitoringVoice=true");
 await run("startSetRecording()");
 assert.equal(calls.screenCaptures,0);
 assert.equal(run("setRecorder"),null);
 assert.match(get("setRecordStatus").textContent,/Turn OFF browser microphone monitoring/);
});

test("first-loop pedal trims dead air before first played chord and replays at DONE boundary",async()=>{
 const {run,get}=rig();await run("startStop()");
 run('setInstrumentSource("pyramid","local")');
 run('record("pyramid")');
 const originalBegin=run("recording.beginAt");
 const requestedEnd=originalBegin+11;
 // First actual note is three eighth-note ticks after arming RECORD.
 run(`ctx.currentTime=transportEpoch+(${originalBegin}+3.08)*tickSeconds();scheduler()`);
 run('beginChord("pyramid",0,"key:late")');
 assert.equal(run("recording.events[0].step"),3);
 run('endChord("key:late")');
 run('var replayed=[];const oldSynth=synth;synth=(...args)=>{replayed.push(args);return oldSynth(...args)}');
 run(`ctx.currentTime=transportEpoch+(${requestedEnd}-.55)*tickSeconds()`);
 run('record("pyramid")');
 assert.equal(run("recording.endAt"),requestedEnd);
 run(`ctx.currentTime=transportEpoch+(${requestedEnd}+1)*tickSeconds();scheduler()`);
 assert.equal(run("recording"),null);
 assert.equal(run("decks.pyramid.anchorStep"),originalBegin+3,"first played note becomes master start");
 assert.equal(run("decks.pyramid.lengthSteps"),8,"three empty pre-roll ticks are not looped");
 assert.equal(run("decks.pyramid.layers[0].events[0].step"),0);
 assert.equal(run("decks.pyramid.anchorStep+decks.pyramid.lengthSteps"),requestedEnd,
  "first replay begins on the actual DONE boundary, no extra silent interval");
 assert.ok(run("replayed.some(x=>x[0]==='pyramid'&&x[1]===0)"),
  "same scheduler pass launches loop from first chord");
 assert.match(get("recordHint-pyramid").textContent,/LOOP PLAYING/);
});
test("chord presses record in played subdivision, never round up and create false lead-in",async()=>{
 const {run}=rig();await run("startStop()");
 run('record("pyramid")');
 const start=run("recording.beginAt");
 run(`ctx.currentTime=transportEpoch+(${start}+.05)*tickSeconds();scheduler()`);
 run(`ctx.currentTime=transportEpoch+(${start}+.68)*tickSeconds()`);
 run('beginChord("pyramid",1,"key:slightly-late")');
 assert.equal(run("recording.events[0].step"),0,
  "played within first subdivision means first chord belongs to the first subdivision");
});
test("live deck no longer exposes misleading moving playhead while loop clock stays functional",async()=>{
 const {run,get}=rig();
 assert.ok(file.includes(".deck-transport .timeline{display:none!important}"));
 assert.match(file,/id="head-pyramid"/);
 assert.match(file,/id="head-fishes"/);
 await run("startStop()");
 assert.equal(run("stageStarted"),true);
 assert.equal(run("tickSeconds()"),30/105);
 run("updateTimeline()");
 assert.match(get("rhythm").textContent,/PAUSE RHYTHM/);
});

test("vocal recorder now accepts Record Done after a custom phrase rather than preset bars",async()=>{
 const {run,calls,get}=rig();await run("startStop()");
 await run('voiceLoop("pyramid")');
 const begin=run("recording.firstStep");
 assert.equal(run("recording.first"),true);
 assert.ok(run("recording.steps")>64,"no eight-bar cap");
 run(`stepNumber=${begin}+13;ctx.currentTime=transportEpoch+(stepNumber-.2)*tickSeconds()`);
 await run('voiceLoop("pyramid")');
 assert.equal(run("recording.finishQueued"),true);
 assert.equal(run("recording.actualSteps"),13);
 assert.equal(calls.workletMessage.type,"finish");
 assert.ok(calls.workletMessage.frames<calls.worklet.opts.processorOptions.frames);
 const full=calls.worklet.opts.processorOptions.frames,short=calls.workletMessage.frames;
 calls.worklet.port.onmessage({data:{type:"complete",data:new Float32Array(full).fill(.3),frames:short,peak:.3,hot:0,missing:0}});
 assert.equal(run("recording"),null);
 assert.equal(run("decks.pyramid.lengthSteps"),13);
 assert.equal(run("decks.pyramid.layers[0].buffer.length"),short);
 assert.equal(run("decks.pyramid.layers[0].loopOriginStep"),begin);
 assert.ok(get("vocalRecordPyramid").textContent.includes("RECORD"));
});
test("lead vocal monitoring starts with Scarlett and headphone routing even before PLAY RHYTHM",async()=>{
 const {run,calls,get}=rig();
 await run("toggleVoiceMonitor()");
 assert.equal(run("monitoringVoice"),true);
 assert.equal(run("stageStarted"),false);
 assert.equal(run("monitorDry.gain.value"),1.1);
 assert.equal(calls.output,"out1");
 assert.match(get("monitorStatus").textContent,/Scarlett Solo USB/);
});
test("manual crossfader persists when switching MIDI scenes and updates native AU while dragging",async()=>{
 const {run,calls,get}=rig();await run("startStop()");
 run("aiNativeReady=true");
 get("mix").value="35";
 get("mix").oninput();
 run('choose("fishes")');
 assert.equal(get("mix").value,"35","song selection must not reset chosen crossfade");
 for(let i=0;i<8;i++)await new Promise(resolve=>setImmediate(resolve));
 const mixes=calls.midi.filter(x=>x.url==="/api/ai/mix");
 assert.ok(mixes.some(x=>JSON.parse(x.opts.body).value===.35));
 assert.equal(get("mixValue").textContent,"65 / 35");
});
test("independent song on/off gates its browser voice and native scene mix",async()=>{
 const {run,get,calls}=rig();await run("startStop()");
 run("aiNativeReady=true");
 get("mix").value="50";run("updateMix()");
 run('setSongEnabled("pyramid")');
 assert.equal(run("decks.pyramid.enabled"),false);
 assert.equal(run("decks.pyramid.voiceBus.gain.value"),0);
 assert.equal(run("effectiveSongMix()"),1);
 assert.equal(get("songEnabled-pyramid").getAttribute?.("aria-pressed")||"false","false");
 run('setSongEnabled("fishes")');
 assert.equal(run("decks.fishes.enabled"),true,"last available song cannot be disabled");
 run('setSongEnabled("pyramid")');
 assert.equal(run("decks.pyramid.enabled"),true);
 assert.equal(run("effectiveSongMix()"),.5);
 for(let i=0;i<7;i++)await new Promise(resolve=>setImmediate(resolve));
 assert.ok(calls.midi.some(x=>x.url==="/api/ai/mix"));
});
test("stage UI hides optional local fallback and experimental voice follower without deleting their code",()=>{
 assert.match(file,/class="song-lead-panel"[^>]+hidden aria-hidden="true"/);
 assert.match(file,/class="voice-ai-follow"[^>]+hidden aria-hidden="true"/);
 assert.match(file,/id="performanceMaster"/);
 assert.match(file,/id="songEnabled-pyramid"/);
 assert.match(file,/id="songEnabled-fishes"/);
 const code=file.slice(file.indexOf("<script>"));
 assert.match(code,/function setSongEnabled\(which\)/);
 assert.match(code,/function updateVoiceEcho\(\)/);
});
