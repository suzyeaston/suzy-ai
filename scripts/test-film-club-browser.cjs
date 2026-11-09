"use strict";
// Zero-npm-dependency Chrome DevTools Protocol smoke. Node >=22 (native WebSocket).
// Unlike --dump-dom, CDP can await OfflineAudioContext.startRendering().
const {spawn}=require("node:child_process");
const fs=require("node:fs");
const os=require("node:os");
const path=require("node:path");

const wait=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const failAfter=(ms,label)=>new Promise((_,reject)=>setTimeout(()=>reject(Error(label+" timed out after "+ms+"ms")),ms));
const chromeBin=process.argv[2]||process.env.CHROME||"google-chrome";
const temp=fs.mkdtempSync(path.join(os.tmpdir(),"suzy-film-chrome-"));
const httpPort=18863,devtoolsPort=18864;
const server=spawn("python3",["-m","http.server",String(httpPort),"--bind","127.0.0.1"],{
  cwd:path.resolve(__dirname,".."),stdio:"ignore"
});
let chrome=null,ws=null,chromeLogs="";
async function ready(url) {
  for(let i=0;i<90;i++){
    try{const response=await fetch(url);if(response.ok)return response;}catch{}
    await wait(200);
  }
  throw Error("HTTP endpoint did not open: "+url);
}
async function run(){
  if(typeof WebSocket!=="function")throw Error("Node 22+ required for built-in WebSocket. Set up Node 22 in CI.");
  await ready("http://127.0.0.1:"+httpPort+"/tests/film_club_browser_smoke.html");
  chrome=spawn(chromeBin,[
    "--headless=new","--no-sandbox","--disable-gpu","--disable-dev-shm-usage",
    "--no-first-run","--remote-allow-origins=*",
    "--remote-debugging-port="+devtoolsPort,"--user-data-dir="+temp,"about:blank"
  ],{stdio:["ignore","ignore","pipe"]});
  chrome.stderr.on("data",chunk=>{chromeLogs=(chromeLogs+chunk.toString()).slice(-4000);});
  const list=await ready("http://127.0.0.1:"+devtoolsPort+"/json/list").then(r=>r.json());
  const tab=list.find(x=>x.type==="page");
  if(!tab?.webSocketDebuggerUrl)throw Error("Chrome did not expose a Page DevTools websocket");
  ws=new WebSocket(tab.webSocketDebuggerUrl);
  await Promise.race([new Promise((resolve,reject)=>{
    ws.addEventListener("open",resolve,{once:true});
    ws.addEventListener("error",reject,{once:true});
  }),failAfter(10000,"CDP connection")]);
  let nextId=0;
  const pending=new Map(),signals=new Map();
  ws.addEventListener("message",event=>{
    let msg;
    try{msg=JSON.parse(event.data);}catch{return;}
    if(msg.id&&pending.has(msg.id)){
      const {resolve,reject}=pending.get(msg.id);pending.delete(msg.id);
      if(msg.error)reject(Error(JSON.stringify(msg.error)));
      else resolve(msg.result);
    }
    if(msg.method&&signals.has(msg.method)){
      for(const resolve of signals.get(msg.method))resolve(msg.params);
      signals.delete(msg.method);
    }
  });
  function send(method,params={}){
    const id=++nextId;
    return new Promise((resolve,reject)=>{
      pending.set(id,{resolve,reject});
      ws.send(JSON.stringify({id,method,params}));
    });
  }
  function signal(method){
    return new Promise(resolve=>{
      if(!signals.has(method))signals.set(method,[]);
      signals.get(method).push(resolve);
    });
  }
  await send("Page.enable");
  await send("Runtime.enable");
  const loaded=signal("Page.loadEventFired");
  await send("Page.navigate",{url:"http://127.0.0.1:"+httpPort+"/tests/film_club_browser_smoke.html"});
  await Promise.race([loaded,failAfter(15000,"Page load")]);
  const expression="new Promise(resolve => {"+
    "let attempts=0;const timer=setInterval(()=>{"+
    "const result=document.body?.dataset?.result;"+
    "if(result==='PASS'||result==='FAIL'){clearInterval(timer);resolve({result,details:document.body.textContent});}"+
    "else if(++attempts>=300){clearInterval(timer);resolve({result:'TIMEOUT',details:document.body?.textContent});}"+
    "},200);})";
  const data=await Promise.race([
    send("Runtime.evaluate",{expression,awaitPromise:true,returnByValue:true}),
    failAfter(70000,"Chrome OfflineAudioContext render")
  ]);
  if(data.exceptionDetails)throw Error("CDP page exception: "+JSON.stringify(data.exceptionDetails));
  const output=data.result?.value;
  if(output?.result!=="PASS")throw Error("Web Audio smoke: "+JSON.stringify(output));
  process.stdout.write("Real Chrome 60s OfflineAudioContext PCM render: "+output.details+"\n");
}
run().catch(err=>{
  process.stderr.write("SOFT RESET browser smoke FAILED: "+(err.stack||err)+"\n");
  if(chromeLogs)process.stderr.write("Chrome stderr tail:\n"+chromeLogs+"\n");
  process.exitCode=1;
}).finally(()=>{
  try{ws?.close();}catch{}
  try{chrome?.kill("SIGTERM");}catch{}
  try{server.kill("SIGTERM");}catch{}
  try{fs.rmSync(temp,{recursive:true,force:true});}catch{}
});
