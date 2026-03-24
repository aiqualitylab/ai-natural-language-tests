---
name: playwright-ai-test-generation
description: Generate Playwright tests for this repository using async await, context-driven selectors, and resilient assertions. Use when creating or refining Playwright output for ai-natural-language-tests.
license: AGPL-3.0-or-later
metadata:
  author: AI Quality Lab
  version: "1.0.0"
  category: testing
---

# Instructions

Generate Playwright tests that follow this repository's patterns:
- Use `@playwright/test` with `async/await` consistently.
- Prefer selectors and URLs from provided context instead of hardcoded values.
- Use resilient assertions and avoid brittle app-specific text unless context requires it.
- Keep generated tests readable and runnable in CI.
