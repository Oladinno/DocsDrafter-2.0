import type { NextConfig } from "next";

/** The FastAPI service. In local development this is the uvicorn server; on
 * Railway set API_PROXY_TARGET (e.g. http://api:8000 or the service's
 * internal/public domain). Proxying keeps session + CSRF cookies same-origin
 * so no CORS or third-party cookie rules apply in the browser. */
const API_TARGET =
  process.env.API_PROXY_TARGET?.replace(/\/$/, "") ?? "http://localhost:8000";

const nextConfig: NextConfig = {
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
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${API_TARGET}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
