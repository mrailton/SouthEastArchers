import { defineConfig } from 'vite'
import { resolve } from 'path'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  root: 'resources/assets',
  base: '/static/',
  plugins: [
    tailwindcss(),
  ],
  build: {
    outDir: '../static',
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'resources/assets/js/main.js'),
        style: resolve(__dirname, 'resources/assets/css/style.css'),
      },
      output: {
        entryFileNames: 'js/[name].min.js',
        chunkFileNames: 'js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          if (assetInfo.name.endsWith('.css')) {
            return 'css/[name].min[extname]'
          }
          return 'assets/[name]-[hash][extname]'
        },
      },
    },
  },
  server: {
    port: 5173,
    strictPort: false,
    origin: 'http://localhost:5173',
  },
  css: {
    transformer: 'lightningcss',
  },
})
