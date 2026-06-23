# Incident Response — AI Natural Language Tests

What to do when something goes wrong.

---

## When to Use This

- AI is generating wrong or harmful output
- A secret or API key was accidentally committed
- Generated tests caused an unintended production change

---

## What to Do

**1. Stop** — Pause the tool or CI/CD pipeline immediately.

**2. Report** — Open an issue with what happened and what the AI produced.  
→ [github.com/aiqualitylab/ai-natural-language-tests/issues](https://github.com/aiqualitylab/ai-natural-language-tests/issues)

**3. Contain**  
- Secret exposed → revoke and rotate the key now  
- Production impacted → roll back the deployment  
- Bad AI output → disable the tool until fixed  

**4. Fix** — Apply the fix, test locally, then re-enable.

**5. Document** — Write what happened and how it was resolved in the issue thread.

---

## Security Issues

Do not post security details publicly. Follow [CONTRIBUTING.md](CONTRIBUTING.md) to report privately.

---

Maintained by [AI Quality Lab](https://aiqualitylab.org) · Last updated June 2026
