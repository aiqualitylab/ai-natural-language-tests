// Requirement: Test login
// Test Type: cy.prompt()

describe('User Login Tests', () => {
    const baseUrl = 'https://the-internet.herokuapp.com/login';

    beforeEach(() => {
        cy.fixture('url_test_data.json').then((testData) => {
            this.testData = testData;
        });
        cy.visit(baseUrl);
    });

    it('should successfully log in with valid credentials', function() {
        cy.prompt([
            'Visit the login page',
            'Enter the username: ' + this.testData.valid_test.username,
            'Enter the password: ' + this.testData.valid_test.password,
            'Click the submit button'
        ]).then(() => {
            cy.url().should('include', '/secure').then(() => {
                cy.get('.flash.success').should('be.visible').and('contain', 'You logged into a secure area!');
            });
        });
    });

    it('should show an error with invalid credentials', function() {
        cy.prompt([
            'Visit the login page',
            'Enter the username: ' + this.testData.invalid_test.username,
            'Enter the password: ' + this.testData.invalid_test.password,
            'Click the submit button'
        ]).then(() => {
            cy.url().should('include', '/login').then(() => {
                cy.get('.flash.error').should('be.visible').and('contain', 'Your username is invalid!');
            });
        });
    });
});