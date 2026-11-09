/* Browser Web Audio renderer for SOFT RESET.
 * This is a local, deterministic synthesizer. Imported Magenta/voice prints
 * remain user-supplied audio; no neural audio is generated in this file.
 */
(function(root, factory) {
  const audio = factory();
  if (typeof module === "object" && module.exports) module.exports = audio;
  else root.SoftResetAudio = audio;
})(typeof globalThis !== "undefined" ? globalThis : this, function() {
  "use strict";
  const noiseCache = new WeakMap();
  const frequency = midi => 440 * Math.pow(2,(midi-69)/12);
  function noise(ctx) {
    if(noiseCache.has(ctx)) return noiseCache.get(ctx);
    const n=Math.round(ctx.sampleRate*.5), buf=ctx.createBuffer(1,n,ctx.sampleRate);
    const a=buf.getChannelData(0);let seed=0xace1;
    for(let i=0;i<n;i++){ seed=(Math.imul(seed,1664525)+1013904223)>>>0;a[i]=(seed/4294967296)*2-1; }
    noiseCache.set(ctx,buf);
    return buf;
  }
  function createMix(ctx, levels, master=.72) {
    const masterGain=ctx.createGain();masterGain.gain.value=master;
    const limiter=ctx.createDynamicsCompressor();
    limiter.threshold.value=-15;limiter.knee.value=12;limiter.ratio.value=5;
    limiter.attack.value=.005;limiter.release.value=.22;
    masterGain.connect(limiter);limiter.connect(ctx.destination);
    const channels={};
    for(const [id,level] of Object.entries(levels)){
      const node=ctx.createGain();node.gain.value=level;node.connect(masterGain);channels[id]=node;
    }
    return {masterGain,limiter,channels};
  }
  function play(ctx,output,ev,at) {
    if(!output || !Number.isFinite(at)) return [];
    const start=Math.max(ctx.currentTime,at), duration=Math.max(.008,ev.dur);
    const v=Math.min(1,Math.max(0,ev.velocity));
    let nodes=[];
    const envelope=(attack,decay,amp=v) => {
      const gain=ctx.createGain();
      gain.gain.setValueAtTime(0,start);
      gain.gain.linearRampToValueAtTime(Math.max(.0001,amp),start+Math.min(attack,duration*.4));
      gain.gain.exponentialRampToValueAtTime(.0001,start+duration+decay);
      gain.connect(output);return gain;
    };
    const oscillator=(type,freq,gain,detune=0) => {
      const osc=ctx.createOscillator();osc.type=type;
      osc.frequency.setValueAtTime(freq,start);osc.detune.value=detune;osc.connect(gain);
      osc.start(start);osc.stop(start+duration+.12);nodes.push(osc);return osc;
    };
    if(ev.kind==="kick"){
      const gain=envelope(.007,.04,v*.65);
      const osc=oscillator("sine",110,gain);
      osc.frequency.exponentialRampToValueAtTime(46,start+.14);
    } else if(ev.kind==="snare" || ev.kind==="hat") {
      const src=ctx.createBufferSource();src.buffer=noise(ctx);
      const filter=ctx.createBiquadFilter();filter.type="highpass";
      filter.frequency.value=ev.kind==="hat"?6500:1250;
      const gain=envelope(.002,.012,(ev.kind==="hat"?.12:.27)*v);
      src.connect(filter);filter.connect(gain);
      src.start(start);src.stop(start+Math.min(duration,.2));nodes.push(src);
    } else if(ev.kind==="metal"){
      const gain=envelope(.003,.06,v*.095);
      oscillator("square",frequency(ev.note),gain);
      oscillator("triangle",frequency(ev.note)*1.414,gain);
    } else if(ev.kind==="strings"){
      const gain=envelope(.4,.36,v*.14);
      const filter=ctx.createBiquadFilter();filter.type="lowpass";filter.frequency.value=950;
      gain.disconnect();gain.connect(filter);filter.connect(output);
      oscillator("sawtooth",frequency(ev.note),gain);
    } else if(ev.kind==="glass"){
      const gain=envelope(.012,.25,v*.16);
      oscillator("sine",frequency(ev.note),gain);
      oscillator("triangle",frequency(ev.note)*2,gain);
    } else if(ev.kind==="human"){
      const gain=envelope(.04,.24,v*.22);
      oscillator("triangle",frequency(ev.note),gain);
      oscillator("sine",frequency(ev.note)*2,gain);
    } else {
      const gain=envelope(.025,.10,v*.22);
      oscillator("sine",frequency(ev.note),gain);
      if(ev.kind==="bass")oscillator("triangle",frequency(ev.note)*.5,gain);
    }
    return nodes;
  }
  function schedule(ctx,mix,events,at,offset=0) {
    const sources=[];
    for(const ev of events){
      if(ev.t+0.0001<offset)continue;
      if(!mix.channels[ev.track])continue;
      const when=at+ev.t;
      sources.push(...play(ctx,mix.channels[ev.track],ev,when));
    }
    return sources;
  }
  function schedulePrint(ctx,mix,buffer,at,offset=0) {
    if(!buffer || !mix.channels.print || !Number.isFinite(buffer.duration) || !buffer.duration)return null;
    const source=ctx.createBufferSource();source.buffer=buffer;source.loop=true;
    source.connect(mix.channels.print);
    source.start(Math.max(ctx.currentTime,at+offset),offset%buffer.duration);
    source.stop(at+60);
    return source;
  }
  function wav(buffer) {
    const channels=Math.min(2,buffer.numberOfChannels), frames=buffer.length;
    const bytes=new ArrayBuffer(44+frames*channels*2),v=new DataView(bytes);
    const ascii=(at,str)=>{for(let i=0;i<str.length;i++)v.setUint8(at+i,str.charCodeAt(i));};
    ascii(0,"RIFF");v.setUint32(4,bytes.byteLength-8,true);ascii(8,"WAVE");
    ascii(12,"fmt ");v.setUint32(16,16,true);v.setUint16(20,1,true);
    v.setUint16(22,channels,true);v.setUint32(24,buffer.sampleRate,true);
    v.setUint32(28,buffer.sampleRate*channels*2,true);
    v.setUint16(32,channels*2,true);v.setUint16(34,16,true);
    ascii(36,"data");v.setUint32(40,bytes.byteLength-44,true);
    const audio=Array.from({length:channels},(_,i)=>buffer.getChannelData(i));
    let p=44;
    for(let i=0;i<frames;i++)for(let ch=0;ch<channels;ch++){
      const sample=Math.max(-1,Math.min(1,audio[ch][i]));
      v.setInt16(p,sample<0?Math.round(sample*32768):Math.round(sample*32767),true);p+=2;
    }
    return new Blob([bytes],{type:"audio/wav"});
  }
  return Object.freeze({frequency,createMix,play,schedule,schedulePrint,wav});
});
