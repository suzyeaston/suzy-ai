"use strict";
const test=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const base=path.join(__dirname,"..","performance","film-club-2026");
const score=require(path.join(base,"score.js"));
const audio=require(path.join(base,"audio.js"));
const html=fs.readFileSync(path.join(base,"index.html"),"utf8");
const app=fs.readFileSync(path.join(base,"app.js"),"utf8");

test("exactly five editorial scenes cover all 60 seconds without a gap",()=>{
  assert.equal(score.DURATION,60);
  assert.equal(score.SCENES.length,5);
  assert.deepEqual(score.SCENES.map(s=>[s.start,s.end]),[[0,10],[10,24],[24,38],[38,48],[48,60]]);
  for(let sec=0;sec<60;sec+=.125){
    const s=score.sceneAt(sec);
    assert.ok(sec>=s.start&&sec<s.end,"missing scene at "+sec);
  }
  assert.equal(score.sceneAt(24).id,"war");
  assert.equal(score.sceneAt(38).id,"intervene");
});
test("accelerando and human tempo interruption are real, not a label",()=>{
  assert.equal(score.tempoAt(0),72);
  assert.ok(score.tempoAt(23.9)>score.tempoAt(11));
  assert.ok(score.tempoAt(37)>score.tempoAt(24));
  assert.equal(score.tempoAt(39),78);
  assert.equal(score.tempoAt(50),104);
  const beats=score.beats();
  assert.ok(beats.length>90&&beats.length<200);
  for(let i=1;i<beats.length;i++)assert.ok(beats[i].t>beats[i-1].t);
  assert.ok(beats.at(-1).t<60);
});
test("original composition has genuinely timed bass, glass, strings, drum, metal and human notes",()=>{
  const events=score.buildScore("soft-reset");
  const tracks=new Set(events.map(e=>e.track));
  for(const track of ["bass","glass","strings","drums","metal","human"])
    assert.ok(tracks.has(track),"missing "+track);
  assert.ok(events.length>130);
  assert.ok(events.every((e,i)=>e.t>=0&&e.t<60&&e.dur>0&&e.t+e.dur<=60.0001&&
     e.velocity>=0&&e.velocity<=1&&(i===0||events[i-1].t<=e.t)));
  assert.ok(events.some(e=>e.t>=24&&e.t<38&&e.track==="metal"));
  assert.ok(!events.some(e=>e.t>=38&&e.t<48&&e.track==="metal"));
  assert.ok(events.some(e=>e.t>=38&&e.t<48&&e.track==="human"));
  assert.ok(events.some(e=>e.t>=48&&e.t<60&&e.track==="human"));
  assert.deepEqual(score.buildScore("soft-reset"),events,"score should be deterministic");
});
test("Pyramid Orbit is a harmonic palette without shipping a cover recording",()=>{
  assert.deepEqual(score.PROGRESSIONS["pyramid-orbit"].map(c=>c.name),["F♯","Gmaj7","A6","F♯"]);
  assert.notDeepEqual(score.buildScore("soft-reset"),score.buildScore("pyramid-orbit"));
  assert.throws(()=>score.buildScore("radiohead-cover"),/Unknown harmonic palette/);
  assert.ok(!html.includes("<audio"));
  assert.ok(html.includes("/toaster/live"));
});
test("cue sheet aligns to simulator film edit, no claim of direct integration",()=>{
  const cues=score.cues();
  assert.deepEqual(cues.map(c=>c.time_sec),[0,10,24,38,48]);
  assert.equal(cues.at(-1).end_sec,60);
  assert.ok(cues.every(c=>typeof c.visual_event==="string"&&c.treatment.length>20));
  assert.match(app,/manual_alignment_required:true/);
  assert.match(app,/original_music:true/);
  assert.match(html,/do not yet control the simulator automatically/i);
});
test("performer interface has independent transport, real rendering and keyboard overdub",()=>{
  for(const id of ["play","stop","loop","palette","pads","overdub","clearOverdub","audioFile","clearAudio","exportWav","exportCues","master","tracks"]){
    assert.match(html,new RegExp('id="'+id+'"'));
  }
  assert.match(app,/new Offline\(2,score.DURATION\*44100,44100\)/);
  assert.match(app,/renderCtx.startRendering\(\)/);
  assert.match(app,/ctx.decodeAudioData\(data.slice\(0\)\)/);
  assert.match(app,/audio.schedulePrint\(renderCtx,bus,printBuffer,0,0\)/);
  assert.match(app,/const keys=\{a:0,s:1,d:2,f:3,g:4\}/);
  assert.doesNotMatch(html,/<script src="https:/i);
  assert.doesNotMatch(app,/fetch\(/);
});
test("PCM export produces a genuine 16-bit stereo RIFF WAV with correct sample values",async()=>{
  const samples=[new Float32Array([-.5,0,.5]),new Float32Array([.25,-.25,1])];
  const blob=audio.wav({numberOfChannels:2,length:3,sampleRate:44100,getChannelData:i=>samples[i]});
  const data=new DataView(await blob.arrayBuffer());
  const str=(at,n)=>Array.from({length:n},(_,i)=>String.fromCharCode(data.getUint8(at+i))).join("");
  assert.equal(str(0,4),"RIFF");assert.equal(str(8,4),"WAVE");assert.equal(str(36,4),"data");
  assert.equal(data.getUint32(24,true),44100);
  assert.equal(data.getUint16(22,true),2);
  assert.equal(data.getUint16(34,true),16);
  assert.equal(data.getInt16(44,true),-16384);
  assert.equal(data.getInt16(46,true),8192);
  assert.equal(blob.size,56);
});
test("Web Audio nodes schedule and preserve an imported print source",()=>{
  const param=()=>({value:0,setValueAtTime(){},linearRampToValueAtTime(){},exponentialRampToValueAtTime(){},setTargetAtTime(){}});
  const node=()=>({gain:param(),frequency:param(),detune:param(),threshold:param(),knee:param(),ratio:param(),attack:param(),release:param(),connect(){return this;},disconnect(){},start(t,offset){this.started=[t,offset];},stop(t){this.stopped=t;}});
  const context={
    sampleRate:44100,currentTime:0,destination:node(),
    createGain:node,createDynamicsCompressor:node,createBiquadFilter:node,
    createOscillator:node,createBufferSource:node,
    createBuffer:(channels,n)=>({getChannelData:()=>new Float32Array(n)})
  };
  const levels=Object.fromEntries(score.TRACKS.map(t=>[t.id,t.level]));
  levels.print=.5;
  const mix=audio.createMix(context,levels,.72);
  const sources=audio.schedule(context,mix,score.buildScore().slice(0,40),.1);
  assert.ok(sources.length>30);
  const imported=audio.schedulePrint(context,mix,{duration:8},.1,3);
  assert.deepEqual(imported.started,[3.1,3]);
  assert.equal(imported.stopped,60.1);
});
