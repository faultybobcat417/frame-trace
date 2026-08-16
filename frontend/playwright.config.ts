import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  use: {
    baseURL: 'http://127.0.0.1:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure'
  },
  webServer: [
    {
      command: 'cd .. && frame-trace demo && frame-trace serve',
      url: 'http://127.0.0.1:8000/health',
      reuseExistingServer: true
    },
    {
      command: 'npm run dev -- --host 127.0.0.1',
      url: 'http://127.0.0.1:5173',
      reuseExistingServer: true
    }
  ]
})
