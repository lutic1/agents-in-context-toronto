import type { NextConfig } from "next";

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
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [{ key: "Permissions-Policy", value: "microphone=(), camera=()" }],
      },
    ];
  },
};

export default nextConfig;
