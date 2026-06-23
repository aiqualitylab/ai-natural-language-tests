const sharedConfig = {
    runner: 'local',
    specs: ['./webdriverio/tests/{generated,prompt-powered,appium-tests}/**/*.spec.js'],
    maxInstances: 1,
    logLevel: 'error',
    bail: 0,
    waitforTimeout: 10000,
    connectionRetryTimeout: 120000,
    connectionRetryCount: 2,
    framework: 'mocha',
    reporters: ['spec'],
    mochaOpts: {
        ui: 'bdd',
        timeout: 60000,
    },
};

module.exports = { sharedConfig };
