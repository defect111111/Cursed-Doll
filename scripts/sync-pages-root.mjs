import { cpSync, existsSync, rmSync } from "node:fs";
import { join } from "node:path";

const root = process.cwd();
const dist = join(root, "dist");

if (!existsSync(join(dist, "index.html"))) {
  throw new Error("Run vite build before syncing GitHub Pages root files.");
}

rmSync(join(root, "assets"), { recursive: true, force: true });
cpSync(join(dist, "assets"), join(root, "assets"), { recursive: true });
cpSync(join(dist, "index.html"), join(root, "index.html"));

console.log("Synced dist output to repository root for branch-root GitHub Pages.");
