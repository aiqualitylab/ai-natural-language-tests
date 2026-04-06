# Prompt Update Guide for Any URL

## One-Page Master Checklist

Use target URL example: `https://the-internet.herokuapp.com/login`

| Step | Action | Command or File | Pass Condition |
|---|---|---|---|
| 1 | Pick requirement and URL | Example requirement: `"Test login"` | Clear requirement and target URL chosen |
| 2 | Generate context once | `python qa_automation.py "Test login" --url https://the-internet.herokuapp.com/login --framework cypress --run` | Context artifacts created |
| 3 | Validate fixture quality | `cypress/fixtures/url_test_data.json` | Usable selectors + valid/invalid test cases present |
| 4 | Update prompt rules | `prompt_specs/test_generation_traditional.yaml` | Cypress rules updated |
| 5 | Update prompt rules | `prompt_specs/test_generation_prompt_powered.yaml` | Cypress prompt-powered rules updated |
| 6 | Update prompt rules | `prompt_specs/test_generation_playwright.yaml` | Playwright rules updated |
| 7 | Update prompt rules | `prompt_specs/test_generation_webdriverio.yaml` | WebdriverIO rules updated |
| 8 | Bump prompt version(s) | `version: 1` -> `version: 2` (or next) | Version incremented in all changed prompt files |
| 9 | Validate Cypress | `python qa_automation.py "Test login" --url https://the-internet.herokuapp.com/login --framework cypress --run` | Exit code 0 |
| 10 | Validate Playwright | `./.venv/Scripts/python.exe qa_automation.py "Test login" --url https://the-internet.herokuapp.com/login --framework playwright --run` | Exit code 0 |
| 11 | Validate WebdriverIO | `python qa_automation.py "Test login" --url https://the-internet.herokuapp.com/login --framework webdriverio --run` | Exit code 0 |
| 12 | Analyze failures if needed | `python qa_automation.py --analyze -f <path-to-failure-log>` | Root cause identified and prompt refined |

## Framework Policy Table

| Framework | Must Enforce | Must Avoid |
|---|---|---|
| Cypress | Dynamic selectors from fixture, explicit URL plus text/state assertions, URL-agnostic success/error checks | Hardcoded routes (`/dashboard`, `/secure`), success URL equality on auth-like pages, click-only/wait-only final checks |
| Playwright | Context-driven locators, non-empty message assertions, auth-like URL movement logic | Hardcoded route assertions, URL checks based on `expected` string, brittle fixed path assumptions |
| WebdriverIO | Async-await consistency, context-driven selectors, URL/text fallback assertion logic | Missing `await`, hardcoded success routes, requiring both URL and message for invalid flow when one signal is enough |

## Copy-Paste Rule Block

Add these intents to each generation prompt:

- Strong assertion policy: every test uses explicit URL plus text/state assertions.
- Weak assertions forbidden: no click-only, wait-only, or existence-only final checks.
- Stable selector policy: data-testid, then data-cy, then role or label, then fallback css.
- URL-agnostic policy: never hardcode success routes unless present in CONTEXT.
- Privacy-safe policy: mask emails, phone numbers, tokens, API keys, and credentials.

## Quick Triage Table

| If this fails | Check this generated file | First 3 things to inspect |
|---|---|---|
| Playwright | `tests/generated/*.spec.ts` | Hardcoded `/dashboard`, URL checks using `expected`, exact route assertions not in context |
| Cypress | `cypress/e2e/generated/*.cy.js` | Success URL equality to login URL, hardcoded success path, weak final assertions |
| WebdriverIO | `webdriverio/tests/generated/*.spec.js` | Missing `await`, hardcoded success route, overly strict invalid-flow assertion |

## Definition of Done

- All three framework runs return exit code 0.
- No hardcoded route assumptions unless explicitly present in context.
- Selectors are context-driven and resilient.
- Assertions are observable and meaningful.
- Prompt versions are incremented for all changed files.
