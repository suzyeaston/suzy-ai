/* SUZY//TOAST Tracks: visible real loop regions, one cycle per song.
 * Designed for performance, not a mock DAW. Clip widths reflect stored takes.
 * No new model, no network, no fake AI audio, no redundant audio clock.
 */
(function(root){
"use strict";
const $=id=>root.document.getElementById(id);
const ORDER=["pyramid","fishes"];
const LANES=[
  ["chords","KEYS","🎹"],
  ["vocal","VOICE","🎙"],
  ["ai","MAGENTA","✦"]
];
function el(tag,cls,text){
 const n=root.document.createElement(tag);
 if(cls)n.className=cls;
 if(text!==undefined)n.textContent=String(text);
 return n;
}
function peakBins(buffer,count=44){
 if(!buffer||!buffer.numberOfChannels)return [];
 const ch=buffer.getChannelData(0),out=[];
 for(let i=0;i<count;i++){
  const start=Math.floor(i*ch.length/count),end=Math.floor((i+1)*ch.length/count);
  let peak=0;
  const stride=Math.max(1,Math.floor((end-start)/80));
  for(let j=start;j<end;j+=stride)peak=Math.max(peak,Math.abs(ch[j]));
  out.push(Math.min(100,Math.round(peak*100)));
 }
 return out;
}
class Tracks{
 constructor({decks,select,record,voice,onMute,onRemove,getRecording,getStep,getRunning}){
  this.decks=decks;this.select=select;this.record=record;this.voice=voice;
  this.onMute=onMute;this.onRemove=onRemove;this.getRecording=getRecording;
  this.getStep=getStep;this.getRunning=getRunning;
  this.draw();
 }
 draw(){
  for(const which of ORDER){
   const d=this.decks[which],bars=(d.lengthSteps||16)/8;
   const column=$("tracks-"+which);if(!column)continue;column.replaceChildren();
   const header=el("div","track-top");
   const title=el("div","track-title",which==="pyramid"?"01 · PYRAMID":"02 · WEIRD FISHES");
   const badge=el("span","track-loop-badge",d.locked?(d.loopEnabled?"↻ LOOP READY":"■ LOOP STOPPED"):"RECORD → DONE → LOOP");
   header.append(title,badge);
   const controls=el("div","track-controls");
   const select=el("button","track-select","↳ PLAY SONG");
   select.type="button";select.onclick=()=>this.select(which);
   const rec=el("button","track-record",d.locked&&d.layers.length?"＋ ADD INSTRUMENT LAYER":"● RECORD FIRST LOOP");
   rec.type="button";rec.onclick=()=>this.record(which);
   const mic=el("button","track-voice","🎙 VOICE");
   mic.type="button";mic.onclick=()=>this.voice(which);
   controls.append(select,rec,mic);
   if(!d.locked){
    const first=el("label","track-first-length","If VOICE is the first take:");
    const length=el("select","track-first-size");
    length.setAttribute("aria-label","Length of first vocal loop for "+which);
    for(const n of [2,4,8,16,32]){
      const o=el("option","",n+" bars");o.value=String(n);length.append(o);
    }
    length.value=String(d.initialBars||8);
    length.onchange=()=>{d.initialBars=Number(length.value);this.draw()};
    first.append(length);controls.append(first);
   }
   const recState=this.getRecording();
   if(recState?.scene===which&&recState.kind==="chords"){
    rec.textContent=recState.finishQueued?"↻ LOOP STARTING":recState.active?(recState.first?"■ DONE → LOOP":"■ DONE LAYER"):"● ARMED";
    rec.classList.add("active");
   }
   if(recState?.scene===which&&recState.kind==="vocal"){
    mic.textContent=recState.first?(recState.finishQueued?"🎙 FINISH QUEUED":"■ FINISH FIRST VOICE"):
      "🎙 VOCAL OVERDUB";
    mic.classList.add("active");
   }
   header.append(controls);
   const status=el("div","track-loop-label",d.locked?"↻ LOOP READY":"FIRST LOOP NOT YET RECORDED");
   status.id="track-loop-label-"+which;header.append(status);
   const progress=el("div","track-loop-progress");const fill=el("div","track-loop-fill");
   fill.id="track-loop-fill-"+which;progress.append(fill);header.append(progress);
   column.append(header);
   // Performer-facing loop view intentionally omits bar/beat numbers.
   // Quantization is retained internally and the arrangement editor still
   // supports its own navigable time ruler.
   const lanes=el("div","track-lanes");
   for(const [kind,label,icon] of LANES){
     const row=el("div","track-lane");
     const name=el("div","track-lane-name",icon+" "+label);
     const surface=el("div","track-lane-surface lane-"+kind);
     surface.style.setProperty("--bars",String(bars));
     const layers=d.layers.filter(l=>l.kind===kind);
     if(layers.length===0)surface.append(el("div","track-empty",kind==="ai"?"Import a real Magenta take":kind==="vocal"?"Record a vocal take":"Play and record keys"));
     else layers.forEach((layer,j)=>{
       const region=el("div","track-region region-"+kind+(layer.muted?" track-muted":""));
       region.title=(kind==="ai"?"Imported Magenta audio":kind==="vocal"?"Recorded microphone audio":"Recorded chord/note events");
       const clipTitle=el("span","track-clip-title",
         (kind==="ai"?"AI TAKE ":kind==="vocal"?"VOICE ":({
           keys:"PIANO ",pad:"PAD ",pluck:"PLUCK ",bass:"BASS "
         }[layer.instrument]||"KEYS "))+(j+1));
       const waveform=el("span","track-wave");
       if(layer.buffer){
         for(const height of peakBins(layer.buffer)){
           const bar=el("i","track-wave-bar");bar.style.height=Math.max(8,height)+"%";waveform.append(bar);
         }
       }else{
         for(const note of (layer.events||[])){
           const noteEl=el("i","track-midi-note");
           const step=Math.max(0,Math.min(d.lengthSteps||16,note.step||0));
           noteEl.style.left=(step/(d.lengthSteps||16)*100)+"%";
           noteEl.style.width=(Math.max(.4,Math.min(note.holdSteps||1,(d.lengthSteps||16)-step))/(d.lengthSteps||16)*100)+"%";
           waveform.append(noteEl);
         }
       }
       const button=el("button","track-clip-mute",layer.muted?"UNMUTE":"MUTE");
       button.type="button";button.onclick=()=>this.onMute(which,layer.id);
       const remove=el("button","track-clip-remove","×");
       remove.type="button";remove.setAttribute("aria-label","Remove "+kind+" clip");
       remove.onclick=()=>this.onRemove(which,layer.id);
       region.append(clipTitle,waveform,button,remove);
       surface.append(region);
     });
     row.append(name,surface);lanes.append(row);
   }
   const head=el("div","track-song-playhead");head.id="track-head-"+which;
   lanes.append(head);column.append(lanes);
   const summary=el("div","track-foot",d.locked&&d.layers.length
     ?"Your first phrase sets the loop length. For another LOCAL SYNTH layer, choose a different NEW LAYER SOUND before recording. Native Magenta remains one shared AI stream. Remove all clips to start over."
     :"Fresh loop: press RECORD FIRST LOOP, play, then DONE. You do not need to reload to start again.");
   column.append(summary);
  }
  this.tick();
 }
 tick(){
  const rec=this.getRecording(),step=this.getStep();
  for(const which of ORDER){
   const col=$("tracks-"+which),head=$("track-head-"+which);
   if(!col||!head)continue;
   const d=this.decks[which],length=d.lengthSteps||16,origin=d.anchorStep||0;
   const phase=((step-origin)%length+length)%length;
   head.style.left="calc(90px + (100% - 90px) * "+(phase/length)+")";
   const label=$("track-loop-label-"+which),fill=$("track-loop-fill-"+which);
   if(label){
     const captured=rec?.scene===which;
     label.textContent=captured?
       (rec.active?(rec.kind==="chords"?(rec.first?"● RECORDING · PRESS DONE":"● RECORDING NEW LAYER"):"● RECORDING VOICE"):"◉ ARMED"):
       !d.locked?"○ READY TO RECORD":
       !this.getRunning()?"Ⅱ PAUSED":
       d.loopEnabled?"↻ LOOPING":"■ LOOP STOPPED";
   }
   if(fill)fill.style.width=((phase/length)*100)+"%";
   col.classList.toggle("is-playing",this.getRunning());
   col.classList.toggle("is-recording",rec?.scene===which);
   col.classList.toggle("is-selected",root.document.getElementById("deck-"+which)?.classList.contains("selected")||false);
  }
 }
}
root.SuzyTrackView=Tracks;
})(window);
