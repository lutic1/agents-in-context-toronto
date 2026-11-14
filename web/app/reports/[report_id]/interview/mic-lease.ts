/**
 * The one way the interview page's own recorder may open the microphone while an avatar session is running (V73).
 *
 * The avatar never listens (V70): while its session lives, `blockMicrophone` (avatar-adapter.ts) makes every audio
 * `getUserMedia` call fail. The page's own "Speak" recorder is the single exception. It takes a lease
 * here, and the guard honours it for exactly one synchronous call. A lease is set and read in the same
 * synchronous run, so no other caller (the avatar SDK included) can be handed it: JavaScript cannot interleave
 * another call between the two.
 */

let leased = false;

/** Run `open`, which must call `getUserMedia` synchronously, with the lease held. The lease never outlives the call. */
export function withRecorderLease<T>(open: () => T): T {
  leased = true;
  try {
    return open();
  } finally {
    leased = false;
  }
}

/** Called by the guard for each audio request. True at most once per lease; reading it uses it up. */
export function takeRecorderLease(): boolean {
  const had = leased;
  leased = false;
  return had;
}
