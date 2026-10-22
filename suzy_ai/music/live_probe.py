"""Experimental live Focusrite audio probe for SUZY//AI (no Swift, files or Logic export).

Captures short phrases and plays AI responses through one PortAudio duplex stream.
This is not stage-safe, beat-synchronized, an Audio Unit, or continuous AI synthesis.
"""
from __future__ import annotations

import argparse
from array import array
import io
import math
import struct
import sys
import time
import wave

from .live import LiveSession

RATE = 48000
CHANNELS = 2
FRAME_BYTES = CHANNELS * 2
BLOCKSIZE = 512


class DuplexBuffer:
    """Bounded capture and one-shot playback. No model/HTTP/file work in callback.

    Python buffer copying still acquires the GIL and is not guaranteed real-time.
    The first prototype intentionally has no input passthrough/monitoring.
    """

    def __init__(self, frames: int):
        if not 1 <= frames <= RATE * 8:
            raise ValueError("capture length must be within eight seconds")
        self.target_bytes = frames * FRAME_BYTES
        self.source = bytearray(self.target_bytes)
        self.written = 0
        self.recording = False
        self.response = b""
        self.played = 0
        self.playing = False
        self.audio_flags = 0
        self._silence = bytes(BLOCKSIZE * FRAME_BYTES)

    def arm(self):
        if self.recording or self.playing:
            raise RuntimeError("finish capture/playback before arming again")
        self.written = 0
        self.recording = True

    def captured(self) -> bytes:
        if self.recording or self.written != self.target_bytes:
            raise RuntimeError("capture is incomplete")
        return bytes(self.source)

    def play(self, pcm: bytes):
        if self.recording or self.playing or len(pcm) % FRAME_BYTES or not pcm:
            raise ValueError("play requires complete stereo PCM16 and idle stream")
        self.response = pcm
        self.played = 0
        self.playing = True

    def callback(self, indata, outdata, frames, time_info=None, status=None):
        size = len(outdata)
        outdata[:] = (self._silence[:size] if size <= len(self._silence)
                      else bytes(size))
        if status:
            self.audio_flags += 1
        if self.recording:
            count = min(self.target_bytes - self.written, frames * FRAME_BYTES)
            if count:
                self.source[self.written:self.written + count] = indata[:count]
                self.written += count
            if self.written == self.target_bytes:
                self.recording = False
        if self.playing:
            count = min(len(self.response) - self.played, size)
            outdata[:count] = self.response[self.played:self.played + count]
            self.played += count
            if self.played == len(self.response):
                self.playing = False

def capture_levels(pcm: bytes) -> list[tuple[float, float]]:
    """Per-channel (peak, RMS) in dBFS; never saves microphone data."""
    if not pcm or len(pcm) % FRAME_BYTES:
        raise ValueError("incomplete stereo PCM capture")
    samples = array("h")
    samples.frombytes(pcm)
    if sys.byteorder != "little":
        samples.byteswap()
    levels = []
    for channel in range(CHANNELS):
        channel_samples = samples[channel::CHANNELS]
        peak = max(abs(sample) for sample in channel_samples) / 32768
        rms = math.sqrt(sum(float(sample) ** 2 for sample in channel_samples)
                        / len(channel_samples)) / 32768
        levels.append((round(peak, 5), round(rms, 5)))
    return levels


def performer_countdown(seconds: int, duration: float, *, read=input,
                        pause=time.sleep, announce=print):
    """Block outside the audio callback until the performer chooses to begin."""
    if not 0 <= seconds <= 10:
        raise ValueError("countdown must be 0–10 seconds")
    read(f"READY: Press Return for a {seconds}-second countdown "
         "(Ctrl+C to stop). ")
    for remaining in range(seconds, 0, -1):
        announce(f"  {remaining}...", flush=True)
        pause(1.0)
    announce(f">>> RECORDING NOW: sing/play for {duration:.1f} seconds <<<",
             flush=True)


def diagnostic_tone(duration: float = 0.75, amplitude: float = 0.06) -> bytes:
    """Low-level two-channel 440-Hz diagnostic tone, with 30-ms end fades."""
    if not 0.2 <= duration <= 2.0 or not 0 < amplitude <= 0.1:
        raise ValueError("diagnostic tone outside safe bounds")
    frames = round(RATE * duration)
    fade_frames = round(RATE * 0.03)
    result = bytearray(frames * FRAME_BYTES)
    for i in range(frames):
        envelope = min(1.0, i / fade_frames, (frames - 1 - i) / fade_frames)
        sample = round(32767 * amplitude * envelope
                       * math.sin(2 * math.pi * 440 * i / RATE))
        struct.pack_into("<hh", result, i * FRAME_BYTES, sample, sample)
    return bytes(result)


