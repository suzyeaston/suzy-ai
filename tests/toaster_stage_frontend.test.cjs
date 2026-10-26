/* Toaster stage smoke tests using only the Node built-in test runner.
   No macOS MIDI driver, model, DAW, browser dependency or network access. */
"use strict";
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const markup = fs.readFileSync(
  path.join(__dirname, "..", "suzy_ai", "music", "toaster_stage.html"), "utf8"
);
const scriptMatch = markup.match(/<script>([\s\S]*?)<\/script>/);
assert.ok(scriptMatch, "inline stage script must exist");

function boot(overrides = {}) {
  const nodes = new Map();
  const events = [];
  const modes = ["low", "direct", "high"].map(mode => ({
    dataset: { mode }, attributes: {},
    setAttribute(key, value) { this.attributes[key] = value; },
    click() { return this.onclick(); }
  }));
  const getNode = id => {
    if (!nodes.has(id)) {
      nodes.set(id, {
        value: ({
          loopOwner: "logic", loopBpm: "120", loopBars: "4", loopBeats: "4"
        })[id] || "", textContent: "", disabled: false, style: {},
        options: [], children: [], appendChild(child) { this.children.push(child); }, classList: {
          items: new Set(),
          add(value) { this.items.add(value); },
          remove(value) { this.items.delete(value); },
          contains(value) { return this.items.has(value); }
        },
        replaceChildren() { this.options = []; this.children = []; },
        add(option) { this.options.push(option); },
        click() { return this.onclick(); }
      });
    }
    return nodes.get(id);
  };
  const status = {
    enabled: true, input_name: null, mode: "direct", gate_open: true,
    keyboard_note_events: 0, held_notes: 0, last_keyboard_note: null
  };
  const doc = {
    getElementById: getNode,
    querySelectorAll(query) {
      assert.equal(query, "[data-mode]");
      return modes;
    },
    querySelector(query) {
      const m = query.match(/^\[data-mode="(low|direct|high)"\]$/);
      return m && modes.find(button => button.dataset.mode === m[1]);
    },
    createElement(tag) {
      assert.ok(["option","li"].includes(tag));
      return { value: "", textContent: "", className: "" };
    },
    addEventListener(name, callback) {
      if (name === "keydown") this.keydown = callback;
    }
  };
  const fetch = async (url, opts = {}) => {
    const headers = opts.headers || {};
    events.push({ url, opts });
    if (opts.method === "POST") {
      assert.equal(headers["X-Suzy-Token"], "test-token");
      assert.equal(headers["Content-Type"], "application/json");
      const body = JSON.parse(opts.body);
      if (overrides.failChord && url === "/api/test") {
        return { ok: false, json: async () => ({ error: "Test cue refused" }) };
      }
      if (url === "/api/mode") status.mode = body.mode;
      if (url === "/api/gate") status.gate_open = body.open;
      if (url === "/api/select") status.input_name = body.input;
      if (url === "/api/disconnect") status.input_name = null;
      if (url === "/api/test") status.held_notes = 4;
      if (url === "/api/release") status.held_notes = 0;
      return { ok: true, json: async () => ({ ...status }) };
    }
    if (url === "/api/inputs") {
      return { ok: true, json: async () => ({ inputs: ["Keystation Mini 32 MK3"] }) };
    }
    if (url === "/api/audio-routing") {
      return { ok: true, json: async () => overrides.audioUnavailable
        ? { available: false, devices: [], message: "unavailable", logic_audio_device_observed: false }
        : { available: true, devices: [
          { name: "Scarlett Solo USB", input_channels: 2, output_channels: 2,
            system_default_input: true, system_default_output: true, scarlett_candidate: true },
          { name: "Built-in Output", input_channels: 0, output_channels: 2,
            system_default_input: false, system_default_output: false, scarlett_candidate: false }
        ], logic_audio_device_observed: false, can_change_host_audio_output: false } };
    }
    assert.equal(url, "/api/status");
    return { ok: true, json: async () => ({ ...status }) };
  };
  const sandbox = {
    document: doc, fetch,
    setInterval() {}, clearTimeout() {},
    setTimeout(callback) { /* Do not erase animation before assertion */ return 1; }
  };
  const script = scriptMatch[1].replace("__MAGENTA_TOKEN__", "test-token");
  new vm.Script(script, { filename: "toaster_stage.inline.js" }).runInNewContext(sandbox);
  return { getNode, modes, events, doc, status };
}

test("toaster stays dependency free and makes its limitations explicit", () => {
  assert.match(markup, /SUZY\/\/TOAST/);
  assert.match(markup, /AUDIO UNVERIFIED/);
  assert.match(markup, /not yet a loadable Logic AUv3/);
  assert.match(markup, /mute the[\s\S]*AI - MRT2[\s\S]*track in Logic/);
  assert.match(markup, /CC 21/);
  assert.match(markup, /CC 26/);
  assert.doesNotMatch(markup, /<script\s+src=/);
  assert.doesNotMatch(markup, /<link[^>]*https?:/);
  assert.doesNotMatch(markup, /AudioContext|MediaRecorder|webkitAudio|navigator\.requestMIDIAccess/);
});

