/* SOFT RESET // original 60-second Film Club score.
 * Independent of the Futureproof PYRAMID ORBIT session: no borrowed recordings,
 * no model synthesis claims and no unlicensed samples.
 * Works in both the browser and Node for deterministic score tests.
 */
(function (root, factory) {
  const score = factory();
  if (typeof module === "object" && module.exports) module.exports = score;
  else root.SoftResetScore = score;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";
  const DURATION = 60;
  const TRACKS = Object.freeze([
    {id:"bass", label:"01 · Harbour sub", role:"Low-frequency pulse", level:.48, color:"#b8d9ff"},
    {id:"glass", label:"02 · Glass / celesta", role:"Fragile melodic circuitry", level:.24, color:"#ffe4b0"},
    {id:"strings", label:"03 · Bowed atmosphere", role:"Sustained tension", level:.22, color:"#cab5fb"},
    {id:"drums", label:"04 · Industrial rhythm", role:"Acceleration and friction", level:.42, color:"#eea0b3"},
    {id:"metal", label:"05 · Metallic interference", role:"The weaponized machine", level:.27, color:"#f5af86"},
    {id:"human", label:"06 · Human intervention", role:"Melody, keys and overdubs", level:.42, color:"#b3e9d3"}
  ]);
  const SCENES = Object.freeze([
    {id:"city", start:0, end:10, title:"01 / CITY BREATHES",
      visual:"Waterfront footfall. Wet pavement, distant traffic, harbour lights. Let Gastown exist before the machine wakes.",
      cue:"grounded_vancouver", intensity:.12},
    {id:"accelerate", start:10, end:24, title:"02 / ACCELERANDO",
      visual:"Camera and traffic gather momentum. Reflections and lights begin repeating faster.",
      cue:"traffic_acceleration", intensity:.6},
    {id:"war", start:24, end:38, title:"03 / WAR MACHINE",
      visual:"Interference, hard edges and visual instability. No need for graphic violence.",
      cue:"machine_conflict", intensity:1},
    {id:"intervene", start:38, end:48, title:"04 / HUMAN INTERRUPTION",
      visual:"A performer stops the machinery with one musical gesture. The environment makes room to listen.",
      cue:"human_interrupt", intensity:.25},
    {id:"reset", start:48, end:60, title:"05 / MAKE ART NOT WAR",
      visual:"The same technology now illuminates the city. A transformed ending, not a reset to innocence.",
      cue:"soft_reset", intensity:.42}
  ]);
  const PROGRESSIONS = Object.freeze({
    "soft-reset": [
      {name:"Em(add9)", notes:[40,52,55,59,66]},
      {name:"Cmaj7(#11)", notes:[36,48,52,55,59,66]},
      {name:"G6", notes:[43,55,59,62,64]},
      {name:"Bsus4", notes:[47,54,59,64,66]}
    ],
    "pyramid-orbit": [
      {name:"F♯", notes:[42,54,58,61,66]},
      {name:"Gmaj7", notes:[43,55,59,62,66]},
      {name:"A6", notes:[45,57,61,64,66]},
      {name:"F♯", notes:[42,54,58,61,66]}
    ]
  });
  const PADS = Object.freeze([
    {name:"E · hold", note:64},
    {name:"G · answer", note:67},
    {name:"A · lift", note:69},
    {name:"B · insist", note:71},
    {name:"D · open", note:74}
  ]);

  const round = n => Math.round(n * 10000) / 10000;
  function sceneAt(second) {
    return SCENES.find(s => second >= s.start && second < s.end) || SCENES[SCENES.length-1];
  }
  function tempoAt(second) {
    const t = Math.max(0, Math.min(DURATION, Number(second) || 0));
    if (t < 10) return 72;
    if (t < 24) return 84 + (t - 10) * 4.4;
    if (t < 38) return 145.6 + (t - 24) * 1.9;
    if (t < 48) return 78;
    return 104;
  }
  function beats() {
    const list = [];
    let t = 0, index = 0;
    while (t < DURATION - .0001 && index < 300) {
      const bpm = tempoAt(t), length = 60 / bpm;
      list.push({t:round(t), index, bpm:round(bpm), length:round(length), scene:sceneAt(t).id});
      t += length;
      index++;
    }
    return list;
  }
  function buildScore(palette="soft-reset") {
    if (!Object.prototype.hasOwnProperty.call(PROGRESSIONS,palette)) throw Error("Unknown harmonic palette");
    const progression = PROGRESSIONS[palette];
    const events = [];
    const add = (t,track,kind,note,dur,velocity) => {
      if (!Number.isFinite(t) || t < 0 || t >= DURATION || dur <= 0) return;
      events.push({t:round(t),track,kind,note,dur:round(Math.min(dur,DURATION-t)),velocity:round(velocity)});
    };
    const b = beats();
    for (const beat of b) {
      const t = beat.t, len = beat.length, s = beat.scene;
      const chordIndex = Math.floor(beat.index / 4) % progression.length;
      const chord = progression[chordIndex].notes;
      const pulse = s !== "intervene";
      const root = chord[0];
      if (s === "city" || s === "reset") {
        if (beat.index % 2 === 0) add(t,"bass","bass",root,Math.min(1.2,len*1.8),.66);
      } else if (s === "accelerate" || s === "war") {
        add(t,"bass","bass",root,len*.8,s === "war"?.9:.74);
      }
      if (s !== "war" && (beat.index % (s === "intervene"?3:2) === 0)) {
        const high = chord.slice(-4);
        add(t,"glass","glass",high[(Math.floor(beat.index/2))%high.length]+12,
            Math.min(.95,len*.9),s === "intervene"?.26:.5);
      }
      if (beat.index % 4 === 0 && s !== "war") {
        for(const n of chord.slice(-4)) add(t,"strings","strings",n,Math.min(3.5,len*3.5),
           s === "intervene"?.12:.17);
      }
      if (pulse) {
        if(s !== "city" || beat.index % 2 === 0) add(t,"drums","kick",36,.28,
           s === "war"?.88:s === "city"?.3:.55);
        if (s === "accelerate" || s === "war" || s === "reset") {
          if (beat.index%2===1) add(t,"drums","snare",38,.19,s==="war"?.7:.4);
          const divisions=s==="war"?4:2;
          for(let i=0;i<divisions;i++)add(t+len*i/divisions,"drums","hat",42,.075,
            s==="war"?.29:.13);
        }
      }
      if (s === "war") {
        if (beat.index%2===0) add(t,"metal","metal",73+(beat.index%5),len*.6,.7);
        for(let i=0;i<3;i++) add(t+(len*i/3),"drums","hat",42,.04,.22);
        if (beat.index%4===0) add(t,"strings","strings",52,Math.min(1.7,len*2.8),.14);
      }
    }
    // Composed, original human melodic entry. The performer can overdub more.
    const human = [
      [38.20,64,1.4,.45],[40.05,67,1.0,.49],[41.55,69,1.8,.5],
      [44.05,71,1.3,.45],[46.15,69,1.2,.52],
      [48.30,67,1.4,.46],[50.35,69,1.1,.49],[52.15,74,1.6,.52],
      [55.20,71,1.4,.48],[57.55,64,2.2,.45]
    ];
    for(const [t,n,d,v] of human)add(t,"human","human",n,d,v);
    events.sort((a,b)=>a.t-b.t || a.track.localeCompare(b.track));
    return events;
  }
  function cues(palette="soft-reset") {
    const harmony = PROGRESSIONS[palette] || PROGRESSIONS["soft-reset"];
    return SCENES.map((scene,index)=>({
      time_sec:scene.start, end_sec:scene.end,scene:scene.id,
      visual_event:scene.cue, intensity:scene.intensity,
      treatment:scene.visual,
      harmony_hint:harmony[index%harmony.length].name
    }));
  }
  return Object.freeze({DURATION, TRACKS, SCENES, PROGRESSIONS, PADS, sceneAt, tempoAt, beats, buildScore, cues});
});
