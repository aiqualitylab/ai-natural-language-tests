const { sharedConfig } = require('./wdio.shared.conf');

exports.config = {
    ...sharedConfig,
    services: [['appium', { command: 'appium' }]],
    // Set APP_PLATFORM=ios to switch to iOS; defaults to Android.
    capabilities: process.env.APP_PLATFORM === 'ios'
        ? [{
              platformName: 'iOS',
              'appium:automationName': 'XCUITest',
              'appium:deviceName': process.env.IOS_DEVICE_NAME || 'iPhone 15',
              'appium:platformVersion': process.env.IOS_PLATFORM_VERSION || '17.5',
              'appium:app': process.env.IOS_APP_PATH,
              'appium:noReset': true,
              'appium:newCommandTimeout': 120,
          }]
        : [{
              platformName: 'Android',
              'appium:automationName': 'UiAutomator2',
              'appium:deviceName': process.env.ANDROID_DEVICE_NAME || 'Android Emulator',
              'appium:platformVersion': process.env.ANDROID_PLATFORM_VERSION || '14',
              'appium:app': process.env.ANDROID_APP_PATH,
              'appium:autoGrantPermissions': true,
              'appium:noReset': true,
              'appium:newCommandTimeout': 120,
          }],
};
