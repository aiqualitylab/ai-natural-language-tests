// Requirement: Test login

const { browser, expect } = require('@wdio/globals');

const testData = {
    url: "https://the-internet.herokuapp.com/login",
    base_url: "https://the-internet.herokuapp.com",
    url_pattern: "/login",
    dynamic_segments: [],
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

function buildUrl(baseUrl, pattern, params) {
    let url = baseUrl + pattern;
    Object.keys(params || {}).forEach(function (key) {
        url = url.replace('{' + key + '}', encodeURIComponent(params[key]));
    });
    return url;
}

async function fillFormFields(testCase, selectors) {
    if (selectors.username && testCase.field_name.username) {
        const usernameField = await $(selectors.username);
        await usernameField.waitForDisplayed();
        await usernameField.setValue(testCase.field_name.username);
    }
    if (selectors.password && testCase.field_name.password) {
        const passwordField = await $(selectors.password);
        await passwordField.waitForDisplayed();
        await passwordField.setValue(testCase.field_name.password);
    }
}

async function getMessageText(selectors) {
    const errorContainer = await $(selectors.error_container);
    const successContainer = await $(selectors.success_container);
    
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
    beforeEach(async () => {
        await browser.url(testData.url);
    });

    for (const testCase of testData.test_cases) {
        it(testCase.description, async () => {
            const urlBefore = await browser.getUrl();
            await fillFormFields(testCase, testData.selectors);
            const submitButton = await $(testData.selectors.submit);
            await submitButton.waitForDisplayed();
            await submitButton.click();

            const currentUrl = await browser.getUrl();
            const errorText = await getMessageText(testData.selectors);
            const errorSignal = await hasErrorSignal(errorText, currentUrl, urlBefore);

            if (testCase.expected === "success") {
                expect(errorText.trim().length).toBeGreaterThan(0);
                expect(currentUrl).not.toContain('/login');
            } else {
                expect(errorSignal).toBe(true);
            }
        });
    }
});