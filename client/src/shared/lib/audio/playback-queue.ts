import { pcmToAudioBuffer } from "./pcm";

export interface ClipHooks {
  onStart?: () => void;
  onEnd?: () => void;
}

const DEFAULT_RATE = 24000;

/**
 * Gapless queued playback of PCM clips. Imperative on purpose: scheduling
 * runs on AudioContext time and must not depend on React renders.
 */
export class PlaybackQueue {
  private ctx: AudioContext | null = null;
  private gain: GainNode | null = null;
  private cursor = 0; // when the next clip should start (ctx time)

  /** Create the AudioContext. Must be called from a user gesture. */
  enable(): void {
    if (this.ctx) return;
    this.ctx = new AudioContext();
    this.gain = this.ctx.createGain();
    this.gain.connect(this.ctx.destination);
  }

  get enabled(): boolean {
    return this.ctx !== null;
  }

  get running(): boolean {
    return this.ctx?.state === "running";
  }

  setMuted(muted: boolean): void {
    if (this.gain) this.gain.gain.value = muted ? 0 : 1;
  }

  // After a browser sleep / audio interruption the context lands in
  // "suspended" (iOS: "interrupted") and must be resume()d — changing gain
  // alone does nothing.
  async resume(): Promise<void> {
    if (!this.ctx || this.ctx.state === "running") return;
    try {
      await this.ctx.resume();
    } catch {
      // needs a user gesture — the mute button click covers it
    }
    this.cursor = 0; // anything scheduled before the suspend is stale; restart the queue from now
  }

  enqueue(b64: string, rate: number = DEFAULT_RATE, hooks: ClipHooks = {}): void {
    if (!this.ctx || !this.gain || !b64) return; // audio not enabled yet — text still flows
    if (this.ctx.state !== "running") {
      // suspended mid-service: try to recover, but drop this clip — this is a
      // live feed and a replayed backlog would lag behind the preacher
      void this.resume();
      return;
    }
    const buf = pcmToAudioBuffer(this.ctx, b64, rate);
    const src = this.ctx.createBufferSource();
    src.buffer = buf;
    src.connect(this.gain);
    const startAt = Math.max(this.ctx.currentTime + 0.05, this.cursor);
    src.start(startAt);
    this.cursor = startAt + buf.duration;
    if (hooks.onStart) setTimeout(hooks.onStart, (startAt - this.ctx.currentTime) * 1000);
    if (hooks.onEnd) src.onended = hooks.onEnd;
  }
}
