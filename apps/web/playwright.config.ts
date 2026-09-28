import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  fullyParallel: false,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: { baseURL: 'http://127.0.0.1:5180', trace: 'retain-on-failure' },
  webServer: [
    { command: 'powershell -ExecutionPolicy Bypass -File ../../scripts/start-e2e-api.ps1', url: 'http://127.0.0.1:8010/api/v1/health', reuseExistingServer: true, timeout: 60_000 },
    { command: 'npm run dev -- --port 5180', url: 'http://127.0.0.1:5180', reuseExistingServer: true, timeout: 60_000,
      env: { MEDFRAUD_API_PORT: '8010' } },
  ],
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
})
