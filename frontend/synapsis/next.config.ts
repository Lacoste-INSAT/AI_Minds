import type { NextConfig } from "next";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  // Proxy API calls to the FastAPI backend during development.
  // This avoids CORS issues and mirrors a production reverse-proxy setup.
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${BACKEND_URL}/:path*`,
      },
    ];
  },

  // Suppress hydration warnings from browser extensions injecting attributes.
  reactStrictMode: true,
};

export default nextConfig;