def test_output(sd, output_device):
    """Independent playback-only test; no microphone or SUZY//AI model involved."""
    info = sd.query_devices(output_device, "output")
    print(f"OUTPUT TEST: {info['name']} ({output_device}) at 48 kHz, stereo.")
    print("Turn speaker/headphone volume DOWN first; playing a quiet 440-Hz tone.")
    pcm = diagnostic_tone()
    with sd.RawOutputStream(device=output_device, samplerate=RATE,
                            channels=CHANNELS, dtype="int16") as stream:
        stream.write(pcm)
        time.sleep(0.1)
    print("Sent tone to output device; audibility still needs your confirmation.")


def choose_listening_output(sd, *, read=input, announce=print, preview=test_output):
    """Select an output by actual listening test, before any mic capture.

    Device indices are session-local PortAudio indices, not stable identifiers.
    """
    choices = {index: info["name"]
               for index, info in enumerate(sd.query_devices())
               if info["max_output_channels"] >= CHANNELS}
    if not choices:
        raise ValueError("No stereo output devices available at this time")
    announce("LISTENING OUTPUT: choose where SUZY//AI should be heard.")
    announce("The microphone will NOT record during this selection.")
    for index, name in choices.items():
        announce(f"  {index}: {name}")
    while True:
        choice = read("Enter an output number (or q to quit): ").strip().lower()
        if choice in ("q", "quit"):
            raise KeyboardInterrupt
        if not choice.isdecimal() or int(choice) not in choices:
            announce("Choose one of the output numbers listed above.")
            continue
        selected = int(choice)
        try:
            preview(sd, selected)
        except (OSError, ValueError) as exc:
            announce(f"Could not play a test tone through {choices[selected]}: {exc}")
            continue
        heard = read("Did you hear the tone in your intended headphones or "
                     "speakers? [y/N]: ").strip().lower()
        if heard in ("y", "yes"):
            announce(f"Confirmed listening output: {choices[selected]} ({selected}).")
            return selected
        announce("Not confirmed. Choose another output or q to quit.")


def response_pcm(wav_bytes: bytes, gain: float) -> bytes:
    """Decode the existing AI renderer's WAV in RAM, applying conservative gain."""
    with wave.open(io.BytesIO(wav_bytes), "rb") as audio:
        if (audio.getnchannels(), audio.getframerate(),
                audio.getsampwidth(), audio.getcomptype()) != (
                    CHANNELS, RATE, 2, "NONE"):
            raise ValueError("unexpected response WAV format")
        samples = array("h")
        samples.frombytes(audio.readframes(audio.getnframes()))
    if sys.byteorder != "little":
        samples.byteswap()
    for i, sample in enumerate(samples):
        samples[i] = round(sample * gain)
    if sys.byteorder != "little":
        samples.byteswap()
    return samples.tobytes()


def route_output_channels(pcm: bytes, mix: str = "auto") -> tuple[bytes, str]:
    """Center a one-sided mono response in both ears, or preserve true stereo.

    Pure post-render audio routing: no effect on the source, AI features or
    real-time callback. Duplicated mono is dual-mono output, not spatial stereo.
    """
    if mix not in ("auto", "stereo", "mono-center"):
        raise ValueError("output mix must be auto, stereo or mono-center")
    if not pcm or len(pcm) % FRAME_BYTES:
        raise ValueError("expected nonempty interleaved stereo PCM16")
    if mix == "stereo":
        return pcm, "preserved independent stereo L/R"

    levels = capture_levels(pcm)
    left, right = levels[0][0], levels[1][0]
    if mix == "auto":
        if left > 0.0005 and right <= min(0.001, left * 0.02):
            source_channel = 0
        elif right > 0.0005 and left <= min(0.001, right * 0.02):
            source_channel = 1
        else:
            return pcm, "preserved independent stereo L/R (both channels active)"
    else:
        source_channel = 0 if left >= right else 1

    samples = array("h")
    samples.frombytes(pcm)
    if sys.byteorder != "little":
        samples.byteswap()
    for offset in range(0, len(samples), CHANNELS):
        value = samples[offset + source_channel]
        samples[offset] = samples[offset + 1] = value
    if sys.byteorder != "little":
        samples.byteswap()
    return samples.tobytes(), (
        f"centered mono from input channel {source_channel + 1} into L+R "
        "(same voice in both headphones; not stereo widening)"
    )


