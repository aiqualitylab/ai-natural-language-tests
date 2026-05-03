// Requirement: Test login

import { test, expect, Page } from '@playwright/test';

const testData = {
  url: "https://the-internet.herokuapp.com/login",
  base_url: "https://the-internet.herokuapp.com",
  url_pattern: "/login",
  selectors: {
    username: {
      cypress: "cy.findByLabelText(/username/i)",
      playwright: "page.getByLabel('Username')",
      fallback_css: "input[name='username']"
    },
    password: {
      cypress: "cy.findByLabelText(/password/i)",
      playwright: "page.getByLabel('Password')",
      fallback_css: "input[name='password']"
    },
    submit: {
      cypress: "cy.findByRole('button', {name: /login/i})",
      playwright: "page.getByRole('button', {name: 'Login'})",
      fallback_css: "button[type='submit']"
    },
    error_container: {
      cypress: "cy.findByRole('alert')",
      playwright: "page.getByRole('alert')",
      fallback_css: "#flash-messages"
    },
    success_container: {
      cypress: "cy.findByText(/success/i)",
      playwright: "page.getByText(/success/i)",
      fallback_css: "#flash-messages"
    }
  },
  test_cases: [
    {
      name: "valid_test",
      description: "Test with valid username and password",
      username: "tomsmith",
      password: "SuperSecretPassword!",
      expected: "success"
    },
    {
      name: "invalid_test",
      description: "Test with invalid username and password",
      username: "invalidUser",
      password: "wrongPassword",
      expected: "error"
    }
  ]
};

function resolveLocator(page: Page, sel: any): any {
  if (!sel) return page.locator('body');
  if (typeof sel === 'string') return page.locator(sel);
  const css = sel.fallback_css || sel;
  return page.locator(typeof css === 'string' ? css : 'body');
}

for (const testCase of testData.test_cases) {
  test(testCase.name, async ({ page }) => {
    await page.goto(testData.url);
    
    if (testCase.username) {
      await resolveLocator(page, testData.selectors.username).fill(testCase.username);
    }
    
    if (testCase.password) {
      await resolveLocator(page, testData.selectors.password).fill(testCase.password);
    }
    
    await resolveLocator(page, testData.selectors.submit).click();
    
    const successLocator = resolveLocator(page, testData.selectors.success_container);
    const errorLocator = resolveLocator(page, testData.selectors.error_container);
    
    if (testCase.expected === "success") {
      await expect(successLocator).toBeVisible();
      await expect(successLocator).toContainText(/\S+/);
      await expect(page).toHaveURL(/^(?!.*\/login\b).*/);
    } else {
      await expect(errorLocator).toBeVisible();
      await expect(errorLocator).toContainText(/\S+/);
      await expect(page).toHaveURL(testData.url);
    }
  });
}