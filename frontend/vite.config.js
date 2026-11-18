import { cpSync } from 'node:fs';
import path from 'node:path';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// The backend stores cover URLs as "/static/covers/..." and generate_covers.py
// writes SVGs into frontend/static, so the folder is kept in place and copied
// into the build output instead of becoming Vite's publicDir.
function copyStaticAssets() {
  return {
    name: 'copy-static-assets',
    apply: 'build',
    closeBundle() {
      cpSync(path.resolve('static'), path.resolve('dist/static'), { recursive: true });
    },
  };
}

export default defineConfig({
  plugins: [react(), copyStaticAssets()],
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
    },
  },
});
