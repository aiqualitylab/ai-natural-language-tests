// Requirement:
// Test login

const { browser, $ , expect } = require('@wdio/globals');

const testData = {
    url: "https://the-internet.herokuapp.com/login",
    base_url: "https://the-internet.herokuapp.com",
    url_pattern: "/login",
    dynamic_segments: [],
    selectors: {
        username: "input[name='username']",
        password: "input[name='password']",
        submit: "button[type='submit']",
        error_container: "#flash",
        success_container: "#flash"
    },
    test_cases: [
        {
            name: "valid_login",
            description: "Test with valid username and password",
            username: "tomsmith",
            password: "SuperSecretPassword!",
            expected: "success"
        },
        {
            name: "invalid_login",
            description: "Test with invalid username and password",
            username: "invalidUser",
            password: "wrongPassword",
            expected: "error"
        }
    ]
};

async function buildUrl(baseUrl, pattern, params) {
    let url = baseUrl + pattern;
    Object.keys(params || {}).forEach(function (key) {
        url = url.replace('{' + key + '}', encodeURIComponent(params[key]));
    });
    return url;
}

async function fillFormFields(testCase, selectors) {
    if (selectors.username) {
        const usernameField = $(selectors.username);
        await usernameField.waitForDisplayed();
        await usernameField.setValue(testCase.username);
    }
    if (selectors.password) {
        const passwordField = $(selectors.password);
        await passwordField.waitForDisplayed();
        await passwordField.setValue(testCase.password);
    }
    if (selectors.submit) {
        const submitButton = $(selectors.submit);
        await submitButton.waitForDisplayed();
        await submitButton.click();
    }
}

async function getMessageText(selectors) {
    const errorContainer = $(selectors.error_container);
    const successContainer = $(selectors.success_container);
    
    if (await errorContainer.isDisplayed()) {
        return await errorContainer.getText();
    } else if (await successContainer.isDisplayed()) {
        return await successContainer.getText();
    }
    return '';
}

async function isAuthLikeUrl() {
    const currentUrl = await browser.getUrl();
    return currentUrl.includes('/login');
}

async function hasErrorSignal(errorText, currentUrl, urlBefore) {
    return errorText.length > 0 || (currentUrl === urlBefore && await isAuthLikeUrl());
}

describe('Login Tests', () => {
    for (const testCase of testData.test_cases) {
        it(testCase.description, async () => {
            await browser.url(testData.url);
            const urlBefore = await browser.getUrl();

            await fillFormFields(testCase, testData.selectors);

            await Promise.any([
                browser.waitUntil(async () => {
                    const currentUrl = await browser.getUrl();
                    return currentUrl !== urlBefore;
                }, { timeout: 60000 }),
                (async () => {
                    const messageText = await getMessageText(testData.selectors);
                    return messageText.length > 0;
                })()
            ]).catch(() => {});

            const currentUrl = await browser.getUrl();
            const messageText = await getMessageText(testData.selectors);
            const errorSignal = await hasErrorSignal(messageText, currentUrl, urlBefore);

            if (testCase.expected === "success") {
                expect(messageText.trim().length).toBeGreaterThan(0);
                expect(currentUrl).not.toContain('/login');
            } else {
                expect(errorSignal).toBe(true);
            }
        });
    }
});