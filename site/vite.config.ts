import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// GitHub Pages serves this project from https://<user>.github.io/epl-2026-27-predictor/,
// so every asset URL needs that path prefix. Adjust if the repo is ever renamed.
const REPO_NAME = 'epl-2026-27-predictor'

export default defineConfig({
  base: `/${REPO_NAME}/`,
  plugins: [react(), tailwindcss()],
})
