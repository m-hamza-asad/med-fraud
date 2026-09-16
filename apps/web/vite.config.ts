import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const runtime = globalThis as typeof globalThis & {
  process?: { env?: Record<string, string | undefined> }
}
const apiPort = runtime.process?.env?.MEDFRAUD_API_PORT ?? '8000'

export default defineConfig({
  plugins: [react()],
  server: { host: '127.0.0.1', port: 5173, proxy: { '/api': `http://127.0.0.1:${apiPort}` } },
  preview: { host: '127.0.0.1', port: 4173 },
})
