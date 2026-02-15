import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  // Only use 'standalone' for Docker deployment, otherwise don't set output
  // This allows rewrites to work in development mode
  ...(process.env.NEXT_OUTPUT_MODE === 'standalone' ? { output: 'standalone' } : {}),
  // Handle ESM packages that streamdown depends on
  transpilePackages: ['streamdown', 'shiki'],
  // Allow API calls to backend
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/:path*`,
      },
    ];
  },
};

export default nextConfig;
