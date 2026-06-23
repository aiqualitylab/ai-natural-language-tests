// Requirement: Test login

import { remote } from 'webdriverio';

const testData = {
    url: "https://the-internet.herokuapp.com/login",
    selectors: {
        username: {
            primary: "input[name='username']",
            fallback: "[data-testid='username']"
        },
        password: {
            primary: "input[name='password']",
            fallback: "[data-testid='password']"
        },
        submit: {
            primary: "button[type='submit']",
            fallback: "[data-testid='submit-button']"
        },
        error_container: {
            primary: "#flash-messages",
            fallback: "[role='alert']"
        },
        success_container: {
            primary: "#flash-messages",
            fallback: "[role='alert']"
        }
    },
    test_cases: [
        {
            name: "valid_test",
            description: "Test with valid username and password",
            field_name: { username: "tomsmith", password: "SuperSecretPassword!" },
            expected: "success"
        },
        {
            name: "invalid_test",
            description: "Test with invalid username and password",
            field_name: { username: "invalidUser", password: "wrongPassword" },
            expected: "error"
        }
    ]
};

const getSelector = async (selector) => {
    try {
        await $(selector.primary).waitForDisplayed({ timeout: 5000 });
        return selector.primary;
    } catch {
        return selector.fallback;
    }
};

const safeSetValue = async (selector, value) => {
    const sel = await getSelector(selector);
    const element = await $(sel);
    await element.waitForDisplayed();
    await element.setValue(value);
};

const safeTap = async (selector) => {
    const sel = await getSelector(selector);
    const element = await $(sel);
    await element.waitForDisplayed();
    await element.click();
};

const getMessageText = async (selector) => {
    const sel = await getSelector(selector);
    const element = await $(sel);
    await element.waitForDisplayed();
    return await element.getText();
};

describe('Login Tests', () => {
    before(async () => {
        await browser.url(testData.url);
    });

    for (const testCase of testData.test_cases) {
        it(testCase.description, async () => {
            await safeSetValue(testData.selectors.username, testCase.field_name.username);
            await safeSetValue(testData.selectors.password, testCase.field_name.password);
            await safeTap(testData.selectors.submit);

            if (testCase.expected === "success") {
                const successMessage = await getMessageText(testData.selectors.success_container);
                expect(successMessage).toContain('You logged into a secure area!');
            } else {
                const errorMessage = await getMessageText(testData.selectors.error_container);
                expect(errorMessage).toContain('Your username is invalid!');
            }
        });
    }
});