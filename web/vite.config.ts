import { defineConfig } from "vite";

// GitHub Pages serves this as a project page (username.github.io/geo-lab/),
// not a custom domain or user/org root, so the production build needs a
// "/geo-lab/" base for asset URLs to resolve. Dev server stays at "/".
export default defineConfig(({ command }) => ({
  root: ".",
  base: command === "build" ? "/geo-lab/" : "/",
  build: {
    outDir: "dist",
  },
}));
