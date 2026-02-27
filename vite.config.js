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
        site: resolve(__dirname, 'resources/assets/js/site.js'),
        admin: resolve(__dirname, 'resources/assets/js/admin.js'),
        logo: resolve(__dirname, 'resources/assets/images/logo.jpeg'),
      },
      output: {
        entryFileNames: 'js/[name].min.js',
        chunkFileNames: 'js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          if (assetInfo.name.endsWith('.css')) {
            return 'css/[name].min[extname]'
          }
          if (assetInfo.name.match(/\.(jpg|jpeg|png|gif|svg)$/)) {
            return 'images/[name][extname]'
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
