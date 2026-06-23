# Model Card — AI Natural Language Tests

**What it does:** Takes plain English requirements and writes automated tests for web applications and mobile apps.

---

## AI Providers

OpenAI · Anthropic · Google — one provider is active at a time based on your API key.

---

## What Gets Sent to the AI

✅ Your test requirement text  
✅ The HTML of the page being tested  
❌ Passwords, personal data, or production content — never sent

---

## What It Does Well

- Writes login, form, and navigation tests from plain English
- Reads the page and picks the right selectors automatically
- Explains test failures in plain language
- Generates mobile tests for Android and iOS via Appium (Experimental)

## Known Limitations

- May pick wrong selectors on complex or dynamic pages
- Output quality depends on how clearly the requirement is written
- Does not test accessibility, security, or performance
- Appium tests require external Appium server and mobile device/emulator to execute

---

## Human Oversight

Use `--approve` to review every generated test before it is saved. Always review tests before running them in production.

---

## Use This For

✅ Writing end-to-end tests during development and QA  
✅ Speeding up test authoring for engineering teams  
✅ Mobile test generation with Appium (Experimental, requires mobile infrastructure)

## Do Not Use This For

❌ Replacing human judgment in test strategy  
❌ Fully automated production deployments without review  

---

## EU AI Act

This is a general-purpose development tool. It is not high-risk under the EU AI Act. Data sent to AI providers is subject to their own terms of service.

---

## Report a Problem

Open an issue → [github.com/aiqualitylab/ai-natural-language-tests/issues](https://github.com/aiqualitylab/ai-natural-language-tests/issues)

---

Maintained by [AI Quality Lab](https://aiqualitylab.org) · Last updated May 2026
