/**
 * The part of `@heygen/liveavatar-web-sdk` (0.0.20) that B08 uses, so the web app type-checks before
 * the package is installed (package.json is B01's; B08 does not add dependencies). Delete this file
 * once the package is a dependency, and TypeScript reads the package's own types.
 *
 * Docs: https://docs.liveavatar.com/docs/full-mode/overview.md and the package's lib/index.d.ts.
 */
declare module "@heygen/liveavatar-web-sdk" {
  export interface SessionConfig {
    apiUrl?: string;
    autoKeepAlive?: boolean;
    voiceChat?: { defaultMuted?: boolean; deviceId?: string };
  }

  export class LiveAvatarSession {
    constructor(sessionAccessToken: string, config?: SessionConfig);
    start(): Promise<void>;
    stop(): Promise<void>;
    attach(element: HTMLMediaElement): void;
    /** Speaks exactly this text (command `avatar.speak_text`). */
    repeat(message: string): string;
    on(event: string, listener: (...args: unknown[]) => void): unknown;
    off(event: string, listener: (...args: unknown[]) => void): unknown;
  }
}