test("lever sends authenticated test chord and never marks neural audio verified", async () => {
  const app = boot();
  await app.getNode("lever").onclick();
  assert.ok(app.events.some(x => x.url === "/api/test" && x.opts.method === "POST"));
  assert.equal(app.getNode("toastMessage").textContent, "MIDI SENT!");
  assert.match(app.getNode("toastDetail").textContent, /Audio still unverified/);
  assert.ok(app.getNode("toasterArt").classList.contains("pop"));
  assert.equal(app.getNode("status").textContent, "LOCAL MIDI BRIDGE · AUDIO UNVERIFIED");
});

test("rejected test chord produces no success animation", async () => {
  const app = boot({ failChord: true });
  await app.getNode("lever").onclick();
  assert.notEqual(app.getNode("toastMessage").textContent, "MIDI SENT!");
  assert.ok(!app.getNode("toasterArt").classList.contains("pop"));
  assert.match(app.getNode("error").textContent, /Test cue refused/);
});

test("MIDI gate and release preserve honest safety messaging", async () => {
  const app = boot();
  await new Promise(setImmediate); // let the initial /api/status poll establish current state
  await app.getNode("gate").onclick();
  assert.equal(app.status.gate_open, false);
  assert.equal(app.getNode("test").disabled, true);
  assert.match(app.getNode("feedback").textContent, /not neural audio/);
  await app.getNode("release").onclick();
  assert.ok(app.events.some(x => x.url === "/api/release"));
  assert.match(app.getNode("feedback").textContent, /Neural audio may continue/);
});

test("browning is visual only; mode buttons call only existing MIDI mode API", async () => {
  const app = boot();
  const slider = app.getNode("heat");
  slider.value = "80";
  slider.oninput();
  assert.equal(app.getNode("heatValue").textContent, "80%");
  assert.match(app.getNode("slice").style.filter, /sepia/);
  assert.ok(!app.events.some(x => x.opts.method === "POST"));
  await app.modes[0].onclick();
  const cmd = app.events.find(x => x.url === "/api/mode");
  assert.deepEqual(JSON.parse(cmd.opts.body), { mode: "low" });
  assert.equal(app.status.mode, "low");
});

test("Audio I/O panel discovers devices without any write or false Logic selection", async () => {
  const app = boot();
  assert.match(markup, /id="audio-io"/);
  assert.match(markup, /id="scanAudio"/);
  assert.match(markup, /In Logic, the host owns/);
  await app.getNode("scanAudio").onclick();
  assert.ok(app.events.some(x => x.url === "/api/audio-routing" && !x.opts.method));
  assert.equal(app.getNode("audioInputs").children.length, 1);
  assert.equal(app.getNode("audioOutputs").children.length, 2);
  assert.match(app.getNode("audioInputs").children[0].textContent, /Scarlett Solo USB/);
  assert.match(app.getNode("audioScanStatus").textContent, /Host routing not observed/);
  assert.ok(!app.events.some(x => x.opts.method === "POST"));
});

test("audio discovery failure does not claim selected output", async () => {
  const app = boot({audioUnavailable:true});
  await app.getNode("scanAudio").onclick();
  assert.match(app.getNode("audioScanStatus").textContent, /Discovery unavailable/);
  assert.match(app.getNode("audioInputs").children[0].textContent, /No compatible devices/);
});

test("loop controls compute a rehearsal reference but never record or touch Logic", async () => {
  const app = boot();
  assert.match(markup, /id="looping"/);
  assert.match(markup, /do <strong>not<\/strong> record, launch, quantize or overdub Logic\/VE-22 audio/);
  assert.equal(app.getNode("loopSeconds").textContent, "8.00 seconds");
  app.getNode("loopBpm").value = "100";
  app.getNode("loopBpm").oninput();
  assert.equal(app.getNode("loopSeconds").textContent, "9.60 seconds");
  app.getNode("loopOwner").value = "ve22";
  app.getNode("loopOwner").onchange();
  assert.match(app.getNode("loopInstructions").textContent, /pedal itself/);
  app.getNode("loopOwner").value = "companion";
  app.getNode("loopOwner").onchange();
  assert.match(app.getNode("loopInstructions").textContent, /--looper-only/);
  app.getNode("loopBpm").value = "999";
  app.getNode("loopBpm").oninput();
  assert.match(app.getNode("loopSeconds").textContent, /Check BPM/);
  assert.ok(!app.events.some(x => x.opts.method === "POST"));
});
