// Requirement: Test login page

import { test, expect } from '@playwright/test';

test.describe('Login Tests', () => {
    const url = 'https://the-internet.herokuapp.com/login';
    const validUsername = 'tomsmith';
    const validPassword = 'SuperSecretPassword!';
    const invalidUsername = 'invalidUser';
    const invalidPassword = 'invalidPassword';

    test('should show error when username is empty', async ({ page }) => {
        await page.goto(url);
        await page.locator('#password').fill(validPassword);
        await page.locator("button[type='submit']").click();
        await expect(page.locator('#flash-messages')).toContainText('Your username is invalid!');
    });

    test('should show error when password is empty', async ({ page }) => {
        await page.goto(url);
        await page.locator('#username').fill(validUsername);
        await page.locator("button[type='submit']").click();
        await expect(page.locator('#flash-messages')).toContainText('Your password is invalid!');
    });

    test('should show error when username and password are incorrect', async ({ page }) => {
        await page.goto(url);
        await page.locator('#username').fill(invalidUsername);
        await page.locator('#password').fill(invalidPassword);
        await page.locator("button[type='submit']").click();
        await expect(page.locator('#flash-messages')).toContainText('Your username is invalid!');
    });

    test('should login successfully with valid credentials', async ({ page }) => {
        await page.goto(url);
        await page.locator('#username').fill(validUsername);
        await page.locator('#password').fill(validPassword);
        await page.locator("button[type='submit']").click();
        await expect(page).toHaveURL(/.*\/secure/);
        await expect(page.locator('#flash-messages')).toContainText('You logged into a secure area!');
    });
});