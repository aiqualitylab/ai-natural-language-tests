// Requirement: Test login with valid credentials

const puppeteer = require('puppeteer');
const { describe, test, expect, beforeAll, afterAll, beforeEach, afterEach } = require('@jest/globals');

const testData = {
  url: "https://the-internet.herokuapp.com/login",
  selectors: {
    username: "input[name='username']",
    password: "input[name='password']",
    submit: "button[type='submit']",
    error_container: "#flash",
    success_container: "#flash"
  },
  test_cases: [
    {
      name: "valid_login",
      description: "Test with valid username and password",
      username: "tomsmith",
      password: "SuperSecretPassword!",
      expected: "success"
    },
    {
      name: "invalid_login",
      description: "Test with invalid username and password",
      username: "invalidUser",
      password: "wrongPassword",
      expected: "error"
    }
  ]
};

let browser;
let page;

const getSelector = (selector) => {
  return selector;
};

const fillFormFields = async (username, password) => {
  if (username) {
    await page.type(getSelector(testData.selectors.username), username);
  }
  if (password) {
    await page.type(getSelector(testData.selectors.password), password);
  }
};

const getMessageText = async () => {
  await page.waitForSelector(getSelector(testData.selectors.success_container), { visible: true });
  return await page.$eval(getSelector(testData.selectors.success_container), el => el.textContent);
};

beforeAll(async () => {
  browser = await puppeteer.launch({ headless: true });
});

afterAll(async () => {
  await browser.close();
});

beforeEach(async () => {
  page = await browser.newPage();
  await page.goto(testData.url);
});

afterEach(async () => {
  await page.close();
});

describe('Login Tests', () => {
  testData.test_cases.forEach(({ name, description, username, password, expected }) => {
    test(name, async () => {
      await fillFormFields(username, password);
      await page.click(getSelector(testData.selectors.submit));

      if (expected === "success") {
        await page.waitForNavigation();
        const message = await getMessageText();
        expect(message).toMatch(/logged into|secure area|success/i);
      } else if (expected === "error") {
        await page.waitForSelector(getSelector(testData.selectors.error_container), { visible: true });
        const message = await page.$eval(getSelector(testData.selectors.error_container), el => el.textContent);
        expect(message).toBeTruthy();
        expect(page.url()).toBe(testData.url);
      }
    });
  });
});