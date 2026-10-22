"""Experimental live Focusrite audio probe for SUZY//AI (no Swift, files or Logic export).

Captures short phrases and plays AI responses through one PortAudio duplex stream.
This is not stage-safe, beat-synchronized, an Audio Unit, or continuous AI synthesis.
"""
from __future__ import annotations

import argparse
from array import array
import io
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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list-devices", action="store_true")
    parser.add_argument("--device", help="PortAudio input/output device index or name substring")
    parser.add_argument("--bpm", type=float, default=120)
    parser.add_argument("--beats", type=int, default=4)
    parser.add_argument("--cycles", type=int, default=1,
                        help="capture/AI/audition cycles (0 = repeat until Ctrl-C)")
    parser.add_argument("--mode", choices=("mirror", "augment", "evolve"), default="mirror")
    parser.add_argument("--provider", choices=("deterministic", "model"),
                        default="deterministic")
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
    if not 40 <= args.bpm <= 240 or not 1 <= args.beats <= 16 or args.cycles < 0:
        parser.error("use 40–240 BPM, 1–16 beats and nonnegative cycles")
    if not 0 < args.gain <= 0.5:
        parser.error("gain must be greater than zero and at most 0.5")
    frames = round(RATE * args.beats * 60 / args.bpm)
    if not RATE // 4 <= frames <= RATE * 8:
        parser.error("phrase duration must be between 0.25 and eight seconds")
    device = int(args.device) if args.device and args.device.isdigit() else args.device
    duplex = DuplexBuffer(frames)
    session = LiveSession()
    print("EXPERIMENTAL | 48 kHz stereo | Focusrite should be macOS input AND output.")
    print("Headphones, low level, no feedback loops. Logic runs separately.")
    print(f"Capture {frames / RATE:.2f}s, {args.provider}/{args.mode}; Ctrl-C stops playback.")
    try:
        with sd.RawStream(device=device, samplerate=RATE, blocksize=BLOCKSIZE,
                          channels=(CHANNELS, CHANNELS), dtype="int16",
                          callback=duplex.callback):
            cycle = 0
            while args.cycles == 0 or cycle < args.cycles:
                cycle += 1
                print(f"\nCycle {cycle}: recording now...", flush=True)
                duplex.arm()
                while duplex.recording:
                    time.sleep(0.02)
                print("Captured. AI working while Logic continues...", flush=True)
                start = time.monotonic()
                cid, wav_bytes, metadata = process(
                    session, duplex.captured(), bpm=args.bpm, mode=args.mode,
                    provider=args.provider, instruction=args.instruction)
                print(f"Response ready in {time.monotonic()-start:.2f}s "
                      f"(provider={metadata['provider']}, model={metadata['model']})")
                pcm = response_pcm(wav_bytes, args.gain)
                duplex.play(pcm)
                print("Playing response once. No WAV exports.", flush=True)
                while duplex.playing:
                    time.sleep(0.02)
                session.action(cid, "stop-audition")
                session.action(cid, "discard")
                print(f"Cycle complete. Device warning callbacks: {duplex.audio_flags}")
    except KeyboardInterrupt:
        print("\nStopped: local output silenced by closing the audio stream.")
    except (OSError, ValueError, RuntimeError) as exc:
        raise SystemExit(f"Live audio probe stopped: {exc}") from exc


if __name__ == "__main__":
    main()
