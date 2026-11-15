import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  // Portul implicit Vite; backendul îl acceptă deja în HOBBYSHOP_CORS_ORIGINS.
  server: { port: 5173 },
})
