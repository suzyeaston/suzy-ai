/* Realtime vocal loop capture: runs on Web Audio render thread, never main JS.
 * Exactly one browser-clock-aligned clip; raw input peaks measured before
 * playback headroom gain. Does not monitor or alter hardware direct monitoring.
 */
class SuzyVocalCaptureProcessor extends AudioWorkletProcessor {
  constructor(options) {
    super();
    const p=options.processorOptions||{};
    this.startFrame=Math.max(0,Math.round(Number(p.startFrame)||0));
    this.frames=Math.min(Math.floor(sampleRate*120),Math.max(1,Math.round(Number(p.frames)||1)));
    this.data=new Float32Array(this.frames);
    this.peak=0;this.hot=0;this.missing=0;this.done=false;
    this.finishFrames=null;
    this.port.onmessage=e=>{
      if(e.data?.type==="stop"){this.done=true;this.data=null;}
      if(e.data?.type==="finish"){
        // Capture size is bounded at creation. No resizing in the audio callback.
        const frames=Number(e.data.frames);
        if(Number.isFinite(frames)){
          this.finishFrames=Math.max(1,Math.min(this.frames,Math.round(frames)));
        }
      }
    };
  }
  process(inputs,outputs) {
    if(this.done)return false;
    const input=inputs[0]?.[0];
    const length=outputs[0]?.[0]?.length||input?.length||128;
    const limit=this.finishFrames??this.frames;
    const start=currentFrame-this.startFrame;
    const from=Math.max(0,-start),to=Math.min(length,limit-start);
    if(to>from){
      if(!input)this.missing+=to-from;
      for(let i=from;i<to;i++){
        const sample=input?.[i]||0;
        const abs=Math.abs(sample);
        if(abs>this.peak)this.peak=abs;
        if(abs>=0.985)this.hot++;
        this.data[start+i]=sample;
      }
    }
    if(start+length>=limit){
      const finished=this.data;
      this.done=true;this.data=null;
      this.port.postMessage({type:"complete",data:finished,frames:limit,peak:this.peak,hot:this.hot,missing:this.missing},[finished.buffer]);
      return false;
    }
    return true;
  }
}
registerProcessor("suzy-vocal-capture",SuzyVocalCaptureProcessor);
