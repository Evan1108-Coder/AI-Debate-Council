const fs = require("fs");
const path = require("path");

const projectRoot = path.resolve(__dirname, "..", "..");
const standaloneDir = path.join(
  projectRoot,
  "frontend",
  ".next",
  "standalone"
);
const stagingDir = path.join(projectRoot, "electron", ".frontend-bundle");

if (fs.existsSync(stagingDir)) {
  fs.rmSync(stagingDir, { recursive: true });
}

fs.cpSync(standaloneDir, stagingDir, { recursive: true });

const staticSrc = path.join(projectRoot, "frontend", ".next", "static");
const staticDest = path.join(stagingDir, ".next", "static");
fs.cpSync(staticSrc, staticDest, { recursive: true });

console.log(`Frontend bundle staged at ${stagingDir}`);
const nmDir = path.join(stagingDir, "node_modules");
console.log(`node_modules exists: ${fs.existsSync(nmDir)}`);
