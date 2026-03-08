// Requirement: Test login

import { test, expect } from '@playwright/test';

test.describe('Login Tests', () => {
    test('should show error when username is empty', async ({ page }) => {
        await page.goto('https://the-internet.herokuapp.com/login');
        await page.locator('#username').fill('');
        await page.locator('#password').fill('SuperSecretPassword!');
        await page.locator("button[type='submit']").click();
        await expect(page.locator('#flash-messages')).toContainText('Your username is invalid!');
    });

    test('should show error when password is empty', async ({ page }) => {
        await page.goto('https://the-internet.herokuapp.com/login');
        await page.locator('#username').fill('tomsmith');
        await page.locator('#password').fill('');
        await page.locator("button[type='submit']").click();
        await expect(page.locator('#flash-messages')).toContainText('Your password is invalid!');
    });

    test('should show success message when credentials are valid', async ({ page }) => {
        await page.goto('https://the-internet.herokuapp.com/login');
        await page.locator('#username').fill('tomsmith');
        await page.locator('#password').fill('SuperSecretPassword!');
        await page.locator("button[type='submit']").click();
        await expect(page.locator('#flash-messages')).toContainText('You logged into a secure area!');
    });

    test('should show error when credentials are invalid', async ({ page }) => {
        await page.goto('https://the-internet.herokuapp.com/login');
        await page.locator('#username').fill('invalidUser');
        await page.locator('#password').fill('invalidPassword');
        await page.locator("button[type='submit']").click();
        await expect(page.locator('#flash-messages')).toContainText('Your username is invalid!');
    });
});