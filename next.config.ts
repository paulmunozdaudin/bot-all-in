import type { NextConfig } from "next";
import path from "node:path";

const nextConfig: NextConfig = {
  // This subproject lives inside the SpeakUp-Web repo but is a separate,
  // unrelated app (docs/ARCHITECTURE.md). Pin the workspace root here so
  // Turbopack never resolves imports against the parent repo's src/ tree.
  turbopack: {
    root: path.join(__dirname),
  },
};

export default nextConfig;
