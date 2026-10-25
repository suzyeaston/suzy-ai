"use strict";
// Node's built-in test runner. No browser, network, hardware or npm deps.
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const test = require("node:test");
const assert = require("node:assert/strict");

const html = fs.readFileSync(path.join(__dirname, "..", "suzy_ai", "music", "stage_panel.html"), "utf8");
const script = html.match(/<script>([\s\S]*?)<\/script>/)?.[1];
assert.ok(script, "stage panel inline JS was not found");

function panel({holdArm=false, failStop=false}={}) {
  const calls = [], timers = new Map(), keyHandlers = new Map();
  const nodes = new Map();
  let timerNo = 0, resolveArm = null;
  let state = {state:"idle",connected:true,progress:0,notes:[],references_offered:[],capture_seconds:0};
  function node(id,tagName="DIV") {
    if(!nodes.has(id)) {
      const n = {id,tagName,dataset:{},options:[],disabled:false,value:"",
        checked:false,textContent:"",isContentEditable:false,
        attributes:{},
        setAttribute(k,v){this.attributes[k]=v;},
        addEventListener(type,fn){this["on"+type]=fn;},
        replaceChildren(){this.options=[];},
        add(opt){this.options.push(opt);},
        click(){if(this.disabled)return;return this.onclick?.();}
      };
      nodes.set(id,n);
    }
    return nodes.get(id);
  }
  const roles = ["space","answer","counter"].map(role=>{
    const n=node("role-"+role,"BUTTON");n.dataset.role=role;return n;
  });
  for(const [id,value] of Object.entries({bpm:"92",beats:"8",chord:"",countdown:"0",channel:"1"}))
    node(id).value=value;
  node("research").checked=true;
  node("state").dataset={};
  const document={
    activeElement:{tagName:"BODY",isContentEditable:false},
    getElementById:id=>node(id),
    querySelectorAll:()=>roles,
    createElement:()=>({value:"",textContent:""}),
    addEventListener:(type,fn)=>keyHandlers.set(type,fn),
  };
  function response(data,ok=true){return {ok,json:async()=>data};}
  async function fetch(url,opts={}) {
    if(!opts.method) {
      if(url==="/api/status")return response({...state});
      if(url==="/api/devices")return response({inputs:[{id:0,name:"Scarlett Solo"}],outputs:[{id:1,name:"Headphones"}]});
      throw Error("Unexpected GET "+url);
    }
    calls.push(url);
    if(url==="/api/arm") {
      if(holdArm) return await new Promise(resolve=>{
        resolveArm=()=>{state={...state,state:"capturing"};resolve(response({...state}));};
      });
      state={...state,state:"capturing"};
    } else if(url==="/api/stop") {
      if(failStop)return response({error:"Stop failed"},false);
      state={...state,state:"idle"};
    } else if(url==="/api/audition") state={...state,state:"playing"};
    else if(url==="/api/connect") state={...state,state:"idle",connected:true};
    return response({...state});
  }
  vm.runInNewContext(script,{
    document,fetch,JSON,Number,Promise,
    setInterval:()=>0,
    setTimeout:fn=>{const id=++timerNo;timers.set(id,fn);return id;},
    clearTimeout:id=>timers.delete(id),
  },{timeout:1000});
  async function settle(){for(let i=0;i<8;i++)await new Promise(resolve=>setImmediate(resolve));}
  function key(key,code,extras={}){
    const e={key,code,shiftKey:false,altKey:false,metaKey:false,ctrlKey:false,repeat:false,isComposing:false,
      target:document.activeElement,preventDefault(){this.prevented=true;},...extras};
    keyHandlers.get("keydown")(e);return e;
  }
  return {node,document,settle,key,calls,timers,releaseArm:()=>resolveArm?.(),state:()=>state};
}

test("bare Space and Enter never capture/audition; shortcuts require Shift and noninteractive focus", async()=>{
  const p=panel();await p.settle();
  p.key(" ","Space");p.key("Enter","Enter");p.key("1","Digit1");
  await p.settle();
  assert.deepEqual(p.calls,[]);
  assert.equal(p.key("L","KeyL",{shiftKey:true}).prevented,true);
  await p.settle();
  assert.deepEqual(p.calls,["/api/arm"]);
  p.document.activeElement={tagName:"BUTTON",isContentEditable:false};
  p.key("P","KeyP",{shiftKey:true});
  await p.settle();
  assert.deepEqual(p.calls,["/api/arm"]);
});

test("Escape during countdown cancels all scheduled capture and still sends STOP", async()=>{
  const p=panel();await p.settle();p.node("countdown").value="3";
  p.node("capture").click();
  assert.ok(p.timers.size>0);
  p.document.activeElement={tagName:"INPUT"};
  assert.equal(p.key("Escape","Escape").prevented,true);
  await p.settle();
  for(const fn of p.timers.values())fn();
  await p.settle();
  assert.deepEqual(p.calls,["/api/stop"]);
  assert.equal(p.state().state,"idle");
});

test("STOP queues after an in-flight arm; no delayed capture remains active",async()=>{
  const p=panel({holdArm:true});await p.settle();
  p.node("capture").click();await p.settle();
  assert.deepEqual(p.calls,["/api/arm"]);
  p.node("stop").click();await p.settle();
  assert.deepEqual(p.calls,["/api/arm"],"STOP must not race past the in-flight arm");
  p.releaseArm();await p.settle();
  assert.deepEqual(p.calls,["/api/arm","/api/stop"]);
  assert.equal(p.state().state,"idle");
  assert.equal(p.node("capture").disabled,false);
});

test("failed STOP leaves new capture locked and warns to mute Logic",async()=>{
  const p=panel({failStop:true});await p.settle();
  p.node("stop").click();await p.settle();
  assert.equal(p.node("capture").disabled,true);
  assert.match(p.node("error").textContent,/STOP NOT CONFIRMED/);
  assert.match(html,/does <strong>not<\/strong> mute the Magenta AU in Logic/);
});
