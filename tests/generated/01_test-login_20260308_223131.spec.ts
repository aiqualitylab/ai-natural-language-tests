// Requirement: Test login

import { test, expect } from '@playwright/test';

const testData = {
    url: "https://the-internet.herokuapp.com/login",
    selectors: {
        username: "#username",
        password: "#password",
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
            expected: "success|redirect|url_change"
        },
        {
            name: "invalid_test",
            description: "Test with invalid data",
            username: "invalid_user",
            password: "wrong_password",
            expected: "error|validation_message"
        },
        {
            name: "empty_test",
            description: "Test with empty required fields",
            username: "",
            password: "",
            expected: "validation_error"
        }
    ]
};

test.describe('Login Tests', () => {
    for (const testCase of testData.test_cases) {
        test(testCase.name, async ({ page }) => {
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

            if (testCase.expected.includes("success")) {
                await expect(page).toHaveURL(/^(?!.*login).*/);
                await expect(page.locator(successLocator)).toBeVisible();
                await expect(page.locator(successLocator)).toContainText(/\S+/);
            } else if (testCase.expected.includes("error")) {
                await expect(page.locator(errorLocator)).toBeVisible();
                await expect(page.locator(errorLocator)).toContainText(/\S+/);
            } else if (testCase.expected.includes("validation_error")) {
                await expect(page.locator(testData.selectors.error_container)).toBeVisible();
                await expect(page.locator(testData.selectors.error_container)).toContainText(/\S+/);
            }
        });
    }
});