const { defineConfig } = require('cypress');

module.exports = defineConfig({
  e2e: {
    setupNodeEvents(on, config) {
      // implement node event listeners here
    },
    baseUrl: 'https://the-internet.herokuapp.com',
    supportFile: false,
    video: true,
    screenshotOnRunFailure: true,
    projectId: "PLEASE_SET_YOUR_OWN_PROJECT_ID",
    // Enable experimental cy.prompt() feature
    experimentalPromptCommand: true,
    
    // Optional: Configure AI behavior
    cypressPromptOptions: {
      // Enable self-healing
      enableSelfHealing: true,
      
      // Show generated code in Command Log
      showGeneratedCode: true,
      
      // Timeout for AI operations
      timeout: 30000,
    },
    
    // Recommended settings for cy.prompt()
    defaultCommandTimeout: 10000,
    viewportWidth: 1280,
    viewportHeight: 720,
  },
});