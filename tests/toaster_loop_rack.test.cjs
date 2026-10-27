/* Browser-free functional QA for TOASTER Loop Rack, using Node built-ins only. */
"use strict";
const {test}=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const vm=require("node:vm");
const path=require("node:path");
const script=fs.readFileSync(path.join(__dirname,"..","suzy_ai/music/toaster_loop_rack.js"),"utf8");
function harness(){
 const nodes=new Map();
 const element=()=>({
  style:{},dataset:{},children:[],disabled:false,hidden:false,value:"",
  replaceChildren(){this.children=[];},appendChild(v){this.children.push(v);return v;},
  append(...v){this.children.push(...v);},
  remove(){},setAttribute(){},
 });
 function get(id){
  if(!nodes.has(id))nodes.set(id,element());
  return nodes.get(id);
 }
 get("rackBars").value="2";get("tempo").value="120";
 const document={
  getElementById:get,createElement:()=>element(),body:element(),
 };
 let currentTime=5;
 class Buffer {
  constructor(ch,length,sr){this.numberOfChannels=ch;this.length=length;this.sampleRate=sr;this.duration=length/sr;
   this.data=Array.from({length:ch},()=>new Float32Array(length));}
  getChannelData(i){return this.data[i];}
 }
 const emitted=[];
 const context={
  sampleRate:48000,
  get currentTime(){return currentTime;}, set currentTime(t){currentTime=t;},
  destination:{},
  createBuffer:(ch,length,sr)=>new Buffer(ch,length,sr),
  createBufferSource(){const n={buffer:null,loop:false,start(...args){emitted.push(["start",...args]);},
    stop(){emitted.push(["stop"]);},connect(){return this;}};return n;},
  createGain(){return {gain:{value:0,setTargetAtTime(v){this.value=v;}},connect(){return this;}};},
  createMediaStreamDestination(){return {stream:{getAudioTracks:()=>[{}]}};},
  decodeAudioData:async()=>new Buffer(1,4800,48000),
 };
 const sourceBus={connect(){}};
 let mic={getAudioTracks:()=>[{}]};
 const messages=[];
 const env={document,requestAnimationFrame(){return 1;},setTimeout(){return 1;},clearTimeout(){},
   confirm(){return true;},URL:{createObjectURL(){return "blob:local";},revokeObjectURL(){}},
   navigator:{mediaDevices:{getDisplayMedia:async()=>({
     getAudioTracks:()=>[],getTracks:()=>[{stop(){}}]
   })}},
 };
 const sandbox={window:env,Blob,MediaRecorder:class {
   constructor(){this.state="inactive";this.mimeType="audio/webm";}
   start(){this.state="recording";}
   stop(){this.state="inactive";this.ondataavailable?.({data:new Blob(["audio"])});this.onstop?.();}
 }};
 vm.runInNewContext(script,sandbox,{filename:"toaster_loop_rack.js"});
 const rack=new env.SuzyLoopRack({
  audio:async()=>context,ensureLocal:async()=>{},getChordBus:()=>sourceBus,
  getMicStream:()=>mic,ensureMic:async()=>{},onMessage:m=>messages.push(m),
 });
 return {rack,get,context,emitted,messages,Buffer,env};
}
test("Loop Lab-style independent chord/voice/AI lanes with mute, solo and remove",async()=>{
 const {rack,get,context,Buffer,emitted}=harness();
 await rack.context();
 const audio=new Buffer(1,9600,48000);audio.getChannelData(0).fill(.3);
 rack.add("chord",audio,{duration:.2,name:"Keys"});
 rack.add("vocal",audio,{name:"VE-22"});
 rack.add("ai",audio,{name:"MRT2 printed audio"});
 assert.equal(rack.layers.length,3);
 assert.equal(rack.length,.2);
 assert.equal(get("rackLayers").children.length,3);
 assert.equal(get("rackMeta").textContent.includes("3 lanes"),true);
 assert.equal(get("rackBars").disabled,true);
 assert.ok(emitted.some(x=>x[0]==="start"));
 rack.mute(2);assert.equal(rack.layers[1].gain.gain.value,0);
 rack.solo(3);assert.equal(rack.layers[0].gain.gain.value,0);
 assert.equal(rack.layers[2].gain.gain.value,.55);
 rack.remove(3);assert.equal(rack.layers.length,2);
 assert.equal(rack.soloId,null);
 rack.toggle();assert.equal(rack.playing,false);
 rack.toggle();assert.equal(rack.playing,true);
 rack.remove(1);rack.remove(2);
 assert.equal(rack.length,0);
 assert.equal(get("rackBars").disabled,false);
});
test("Magenta audio never auto-populates from MIDI: explicit import only",async()=>{
 const {rack,get,context}=harness();
 await rack.context();
 assert.equal(rack.layers.length,0);
 await rack.capture("ai");
 assert.equal(rack.layers.length,0,"no audio track in screen share is not captured AI");
 assert.match(get("rackMessage").textContent,/did not share Collider audio/);
 const f={name:"magenta-recording.wav",type:"audio/wav",size:100,
   arrayBuffer:async()=>new ArrayBuffer(20)};
 await rack.importAI(f);
 assert.equal(rack.layers.length,1);
 assert.equal(rack.layers[0].kind,"ai");
 assert.match(rack.layers[0].name,/magenta-recording.wav/);
});
test("WAV export is deterministic RIFF PCM and destructive clear is guarded",async()=>{
 const {rack,Buffer,get,env}=harness();
 await rack.context();
 const sample=new Buffer(2,3000,48000);
 sample.getChannelData(0).fill(.5);
 const bytes=env.SuzyLoopRackWav(sample),d=new DataView(bytes);
 assert.equal(String.fromCharCode(...new Uint8Array(bytes,0,4)),"RIFF");
 assert.equal(String.fromCharCode(...new Uint8Array(bytes,8,4)),"WAVE");
 assert.equal(d.getUint16(22,true),2);
 assert.equal(bytes.byteLength,44+3000*4);
 rack.add("chord",sample,{duration:.0625,name:"Synth"});
 rack.clear();assert.equal(rack.layers.length,0);
 assert.equal(get("rackLayers").children.length,0);
});

test("real mixer faders affect audible rack lanes without mutating clips",async()=>{
 const {rack,Buffer,get}=harness();
 await rack.context();
 const buffer=new Buffer(1,9600,48000);
 rack.add("chord",buffer,{duration:.2,name:"Synth"});
 rack.add("vocal",buffer,{name:"Voice"});
 rack.add("ai",buffer,{name:"Actual captured AI"});
 rack.setKindGain("chord",.25);
 rack.setKindGain("vocal",0);
 rack.setKindGain("ai",.75);
 assert.equal(rack.layers[0].gain.gain.value,.55*.25);
 assert.equal(rack.layers[1].gain.gain.value,0);
 assert.equal(rack.layers[2].gain.gain.value,.55*.75);
 assert.equal(rack.layers.length,3);
 assert.equal(get("rackRuler").children.length,2);
 assert.throws(()=>rack.setKindGain("fake",.5),/Unknown/);
 assert.throws(()=>rack.setKindGain("ai",2),/outside/);
});
