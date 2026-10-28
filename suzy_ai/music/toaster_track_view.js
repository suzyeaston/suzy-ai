/* TOASTER // CHORDS FIRST
 * A compact Logic-inspired arrangement for two song-length loop cycles.
 * Regions display real MIDI events or buffered PCM. Dragging (or arrows)
 * shifts ACTUAL playback phase on the shared clock, snapped to whole bars.
 */
(function(root){
"use strict";
const $=id=>root.document.getElementById(id);
const SONGS=[["pyramid","01 · PYRAMID"],["fishes","02 · WEIRD FISHES"]];
const LANES=[["chords","KEYS","🎹"],["vocal","VOICE","🎙"],["ai","MAGENTA","✦"]];
const mod=(n,m)=>((n%m)+m)%m;
const clamp=(n,lo,hi)=>Math.max(lo,Math.min(hi,n));
function el(tag,cls,text){
 const n=root.document.createElement(tag);
 if(cls)n.className=cls;
 if(text!==undefined)n.textContent=String(text);
 return n;
}
function bins(buffer,count=80){
 if(!buffer?.numberOfChannels)return [];
 const ch=buffer.getChannelData(0),out=[];
 for(let i=0;i<count;i++){
  const a=Math.floor(i*ch.length/count),b=Math.ceil((i+1)*ch.length/count);
  let peak=0,delta=Math.max(1,Math.floor((b-a)/80));
  for(let j=a;j<b&&j<ch.length;j+=delta)peak=Math.max(peak,Math.abs(ch[j]));
  out.push(Math.min(100,Math.round(peak*100)));
 }
 return out;
}
class TrackView {
 constructor({decks,select,record,voice,onMute,onRemove,onShift,getRecording,getStep,getRunning}){
  this.decks=decks;this.select=select;this.record=record;this.voice=voice;
  this.onMute=onMute;this.onRemove=onRemove;this.onShift=onShift;
  this.getRecording=getRecording;this.getStep=getStep;this.getRunning=getRunning;
  // Preserve original playable nodes between renders, including event listeners.
  this.pads=Object.fromEntries(SONGS.map(([which])=>[which,$("pads-"+which)]));
  this.draw();
 }
 draw(){
  for(const [which,title] of SONGS){
   const d=this.decks[which],length=d.lengthSteps||16,bars=length/8;
   const col=$("tracks-"+which);if(!col)continue;
   col.replaceChildren();
   const head=el("div","track-top");
   const heading=el("div","track-heading");
   heading.append(el("div","track-title",title),
     el("span","track-loop-badge",d.locked?bars+"-BAR LOOP":"FIRST TAKE SETS LOOP"));
   head.append(heading);
   const padSlot=el("div","track-pad-slot");
   padSlot.id="track-pad-slot-"+which;
   head.append(padSlot);
   col.append(head);
   // MOVES the existing pads, not clones. Their original pointer/MIDI handlers
   // still work, and keyboard keys 1–4 still play the selected song.
   const existing=this.pads[which];
   if(existing){existing.classList.add("track-main-pads");padSlot.append(existing);}
   const controls=el("div","track-controls");
   const play=el("button","track-select","▶ SELECT");
   play.type="button";play.onclick=()=>this.select(which);
   const rec=el("button","track-record","● LOOP KEYS");
   rec.type="button";rec.onclick=()=>this.record(which);
   const mic=el("button","track-voice","🎙 LOOP VOICE");
   mic.type="button";mic.onclick=()=>this.voice(which);
   controls.append(play,rec,mic);
   if(!d.locked){
     const first=el("label","track-first-length","FIRST VOCAL TAKE");
     const select=el("select","track-first-size");
     select.setAttribute("aria-label",title+" first vocal loop length");
     for(const n of [2,4,8,16,32]){
       const o=el("option","",n+" bars");o.value=String(n);select.append(o);
     }
     select.value=String(d.initialBars||8);
     select.onchange=()=>{d.initialBars=Number(select.value);};
     first.append(select);controls.append(first);
   }
   const recording=this.getRecording();
   if(recording?.scene===which&&recording.kind==="chords"){
     rec.classList.add("active");
     rec.textContent=recording.active&&!d.locked?"■ FINISH FIRST LOOP":
       recording.active?"● OVERDUBBING":"● ARMED";
   }
   col.append(controls);
   const ruler=el("div","track-ruler");
   for(let n=0;n<bars;n++){
     const mark=el("span","track-bar",(n%4===0||bars<=8)?String(n+1):"·");
     ruler.append(mark);
   }
   col.append(ruler);
   const lanes=el("div","track-lanes");
   for(const [kind,label,icon] of LANES){
     const row=el("div","track-lane");
     row.append(el("div","track-lane-name",icon+" "+label));
     const surface=el("div","track-lane-surface");
     surface.style.setProperty("--bars",String(bars));
     const layers=d.layers.filter(l=>l.kind===kind);
     if(!layers.length)surface.append(el("div","track-empty",
       kind==="chords"?"Your recorded notes appear here":
       kind==="vocal"?"Sing a first take or overdub":"Imported real Magenta audio"));
     layers.forEach((layer,i)=>surface.append(this.region(which,layer,i,length)));
     row.append(surface);lanes.append(row);
   }
   const playhead=el("div","track-song-playhead");playhead.id="track-head-"+which;
   lanes.append(playhead);col.append(lanes);
   const footer=el("div","track-foot",
      (d.locked?bars+"-bar master phrase · ":"Record the first phrase to set the loop length · ")+
      "drag regions left/right to shift by a bar · click a chord to play");
   col.append(footer);
  }
  this.tick();
 }
 region(which,layer,i,length){
   const kind=layer.kind,shift=mod(layer.shiftSteps||0,length),bars=length/8;
   const region=el("div","track-region region-"+kind+(layer.muted?" track-muted":""));
   region.tabIndex=0;region.setAttribute("role","group");
   region.setAttribute("aria-label",
     "Loop "+(i+1)+" "+kind+". Drag horizontally or use left/right arrow to shift playback by bars.");
   region.title="Drag left/right to shift the actual loop by whole bars. Keyboard: left/right arrows.";
   const head=el("div","track-region-head");
   const text=el("span","track-clip-title",
     (kind==="chords"?"KEYS ":kind==="vocal"?"VOICE ":"AI ")+(i+1));
   const offset=el("span","track-offset",shift?"+"+(shift/8)+" bars":"BAR 1");
   const mute=el("button","track-clip-mute",layer.muted?"UNMUTE":"MUTE");
   mute.type="button";mute.onclick=()=>this.onMute(which,layer.id);
   const remove=el("button","track-clip-remove","×");
   remove.type="button";remove.setAttribute("aria-label","Remove "+kind+" loop");
   remove.onclick=()=>this.onRemove(which,layer.id);
   head.append(text,offset,mute,remove);
   const visual=el("div","track-wave");
   if(layer.buffer){
     const values=bins(layer.buffer,80);
     const displacement=Math.round(shift/length*values.length);
     for(let n=0;n<values.length;n++){
       const bar=el("i","track-wave-bar");
       bar.style.height=Math.max(5,values[mod(n-displacement,values.length)])+"%";
       visual.append(bar);
     }
   }else{
     for(const note of (layer.events||[])){
       const start=mod((note.step||0)+shift,length);
       const duration=clamp(note.holdSteps||1,.25,length);
       for(const [pos,span] of [[start,Math.min(duration,length-start)],
          ...(duration>length-start?[[0,duration-(length-start)]]:[])]){
         const noteEl=el("i","track-midi-note");
         noteEl.style.left=(pos/length*100)+"%";
         noteEl.style.width=(span/length*100)+"%";
         visual.append(noteEl);
       }
     }
   }
   region.append(head,visual);
   this.drag(region,which,layer,length,offset);
   return region;
 }
 drag(region,which,layer,length,offset){
   let current=null;
   region.addEventListener("pointerdown",e=>{
     if(e.button!==0||e.target.closest?.("button"))return;
     if(!this.decks[which].locked)return;
     const surface=region.closest(".track-lane-surface");
     const width=surface.getBoundingClientRect().width;
     if(width<=0)return;
     current={pointerId:e.pointerId,x:e.clientX,base:mod(layer.shiftSteps||0,length),width,bars:length/8,preview:0};
     region.setPointerCapture?.(e.pointerId);
     region.classList.add("track-dragging");
     e.preventDefault();
   });
   region.addEventListener("pointermove",e=>{
     if(!current||e.pointerId!==current.pointerId)return;
     const bars=Math.round((e.clientX-current.x)/(current.width/current.bars));
     current.preview=mod(current.base+bars*8,length);
     offset.textContent="MOVE → BAR "+(current.preview/8+1);
     region.style.setProperty("--drag-preview",String(bars));
   });
   const finish=e=>{
     if(!current||e.pointerId!==current.pointerId)return;
     const target=current.preview;
     region.classList.remove("track-dragging");
     current=null;
     this.onShift(which,layer.id,target);
   };
   region.addEventListener("pointerup",finish);
   region.addEventListener("pointercancel",e=>{
     if(!current||e.pointerId!==current.pointerId)return;
     current=null;this.draw();
   });
   region.addEventListener("keydown",e=>{
     if(!this.decks[which].locked)return;
     if(e.key!=="ArrowLeft"&&e.key!=="ArrowRight")return;
     e.preventDefault();e.stopPropagation();
     const next=mod((layer.shiftSteps||0)+(e.key==="ArrowRight"?8:-8),length);
     this.onShift(which,layer.id,next);
   });
 }
 tick(){
   const recording=this.getRecording(),step=this.getStep();
   for(const [which] of SONGS){
     const col=$("tracks-"+which),head=$("track-head-"+which);
     if(!col||!head)continue;
     const d=this.decks[which],length=d.lengthSteps||16,origin=d.anchorStep||0;
     const phase=mod(step-origin,length);
     head.style.left="calc(86px + (100% - 86px) * "+(phase/length)+")";
     col.classList.toggle("is-playing",this.getRunning());
     col.classList.toggle("is-recording",recording?.scene===which);
     col.classList.toggle("is-selected",
       root.document.getElementById("deck-"+which)?.classList.contains("selected")||false);
   }
 }
}
root.SuzyTrackView=TrackView;
})(window);
