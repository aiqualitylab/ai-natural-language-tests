// Requirement: Test login

const { browser, $ , expect } = require('@wdio/globals');

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

async function getSelector(selector) {
    return selector || null;
}

async function fillFormFields(testCase, selectors) {
    if (selectors.username) {
        const usernameField = $(selectors.username);
        await usernameField.waitForDisplayed();
        if (testCase.username) {
            await usernameField.setValue(testCase.username);
        }
    }
    if (selectors.password) {
        const passwordField = $(selectors.password);
        await passwordField.waitForDisplayed();
        if (testCase.password) {
            await passwordField.setValue(testCase.password);
        }
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
    beforeEach(async () => {
        await browser.url(testData.url);
    });

    for (const testCase of testData.test_cases) {
        it(testCase.description, async () => {
            const urlBefore = await browser.getUrl();
            await fillFormFields(testCase, testData.selectors);
            const submitButton = $(testData.selectors.submit);
            await submitButton.waitForDisplayed();
            await submitButton.click();
            const currentUrl = await browser.getUrl();
            const errorText = await getMessageText(testData.selectors);
            
            if (testCase.expected === "success") {
                expect(errorText.trim().length).toBeGreaterThan(0);
                expect(currentUrl).not.toContain('/login');
            } else {
                const errorSignal = await hasErrorSignal(errorText, currentUrl, urlBefore);
                expect(errorSignal).toBe(true);
            }
        });
    }
});