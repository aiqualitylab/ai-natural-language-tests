// Requirement: Test login

import { test, expect } from '@playwright/test';

const testData = {
  url: "https://the-internet.herokuapp.com/login",
  selectors: {
    username: "input[name='username']",
    password: "input[name='password']",
    submit: "button[type='submit']",
    error_container: "#flash",
    success_container: "#flash"
  },
  test_cases: [
    {
      name: "valid_test",
      description: "Test with valid data",
      username: "tomsmith",
      password: "SuperSecretPassword!",
      expected: "success"
    },
    {
      name: "invalid_test",
      description: "Test with invalid data",
      username: "invalidUser",
      password: "wrongPassword",
      expected: "error"
    }
  ]
};

for (const testCase of testData.test_cases) {
  test(testCase.description, async ({ page }) => {
    await page.goto(testData.url);
    
    if (testCase.username) {
      await page.locator(testData.selectors.username).fill(testCase.username);
    }
    
    if (testCase.password) {
      await page.locator(testData.selectors.password).fill(testCase.password);
    }
    
    await page.locator(testData.selectors.submit).click();
    
    const successLocator = testData.selectors.success_container;
    const errorLocator = testData.selectors.error_container;

    if (testCase.expected === "success") {
      await expect(page).toHaveURL(/^(?!.*\/login\b).*/);
      await expect(page.locator(successLocator)).toContainText(/\S+/);
    } else {
      await expect(page.locator(errorLocator)).toContainText(/\S+/);
      await expect(page).toHaveURL(testData.url);
    }
  });
}