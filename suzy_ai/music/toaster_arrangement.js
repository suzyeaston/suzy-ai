/* Browser-only, editable arrangement cues for SUZY//TOAST.
 * Quantized to the existing two-bar Web Audio scheduler; NOT native AU sample-sync.
 * No generation, no transport duplication, no new downloaded dependencies.
 */
(function(root) {
  "use strict";
  const KEY="suzy-toaster-arrangement-v1";
  const BAR_OPTIONS=[2,4,8,16,32,64];
  // 392 bars ≈ 14.9 minutes at 105 BPM; all sections remain editable,
  // cueable and skippable. No auto-triggered chords in the starter arrangement.
  const starter=[
    {name:"Pyramid · opening space",scene:"pyramid",bars:64,chord:-1,mix:0},
    {name:"Pyramid · live piano & voice",scene:"pyramid",bars:64,chord:-1,mix:0},
    {name:"Pyramid · improvisation",scene:"pyramid",bars:32,chord:-1,mix:0},
    {name:"Suspended transition",scene:"pyramid",bars:32,chord:-1,mix:50},
    {name:"Fishes · enter the current",scene:"fishes",bars:64,chord:-1,mix:75},
    {name:"Fishes · live arpeggios",scene:"fishes",bars:64,chord:-1,mix:100},
    {name:"Fishes · build / evolve",scene:"fishes",bars:64,chord:-1,mix:100},
    {name:"Fishes · resolve",scene:"fishes",bars:8,chord:-1,mix:100}
  ];
  const $=id=>root.document.getElementById(id);
  const clamp=(v,lo,hi)=>Math.min(hi,Math.max(lo,Number(v)||0));
  const valid=(c,i)=>({
    name:String(c.name||"Cue "+(i+1)).slice(0,54),
    scene:c.scene==="fishes"?"fishes":"pyramid",
    bars:BAR_OPTIONS.includes(Number(c.bars))?Number(c.bars):8,
    chord:Number.isInteger(Number(c.chord))&&Number(c.chord)>=-1&&Number(c.chord)<=3?Number(c.chord):-1,
    mix:Math.round(clamp(c.mix,0,100))
  });
  class Arrangement {
    constructor({getBpm,onCue,onChord,onMessage}) {
      this.getBpm=getBpm;this.onCue=onCue;this.onChord=onChord;this.onMessage=onMessage;
      this.cues=starter.map(valid);this.armed=false;this.index=-1;this.startBar=0;
      this.endBar=0;this.lastBar=0;this.skip=false;this.jumpTo=null;this.changed=false;
      try{
        const saved=JSON.parse(root.localStorage.getItem(KEY)||"null");
        if(Array.isArray(saved)&&saved.length>0&&saved.length<=32)this.cues=saved.map(valid);
      }catch{}
      $("arrArm").onclick=()=>this.arm(!this.armed);
      $("arrNext").onclick=()=>{if(this.armed){this.skip=true;this.status("Next cue queued for the next two-bar boundary.");}};
      $("arrAdd").onclick=()=>{if(this.cues.length>=32)return this.status("32 cue limit reached.");this.cues.push(valid({name:"New cue",scene:"fishes",bars:8,chord:-1,mix:100},this.cues.length));this.save();this.render();};
      $("arrReset").onclick=()=>{
        if(!root.confirm("Restore the eight starter cues? Your edited timeline will be replaced."))return;
        this.cues=starter.map(valid);this.arm(false);this.save();this.render();
      };
      $("arrCues").addEventListener("change",e=>this.change(e));
      $("arrCues").addEventListener("click",e=>this.click(e));
      this.render();
    }
    save(){try{root.localStorage.setItem(KEY,JSON.stringify(this.cues));}catch{}}
    arm(value) {
      this.armed=Boolean(value);this.index=-1;this.skip=false;this.jumpTo=null;
      $("arrArm").textContent=this.armed?"■ DISARM TIMELINE":"▶ ARM TIMELINE";
      $("arrArm").setAttribute("aria-pressed",String(this.armed));
      $("arrNext").disabled=!this.armed;
      this.status(this.armed?"Timeline armed. First cue starts on the next two-bar boundary.":"Manual playing remains available. Timeline automation is off.");
      this.render();
    }
    resetClock(){this.index=-1;this.lastBar=0;this.skip=false;this.jumpTo=null;this.render();}
    status(message){$("arrStatus").textContent=message;}
    totalBars(){return this.cues.reduce((n,c)=>n+c.bars,0);}
    render(){
      const minutes=(this.totalBars()*4/Math.max(1,Number(this.getBpm()))).toFixed(1);
      $("arrTotal").textContent=this.totalBars()+" bars · approx "+minutes+" min at current BPM";
      const rows=$("arrCues");rows.replaceChildren();
      this.cues.forEach((c,i)=>{
        const row=root.document.createElement("div");
        row.className="arr-row"+(this.armed&&this.index===i?" current":"");
        row.dataset.index=String(i);
        const num=root.document.createElement("span");num.className="arr-number";num.textContent=String(i+1).padStart(2,"0");
        row.append(num);
        const name=root.document.createElement("input");name.setAttribute("aria-label","Cue "+(i+1)+" name");name.value=c.name;name.dataset.field="name";name.maxLength=54;row.append(name);
        const select=(field,options,value,label)=>{
          const el=root.document.createElement("select");el.dataset.field=field;el.setAttribute("aria-label",label);
          for(const [v,title] of options){const op=root.document.createElement("option");op.value=String(v);op.textContent=title;el.append(op);}
          el.value=String(value);row.append(el);
        };
        select("scene",[["pyramid","Pyramid"],["fishes","Fishes"]],c.scene,"Song for cue "+(i+1));
        select("bars",BAR_OPTIONS.map(n=>[n,n+" bars"]),c.bars,"Cue length in bars");
        select("chord",[[-1,"Live / none"],[0,"Chord 1"],[1,"Chord 2"],[2,"Chord 3"],[3,"Chord 4"]],c.chord,"Optional repeating harmony");
        select("mix",[[0,"Pyramid 100%"],[25,"25% Fishes"],[45,"45% Fishes"],[50,"50 / 50"],[75,"75% Fishes"],[100,"Fishes 100%"]],c.mix,"Fishes crossfade percent");
        for(const [action,text,title] of [["cue","▶","Queue cue at next two-bar boundary"],["up","↑","Move earlier"],["down","↓","Move later"],["duplicate","+","Duplicate cue"],["remove","×","Remove cue"]]){
          const btn=root.document.createElement("button");btn.type="button";btn.dataset.action=action;btn.textContent=text;btn.title=title;btn.setAttribute("aria-label",title+" "+(i+1));btn.disabled=(action==="up"&&i===0)||(action==="down"&&i===this.cues.length-1)||(action==="remove"&&this.cues.length===1)||(action==="duplicate"&&this.cues.length>=32);row.append(btn);
        }
        rows.append(row);
      });
      const live=this.armed&&this.index>=0?this.cues[this.index]:null;
      $("arrNow").textContent=live?"PLAYING "+(this.index+1)+"/"+this.cues.length+" · "+live.name:"No active cue";
      $("arrNext").disabled=!this.armed;
    }
    change(event){
      const field=event.target?.dataset?.field;
      const index=Number(event.target?.closest(".arr-row")?.dataset?.index);
      if(!field||!Number.isInteger(index)||!this.cues[index])return;
      const next={...this.cues[index],[field]:event.target.value};
      this.cues[index]=valid(next,index);
      this.changed=true;this.save();this.render();
      this.status("Cue updated. Changes apply at the next two-bar boundary.");
    }
    click(event){
      const action=event.target?.dataset?.action;
      const index=Number(event.target?.closest(".arr-row")?.dataset?.index);
      if(!action||!Number.isInteger(index)||!this.cues[index])return;
      if(action==="cue"){
        if(!this.armed)this.arm(true);
        this.jumpTo=index;this.status("Cue "+(index+1)+" queued for the next two-bar boundary.");return;
      }
      if(action==="remove"&&this.cues.length>1)this.cues.splice(index,1);
      else if(action==="duplicate"&&this.cues.length<32)this.cues.splice(index+1,0,{...this.cues[index]});
      else if(action==="up"&&index>0)[this.cues[index-1],this.cues[index]]=[this.cues[index],this.cues[index-1]];
      else if(action==="down"&&index<this.cues.length-1)[this.cues[index+1],this.cues[index]]=[this.cues[index],this.cues[index+1]];
      else return;
      // Avoid changing the active cue's identity mid-cycle after a reorder.
      this.index=-1;this.skip=false;this.jumpTo=null;this.changed=true;this.save();this.render();
      this.status("Timeline edited. Next cycle restarts at cue 1 if armed.");
    }
    onCycle(bar){
      this.lastBar=bar;
      if(!this.armed)return;
      if(this.jumpTo!==null){
        this.index=this.jumpTo;this.jumpTo=null;this.skip=false;
        this.startBar=bar;this.endBar=bar+this.cues[this.index].bars;this.changed=false;this.apply();
      }
      else if(this.index<0){this.index=0;this.startBar=bar;this.endBar=bar+this.cues[0].bars;this.changed=false;this.apply();}
      else if(this.skip||bar>=this.endBar){
        this.skip=false;this.index++;
        if(this.index>=this.cues.length){this.arm(false);this.status("Timeline finished. Rhythm and live performance continue.");return;}
        this.startBar=bar;this.endBar=bar+this.cues[this.index].bars;this.changed=false;this.apply();
      }else if(this.changed){
        this.changed=false;this.endBar=Math.max(bar+2,this.startBar+this.cues[this.index].bars);this.apply();
      }
      const c=this.cues[this.index];
      if(c.chord>=0)this.onChord(c);
      this.update();
    }
    apply(){
      const c=this.cues[this.index];this.onCue(c);
      this.render();
      this.status("Cue "+(this.index+1)+" · "+c.name+" · "+c.bars+" bars. Edit any upcoming cue while playing.");
    }
    update(){
      if(!this.armed||this.index<0)return;
      const left=Math.max(0,this.endBar-this.lastBar);
      $("arrNow").textContent="CUE "+(this.index+1)+"/"+this.cues.length+" · "+this.cues[this.index].name+" · "+left+" bars left";
      const pct=100*clamp(this.lastBar-this.startBar,0,this.endBar-this.startBar)/Math.max(1,this.endBar-this.startBar);
      $("arrProgress").style.width=pct+"%";
    }
  }
  root.SuzyArrangement=Arrangement;
})(window);