def process(session: LiveSession, audio: bytes, *, bpm: float, mode: str,
            provider: str, instruction: str, max_wait: float = 12.0):
    config = dict(sample_rate=RATE, channels=CHANNELS, bpm=bpm, mode=mode,
                  provider=provider, instruction=instruction, section="live-probe",
                  key="")
    capture_id = session.arm(config)["id"]
    try:
        for seq, offset in enumerate(range(0, len(audio), 65536)):
            session.append(capture_id, seq, audio[offset:offset + 65536])
        session.finish(capture_id)
        started = time.monotonic()
        while True:
            state = session.status()
            if state["state"] != "processing":
                break
            if time.monotonic() - started > max_wait:
                session.action(capture_id, "discard")
                raise RuntimeError("AI deadline exceeded; no audio will play")
            time.sleep(0.05)
        if state["state"] != "ready":
            raise RuntimeError(state.get("error") or "response failed")
        # The service's audition action grants permission to retrieve audio;
        # audible playback remains explicitly owned by our duplex stream.
        session.action(capture_id, "audition")
        return capture_id, session.audio(capture_id), state["response"]
    except Exception:
        try:
            session.action(capture_id, "discard")
        except (ValueError, RuntimeError):
            pass
        raise

def resolve_devices(device=None, input_device=None, output_device=None):
    """PortAudio device selection: one duplex device or an explicit I/O pair."""
    if device is not None and (input_device is not None or output_device is not None):
        raise ValueError("--device cannot be combined with separate input/output devices")
    if (input_device is None) != (output_device is None):
        raise ValueError("specify both --input-device and --output-device")

    def parse(value):
        return int(value) if isinstance(value, str) and value.isdecimal() else value

    if input_device is not None:
        return parse(input_device), parse(output_device)
    return parse(device)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list-devices", action="store_true")
    parser.add_argument("--test-output", action="store_true",
                        help="play a low-volume tone to output only, with no mic recording")
    parser.add_argument("--choose-output", action="store_true",
                        help="choose speaker/headphone output interactively using a test tone")
    parser.add_argument("--device", help="one PortAudio device used for both input/output")
    parser.add_argument("--input-device", help="input device index, e.g. 0 for Scarlett Solo")
    parser.add_argument("--output-device", help="output device index, e.g. 4 for MacBook speakers")
    parser.add_argument("--bpm", type=float, default=120)
    parser.add_argument("--beats", type=int, default=8,
                        help="phrase length in beats (default 8; 4 seconds at 120 BPM)")
    parser.add_argument("--countdown", type=int, default=3,
                        help="seconds after you press Return before capture (default 3)")
    parser.add_argument("--cycles", type=int, default=1,
                        help="capture/AI/audition cycles (0 = repeat until Ctrl-C)")
    parser.add_argument("--mode", choices=("mirror", "augment", "evolve"), default="mirror")
    parser.add_argument("--provider", choices=("deterministic", "model"),
                        default="deterministic")
    parser.add_argument("--output-mix", choices=("auto", "stereo", "mono-center"),
                        default="auto",
                        help="auto centers a one-sided mono response in both headphones; stereo preserves L/R")
    parser.add_argument("--gain", type=float, default=0.3,
                        help="output amplitude multiplier, 0.0 to 0.5")
    parser.add_argument("--instruction", default="Keep my phrase recognizable; leave room for vocals.")
    args = parser.parse_args(argv)
    try:
        import sounddevice as sd
    except (ImportError, OSError) as exc:
        parser.error(f"sounddevice unavailable: {exc}. Install with python -m pip install -e '.[live]'")
    if args.list_devices:
        print(sd.query_devices())
        return
    if args.test_output:
        if args.choose_output:
            parser.error("--choose-output cannot be combined with --test-output")
        if args.device is not None and args.output_device is not None:
            parser.error("use either --device or --output-device for --test-output")
        selected = args.output_device or args.device
        if selected is None:
            selected = sd.default.device[1]
        elif selected.isdecimal():
            selected = int(selected)
        try:
            test_output(sd, selected)
        except (OSError, ValueError) as exc:
            parser.error(f"output device test failed: {exc}")
        return
    if not 40 <= args.bpm <= 240 or not 1 <= args.beats <= 16 or args.cycles < 0 or not 0 <= args.countdown <= 10:
        parser.error("use 40–240 BPM, 1–16 beats, 0–10 second countdown and nonnegative cycles")
    if not 0 < args.gain <= 0.5:
        parser.error("gain must be greater than zero and at most 0.5")
    frames = round(RATE * args.beats * 60 / args.bpm)
    if not RATE // 4 <= frames <= RATE * 8:
        parser.error("phrase duration must be between 0.25 and eight seconds")
    if args.choose_output:
        if args.device is not None or args.output_device is not None:
            parser.error("--choose-output replaces --device/--output-device")
        if args.input_device is None:
            parser.error("--choose-output requires --input-device (0 for Scarlett Solo)")
        try:
            chosen_output = choose_listening_output(sd)
            device = resolve_devices(input_device=args.input_device,
                                     output_device=chosen_output)
        except ValueError as exc:
            parser.error(str(exc))
    else:
        try:
            device = resolve_devices(args.device, args.input_device, args.output_device)
        except ValueError as exc:
            parser.error(str(exc))
    duplex = DuplexBuffer(frames)
    session = LiveSession()
    print("EXPERIMENTAL | 48 kHz stereo | choose your Focusrite mic input and desired output.")
    print(f"PortAudio devices (input, output): {device}")
    if isinstance(device, tuple):
        input_index, output_index = device
    elif device is None:
        input_index, output_index = sd.default.device
    else:
        input_index = output_index = device
    print(f"Input device: {sd.query_devices(input_index, 'input')['name']}")
    print(f"Output device: {sd.query_devices(output_index, 'output')['name']}")
    print("Headphones, low level, no feedback loops. Logic runs separately.")
    print(f"Capture {frames / RATE:.2f}s after Return + {args.countdown}s countdown, "
          f"{args.provider}/{args.mode}; Ctrl-C stops playback.")
    try:
        with sd.RawStream(device=device, samplerate=RATE, blocksize=BLOCKSIZE,
                          channels=(CHANNELS, CHANNELS), dtype="int16",
                          callback=duplex.callback):
            cycle = 0
            while args.cycles == 0 or cycle < args.cycles:
                cycle += 1
                print(f"\nCycle {cycle}: audio is idle until YOU start.", flush=True)
                performer_countdown(args.countdown, frames / RATE)
                duplex.arm()
                while duplex.recording:
                    time.sleep(0.02)
                captured = duplex.captured()
                levels = capture_levels(captured)
                print("Capture finished. Input peaks: "
                      + ", ".join(f"channel {i + 1}={peak:.1%} (RMS {rms:.1%})"
                                  for i, (peak, rms) in enumerate(levels)), flush=True)
                if max(peak for peak, _ in levels) < 0.005:
                    print("WARNING: very low input. Check VE-22, Scarlett gain, "
                          "the input channel and microphone permission.", flush=True)
                if max(peak for peak, _ in levels) >= 0.98:
                    print("WARNING: likely clipping. Turn down the Scarlett input gain.",
                          flush=True)
                print("AI processing while Logic continues...", flush=True)
                start = time.monotonic()
                cid, wav_bytes, metadata = process(
                    session, captured, bpm=args.bpm, mode=args.mode,
                    provider=args.provider, instruction=args.instruction)
                print(f"Response ready in {time.monotonic()-start:.2f}s "
                      f"(provider={metadata['provider']}, model={metadata['model']})")
                rendered_pcm = response_pcm(wav_bytes, args.gain)
                pcm, route = route_output_channels(rendered_pcm, args.output_mix)
                print(f"Output mix ({args.output_mix}): {route}", flush=True)
                output_levels = capture_levels(pcm)
                print("Output levels (after gain): "
                      + ", ".join(f"channel {i + 1}={peak:.2%} peak / {rms:.2%} RMS"
                                  for i, (peak, rms) in enumerate(output_levels)),
                      flush=True)
                if max(peak for peak, _ in output_levels) < 0.005:
                    print("WARNING: response output is very quiet. "
                          "Try --gain 0.3 after confirming the output route.",
                          flush=True)
                duplex.play(pcm)
                print("Sending response through the selected output device. "
                      "No WAV exports.", flush=True)
                while duplex.playing:
                    time.sleep(0.02)
                session.action(cid, "stop-audition")
                session.action(cid, "discard")
                print(f"Playback queued {len(pcm) // FRAME_BYTES} stereo frames; "
                      f"audio callback copied {duplex.played // FRAME_BYTES} frames.")
                print(f"Cycle complete. Device warning callbacks: {duplex.audio_flags}")
                print("Playback copied to the driver, not yet independently "
                      "confirmed audible. If silent, run --test-output.")
    except KeyboardInterrupt:
        print("\nStopped: local output silenced by closing the audio stream.")
    except EOFError:
        raise SystemExit("Live audio probe needs an interactive Terminal to press Return.")
    except (OSError, ValueError, RuntimeError) as exc:
        raise SystemExit(
            f"Live audio probe stopped: {exc}. If separate input/output devices "
            "fail to open together, report the error; some Core Audio combinations "
            "cannot share one duplex stream."
        ) from exc


if __name__ == "__main__":
    main()
