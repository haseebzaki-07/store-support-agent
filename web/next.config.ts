import type { NextConfig } from "next";

/**
 * When BACKEND_URL is set, /api/chat/* is proxied to the Python backend
 * (see ../backend). When it is unset, the legacy TypeScript route handlers
 * in app/api/chat keep working, so the UI is never left without a backend
 * during the migration.
 *
 * TODO(migration): once the Python port is complete, delete the legacy
 * TypeScript backend (app/api/chat, lib/llm.ts, lib/tools, lib/services,
 * lib/redis.ts, prisma/) and make BACKEND_URL required.
 */
const backendUrl = process.env.BACKEND_URL?.replace(/\/$/, "");

const nextConfig: NextConfig = {
  async rewrites() {
    return {
      // beforeFiles so the proxy wins over the legacy route handlers.
      beforeFiles: backendUrl
        ? [
            {
              source: "/api/chat/:path*",
              destination: `${backendUrl}/api/chat/:path*`,
            },
          ]
        : [],
      afterFiles: [],
      fallback: [],
    };
  },
};

export default nextConfig;
