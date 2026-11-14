/**
 * Conversation mode (V75): hands-free voice questions. The microphone is opened once, through the same one-call lease
 * as the push-to-record recorder (mic-lease.ts), so an avatar session's guard still lets only this page's recorder
 * through. A small voice-activity detector on that one stream cuts it into spoken segments:
 *
 * - First ~500 ms: the ambient noise level is measured, and the speech threshold is set above it.
 * - Speech starts when the level stays above the threshold for ~150 ms. About 300 ms of audio before that is kept,
 *   so the first syllable is not lost.
 * - The segment ends after 2.0 s of continuous silence, or at 29.5 s (the transcription cap is 30 s).
 * - A segment with less than ~400 ms of speech is thrown away.
 *
 * Each segment is encoded as 16 kHz mono 16-bit PCM `audio/wav` (encodeWav, voice-recorder.ts), which every browser
 * can produce and which keeps the pre-roll. 30 s is about 960 KB, under the 1 MB cap.
 *
 * While paused (an answer is pending, the avatar is starting or speaking, or a segment is being transcribed) the
 * captured audio is dropped and nothing is detected, so the avatar's own voice is never recorded. Audio is never
 * stored: a segment Blob goes to `onSegment` and nowhere else.
 */

import { withRecorderLease } from "./mic-lease";
import { RecorderError, canRecord, encodeWav } from "./voice-recorder";

/** Tunable thresholds. RMS values are on the -1..1 float sample scale. */
export const VAD = {
  calibrationMs: 500,
  /** The threshold is never below this, so a silent room does not make every breath "speech". */
  minThreshold: 0.015,
  /** The threshold is never above this, so a noisy calibration does not make normal speech "silence". */
  maxThreshold: 0.08,
  /** Threshold = ambient RMS times this. */
  ambientFactor: 3,
  speechStartMs: 150,
  silenceEndMs: 2000,
  minSpeechMs: 400,
  maxSegmentMs: 29_500,
  preRollMs: 300,
} as const;

export type ConversationState = "calibrating" | "listening" | "hearing" | "paused";

export type Conversation = {
  /** Paused: the audio is dropped and nothing is detected. A segment being heard is thrown away. */
  setPaused(paused: boolean): void;
  /** Close the microphone and the audio graph. Safe to call more than once. */
  stop(): void;
};

function webAudioContext(): typeof AudioContext | undefined {
  const w = window as unknown as { AudioContext?: typeof AudioContext; webkitAudioContext?: typeof AudioContext };
  return w.AudioContext ?? w.webkitAudioContext;
}

function rms(samples: Float32Array): number {
  let sum = 0;
  for (let i = 0; i < samples.length; i++) sum += samples[i] * samples[i];
  return Math.sqrt(sum / Math.max(1, samples.length));
}

/**
 * Open the microphone and start listening. `onSegment` is called with each spoken segment; the detector pauses itself
 * before calling it and stays paused until `setPaused(false)`. Rejects with a RecorderError.
 */
