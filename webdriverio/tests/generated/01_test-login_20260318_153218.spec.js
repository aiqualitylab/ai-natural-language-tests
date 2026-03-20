// Requirement: Test login

const { browser, $ , expect } = require('@wdio/globals');

const testData = {
    url: "https://the-internet.herokuapp.com/login",
    selectors: {
        username: {
            fallback_css: "input[name='username']"
        },
        password: {
            fallback_css: "input[name='password']"
        },
        submit: {
            fallback_css: "button[type='submit']"
        },
        error_container: {
            fallback_css: "#flash-messages"
        },
        success_container: {
            fallback_css: "#flash-messages"
        }
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
    return selector.fallback_css || null;
}

async function fillFormFields(testCase, selectors) {
    const usernameSelector = await getSelector(selectors.username);
    const passwordSelector = await getSelector(selectors.password);
    
    if (usernameSelector && testCase.username) {
        const usernameField = $(usernameSelector);
        await usernameField.waitForDisplayed();
        await usernameField.setValue(testCase.username);
    }
    
    if (passwordSelector && testCase.password) {
        const passwordField = $(passwordSelector);
        await passwordField.waitForDisplayed();
        await passwordField.setValue(testCase.password);
    }
}

async function getMessageText(selector) {
    const messageSelector = await getSelector(selector);
    if (messageSelector) {
        const messageElement = $(messageSelector);
        await messageElement.waitForDisplayed({ timeout: 2000 }).catch(() => {});
        if (await messageElement.isDisplayed()) {
            const messageText = await messageElement.getText();
            return messageText.trim();
        }
    }
    return '';
}

async function isAuthLikeUrl() {
    const currentUrl = await browser.getUrl();
    return currentUrl.includes('/login');
}

async function hasErrorSignal(errorText, currentUrl, urlBefore) {
    return errorText.length > 0 || (await isAuthLikeUrl() && currentUrl === urlBefore);
}

describe('Login Tests', () => {
    beforeEach(async () => {
        await browser.url(testData.url);
    });

    for (const testCase of testData.test_cases) {
        it(testCase.description, async () => {
            await fillFormFields(testCase, testData.selectors);
            const submitSelector = await getSelector(testData.selectors.submit);
            if (submitSelector) {
                const urlBefore = await browser.getUrl();
                const submitButton = $(submitSelector);
                await submitButton.waitForDisplayed();
                await submitButton.click();
                
                const currentUrl = await browser.getUrl();
                const successText = await getMessageText(testData.selectors.success_container);
                const errorText = await getMessageText(testData.selectors.error_container);
                
                if (testCase.expected === "success") {
                    const successSignal = successText.length > 0 || !(await isAuthLikeUrl());
                    expect(successSignal).toBe(true);
                } else if (testCase.expected === "error") {
                    const errorSignal = await hasErrorSignal(errorText, currentUrl, urlBefore);
                    expect(errorSignal).toBe(true);
                }
            }
        });
    }
});