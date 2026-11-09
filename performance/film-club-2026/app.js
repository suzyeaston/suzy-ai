/* SOFT RESET / Film Club 2026: browser-only performance controller.
 * A 60-second video cue clock is the source of truth. Pyramid is a harmonic
 * palette; the original Futureproof instrument is a separate, unchanged app.
 */
"use strict";
(() => {
  const $ = id => document.getElementById(id);
  const score = window.SoftResetScore, audio = window.SoftResetAudio;
  if (!score || !audio) throw Error("Film Club score and audio modules are required");
  const levels = Object.fromEntries(score.TRACKS.map(t => [t.id,t.level]));
  levels.print=.55;
  let palette="soft-reset", events=score.buildScore(palette), humanTakes=[];
  let ctx=null,mix=null,playing=false,looping=true,armed=false,position=0;
  let cycleStart=0,activeSources=[],queuedSources=[],queued=false,ticker=null;
  let printBuffer=null,printName=null,exporting=false;
  const keys={a:0,s:1,d:2,f:3,g:4};
  const held=new Set();
  const clamp=(n,lo,hi)=>Math.min(hi,Math.max(lo,n));
  const timestamp=t=>"00:"+String(Math.floor(clamp(t,0,60))).padStart(2,"0");
  const allEvents=()=>events.concat(humanTakes).sort((a,b)=>a.t-b.t);
  function notify(message,error=false){$("status").textContent=message;$("status").classList.toggle("error",error);}
  function currentPosition(){return playing&&ctx?clamp(ctx.currentTime-cycleStart,0,score.DURATION):position;}
  function makeMix(){mix=audio.createMix(ctx,levels,Number($("master").value)/100);}
  async function ensureAudio(){
    if(!ctx){
      const Context=window.AudioContext||window.webkitAudioContext;
      if(!Context)throw Error("This browser does not support Web Audio.");
      ctx=new Context();makeMix();
    }
    if(ctx.state==="suspended")await ctx.resume();
    return ctx;
  }
  function stopSources(sources){
    for(const src of sources)try{src.stop(0);}catch{}
  }
  function cancelAudio(){
    stopSources(activeSources);stopSources(queuedSources);
    activeSources=[];queuedSources=[];queued=false;
  }
  function schedulePass(start,offset=0){
    const scheduled=audio.schedule(ctx,mix,allEvents(),start,offset);
    const print=audio.schedulePrint(ctx,mix,printBuffer,start,offset);
    if(print)scheduled.push(print);
    return scheduled;
  }
  function updateUi(){
    const pos=currentPosition(),scene=score.sceneAt(Math.min(pos,59.999));
    $("timecode").innerHTML=timestamp(pos)+' <span>/ 01:00</span>';
    $("progress").style.width=(pos/score.DURATION*100).toFixed(2)+"%";
    $("ruler").setAttribute("aria-valuenow",pos.toFixed(1));
    $("nowScene").textContent=scene.title;
    $("bpm").textContent=Math.round(score.tempoAt(pos))+" BPM";
    $("cueIndex").textContent=scene.start+"–"+scene.end+" SEC";
    $("cueTitle").textContent=scene.title;
    $("cueDescription").textContent=scene.visual;
    for(const button of document.querySelectorAll(".scene"))
      button.classList.toggle("active",button.dataset.scene===scene.id);
    $("play").textContent=playing?"Ⅱ PAUSE / STOP":"▶ PLAY FILM SCORE";
  }
  function tick(){
    if(!playing||!ctx)return;
    const now=ctx.currentTime;
    if(looping&&!queued&&now>=cycleStart+score.DURATION-1.5){
      queuedSources=schedulePass(cycleStart+score.DURATION,0);
      queued=true;
    }
    if(now>=cycleStart+score.DURATION){
      if(looping){
        cycleStart+=score.DURATION;
        activeSources=queuedSources;queuedSources=[];queued=false;
      }else{
        position=0;playing=false;cancelAudio();
        clearInterval(ticker);ticker=null;
        notify("ONE-MINUTE PASS COMPLETE · Ready to render or restart.");
      }
    }
    updateUi();
  }
  async function start(at=position){
    try{
      await ensureAudio();
      if(playing)cancelAudio();
      position=clamp(at,0,59.99);
      cycleStart=ctx.currentTime+.085-position;
      activeSources=schedulePass(cycleStart,position);
      playing=true;
      clearInterval(ticker);ticker=setInterval(tick,90);
      tick();
      notify("PLAYING · "+score.sceneAt(position).title+" · original browser audio.");
    }catch(e){notify("AUDIO FAILED · "+(e.message||e),true);}
  }
  function stop(reset=true){
    if(playing)position=currentPosition();
    playing=false;cancelAudio();
    if(reset)position=0;
    clearInterval(ticker);ticker=null;
    updateUi();
  }
  function seek(time){
    const wasPlaying=playing;
    stop(false);
    position=clamp(time,0,59.99);
    updateUi();
    if(wasPlaying)void start(position);
  }
  function setPalette(which){
    if(!Object.hasOwn(score.PROGRESSIONS,which))return;
    const resumeAt=currentPosition(),wasPlaying=playing;
    stop(false);palette=which;events=score.buildScore(palette);
    position=resumeAt;updateUi();
    if(wasPlaying)void start(position);
    notify("HARMONY · "+(which==="soft-reset"?"SOFT RESET original score":"PYRAMID ORBIT reference chord palette")+". No copyrighted audio was loaded.");
  }
  function renderTracks(){
    const tracks=score.TRACKS.concat([{id:"print",label:"07 · Your audio print",role:"Imported take (optional)",level:.55,color:"#bbd8a3"}]);
    const wrap=$("tracks");wrap.replaceChildren();
    for(const track of tracks){
      const row=document.createElement("div");
      row.className="track";row.style.setProperty("--accent",track.color);
      const mute=document.createElement("button");mute.type="button";mute.textContent="◖))";
      mute.setAttribute("aria-label","Mute "+track.label);mute.setAttribute("aria-pressed","false");
      mute.addEventListener("click",()=>{
        const muted=mute.getAttribute("aria-pressed")==="true";
        mute.setAttribute("aria-pressed",String(!muted));
        mute.textContent=muted?"◖))":"×";
        mute.setAttribute("aria-label",(muted?"Mute ":"Unmute ")+track.label);
        const next=muted?Number(fader.value)/100:0;
        levels[track.id]=next;
        if(mix)mix.channels[track.id].gain.setTargetAtTime(next,ctx.currentTime,.025);
        notify((muted?"UNMUTED":"MUTED")+" · "+track.label);
      });
      const name=document.createElement("div");name.className="track-name";
      const title=document.createElement("div");title.className="track-title";title.textContent=track.label;
      const role=document.createElement("div");role.className="track-role";role.textContent=track.role;
      name.append(title,role);
      const fader=document.createElement("input");fader.type="range";fader.min="0";fader.max="100";
      fader.value=String(Math.round(track.level*100));fader.setAttribute("aria-label",track.label+" level");
      const output=document.createElement("output");output.textContent=fader.value+"%";
      fader.addEventListener("input",()=>{
        output.textContent=fader.value+"%";
        const muted=mute.getAttribute("aria-pressed")==="true";
        if(!muted)levels[track.id]=Number(fader.value)/100;
        if(mix)mix.channels[track.id].gain.setTargetAtTime(levels[track.id],ctx.currentTime,.025);
      });
      row.append(mute,name,fader,output);wrap.append(row);
    }
  }
  function quantize(t){
    let best=0,distance=Infinity;
    for(const beat of score.beats()){
      for(const factor of [0,.5]){
        const candidate=beat.t+beat.length*factor;
        const diff=Math.abs(candidate-t);
        if(candidate<score.DURATION&&diff<distance){best=candidate;distance=diff;}
      }
    }
    return Math.round(best*1000)/1000;
  }
  async function playPad(index){
    const pad=score.PADS[index];
    if(!pad)return;
    try{
      await ensureAudio();
      const ev={t:0,track:"human",kind:"human",note:pad.note,dur:.85,velocity:.73};
      activeSources.push(...audio.play(ctx,mix.channels.human,ev,ctx.currentTime+.008));
      if(armed&&playing){
        if(humanTakes.length>=256){notify("256-gesture limit reached. Export before clearing.",true);return;}
        const t=quantize(currentPosition());
        const take={...ev,t};
        humanTakes.push(take);
        // If the next loop was queued before this gesture, still schedule it.
        if(queued)queuedSources.push(...audio.schedule(ctx,mix,[take],cycleStart+score.DURATION));
        $("takeCount").textContent=humanTakes.length+" notes saved";
        notify("OVERDUB · "+pad.name+" at "+timestamp(t)+" · returns on the next loop.");
      }
    }catch(e){notify("PAD AUDIO FAILED · "+(e.message||e),true);}
  }
  function renderPads(){
    const wrap=$("pads");wrap.replaceChildren();
    for(const [index,pad] of score.PADS.entries()){
      const btn=document.createElement("button");btn.type="button";btn.className="pad";
      btn.innerHTML="<kbd>"+Object.keys(keys)[index].toUpperCase()+"</kbd><span>"+pad.name+"</span>";
      btn.addEventListener("pointerdown",()=>{btn.classList.add("pressed");void playPad(index);});
      for(const name of ["pointerup","pointercancel","pointerleave"])btn.addEventListener(name,()=>btn.classList.remove("pressed"));
      wrap.append(btn);
    }
  }
  function download(blob,name){
    const url=URL.createObjectURL(blob);
    const link=document.createElement("a");link.href=url;link.download=name;
    document.body.append(link);link.click();link.remove();
    setTimeout(()=>URL.revokeObjectURL(url),10000);
  }
  function exportCues(){
    const cueSheet={
      schema_version:"suzy-film-cues/v1",project:"SOFT RESET",
      duration_sec:score.DURATION,original_music:true,
      soundtrack_source:"SUZY//AI local Web Audio + optional user-provided print",
      visual_project:"Gastown Simulator",manual_alignment_required:true,
      palette,tempo_curve:"piecewise acceleration + human slowdown",
      cues:score.cues(palette),beats:score.beats().map(b=>({second:b.t,bpm:b.bpm})),
      overdubs:humanTakes.map(ev=>({time_sec:ev.t,midi_note:ev.note,duration_sec:ev.dur})),
      imported_print:printName?{filename:printName,embedded:false}:null
    };
    download(new Blob([JSON.stringify(cueSheet,null,2)+"\n"],{type:"application/json"}),"soft-reset-gastown-cues.json");
    notify("VISUAL CUES EXPORTED · Import/recreate timing in Gastown Simulator or your editor.");
  }
  async function exportWav(){
    if(exporting)return;
    exporting=true;$("exportWav").disabled=true;
    notify("RENDERING · 60 seconds of real PCM audio in the browser.");
    try{
      const Offline=window.OfflineAudioContext||window.webkitOfflineAudioContext;
      if(!Offline)throw Error("OfflineAudioContext is unsupported in this browser");
      const renderCtx=new Offline(2,score.DURATION*44100,44100);
      const bus=audio.createMix(renderCtx,levels,Number($("master").value)/100);
      audio.schedule(renderCtx,bus,allEvents(),0,0);
      audio.schedulePrint(renderCtx,bus,printBuffer,0,0);
      const pcm=await renderCtx.startRendering();
      download(audio.wav(pcm),"soft-reset-60s-master.wav");
      notify("WAV EXPORTED · 60s / stereo / 44.1 kHz / 16-bit PCM. Listen and approve before submission.");
    }catch(e){notify("WAV RENDER FAILED · "+(e.message||e),true);}
    finally{exporting=false;$("exportWav").disabled=false;}
  }
  async function importPrint(file){
    if(!file)return;
    try{
      if(file.size>70*1024*1024)throw Error("Audio print exceeds the 70 MB first-iteration limit");
      await ensureAudio();
      const data=await file.arrayBuffer();
      const decoded=await ctx.decodeAudioData(data.slice(0));
      if(!decoded.duration||decoded.duration>600)throw Error("Expected an audio print up to ten minutes");
      printBuffer=decoded;printName=file.name;
      $("fileName").textContent=file.name+" · "+decoded.duration.toFixed(1)+" s";
      if(playing)seek(currentPosition());
      notify("PRINT LOADED · User-supplied audio, repeated if shorter than 60s. No AI provenance is assumed.");
    }catch(e){notify("IMPORT FAILED · "+(e.message||e),true);}
  }
  function bind(){
    renderTracks();renderPads();
    for(const scene of score.SCENES){
      const b=document.createElement("button");b.type="button";b.className="scene";b.dataset.scene=scene.id;
      b.title=scene.title+" · jump to "+scene.start+"s";
      b.innerHTML='<span class="number">'+(score.SCENES.indexOf(scene)+1)+'</span><span>'+scene.title.split(" / ")[1]+'</span><span class="sec">'+scene.start+'–'+scene.end+'s</span>';
      b.onclick=()=>seek(scene.start);$("scenes").append(b);
    }
    $("play").onclick=()=>{if(playing){stop(false);notify("STOPPED · Tap PLAY to begin again.");}else void start(position);};
    $("stop").onclick=()=>{stop();notify("STOPPED · Back at the opening.");};
    $("loop").onclick=()=>{
      looping=!looping;$("loop").setAttribute("aria-pressed",String(looping));
      $("loop").textContent=looping?"∞ LOOP ON":"↦ ONE PASS";
      if(!looping&&queued){stopSources(queuedSources);queuedSources=[];queued=false;}
      notify(looping?"60-second loop enabled.":"One-pass mode. Playback ends at 60 seconds.");
    };
    $("ruler").onclick=e=>{
      const r=e.currentTarget.getBoundingClientRect();
      seek((e.clientX-r.left)/r.width*score.DURATION);
    };
    $("palette").onchange=e=>setPalette(e.target.value);
    $("master").oninput=e=>{
      const v=Number(e.target.value)/100;
      $("masterRead").textContent=Math.round(v*100)+"%";
      if(mix)mix.masterGain.gain.setTargetAtTime(v,ctx.currentTime,.03);
    };
    $("overdub").onclick=()=>{
      armed=!armed;$("overdub").setAttribute("aria-pressed",String(armed));
      $("overdub").textContent=armed?"● RECORDING GESTURES":"● ARM OVERDUB";
      notify(armed?"OVERDUB ARMED · Play A S D F G while the transport runs.":"OVERDUB DISARMED · Recorded gestures remain in the song.");
    };
    $("clearOverdub").onclick=()=>{
      if(humanTakes.length&&!confirm("Clear your saved human gestures? The built-in melody stays."))return;
      humanTakes=[];$("takeCount").textContent="0 notes saved";
      if(playing)seek(currentPosition());
      notify("RECORDED HUMAN GESTURES CLEARED · Composed melody retained.");
    };
    $("audioFile").onchange=e=>{
      const file=e.target.files&&e.target.files[0];if(file)void importPrint(file);
      e.target.value="";
    };
    $("clearAudio").onclick=()=>{
      printBuffer=null;printName=null;$("fileName").textContent="Nothing loaded";
      if(playing)seek(currentPosition());
      notify("IMPORTED AUDIO REMOVED · Synthetic tracks unaffected.");
    };
    $("exportCues").onclick=exportCues;
    $("exportWav").onclick=()=>void exportWav();
    document.addEventListener("keydown",e=>{
      if(e.metaKey||e.ctrlKey||e.altKey||e.repeat)return;
      const target=e.target;
      if(target&&(target.isContentEditable||["INPUT","SELECT","TEXTAREA"].includes(target.tagName)))return;
      const key=e.key.toLowerCase();
      if(Object.hasOwn(keys,key)){
        e.preventDefault();if(held.has(key))return;held.add(key);void playPad(keys[key]);
        $("pads").children[keys[key]].classList.add("pressed");
      }
      if(e.code==="Space"){e.preventDefault();$("play").click();}
      if(e.key==="Escape"){stop();notify("TRANSPORT HALTED · No native Magenta host was changed.");}
    });
    document.addEventListener("keyup",e=>{
      const key=e.key.toLowerCase();held.delete(key);
      if(Object.hasOwn(keys,key))$("pads").children[keys[key]].classList.remove("pressed");
    });
    window.addEventListener("blur",()=>{held.clear();for(const b of $("pads").children)b.classList.remove("pressed");});
    updateUi();
  }
  bind();
})();
