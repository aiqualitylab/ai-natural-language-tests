// Requirement: User can login
describe('User Login Tests', () => {
    const baseUrl = 'https://the-internet.herokuapp.com/login';

    beforeEach(() => {
        cy.visit(baseUrl);
    });

    it('should successfully log in with valid credentials', () => {
        cy.get('input[type="text"]').type('tomsmith');
        cy.get('input[type="password"]').type('SuperSecretPassword!');
        cy.get('button[type="submit"]').click();

        cy.url().should('include', '/secure');
        cy.get('.flash.success').should('be.visible').and('contain', 'You logged into a secure area!');
    });

    it('should show an error message with invalid credentials', () => {
        cy.get('input[type="text"]').type('invalidUser');
        cy.get('input[type="password"]').type('wrongPassword');
        cy.get('button[type="submit"]').click();

        cy.url().should('include', '/login');
        cy.get('.flash.error').should('be.visible').and('contain', 'Your username is invalid!');
    });
});
