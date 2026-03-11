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
            field_name: { username: "tomsmith", password: "SuperSecretPassword!" },
            expected: "success"
        },
        {
            name: "invalid_test",
            description: "Test with invalid data",
            field_name: { username: "invalidUser", password: "wrongPassword" },
            expected: "error"
        }
    ]
};

test.describe('Login Tests', () => {
    testData.test_cases.forEach(({ name, description, field_name, expected }) => {
        test(name, async ({ page }) => {
            await page.goto(testData.url);
            if (field_name.username) {
                await page.locator(testData.selectors.username).fill(field_name.username);
            }
            if (field_name.password) {
                await page.locator(testData.selectors.password).fill(field_name.password);
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