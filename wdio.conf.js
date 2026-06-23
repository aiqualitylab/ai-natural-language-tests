const { sharedConfig } = require('./wdio.shared.conf');

exports.config = {
    ...sharedConfig,
    specs: ['./webdriverio/tests/{generated,prompt-powered}/**/*.spec.js'],
    services: ['chromedriver'],
    capabilities: [{
        maxInstances: 1,
        browserName: 'chrome',
        acceptInsecureCerts: true,
        'goog:chromeOptions': {
            args: [
                '--headless=new',
                '--disable-gpu',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--window-size=1440,900',
            ],
        },
    }],
};