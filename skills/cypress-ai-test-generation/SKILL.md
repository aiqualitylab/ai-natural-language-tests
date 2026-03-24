---
name: cypress-ai-test-generation
description: Generate Cypress tests for this repository using fixture-driven selectors, function syntax for this.testData, and resilient assertions. Use when creating or refining Cypress output for ai-natural-language-tests.
license: AGPL-3.0-or-later
metadata:
  author: AI Quality Lab
  version: "1.0.0"
  category: testing
---

# Instructions

Generate Cypress tests that follow this repository's patterns:
- Use `function()` syntax when relying on `this.testData`.
- Resolve selector objects via `fallback_css` before calling `cy.get(...)`.
- Support both flat test case values and values nested under `field_name`.
- Avoid hardcoded credentials, selectors, or URLs when context provides them.
- Prefer resilient message assertions with configured selectors and `#flash` fallback where appropriate.
