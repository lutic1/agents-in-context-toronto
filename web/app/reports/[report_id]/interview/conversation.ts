/**
 * Conversation mode (V75): hands-free voice questions. The microphone is opened once, through the same one-call lease
 * as the push-to-record recorder (mic-lease.ts), so an avatar session's guard still lets only this page's recorder
 * through. A small voice-activity detector on that one stream cuts it into spoken segments:
 *
 * - First ~500 ms: the ambient noise level is measured. After that a running noise floor follows the room while
 *   nobody speaks (slow to rise, quicker to fall), and the start threshold is clamp(floor x 3, 0.015, 0.08).
 * - Speech starts when the level stays above the start threshold for ~150 ms. About 300 ms of audio before that is
 *   kept, so the first syllable is not lost.
 * - While hearing, the speaker's own level is tracked. A frame is silent when its level is under
 *   max(floor x 2, min(0.35 x speaker level, 0.12), 0.0105): relative to the speaker, not only the room, so a noisy
 *   room (or echo cancellation and gain control lifting the noise after speech) still ends the segment.
 * - The segment ends after 1.5 s of continuous silent frames, or at 29.5 s (the transcription cap is 30 s), or, as a
 *   fallback, once it is over 8 s long and its speech time has not grown for 1.5 s.
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
  /** The start threshold is never below this, so a silent room does not make every breath "speech". */
  minThreshold: 0.015,
  /** The start threshold is never above this, so a noisy room does not make normal speech "silence". */
  maxThreshold: 0.08,
  /** Start threshold = noise floor times this. */
  ambientFactor: 3,
  /** Noise floor EMA per frame while not hearing: slow to rise (speech must not lift it), quicker to fall. */
  floorRise: 0.02,
  floorFall: 0.1,
  /** A frame is silent below max(floor x silenceFloorFactor, speechLevel x silenceSpeechFactor, minThreshold x silenceMinFactor). */
  silenceFloorFactor: 2,
  silenceSpeechFactor: 0.35,
  silenceMinFactor: 0.7,
  /** The speech-relative part of the silence cutoff is capped, so one shout does not turn normal speech into "silence". */
  silenceSpeechCap: 0.12,
  speechStartMs: 150,
  silenceEndMs: 1500,
  minSpeechMs: 400,
  maxSegmentMs: 29_500,
  /** Fallback: a segment heard for longer than this ends once its speech time has not grown for stalledMs. */
  stalledAfterMs: 8000,
  stalledMs: 1500,
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
  onBlocked,
}: {
  onState: (state: ConversationState) => void;
  onSegment: (clip: Blob) => void;
  /** True while the browser keeps the audio context suspended until the user clicks or types somewhere. */
  onBlocked?: (blocked: boolean) => void;
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
  // Running noise floor (EMA of quiet-time RMS) and the start threshold derived from it.
  let floor = 0;
  let threshold: number = VAD.minThreshold;
  // Recent frames before speech starts (pre-roll), and the frames of the segment being heard.
  let recent: Float32Array[] = [];
  let segment: Float32Array[] = [];
  let hearing = false;
  let aboveMs = 0;
  let speechMs = 0;
  let silenceMs = 0;
  let segmentMs = 0;
  // The speaker's own level in this segment (EMA leaning to peaks), and how long since speechMs last grew.
  let speechLevel = 0;
  let sinceSpeechMs = 0;
  let state: ConversationState | null = null;
  // Diagnostics: per-second min and max RMS, logged with the floor and thresholds.
  let logMs = 0;
  let logMin = Infinity;
  let logMax = 0;

  const setState = (next: ConversationState) => {
    if (next === state) return;
    state = next;
    onState(next);
  };

  const startThreshold = () => Math.min(VAD.maxThreshold, Math.max(VAD.minThreshold, floor * VAD.ambientFactor));
  const silenceCutoff = () =>
    Math.max(
      floor * VAD.silenceFloorFactor,
      Math.min(VAD.silenceSpeechCap, speechLevel * VAD.silenceSpeechFactor),
      VAD.minThreshold * VAD.silenceMinFactor,
    );

  const reset = () => {
    recent = [];
    segment = [];
    hearing = false;
    aboveMs = 0;
    speechMs = 0;
    silenceMs = 0;
    segmentMs = 0;
    speechLevel = 0;
    sinceSpeechMs = 0;
  };

  const endSegment = (why: string) => {
    const frames = segment;
    const spoken = speechMs;
    console.debug("[conversation] segment end", { why, segmentMs: Math.round(segmentMs), speechMs: Math.round(spoken), speechLevel: +speechLevel.toFixed(4) });
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

    logMs += frameMs;
    logMin = Math.min(logMin, level);
    logMax = Math.max(logMax, level);
    if (logMs >= 1000) {
      console.debug("[conversation] level", {
        state,
        floor: +floor.toFixed(4),
        threshold: +threshold.toFixed(4),
        silenceCutoff: hearing ? +silenceCutoff().toFixed(4) : null,
        min: +logMin.toFixed(4),
        max: +logMax.toFixed(4),
        silenceMs: hearing ? Math.round(silenceMs) : null,
      });
      logMs = 0;
      logMin = Infinity;
      logMax = 0;
    }

    if (calibratedMs < VAD.calibrationMs) {
      calibratedMs += frameMs;
      ambientSum += level;
      ambientFrames += 1;
      if (calibratedMs >= VAD.calibrationMs) {
        floor = ambientSum / Math.max(1, ambientFrames);
        threshold = startThreshold();
        console.debug("[conversation] calibrated", { floor: +floor.toFixed(4), threshold: +threshold.toFixed(4), frameMs: +frameMs.toFixed(1) });
        setState("listening");
      }
      return;
    }

    if (!hearing) {
      const loud = level >= threshold;
      // The floor follows the room only while nobody is speaking; a loud frame barely lifts it.
      if (!loud) floor += (level - floor) * (level > floor ? VAD.floorRise : VAD.floorFall);
      else floor += (Math.min(level, threshold) - floor) * VAD.floorRise * 0.25;
      threshold = startThreshold();
      recent.push(frame);
      if (recent.length > preRollFrames + Math.ceil(VAD.speechStartMs / frameMs) + 1) recent.shift();
      if (loud) {
        aboveMs += frameMs;
        speechLevel = Math.max(speechLevel, level);
      } else {
        aboveMs = 0;
        speechLevel = 0;
      }
      if (aboveMs >= VAD.speechStartMs) {
        hearing = true;
        segment = recent;
        recent = [];
        speechMs = aboveMs;
        segmentMs = segment.length * frameMs;
        silenceMs = 0;
        sinceSpeechMs = 0;
        console.debug("[conversation] speech start", { floor: +floor.toFixed(4), threshold: +threshold.toFixed(4), speechLevel: +speechLevel.toFixed(4) });
        setState("hearing");
      }
      return;
    }

    segment.push(frame);
    segmentMs += frameMs;
    // Silence is judged against the room AND the speaker's own level, so a noisy room after speech still ends it.
    const silent = level < silenceCutoff();
    if (silent) {
      silenceMs += frameMs;
    } else {
      silenceMs = 0;
      // Track the speaker's level, leaning to peaks: rises fast, falls slowly.
      speechLevel += (level - speechLevel) * (level > speechLevel ? 0.3 : 0.03);
    }
    if (!silent && level >= threshold) {
      speechMs += frameMs;
      sinceSpeechMs = 0;
    } else {
      sinceSpeechMs += frameMs;
    }
    if (silenceMs >= VAD.silenceEndMs) endSegment("silence");
    else if (segmentMs >= VAD.maxSegmentMs) endSegment("max_length");
    else if (segmentMs > VAD.stalledAfterMs && sinceSpeechMs >= VAD.stalledMs) endSegment("stalled");
  };
  // Connected to the destination so the node runs; its own output is silent (the output buffer is never written).
  source.connect(processor);
  processor.connect(context.destination);

  // A suspended context never calls onaudioprocess. Resume it now, on every state change, and, if the browser wants a
  // user gesture first, on the next pointerdown or keydown anywhere on the page.
  const onGesture = () => {
    if (stopped) return;
    void context.resume().catch(() => {});
  };
  const watchGesture = (on: boolean) => {
    onBlocked?.(on);
    if (on) {
      document.addEventListener("pointerdown", onGesture, true);
      document.addEventListener("keydown", onGesture, true);
    } else {
      document.removeEventListener("pointerdown", onGesture, true);
      document.removeEventListener("keydown", onGesture, true);
    }
  };
  const checkState = () => {
    if (stopped) return;
    console.debug("[conversation] audio context", context.state);
    if (context.state === "running") {
      watchGesture(false);
    } else if (context.state === "suspended") {
      watchGesture(true);
      void context.resume().catch(() => {});
    }
  };
  context.onstatechange = checkState;
  if (context.state === "suspended") {
    void context.resume().catch(() => {});
    // Give the resume a moment; if it is still suspended the browser is waiting for a gesture.
    window.setTimeout(checkState, 300);
  }
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
      context.onstatechange = null;
      onBlocked?.(false);
      document.removeEventListener("pointerdown", onGesture, true);
      document.removeEventListener("keydown", onGesture, true);
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
