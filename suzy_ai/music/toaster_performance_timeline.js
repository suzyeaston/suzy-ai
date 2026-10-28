/* TOASTER performance arrangement: the whole set, not a decorative loop ruler.
 * Clips represent ACTUAL recorded layers. Their start and end bars gate the
 * WebAudio chord scheduler and recorded-audio playback. Changes are snapped
 * to the shared bar clock, and apply at the next bar for a live set.
 */
(function(root){
"use strict";
const $=id=>root.document.getElementById(id);
const order=[["pyramid","PYRAMID"],["fishes","WEIRD FISHES"]];
const kinds=[["chords","KEYS"],["vocal","VOCALS"],["ai","AI PRINT"]];
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const node=(tag,cls,txt)=>{
 const n=root.document.createElement(tag);if(cls)n.className=cls;
 if(txt!==undefined)n.textContent=String(txt);return n;
};
const mod=(x,n)=>((x%n)+n)%n;
class PerformanceTimeline{
 constructor({decks,getCues,getStep,getTempo,onEdit,onSelect,onAction}){
  this.decks=decks;this.getCues=getCues;this.getStep=getStep;
  this.getTempo=getTempo;this.onEdit=onEdit;this.onSelect=onSelect;
  this.onAction=onAction;this.selected=null;this.clipboard=null;
  this.target={which:"pyramid",kind:"chords",bar:0};
  this.zoom=6;this.total=320;
  this.minutes=15;
  $("fullDuration").onchange=e=>{
   this.minutes=clamp(Number(e.target.value)||15,5,30);
   e.target.value=String(this.minutes);
   this.render();
  };
  $("fullZoom").oninput=e=>{this.zoom=Number(e.target.value)||6;this.render()};
  for(const [id,action] of [["fullCopy","copy"],["fullCut","cut"],["fullPaste","paste"],
     ["fullDelete","delete"],["fullSplit","split"]])$(id).onclick=()=>this.perform(action);
  root.document.addEventListener("keydown",e=>{
   if(e.target?.isContentEditable||["INPUT","SELECT","TEXTAREA"].includes(e.target?.tagName))return;
   const cmd=e.metaKey||e.ctrlKey,key=String(e.key).toLowerCase();
   const action=cmd?{c:"copy",x:"cut",v:"paste"}[key]:["delete","backspace"].includes(key)?"delete":null;
   if(!action||(["copy","cut","delete"].includes(action)&&!this.selected))return;
   e.preventDefault();this.perform(action);
  });
  $("fullFit").onclick=()=>{
    const width=$("fullViewport").clientWidth||1000;
    this.zoom=clamp(Math.floor((width-100)/this.total),3,12);
    $("fullZoom").value=String(this.zoom);this.render();
  };
  this.render();
 }
 barWidth(){return this.zoom}
 totalBars(){
  const cues=this.getCues(),n=cues.reduce((sum,c)=>sum+(Number(c.bars)||0),0);
  // Not capped at one loop. A bar ruler covers the full cue-programmed show.
  const barsForDuration=Math.ceil(this.minutes*60/(240/Math.max(40,Number(this.getTempo())||105)));
  return clamp(Math.max(n,barsForDuration),32,1024);
 }
 render(){
  this.total=this.totalBars();
  const px=this.barWidth(),width=this.total*px;
  const barSeconds=240/Math.max(40,Number(this.getTempo())||105);
  $("fullLength").textContent=this.total+" bars · "+(this.total*barSeconds/60).toFixed(1)+" min at current BPM";
  const list=$("fullLanes");list.replaceChildren();
  list.style.width=width+"px";
  const ruler=$("fullRuler");ruler.replaceChildren();ruler.style.width=width+"px";
  for(let bar=0;bar<this.total;bar+=4){
   const tick=node("span","full-bar-label",String(bar+1));
   tick.style.left=(bar*px)+"px";ruler.append(tick);
  }
  let elapsed=0;
  for(const cue of this.getCues()){
   const span=Number(cue.bars)||0;if(!span)continue;
   const mark=node("div","full-section "+(cue.scene==="fishes"?"fishes":"pyramid"),cue.name||cue.scene);
   mark.style.left=(elapsed*px)+"px";mark.style.width=(span*px)+"px";
   ruler.append(mark);elapsed+=span;
  }
  if(elapsed<this.total){
   const improv=node("div","full-section pyramid","FREE IMPROVISATION / OUTRO");
   improv.style.left=(elapsed*px)+"px";
   improv.style.width=((this.total-elapsed)*px)+"px";
   ruler.append(improv);
  }
  for(const [which,title] of order){
   for(const [kind,label] of kinds){
    const row=node("div","full-lane");row.dataset.scene=which;row.dataset.kind=kind;
    row.title="Click a bar to choose where to paste a clip";
    row.addEventListener("click",e=>{
      if(e.target!==row)return;
      const rect=row.getBoundingClientRect();
      const bar=clamp(Math.round((e.clientX-rect.left)/this.barWidth()),0,this.total-1);
      this.target={which,kind,bar};
      this.announce("Paste target: "+title+" / "+label+" bar "+(bar+1));
    });
    row.style.width=width+"px";
    const entries=this.decks[which].layers.filter(l=>l.kind===kind);
    for(let index=0;index<entries.length;index++){
     const layer=entries[index],every=Math.max(2,Math.floor((this.decks[which].lengthSteps||16)/8));
     const start=clamp(Number(layer.arrStartBar??0),0,this.total-1);
     const end=clamp(Number(layer.arrEndBar??this.total),start+1,this.total);
     // Primary movable region with actual source/timbre name.
     const titleText=(layer.kind==="chords"?(layer.instrument||"KEYS").toUpperCase():label)+
       " "+(index+1)+" · "+every+" bars ↻";
     const block=node("div","full-clip "+kind+(layer.muted?" is-muted":""),titleText);
     block.style.left=(start*px)+"px";
     block.style.width=Math.max(5,(end-start)*px)+"px";
     block.dataset.layer=String(layer.id);
     if(this.selected?.which===which&&this.selected.id===layer.id)block.classList.add("is-selected");
     block.addEventListener("click",e=>{e.stopPropagation();this.selectClip(which,kind,layer.id)});
     block.tabIndex=0;block.setAttribute("role","group");
     block.setAttribute("aria-label",title+" "+titleText+", drag to change start, drag right handle to set end");
     block.title="Drag to move this layer's entry across the whole performance. Drag the right edge to choose when it exits.";
     // Draw actual loop repeat boundaries throughout the arrangement region.
     block.style.backgroundSize=(every*px)+"px 100%";
     const handle=node("span","full-resize","⋮");
     handle.title="Drag to change when this layer stops playing";
     handle.setAttribute("role","slider");handle.tabIndex=0;
     handle.setAttribute("aria-label","End bar for "+titleText);
     block.append(handle);
     this.drag(block,handle,which,layer,start,end);
     row.append(block);
    }
    list.append(row);
   }
  }
  this.update();
 }
 drag(block,handle,which,layer,start,end){
  let hold=null;
  const press=(e,mode)=>{
   if(e.button!==0)return;
   this.selected={which,kind:layer.kind,id:layer.id};
   this.target={which,kind:layer.kind,bar:Math.max(0,Math.floor(this.getStep()/8))};
   block.classList.add("is-selected");
   e.preventDefault();e.stopPropagation();
   hold={x:e.clientX,start,end,mode,pointerId:e.pointerId};
   block.setPointerCapture?.(e.pointerId);
   block.classList.add("moving");
  };
  block.addEventListener("pointerdown",e=>{
   if(e.target===handle)return;
   press(e,"move");
  });
  handle.addEventListener("pointerdown",e=>press(e,"end"));
  block.addEventListener("pointermove",e=>{
   if(!hold||e.pointerId!==hold.pointerId)return;
   const delta=Math.round((e.clientX-hold.x)/this.barWidth());
   if(hold.mode==="move"){
    const dur=hold.end-hold.start;
    start=clamp(hold.start+delta,0,this.total-dur);end=start+dur;
   }else end=clamp(hold.end+delta,start+1,this.total);
   block.style.left=(start*this.barWidth())+"px";
   block.style.width=((end-start)*this.barWidth())+"px";
  });
  const finish=e=>{
   if(!hold||e.pointerId!==hold.pointerId)return;
   hold=null;block.classList.remove("moving");
   this.onEdit(which,layer.id,start,end);
  };
  block.addEventListener("pointerup",finish);
  block.addEventListener("pointercancel",e=>{if(!hold||e.pointerId!==hold.pointerId)return;hold=null;this.render()});
  block.addEventListener("keydown",e=>{
   if(!["ArrowLeft","ArrowRight"].includes(e.key))return;
   e.preventDefault();e.stopPropagation();
   const delta=e.key==="ArrowRight"?1:-1;
   const duration=end-start,next=clamp(start+delta,0,this.total-duration);
   this.onEdit(which,layer.id,next,next+duration);
  });
  handle.addEventListener("keydown",e=>{
   if(!["ArrowLeft","ArrowRight"].includes(e.key))return;
   e.preventDefault();e.stopPropagation();
   const next=clamp(end+(e.key==="ArrowRight"?1:-1),start+1,this.total);
   this.onEdit(which,layer.id,start,next);
  });
 }
 announce(message){$("fullSelection").textContent=message}
 selectClip(which,kind,id){
  this.selected={which,kind,id};
  this.target={which,kind,bar:Math.max(0,Math.floor(this.getStep()/8))};
  this.announce("Selected "+which.toUpperCase()+" / "+kind+
   ". COPY, CUT or DELETE. Click another lane/bar to set PASTE target.");
  this.render();
 }
 perform(action){
  const selected=this.selected;
  if(["copy","cut","delete","split"].includes(action)&&!selected){
   this.announce("Select a recorded clip first.");return;
  }
  if(action==="copy"||action==="cut"){
    const layer=this.decks[selected.which].layers.find(l=>l.id===selected.id);
    if(!layer)return;
    this.clipboard={which:selected.which,kind:selected.kind,
      layer:{...layer,events:layer.events?.map(e=>({...e})),source:null,gain:null}};
    this.announce((action==="cut"?"CUT":"COPIED")+" "+selected.which+" / "+selected.kind+
      ". Click a destination lane/bar, then PASTE.");
  }
  if(action==="paste"&&!this.clipboard){
    this.announce("Copy or cut a recorded clip before pasting.");return;
  }
  if(action==="paste"&&this.target.kind!==this.clipboard.kind){
    this.announce("Paste to the matching KEYS, VOCALS or AI lane.");return;
  }
  this.onAction({action,selected,target:{...this.target},clipboard:this.clipboard});
  if(action==="cut"||action==="delete")this.selected=null;
  this.render();
 }
 update(){
  const bar=Math.max(0,Math.floor((Number(this.getStep())||0)/8));
  const marker=$("fullPlayhead");if(marker)marker.style.left=(bar*this.barWidth())+"px";
  const readout=$("fullPosition");if(readout)readout.textContent="BAR "+(bar+1)+" / "+this.total;
 }
}
root.SuzyPerformanceTimeline=PerformanceTimeline;
})(window);
