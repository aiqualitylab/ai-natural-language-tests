# Framework Rules

## Cypress
- Use dynamic selectors from fixture/context.
- Use `function()` when accessing `this.testData`.
- Support values in both flat and `field_name` shapes.

## Playwright
- Use `@playwright/test` patterns with `async/await`.
- Prefer semantic locators where appropriate.
- Keep assertions resilient and avoid brittle hardcoded text.

## WebdriverIO
- Use async WebdriverIO APIs consistently.
- Resolve selector objects via `fallback_css`.
- For invalid-login/error scenarios, accept either non-empty error text or auth-like URL retention.
