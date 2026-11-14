import type { NextConfig } from "next";

import { parseFeatures } from "./lib/features";

// V73: read at build time, like the client bundle reads it. The microphone is opened up on the interview page
// only when voice_input is in this build.
const voiceInput = parseFeatures(process.env.NEXT_PUBLIC_DXP_FEATURES).voice_input;

const nextConfig: NextConfig = {
  /* config options here */
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
  // V70: the avatar listens to nothing. The LiveAvatar SDK (0.0.20) always asks for the
  // microphone, even muted, so the browser is told no DxP page may use the mic or camera.
  // V73: the one exception is the interview page, and only in a build with voice_input on: it records a short
  // clip for transcription (the page's own recorder; the avatar still never listens). The camera stays blocked
  // everywhere. When two rules set the same header the later one wins (Next "Header Overriding Behavior"),
  // so the interview rule comes last.
  async headers() {
    const rules = [
      {
        source: "/:path*",
        headers: [{ key: "Permissions-Policy", value: "microphone=(), camera=()" }],
      },
    ];
    if (voiceInput) {
      rules.push({
        source: "/reports/:report_id/interview",
        headers: [{ key: "Permissions-Policy", value: "microphone=(self), camera=()" }],
      });
    }
    return rules;
  },
};

export default nextConfig;
