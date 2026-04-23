import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  webpack(config, { isServer }) {
    if (isServer && config.output) {
      config.output.chunkFilename = "chunks/[name].js";
    }
    return config;
  }
};

export default nextConfig;
