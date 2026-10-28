/* Voice → MRT2: locally estimate sung fundamental, emit MIDI steering notes.
 * This is not a synthetic singer, lyric generator, or voice cloning model.
 * Microphone audio is never sent to a server.
 */
class SuzyVoiceFollowProcessor extends AudioWorkletProcessor {
 constructor(){
  super();
  this.samples=new Float32Array(2048);
  this.cursor=0;this.decimate=0;this.frames=0;this.lastNote=null;this.finished=false;
  this.stable=null;this.count=0;
  this.port.onmessage=e=>{if(e.data?.type==="stop")this.finished=true};
 }
 process(inputs){
  if(this.finished)return false;
  const mic=inputs[0]?.[0];
  if(!mic)return true;
  for(let i=0;i<mic.length;i++){
   if(this.decimate++%2===0){
    this.samples[this.cursor]=mic[i];
    this.cursor=(this.cursor+1)%this.samples.length;
   }
  }
  this.frames+=mic.length;
  if(this.frames<Math.round(sampleRate*.14))return true;
  this.frames=0;
  // A decimated time-domain fundamental detector. Limit workload on 8GB Mac.
  const data=new Float32Array(1024);
  const start=(this.cursor-this.samples.length+this.samples.length)%this.samples.length;
  for(let i=0;i<1024;i++)data[i]=this.samples[(start+1024+i)%this.samples.length];
  let energy=0;
  for(const v of data)energy+=v*v;
  const rms=Math.sqrt(energy/data.length);
  if(rms<.014){this.report(null,0);return true;}
  const rate=sampleRate/2,minLag=Math.floor(rate/750),maxLag=Math.ceil(rate/105);
  let bestLag=0,best=-1;
  const matches=[];
  for(let lag=minLag;lag<=maxLag;lag++){
    let cor=0,a=0,b=0;
    for(let i=0;i<data.length-lag;i+=2){
      const x=data[i],y=data[i+lag];
      cor+=x*y;a+=x*x;b+=y*y;
    }
    const strength=cor/Math.sqrt(a*b+1e-10);
    matches.push({lag,strength});
    if(strength>best){best=strength;bestLag=lag}
  }
  if(best<.72||!bestLag){this.report(null,best);return true;}
  // Favor the earliest strong peak: the global maximum alone often selects
  // twice the fundamental period and sends a note one octave too low.
  const firstStrong=matches.find(m=>m.strength>=Math.max(.85,best-.025));
  if(firstStrong)bestLag=firstStrong.lag;
  const hz=rate/bestLag,note=Math.round(69+12*Math.log2(hz/440));
  if(note<36||note>96){this.report(null,best);return true}
  if(this.stable===note)this.count++;
  else{this.stable=note;this.count=1;}
  if(this.count>=2)this.report(note,best);
  return true;
 }
 report(note,confidence){
  if(note===this.lastNote)return;
  if(note===null){this.stable=null;this.count=0;}
  this.lastNote=note;
  this.port.postMessage({type:"pitch",note,confidence});
 }
}
registerProcessor("suzy-voice-follow",SuzyVoiceFollowProcessor);