export async function startConversation({
  onState,
  onSegment,
}: {
  onState: (state: ConversationState) => void;
  onSegment: (clip: Blob) => void;
}): Promise<Conversation> {
  const Context = typeof window === "undefined" ? undefined : webAudioContext();
  if (!canRecord() || !Context) throw new RecorderError("unsupported");

  let stream: MediaStream;
  try {
    // The lease is taken and used in this one synchronous call; see mic-lease.ts.
    stream = await withRecorderLease(() => navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } }));
  } catch (error) {
    const name = error instanceof DOMException ? error.name : "";
    throw new RecorderError(name === "NotAllowedError" || name === "SecurityError" ? "denied" : "failed");
  }

  let context: AudioContext;
  let source: MediaStreamAudioSourceNode;
  let processor: ScriptProcessorNode;
  try {
    context = new Context();
    source = context.createMediaStreamSource(stream);
    // ScriptProcessorNode is deprecated but is the one capture path every browser (Safari included) has.
    processor = context.createScriptProcessor(2048, 1, 1);
  } catch {
    stream.getTracks().forEach((track) => track.stop());
    throw new RecorderError("failed");
  }
  const rate = context.sampleRate;
  const frameMs = (2048 / rate) * 1000;
  const preRollFrames = Math.max(1, Math.round(VAD.preRollMs / frameMs));

  let stopped = false;
  let paused = false;
  let calibratedMs = 0;
  let ambientSum = 0;
  let ambientFrames = 0;
  let threshold: number = VAD.minThreshold;
  // Recent frames before speech starts (pre-roll), and the frames of the segment being heard.
  let recent: Float32Array[] = [];
  let segment: Float32Array[] = [];
  let hearing = false;
  let aboveMs = 0;
  let speechMs = 0;
  let silenceMs = 0;
  let segmentMs = 0;
  let state: ConversationState | null = null;

  const setState = (next: ConversationState) => {
    if (next === state) return;
    state = next;
    onState(next);
  };

  const reset = () => {
    recent = [];
    segment = [];
    hearing = false;
    aboveMs = 0;
    speechMs = 0;
    silenceMs = 0;
    segmentMs = 0;
  };

  const endSegment = () => {
    const frames = segment;
    const spoken = speechMs;
    reset();
    if (spoken < VAD.minSpeechMs) {
      setState("listening");
      return;
    }
    // Pause before handing the clip over, so nothing is heard until the page says to listen again.
    paused = true;
    setState("paused");
    onSegment(encodeWav(frames, rate));
  };

  processor.onaudioprocess = (event) => {
    if (stopped || paused) return;
    const frame = new Float32Array(event.inputBuffer.getChannelData(0));
    const level = rms(frame);

    if (calibratedMs < VAD.calibrationMs) {
      calibratedMs += frameMs;
      ambientSum += level;
      ambientFrames += 1;
      if (calibratedMs >= VAD.calibrationMs) {
        const ambient = ambientSum / Math.max(1, ambientFrames);
        threshold = Math.min(VAD.maxThreshold, Math.max(VAD.minThreshold, ambient * VAD.ambientFactor));
        setState("listening");
      }
      return;
    }

    const loud = level >= threshold;
    if (!hearing) {
      recent.push(frame);
      if (recent.length > preRollFrames + Math.ceil(VAD.speechStartMs / frameMs) + 1) recent.shift();
      aboveMs = loud ? aboveMs + frameMs : 0;
      if (aboveMs >= VAD.speechStartMs) {
        hearing = true;
        segment = recent;
        recent = [];
        speechMs = aboveMs;
        segmentMs = segment.length * frameMs;
        silenceMs = 0;
        setState("hearing");
      }
      return;
    }

    segment.push(frame);
    segmentMs += frameMs;
    if (loud) {
      speechMs += frameMs;
      silenceMs = 0;
    } else {
      silenceMs += frameMs;
    }
    if (silenceMs >= VAD.silenceEndMs || segmentMs >= VAD.maxSegmentMs) endSegment();
  };
  // Connected to the destination so the node runs; its own output is silent (the output buffer is never written).
  source.connect(processor);
  processor.connect(context.destination);
  if (context.state === "suspended") void context.resume().catch(() => {});
  setState("calibrating");

  return {
    setPaused(next: boolean) {
      if (stopped || next === paused) return;
      paused = next;
      reset();
      if (next) setState("paused");
      else setState(calibratedMs >= VAD.calibrationMs ? "listening" : "calibrating");
    },
    stop() {
      if (stopped) return;
      stopped = true;
      processor.onaudioprocess = null;
      try {
        source.disconnect();
        processor.disconnect();
      } catch {
        /* already disconnected */
      }
      stream.getTracks().forEach((track) => track.stop());
      void context.close().catch(() => {});
      reset();
    },
  };
}
