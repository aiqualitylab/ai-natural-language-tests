// Requirement: Test login

import { test, expect } from '@playwright/test';

const testData = {
    url: "https://the-internet.herokuapp.com/login",
    selectors: {
        username: "input[name='username']",
        password: "input[name='password']",
        submit: "button[type='submit']",
        error_container: "#flash-messages",
        success_container: "#flash-messages"
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

test.describe('Login Tests', () => {
    testData.test_cases.forEach(({ name, description, username, password, expected }) => {
        test(name, async ({ page }) => {
            await page.goto(testData.url);
            if (username) {
                await page.locator(testData.selectors.username).fill(username);
            }
            if (password) {
                await page.locator(testData.selectors.password).fill(password);
            }
            await page.locator(testData.selectors.submit).click();

            const successLocator = page.locator(testData.selectors.success_container);
            const errorLocator = page.locator(testData.selectors.error_container);

            if (expected === "success") {
                await expect(successLocator).toBeVisible();
                await expect(successLocator).toContainText(/\S+/);
            } else {
                await expect(errorLocator).toBeVisible();
                await expect(errorLocator).toContainText(/\S+/);
            }
        });
    });
});