/* SUZY//TOAST Loop Rack. Inspired by Suzy's own Loop Lab (suzyeastonca/js/loop-lab.js).
 * Browser-local: audible chord synth bus, Scarlett/VE-22 mic, or explicitly captured/
 * imported Magenta AUDIO. Only an actual AI-audio track earns the "AI" label.
 * Not sample-accurate host-DAW synchronization. No third-party dependencies.
 */
(function(root) {
  "use strict";
  const KIND = Object.freeze({chord:"CHORD",vocal:"VOCAL",ai:"MAGENTA AI"});
  const MAX_TRACKS = 16;
  const MAX_SECONDS = 16.5;
  const $ = id => root.document.getElementById(id);

  function wav(buffer) {
    const channels = Math.min(2, Math.max(1, buffer.numberOfChannels));
    const frames = buffer.length;
    const size = 44 + frames * channels * 2;
    const bytes = new ArrayBuffer(size);
    const d = new DataView(bytes);
    const tag = (at, s) => { for(let i=0;i<s.length;i++)d.setUint8(at+i,s.charCodeAt(i)); };
    tag(0,"RIFF");d.setUint32(4,size-8,true);tag(8,"WAVE");tag(12,"fmt ");
    d.setUint32(16,16,true);d.setUint16(20,1,true);d.setUint16(22,channels,true);
    d.setUint32(24,buffer.sampleRate,true);d.setUint32(28,buffer.sampleRate*channels*2,true);
    d.setUint16(32,channels*2,true);d.setUint16(34,16,true);
    tag(36,"data");d.setUint32(40,size-44,true);
    const data=Array.from({length:channels},(_,ch)=>buffer.getChannelData(ch));
    let p=44;
    for(let i=0;i<frames;i++)for(let ch=0;ch<channels;ch++){
      const x=Math.max(-1,Math.min(1,Number.isFinite(data[ch][i])?data[ch][i]:0));
      d.setInt16(p,x<0?Math.round(x*32768):Math.round(x*32767),true);p+=2;
    }
    return bytes;
  }
  function download(buffer,name){
    const url=URL.createObjectURL(new Blob([wav(buffer)],{type:"audio/wav"}));
    const a=root.document.createElement("a");
    a.href=url;a.download=name;
    root.document.body.appendChild(a);a.click();a.remove();
    root.setTimeout(()=>URL.revokeObjectURL(url),3000);
  }
  function waveBars(buffer) {
    const bins=48,d=buffer.getChannelData(0),step=Math.max(1,Math.floor(d.length/bins));
    const values=[];
    for(let i=0;i<bins;i++){
      let peak=0;for(let j=i*step;j<Math.min(d.length,(i+1)*step);j+=Math.max(1,Math.floor(step/128)))peak=Math.max(peak,Math.abs(d[j]));
      values.push(Math.max(5,Math.round(peak*100)));
    }
    return values;
  }

  class Rack {
    constructor({audio,ensureLocal,getChordBus,getMicStream,ensureMic,onMessage,getAudioBus}){
      this.audio=audio;this.ensureLocal=ensureLocal;this.getChordBus=getChordBus;
      this.getMicStream=getMicStream;this.ensureMic=ensureMic;this.onMessage=onMessage;
      this.getAudioBus=getAudioBus||(()=>this.ctx.destination);
      this.kindGains={chord:1,vocal:1,ai:1};
      this.ctx=null;this.layers=[];this.epoch=0;this.length=0;this.bpm=0;
      this.bars=0;this.bus=null;this.recorder=null;this.timer=null;this.pending=false;
      this.trackId=0;this.playing=true;this.raf=0;this.tempStream=null;
      this.soloId=null;
      $("rackChord").onclick=()=>this.capture("chord");
      $("rackVocal").onclick=()=>this.capture("vocal");
      $("rackAI").onclick=()=>this.capture("ai");
      $("rackImport").onchange=e=>{const file=e.target.files?.[0];if(file)this.importAI(file);e.target.value="";};
      $("rackStopCapture").onclick=()=>this.stopCapture();
      $("rackToggle").onclick=()=>this.toggle();
      $("rackClear").onclick=()=>this.clear();
      $("rackExport").onclick=()=>this.exportMix();
      $("rackBars").onchange=()=>this.showStatus();
      this.render();this.tick();
    }
    notify(msg,failed=false){
      $("rackMessage").textContent=msg;
      $("rackMessage").style.color=failed?"#ffbbc1":"var(--mint)";
      if(this.onMessage)this.onMessage(msg);
    }
    async context(){
      this.ctx=await this.audio();
      return this.ctx;
    }
    duration(){
      if(this.length)return this.length;
      const bars=Number($("rackBars").value),tempo=Number($("tempo").value);
      if(![1,2,4].includes(bars)||!Number.isFinite(tempo)||tempo<60||tempo>190)
        throw Error("Choose 1, 2 or 4 bars and a tempo from 60–190 BPM");
      const seconds=bars*4*60/tempo;
      if(seconds>MAX_SECONDS)throw Error("Loop too long for this live browser rack");
      return seconds;
    }
    async capture(kind){
      let stream=null,screen=null;
      if(this.pending||this.recorder)return this.notify("A recording is already in progress.",true);
      if(this.layers.length>=MAX_TRACKS)return this.notify("16 layer limit reached. Export or remove a lane.",true);
      try{
        this.pending=true;
        // macOS/Chrome requires getDisplayMedia while the user's direct click
        // still has activation. Request immediately, before awaiting AudioContext.
        let screenRequest=null;
        if(kind==="ai"){
          if(!root.navigator.mediaDevices?.getDisplayMedia)
            throw Error("No screen-audio capture in this browser. Import a Magenta WAV instead.");
          screenRequest=root.navigator.mediaDevices.getDisplayMedia({video:true,audio:true});
        }
        const ctx=await this.context(),len=this.duration();
        if(typeof MediaRecorder==="undefined")throw Error("MediaRecorder is unavailable in this browser");
        if(kind==="chord"){
          await this.ensureLocal();
          if(!this.bus){this.bus=ctx.createMediaStreamDestination();this.getChordBus().connect(this.bus);}
          stream=this.bus.stream;
        }else if(kind==="vocal"){
          if(!this.getMicStream())await this.ensureMic();
          stream=this.getMicStream();
          if(!stream?.getAudioTracks().length)throw Error("Enable Scarlett/VE-22 mic first in Vocal Input below");
        }else if(kind==="ai"){
          screen=await screenRequest;
          if(!screen.getAudioTracks().length){
            screen.getTracks().forEach(t=>t.stop());
            throw Error("macOS did not share Collider audio. This is not captured AI. Export/print Magenta in Logic then IMPORT AI WAV.");
          }
          stream=new MediaStream(screen.getAudioTracks());
          this.tempStream=screen;
        }else throw Error("Invalid capture lane");
        const chunks=[];
        const recorder=new MediaRecorder(stream);
        this.recorder=recorder;this.pending=false;
        $("rackStopCapture").disabled=false;
        $("rackChord").disabled=$("rackVocal").disabled=$("rackAI").disabled=true;
        const startAt=this.length&&this.playing?this.epoch+Math.ceil(Math.max(0,ctx.currentTime-this.epoch)/this.length)*this.length:ctx.currentTime;
        const delay=Math.max(0,startAt-ctx.currentTime);
        this.notify("ARMED "+KIND[kind]+" · "+(delay>0?"next loop boundary in "+delay.toFixed(1)+"s":"start now")+". Keep playing.");
        const run=()=>{
          if(this.recorder!==recorder)return;
          recorder.ondataavailable=e=>{if(e.data?.size)chunks.push(e.data);};
          recorder.onerror=e=>this.notify("Capture device error: "+(e.error?.message||"unknown"),true);
          recorder.onstop=async()=>{
            this.recorder=null;this._resetCaptureUI();
            if(this.tempStream){this.tempStream.getTracks().forEach(t=>t.stop());this.tempStream=null;}
            try{
              if(!chunks.length)throw Error("No audio data recorded");
              const blob=new Blob(chunks,{type:recorder.mimeType});
              const decoded=await ctx.decodeAudioData(await blob.arrayBuffer());
              this.add(kind,decoded,{duration:len,baseEpoch:startAt,
                name:kind==="ai"?"Magenta · captured shared audio":kind==="vocal"?"VE-22 / Scarlett":"TOASTER · chords"});
              this.notify(KIND[kind]+" recorded and looping. Mute, solo or remove it below.");
            }catch(e){this.notify("Capture not saved: "+e.message,true);}
          };
          try{recorder.start();this.notify("RECORDING "+KIND[kind]+" · "+len.toFixed(1)+" seconds");}
          catch(e){this.recorder=null;this._resetCaptureUI();this.notify(e.message,true);return;}
          this.timer=root.setTimeout(()=>{if(recorder.state==="recording")recorder.stop();},len*1000);
        };
        if(delay>0)this.timer=root.setTimeout(run,delay*1000);else run();
      }catch(e){
        this.pending=false;
        if(screen){screen.getTracks().forEach(t=>t.stop());this.tempStream=null;}
        this._resetCaptureUI();this.notify(e.message||String(e),true);
      }
    }
    _resetCaptureUI(){
      $("rackStopCapture").disabled=true;
      for(const id of ["rackChord","rackVocal","rackAI"])$(id).disabled=false;
      if(this.timer){root.clearTimeout(this.timer);this.timer=null;}
    }
    stopCapture(){
      if(this.pending)return;
      if(this.timer){root.clearTimeout(this.timer);this.timer=null;}
      if(this.recorder?.state==="recording"){this.recorder.stop();return;}
      if(this.recorder){
        this.recorder=null;
        if(this.tempStream){this.tempStream.getTracks().forEach(t=>t.stop());this.tempStream=null;}
        this._resetCaptureUI();
        this.notify("Armed capture cancelled.");
      }
    }
    normalize(buffer,seconds){
      const frames=Math.round(seconds*buffer.sampleRate),ch=Math.min(2,buffer.numberOfChannels);
      const target=this.ctx.createBuffer(ch,frames,buffer.sampleRate);
      for(let c=0;c<ch;c++){
        const src=buffer.getChannelData(c),dst=target.getChannelData(c);
        dst.set(src.subarray(0,Math.min(src.length,dst.length)));
      }
      return target;
    }
    add(kind,buffer,{duration=null,name="",baseEpoch=null}={}){
      if(!this.ctx)throw Error("Audio not initialized");
      if(this.layers.length>=MAX_TRACKS)throw Error("16 layer maximum");
      if(kind!=="chord"&&kind!=="vocal"&&kind!=="ai")throw Error("Invalid lane");
      const length=this.length||duration||this.duration();
      if(!this.length){
        this.length=length;this.bpm=Number($("tempo").value);this.bars=Number($("rackBars").value);
        this.epoch=baseEpoch??this.ctx.currentTime;
      }
      const clip=this.normalize(buffer,this.length);
      const id=++this.trackId;
      const layer={id,kind,name:name||KIND[kind],buffer:clip,muted:false,
          level:.55,source:null,gain:null,peaks:waveBars(clip)};
      this.layers.push(layer);
      if(this.playing)this.startLayer(layer);
      this.render();
      return layer;
    }
    startLayer(layer){
      if(layer.source)try{layer.source.stop();}catch{}
      const ctx=this.ctx;
      const src=ctx.createBufferSource(),gain=ctx.createGain();
      src.buffer=layer.buffer;src.loop=true;
      gain.gain.value=this.effectiveGain(layer);
      src.connect(gain);gain.connect(this.getAudioBus()||ctx.destination);
      const when=ctx.currentTime+.025;
      const offset=((when-this.epoch)%this.length+this.length)%this.length;
      src.start(when,offset);
      layer.source=src;layer.gain=gain;
    }
    effectiveGain(layer){return layer.muted||(this.soloId!==null&&layer.id!==this.soloId)?0:layer.level*this.kindGains[layer.kind];}
    setKindGain(kind,value){
      if(!Object.prototype.hasOwnProperty.call(this.kindGains,kind))throw Error('Unknown loop mixer channel');
      if(!Number.isFinite(value)||value<0||value>1)throw Error('Mixer fader outside 0..1');
      this.kindGains[kind]=value;
      this.updateLevels();
    }
    updateLevels(){
      for(const layer of this.layers){
        if(layer.gain)layer.gain.gain.setTargetAtTime(this.effectiveGain(layer),this.ctx.currentTime,.02);
      }
    }
    mute(id){
      const l=this.layers.find(x=>x.id===id);if(!l)return;
      l.muted=!l.muted;this.updateLevels();this.render();
    }
    solo(id){
      this.soloId=this.soloId===id?null:id;this.updateLevels();this.render();
    }
    remove(id){
      if(this.recorder||this.pending){this.notify("Finish recording before removing a lane.",true);return;}
      const idx=this.layers.findIndex(x=>x.id===id);if(idx<0)return;
      const layer=this.layers[idx];if(layer.source)try{layer.source.stop();}catch{}
      this.layers.splice(idx,1);
      if(this.soloId===id)this.soloId=null;
      if(!this.layers.length){this.length=0;this.epoch=0;this.soloId=null;}
      this.render();this.notify(KIND[layer.kind]+" lane removed. Other loops continue.");
    }
    toggle(){
      if(!this.layers.length)return this.notify("Capture your first loop before pressing Play.",true);
      this.playing=!this.playing;
      if(this.playing){
        this.epoch=this.ctx.currentTime;
        for(const l of this.layers)this.startLayer(l);
      }else for(const l of this.layers){if(l.source)try{l.source.stop();}catch{}l.source=null;l.gain=null;}
      this.render();this.notify(this.playing?"All unmuted lanes playing.":"Rack playback paused.");
    }
    clear(){
      if(this.recorder||this.pending)return this.notify("Finish recording first.",true);
      if(!this.layers.length)return;
      if(!root.confirm("Clear ALL "+this.layers.length+" loop lanes? Export anything you want to keep first."))return;
      this.layers.forEach(l=>{if(l.source)try{l.source.stop();}catch{}});
      this.layers=[];this.length=0;this.epoch=0;this.soloId=null;
      this.render();this.notify("Rack cleared. The VE-22/Scarlett routing is unchanged.");
    }
    async importAI(file){
      if(this.pending||this.recorder)return this.notify("Finish recording before importing.",true);
      if(this.layers.length>=MAX_TRACKS)return this.notify("16 lane limit. Remove one first.",true);
      try{
        if(file.size>30*1024*1024)throw Error("Keep imported Magenta audio below 30 MB");
        if(!(/audio\//.test(file.type)||/\.(wav|aiff?|mp3|m4a)$/i.test(file.name)))throw Error("Choose a valid audio file");
        await this.context();
        const b=await this.ctx.decodeAudioData(await file.arrayBuffer());
        if(!Number.isFinite(b.duration)||b.duration<=0)throw Error("Audio file empty");
        this.add("ai",b,{name:"Magenta · imported "+file.name,duration:this.duration(),baseEpoch:this.ctx.currentTime});
        this.notify("Imported AI audio. Verify provenance: this lane plays real supplied sound, not MIDI.");
      }catch(e){this.notify("Import failed: "+e.message,true);}
    }
    async exportMix(){
      if(!this.layers.length||!this.length)return this.notify("No recorded loops to export.",true);
      if(this.pending||this.recorder)return this.notify("Finish recording before export.",true);
      try{
        const rate=this.ctx.sampleRate,len=Math.round(this.length*rate);
        const offline=new OfflineAudioContext(2,len,rate);
        let count=0;
        for(const l of this.layers){
          const gain=this.effectiveGain(l);if(gain===0)continue;
          const source=offline.createBufferSource(),v=offline.createGain();
          source.buffer=l.buffer;source.loop=true;v.gain.value=gain;
          source.connect(v);v.connect(offline.destination);source.start(0);count++;
        }
        if(!count)throw Error("Every lane is muted or excluded by solo");
        const mixed=await offline.startRendering();
        download(mixed,"SUZY_TOAST_loop_mix_"+new Date().toISOString().slice(0,10)+".wav");
        this.notify("WAV mix exported. Import this in Logic to keep it permanently.");
      }catch(e){this.notify("Export failed: "+e.message,true);}
    }
    render(){
      const host=$("rackLayers");host.replaceChildren();
      $("rackEmpty").hidden=this.layers.length>0;
      $("rackBars").disabled=this.layers.length>0;
      $("rackToggle").textContent=this.playing?"Ⅱ PAUSE RACK":"▶ PLAY RACK";
      $("rackExport").disabled=this.layers.length===0;
      $("rackClear").disabled=this.layers.length===0;
      $("rackMeta").textContent=this.layers.length?
        this.layers.length+" clips · "+this.bars+" bars · "+this.bpm+" BPM · "+this.length.toFixed(2)+"s loop · RAM only":
        "NO LOOP YET · first captured lane sets the duration";
      const ruler=$("rackRuler");
      if(ruler){
        ruler.replaceChildren();
        const beats=this.layers.length?this.bars:Number($("rackBars").value);
        for(let i=1;i<=beats;i++){
          const cell=root.document.createElement("span");
          cell.textContent="BAR "+i;
          ruler.appendChild(cell);
        }
      }
      for(const l of this.layers){
        const row=root.document.createElement("div");row.className="rack-layer";row.dataset.kind=l.kind;
        const top=root.document.createElement("div");top.className="rack-layer-top";
        const title=root.document.createElement("strong");title.textContent=l.name;
        const meta=root.document.createElement("span");meta.textContent=(l.muted?"MUTED":this.soloId===l.id?"SOLO":"LIVE")+" · "+this.length.toFixed(1)+"s";
        top.append(title,meta);
        const bars=root.document.createElement("div");bars.className="rack-wave";bars.setAttribute("aria-label","Audio waveform");
        l.peaks.forEach(v=>{const bar=root.document.createElement("i");bar.style.height=v+"%";bars.appendChild(bar);});
        const actions=root.document.createElement("div");actions.className="rack-layer-actions";
        const button=(label,handler)=>{const b=root.document.createElement("button");b.type="button";b.textContent=label;b.onclick=handler;actions.appendChild(b);return b;};
        button(l.muted?"UNMUTE":"MUTE",()=>this.mute(l.id));
        button(this.soloId===l.id?"UNSOLO":"SOLO",()=>this.solo(l.id));
        button("REMOVE",()=>this.remove(l.id));
        button("↓ WAV",()=>download(l.buffer,"SUZY_TOAST_"+l.kind+"_"+l.id+".wav"));
        row.append(top,bars,actions);host.appendChild(row);
      }
    }
    showStatus(){if(!this.layers.length)$("rackMeta").textContent="First take sets "+$("rackBars").value+" bar loop length, current TOASTER BPM.";}
    tick(){
      if(this.length&&this.ctx&&this.playing){
        const phase=((this.ctx.currentTime-this.epoch)%this.length+this.length)%this.length;
        $("rackProgress").style.width=(phase/this.length*100)+"%";
        if($("rackTrackField"))$("rackTrackField").style.setProperty("--phase",(phase/this.length*100)+"%");
        $("rackClock").textContent=phase.toFixed(1)+" / "+this.length.toFixed(1)+" s";
      }else{
        $("rackProgress").style.width="0%";
        if($("rackTrackField"))$("rackTrackField").style.setProperty("--phase","0%");
        $("rackClock").textContent=this.length?this.length.toFixed(1)+" s · paused":"0.0s";
      }
      this.raf=root.requestAnimationFrame(()=>this.tick());
    }
  }
  root.SuzyLoopRack=Rack;
  root.SuzyLoopRackWav=wav;
})(window);
