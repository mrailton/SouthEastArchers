import { defineConfig } from "vite";
import tailwindcss from "@tailwindcss/vite";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [tailwindcss()],
  build: {
    outDir: "app/resources/static/dist",
    emptyOutDir: true,
    rollupOptions: {
      input: {
        site: path.resolve(__dirname, "app/resources/static/js/site.js"),
        admin: path.resolve(__dirname, "app/resources/static/js/admin.js"),
      },
      output: {
        entryFileNames: "assets/[name].js",
        chunkFileNames: "assets/[name].js",
        assetFileNames: "assets/[name][extname]",
      },
    },
  },
});
