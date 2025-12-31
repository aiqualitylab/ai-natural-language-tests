// Requirement: Test login
// Test Type: Traditional

describe('Login Tests', function () {
    beforeEach(function () {
        cy.fixture('url_test_data').then((data) => {
            this.testData = data;
        });
    });

    it('should login successfully with valid credentials', function () {
        cy.visit(this.testData.url);
        const valid = this.testData.test_cases.find(tc => tc.name === 'valid_test');
        cy.get('#username').type(valid.username);
        cy.get('#password').type(valid.password);
        cy.get("button[type='submit']").click();
        cy.url().should('include', '/secure');
    });

    it('should show error with invalid credentials', function () {
        cy.visit(this.testData.url);
        const invalid = this.testData.test_cases.find(tc => tc.name === 'invalid_test');
        cy.get('#username').type(invalid.username);
        cy.get('#password').type(invalid.password);
        cy.get("button[type='submit']").click();
        cy.get('#flash').should('contain', 'invalid');
    });
});