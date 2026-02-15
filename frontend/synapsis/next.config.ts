import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  turbopack: {
    resolveAlias: {
      tailwindcss: path.resolve(process.cwd(), "node_modules/tailwindcss"),
      "tw-animate-css": path.resolve(
        process.cwd(),
        "node_modules/tw-animate-css"
      ),
    },
  },
};

export default nextConfig;
