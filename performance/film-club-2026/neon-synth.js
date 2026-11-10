/* ACCELERANDO · Film-only NEON synth patch.
 * Deliberately audible without Google's separate AU prompt editor.
 * Mutates ONLY this Film Club page's in-memory instrument presets, keeping
 * the original Futureproof /toaster/live source and native audio intact.
 * This is an original Web Audio synthesizer, NOT generated Magenta audio.
 */
(() => {
  "use strict";
  const button=document.getElementById("filmSynthKeys");
  const status=document.getElementById("filmSynthKeysStatus");
  if(!button||!status)return;
  if(typeof INSTRUMENTS==="undefined" ||
     typeof makeVoice!=="function" ||
     typeof releaseVoice!=="function" ||
     typeof setInstrumentSource!=="function" ||
     typeof synth!=="function"){
    status.textContent="NEON SYNTH UNAVAILABLE · ORIGINAL AUDIO ENGINE DID NOT LOAD";
    button.disabled=true;
    return;
  }
  // One instrument, one master clock. Other lanes remain individually
  // switchable to Google's MRT2 generator or local browser instruments.
  window.suzyFilmClubSynthPiano=true;
  Object.assign(INSTRUMENTS.keys,{
    name:"NEON FM SYNTH PIANO",wave:"sawtooth",overtone:"triangle",
    mix:.30,attack:.009,release:.17,sustain:.38,octave:0,filter:6600
  });
  Object.assign(INSTRUMENTS.pad,{
    name:"GLACIAL SUPERSAW PAD",wave:"sawtooth",overtone:"triangle",
    mix:.15,attack:.18,release:.60,sustain:.73,octave:0,filter:2800
  });
  Object.assign(INSTRUMENTS.pluck,{
    name:"PIXEL GLASS PLUCK",wave:"square",overtone:"sine",
    mix:.10,attack:.004,release:.11,sustain:.21,octave:12,filter:5200
  });
  Object.assign(INSTRUMENTS.bass,{
    name:"RUBBER ANALOG SUB",wave:"sawtooth",overtone:"sine",
    mix:.05,attack:.013,release:.19,sustain:.78,octave:-12,filter:1150
  });
  Object.assign(INSTRUMENTS.violin,{
    name:"NEON SAW LEAD",wave:"sawtooth",overtone:"triangle",
    mix:.32,attack:.065,release:.22,sustain:.71,octave:0,filter:4300
  });
  Object.assign(INSTRUMENTS.nylon,{
    name:"SHARP DIGITAL ARP",wave:"square",overtone:"triangle",
    mix:.12,attack:.004,release:.10,sustain:.22,octave:12,filter:4300
  });

  // Extend the original synthesizer with a clean, musical FM-like
  // transient, a detuned partial and a descending filter sweep.
  // Existing gain buses, loop capture, and transport stay untouched.
  const makeOriginalVoice=makeVoice;
  makeVoice=function(which,pitch,time,instrument,peak,live,role="chord"){
    const voice=makeOriginalVoice(which,pitch,time,instrument,peak,live,role);
    if(!voice || !window.suzyFilmClubSynthPiano || instrument!=="keys")
      return voice;
    const frequency=voice.osc.frequency.value;
    voice.osc.detune.value=-4;
    voice.soft.detune.value=+6;
    const mod=ctx.createOscillator(),depth=ctx.createGain();
    mod.type="sine";
    mod.frequency.setValueAtTime(frequency*2.01,time);
    depth.gain.setValueAtTime(frequency*.12,time);
    depth.gain.exponentialRampToValueAtTime(Math.max(1,frequency*.008),time+.27);
    mod.connect(depth);
    depth.connect(voice.osc.frequency);
    mod.start(time);
    voice.filmMod=mod;
    voice.filmModDepth=depth;
    return voice;
  };
  const releaseOriginalVoice=releaseVoice;
  releaseVoice=function(voice,time){
    if(voice?.filmMod){
      // A scheduled release must stop the FM carrier modulation too,
      // or repeated Film Club chords leak invisible oscillators.
      try{voice.filmMod.stop(time+Math.max(.50,voice.release*5))}catch{}
    }
    return releaseOriginalVoice(voice,time);
  };

  // Human-played chords and recorded chord loops get a lightweight
  // upward syncopated sequence. These are true scheduled Web Audio notes
  // at the same clock time as the original master MIDI/PCM loop.
  const synthOriginal=synth;
  synth=function(which,index,time=ctx.currentTime+.01,quiet=false,
                 holdSeconds=.85,instrument=decks[which].instrument){
    synthOriginal(which,index,time,quiet,holdSeconds,instrument);
    if(!window.suzyFilmClubSynthPiano || which!=="pyramid" ||
       instrument!=="keys" || typeof localInstrumentAudible!=="function" ||
       !localInstrumentAudible(which))return;
    const notes=SCENES.pyramid.notes[index];
    if(!Array.isArray(notes)||notes.length<3)return;
    const order=[0,2,1,3];
    // 100 BPM, one sixteenth note = 0.15 sec. Keep the existing tempo,
    // master beat-one alignment and recording layers unchanged.
    const step=60/Math.max(60,Number(bpm)||100)/4;
    for(let i=0;i<4;i++){
      const note=notes[order[i]%notes.length]+12;
      const at=time+step*i;
      const v=makeVoice(which,note,at,"keys",quiet?.008:.013,false);
      releaseVoice(v,at+step*.73);
    }
  };

  function readout(){
    const active=decks?.pyramid?.instrumentSource==="local";
    button.setAttribute("aria-pressed",String(active));
    button.textContent=active?"✦ NEON SYNTH PIANO · ON":"✦ ENABLE NEON SYNTH PIANO";
    status.textContent=active?
      "LIVE FM SYNTH + SIXTEENTH ARPS · NO GOOGLE PROMPTS REQUIRED":
      "GOOGLE MRT2 SELECTED · NATIVE SOUND BANK MAY DIFFER";
  }

  // Film Club alone defaults to playable local synth keys. This prevents
  // a stuck/old Google AU from silencing the core piano chord instrument.
  if(typeof stageStarted!=="undefined" && !stageStarted)
    setInstrumentSource("pyramid","local");
  readout();
  button.addEventListener("click",async()=>{
    try{
      if(typeof openAudio==="function")await openAudio();
      setInstrumentSource("pyramid",
        decks.pyramid.instrumentSource==="local"?"ai":"local");
      readout();
    }catch(error){
      status.textContent="NEON SYNTH AUDIO COULD NOT START · "+(error?.message||error);
    }
  });
})();
