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
    const submitSelector = await getSelector(selectors.submit);

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

    if (submitSelector) {
        const submitButton = $(submitSelector);
        await submitButton.waitForDisplayed();
        await submitButton.click();
    }
}

async function getMessageText(selectors) {
    const errorSelector = await getSelector(selectors.error_container);
    const successSelector = await getSelector(selectors.success_container);
    
    if (errorSelector) {
        const errorMessage = $(errorSelector);
        if (await errorMessage.isDisplayed()) {
            return await errorMessage.getText();
        }
    }

    if (successSelector) {
        const successMessage = $(successSelector);
        if (await successMessage.isDisplayed()) {
            return await successMessage.getText();
        }
    }

    return '';
}

async function isAuthLikeUrl() {
    const currentUrl = await browser.getUrl();
    return currentUrl.includes('/login');
}

async function hasErrorSignal(errorText, currentUrl, urlBefore) {
    return errorText.length > 0 || (currentUrl === urlBefore);
}

describe('Login Tests', () => {
    beforeEach(async () => {
        await browser.url(testData.url);
    });

    for (const testCase of testData.test_cases) {
        it(testCase.description, async () => {
            const urlBefore = await browser.getUrl();
            await fillFormFields(testCase, testData.selectors);
            const currentUrl = await browser.getUrl();
            const errorText = await getMessageText(testData.selectors);

            if (testCase.expected === "success") {
                const successSignal = await getMessageText(testData.selectors);
                expect(successSignal.trim().length).toBeGreaterThan(0);
                expect(currentUrl).not.toContain('/login');
            } else if (testCase.expected === "error") {
                const errorSignal = await hasErrorSignal(errorText, currentUrl, urlBefore);
                expect(errorSignal).toBe(true);
            }
        });
    }
});