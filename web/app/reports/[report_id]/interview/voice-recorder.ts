/**
 * The page's own push-to-record recorder (V73). It records a short clip and hands back one audio Blob, nothing
 * else: no upload, no storage. The Blob goes to the transcribe route and is dropped.
 *
 * Format: `audio/webm;codecs=opus` through MediaRecorder where the browser supports it. Safari does not (older
 * versions), so there the microphone is read through the Web Audio API and encoded as 16 kHz mono 16-bit PCM
 * `audio/wav`. Both stay well under the proxy's 2 MB cap for 30 seconds.
 *
 * The microphone is opened only through `withRecorderLease` (mic-lease.ts), so an avatar session's guard lets
 * this recorder through and nothing else. Every track is stopped when a recording ends or is cancelled.
 */

import { withRecorderLease } from "./mic-lease";

/** The longest recording, in seconds. The page stops the clip here. */
export const MAX_RECORDING_SECONDS = 30;

const WEBM_OPUS = "audio/webm;codecs=opus";
const WAV_RATE = 16_000;

export type RecorderFailure = "unsupported" | "denied" | "failed";

export class RecorderError extends Error {
  readonly reason: RecorderFailure;
  constructor(reason: RecorderFailure) {
    super(`Could not record (${reason}).`);
    this.name = "RecorderError";
    this.reason = reason;
  }
}

export type Recording = {
  /** The audio type the Blob will have: "audio/webm" or "audio/wav". */
  readonly type: "audio/webm" | "audio/wav";
  /** Stop recording, release the microphone and resolve with the clip. */
  stop(): Promise<Blob>;
  /** Stop recording, release the microphone and throw the clip away. */
  cancel(): void;
};

/** True when this browser can open a microphone at all. */
export function canRecord(): boolean {
  return typeof navigator !== "undefined" && typeof navigator.mediaDevices?.getUserMedia === "function";
}

function webAudioContext(): typeof AudioContext | undefined {
  const w = window as unknown as { AudioContext?: typeof AudioContext; webkitAudioContext?: typeof AudioContext };
  return w.AudioContext ?? w.webkitAudioContext;
}

function supportsMediaRecorder(): boolean {
  return typeof MediaRecorder !== "undefined" && MediaRecorder.isTypeSupported(WEBM_OPUS);
}

/** Ask for the microphone and start recording. Rejects with a RecorderError. */
export async function startRecording(): Promise<Recording> {
  if (!canRecord()) throw new RecorderError("unsupported");
  const mediaRecorder = supportsMediaRecorder();
  if (!mediaRecorder && !webAudioContext()) throw new RecorderError("unsupported");

  let stream: MediaStream;
  try {
    // The lease is taken and used in this one synchronous call; see mic-lease.ts.
    stream = await withRecorderLease(() => navigator.mediaDevices.getUserMedia({ audio: true }));
  } catch (error) {
    const name = error instanceof DOMException ? error.name : "";
    throw new RecorderError(name === "NotAllowedError" || name === "SecurityError" ? "denied" : "failed");
  }
  const release = () => stream.getTracks().forEach((track) => track.stop());
  try {
    return mediaRecorder ? recordWebm(stream, release) : recordWav(stream, release);
  } catch {
    release();
    throw new RecorderError("failed");
  }
}

function recordWebm(stream: MediaStream, release: () => void): Recording {
  const recorder = new MediaRecorder(stream, { mimeType: WEBM_OPUS });
  const chunks: Blob[] = [];
  recorder.ondataavailable = (event) => {
    if (event.data.size > 0) chunks.push(event.data);
  };
  recorder.start();
  let finished: Promise<Blob> | null = null;
  const finish = (keep: boolean): Promise<Blob> => {
    finished ??= new Promise<Blob>((resolve, reject) => {
      recorder.onstop = () => {
        release();
        if (keep) resolve(new Blob(chunks, { type: "audio/webm" }));
        else reject(new RecorderError("failed"));
      };
      recorder.onerror = () => {
        release();
        reject(new RecorderError("failed"));
      };
      if (recorder.state === "inactive") {
        release();
        if (keep) resolve(new Blob(chunks, { type: "audio/webm" }));
        else reject(new RecorderError("failed"));
      } else {
        recorder.stop();
      }
    });
    return finished;
  };
  return {
    type: "audio/webm",
    stop: () => finish(true),
    cancel: () => {
      chunks.length = 0;
      finish(false).catch(() => {});
    },
  };
}

function recordWav(stream: MediaStream, release: () => void): Recording {
  const Context = webAudioContext() as typeof AudioContext;
  const context = new Context();
  const source = context.createMediaStreamSource(stream);
  // ScriptProcessorNode is deprecated but is the one capture path every Safari has; it only ever sees this stream.
  const processor = context.createScriptProcessor(4096, 1, 1);
  const chunks: Float32Array[] = [];
  const rate = context.sampleRate;
  processor.onaudioprocess = (event) => {
    chunks.push(new Float32Array(event.inputBuffer.getChannelData(0)));
  };
  // Connected to the destination so the node runs; its own output is silent (the output buffer is never written).
  source.connect(processor);
  processor.connect(context.destination);

  let done = false;
  const teardown = () => {
    if (done) return;
    done = true;
    processor.onaudioprocess = null;
    try {
      source.disconnect();
      processor.disconnect();
    } catch {
      /* already disconnected */
    }
    release();
    void context.close().catch(() => {});
  };
  return {
    type: "audio/wav",
    stop: async () => {
      teardown();
      return encodeWav(chunks, rate);
    },
    cancel: () => {
      chunks.length = 0;
      teardown();
    },
  };
}

/** Join the captured chunks, average down to 16 kHz mono and write a 16-bit PCM WAV file. */
export function encodeWav(chunks: Float32Array[], inputRate: number): Blob {
  let total = 0;
  for (const chunk of chunks) total += chunk.length;
  const ratio = Math.max(1, inputRate / WAV_RATE);
  const outLength = Math.floor(total / ratio);
  const pcm = new Int16Array(outLength);
  const samples = new Float32Array(total);
  let at = 0;
  for (const chunk of chunks) {
    samples.set(chunk, at);
    at += chunk.length;
  }
  for (let i = 0; i < outLength; i++) {
    const from = Math.floor(i * ratio);
    const to = Math.min(total, Math.max(from + 1, Math.floor((i + 1) * ratio)));
    let sum = 0;
    for (let j = from; j < to; j++) sum += samples[j];
    const value = Math.max(-1, Math.min(1, sum / (to - from)));
    pcm[i] = value < 0 ? value * 0x8000 : value * 0x7fff;
  }
  const rate = inputRate < WAV_RATE ? inputRate : WAV_RATE;
  const header = new ArrayBuffer(44);
  const view = new DataView(header);
  const text = (offset: number, value: string) => {
    for (let i = 0; i < value.length; i++) view.setUint8(offset + i, value.charCodeAt(i));
  };
  text(0, "RIFF");
  view.setUint32(4, 36 + pcm.byteLength, true);
  text(8, "WAVE");
  text(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true); // PCM
  view.setUint16(22, 1, true); // mono
  view.setUint32(24, rate, true);
  view.setUint32(28, rate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  text(36, "data");
  view.setUint32(40, pcm.byteLength, true);
  return new Blob([header, pcm.buffer], { type: "audio/wav" });
}
