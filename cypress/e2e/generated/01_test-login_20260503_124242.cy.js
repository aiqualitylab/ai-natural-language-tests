// Requirement: Test login

describe('Login Tests', function () {

    function getSelector(selectorEntry) {
        if (!selectorEntry) { return null; }
        if (typeof selectorEntry === 'string') { return selectorEntry; }
        if (typeof selectorEntry === 'object') { return selectorEntry.fallback_css || null; }
        return null;
    }

    function buildUrl(baseUrl, pattern, params) {
        let url = baseUrl + pattern;
        Object.keys(params || {}).forEach(function (key) {
            url = url.replace('{' + key + '}', encodeURIComponent(params[key]));
        });
        return url;
    }

    function fillFormFields(testCase, selectors) {
        const values = testCase.field_name || testCase;
        Object.keys(values).forEach(function (field) {
            const selector = getSelector(selectors[field]);
            const value = values[field];
            if (selector && typeof value === 'string' && value) {
                cy.get(selector).clear().type(value);
            }
        });
    }

    beforeEach(function () {
        cy.fixture('url_test_data').then((data) => {
            this.testData = data;
        });
    });

    it('should succeed with valid data', function () {
        const valid = this.testData.test_cases.find(tc => tc.name === 'valid_test');
        const selectors = this.testData.selectors;
        cy.visit(this.testData.url);

        fillFormFields(valid, selectors);

        const submitSelector = getSelector(selectors.submit);
        cy.get(submitSelector).click();

        const successSelector = getSelector(selectors.success_container) || '#flash';
        cy.get(successSelector).should('be.visible');
    });

    it('should fail with invalid data', function () {
        const invalid = this.testData.test_cases.find(tc => tc.name === 'invalid_test');
        const selectors = this.testData.selectors;
        cy.visit(this.testData.url);

        fillFormFields(invalid, selectors);

        const submitSelector = getSelector(selectors.submit);
        cy.get(submitSelector).click();

        const errorSelector = getSelector(selectors.error_container) || '#flash';
        cy.get(errorSelector).should('be.visible');
        cy.get(errorSelector).invoke('text').then((text) => {
            expect(text.toLowerCase()).to.match(/invalid|error|incorrect|failed/);
        });
    });
});