# Rules

## Test Generation Rules
- Use framework-specific APIs only (Cypress vs Playwright vs WebdriverIO vs Appium).
- Prefer selector resolution from fixture data (including object selectors with `fallback_css`).
- Avoid hardcoded URLs, credentials, and app-specific strings unless explicitly present in context.

## Framework-Specific Rules
- Cypress: prefer `function()` for tests using `this.testData`.
- Playwright: keep `async/await` flow and resilient locator/assertion usage.
- WebdriverIO: keep async element commands and resilient success/error assertions.
- Appium *(Experimental)*: use accessibility id (`~selector`) first, fall back to id or css; always use `await`; tests output to `webdriverio/tests/appium-tests/`.

## Repository Rules
- Keep prompt templates in `prompt_specs/*.yaml`.
- Keep release tags, docs references, and package version aligned.
- Keep generated artifacts out of commits unless intentionally versioned.
- Appium test execution requires external Appium server and mobile device/emulator — document this in test output.
