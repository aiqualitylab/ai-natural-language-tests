import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  retries: 0,
  reporter: 'html',
  timeout: 120000,
  expect: {
    timeout: 45000,
  },
  use: {
    baseURL: 'https://the-internet.herokuapp.com',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    navigationTimeout: 45000,
    actionTimeout: 45000,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
