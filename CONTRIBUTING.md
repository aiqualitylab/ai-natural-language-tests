# Contributing Guide

Thank you for contributing to `ai-natural-language-tests`.

This project follows enterprise-style contribution standards to maintain reliability, security, and traceability.

## Table of Contents

0. [Volunteer Testing (no coding needed)](#volunteer-testing)
1. [Contribution Principles](#contribution-principles)
2. [Development Setup](#development-setup)
3. [Forking and Clone Strategy](#forking-and-clone-strategy)
4. [Branching Strategy](#branching-strategy)
5. [Commit Standards](#commit-standards)
6. [Pull Request Requirements](#pull-request-requirements)
7. [Testing Requirements](#testing-requirements)
8. [Documentation Requirements](#documentation-requirements)
9. [Security Requirements](#security-requirements)
10. [Observability Requirements](#observability-requirements)
11. [Code Review Checklist](#code-review-checklist)
12. [Release Contribution Notes](#release-contribution-notes)
13. [Publishing a Docker Image (GHCR)](#publishing-a-docker-image-ghcr)
14. [Architecture Contribution Notes](#architecture-contribution-notes)

## Volunteer Testing

**No coding needed.** New here? Welcome. This is simply an invitation to explore the repo and try the tool. There is no commitment and no deadline; do as much or as little as you like.

The rest of this guide (from *Contribution Principles* onward) is for code contributors. If you only want to try the tool and share feedback, this section is all you need.

### 1. Open the tool

- **No install:** [Hugging Face Space](https://huggingface.co/spaces/aiqualitylab/ai-natural-language-tests)
- **On your computer:** follow the [Quick Start](README.md#quick-start-5-minutes) in the README.

You'll need your own **OpenAI API key**. By default the tool uses **GPT-4o-mini**, which keeps costs low.
Prefer not to use a key? A free offline model via Ollama is also available (see the README, *Use Your Own Local Model*).

### 2. Pick a website you are allowed to test

- your own app or website
- a local or staging (test) version of an app you work on, with permission
- a public practice site, for example:
  - https://the-internet.herokuapp.com/login
  - https://www.saucedemo.com
  - https://demoqa.com

Please don't test other people's live websites.

The page HTML is sent to OpenAI to generate the test, so avoid pages with real personal or company data, or use the offline model, where nothing leaves your computer.

### 3. Generate a test

Type what you want to test in plain English, for example:

> Test login fails with wrong password

Choose a framework (Cypress, Playwright or WebdriverIO) and generate the test.

### 4. Check the result

- Does the test run?
- Does it test the right thing?
- Does it use stable selectors (not fragile ones)?
- Did the AI make up buttons or fields that aren't on the page?

### 5. Tell us what you found

[Open a "Generated test feedback" issue](../../issues/new?template=generated-test-feedback.yml) and include:

- the website URL
- what you typed
- the framework and AI model you used
- the test it generated
- what was wrong, or what worked well

Questions? Ask in [GitHub Discussions](../../discussions).

### 6. Contributing code

To work on the code, fork the repo (see [Forking and Clone Strategy](#forking-and-clone-strategy)) and open a pull request (see [Pull Request Requirements](#pull-request-requirements)).
Issues labeled [`good first issue`](../../labels/good%20first%20issue) are a good place to begin.
Starring the repo lets you follow updates and helps other testers find it.

Anyone can help, beginners and experts both welcome.

## Contribution Principles

- Keep changes focused and scoped to a single objective.
- Prefer small, reviewable pull requests.
- Maintain backward compatibility unless explicitly planned as breaking change.
- Update documentation for any behavior, CLI, config, or workflow change.

## Development Setup

You can use either a local Python/Node setup or Docker.

### Option A: Local Setup

```bash
git clone https://github.com/aiqualitylab/ai-natural-language-tests.git
cd ai-natural-language-tests
pip install -r requirements.txt
npm ci
npx cypress install
npx cypress verify
npx playwright install chromium
```

Create `.env` from `.env.example` and populate required keys.

`npm ci` installs Cypress, Playwright, and WebdriverIO dependencies from `devDependencies`. `npx cypress install` and `npx cypress verify` ensure the Cypress binary is available, and `npx playwright install chromium` installs the Playwright browser runtime.

### Option B: Docker Setup

```bash
git clone https://github.com/aiqualitylab/ai-natural-language-tests.git
cd ai-natural-language-tests
cp .env.example .env
docker compose up --build
```

Use Docker when you want reproducible dependencies or to avoid local Python/Node version drift.

## Forking and Clone Strategy

- External contributors should fork the repository first, then clone their fork and open pull requests back to `aiqualitylab/ai-natural-language-tests`.
- Maintainers and trusted internal contributors with write access can branch directly from the main repository.

Example fork flow:

```bash
git clone https://github.com/<your-username>/ai-natural-language-tests.git
cd ai-natural-language-tests
git remote add upstream https://github.com/aiqualitylab/ai-natural-language-tests.git
```

## Branching Strategy

Use short-lived feature branches:

- `feature/<short-description>`
- `fix/<short-description>`
- `docs/<short-description>`
- `chore/<short-description>`

Examples:

- `feature/playwright-selector-fallback`
- `fix/loki-write-token-validation`
- `docs/readme-observability-section`

## Commit Standards

Use conventional-style commit messages:

- `feat: add otel span around workflow execution`
- `fix: handle missing loki credentials gracefully`
- `docs: update docker observability configuration`
- `test: add generated test validation scenario`
- `chore: pin opentelemetry dependency`

Guidelines:

- Subject line in imperative tense.
- Keep subject line concise.
- Add body when context is needed (why, impact, migration notes).

## Pull Request Requirements

Every pull request should include:

- Summary of change.
- Motivation and business/engineering impact.
- Testing evidence (local output, CI run, or screenshots where relevant).
- Risk and rollback notes for non-trivial changes.
- Documentation updates for user-facing behavior.

## Testing Requirements

Before opening a PR, run:

```bash
python qa_automation.py --help
python qa_automation.py "Test login" --url https://the-internet.herokuapp.com/login --framework cypress
```

If change affects runtime execution, also run the relevant framework:

```bash
python qa_automation.py "Test login" --url https://the-internet.herokuapp.com/login --framework playwright --run
python qa_automation.py "Test login" --url https://the-internet.herokuapp.com/login --framework webdriverio --run
```

If change affects Cypress pathing or prompt mode, run at least one Cypress generation command.

If change affects conversational refinement, also check error recovery and panel integrity (a failed refinement must keep the original code).

For UI refinement testing in the app, generate tests normally, then use the "Refine" textbox and button to verify refinement updates both the panel and disk files correctly.

## Documentation Requirements

Update these files whenever applicable:

- `README.md` for setup/config/usage changes.
- `.env.example` for new environment variables.
- `requirements.txt` / `package.json` for dependency changes.
- `prompt_specs/*.yaml` for parser contract or output-shape changes.

Avoid undocumented behavior changes.

## Security Requirements

- Never commit real API keys or tokens.
- Use least-privilege Grafana and LLM credentials.
- Use `logs:write` only when Loki push is required.
- Rotate leaked credentials immediately and document remediation in PR notes.

## Observability Requirements

For changes to tracing/logging:

- Ensure OTLP config remains compatible with Grafana Tempo.
- Ensure Loki config remains optional and non-blocking.
- Ensure transient Loki transport failures do not crash or spam traceback output.
- Validate that logs/spans still emit during normal generation flow.

Recommended verification queries:

- Tempo: `{resource.service.name="ai-natural-language-tests"}`
- Loki: `{service_name="ai-natural-language-tests"}`

## Code Review Checklist

Reviewers should validate:

- Correctness and backward compatibility.
- Error handling and user messaging quality.
- Security of secrets and tokens.
- Test and documentation coverage.
- No unrelated refactors bundled with the change.

## Release Contribution Notes

If your change affects user workflows, include a short release note proposal in the PR description:

- What changed.
- Why it matters.
- Any migration step required.

For `v6.0.0` and later, release notes should explicitly call out changes in these areas when applicable:

- HITL behavior (`--approve` flow and approval UX)
- Replay behavior (`--list-html-replays`, `--replay-html-analysis`)
- Architecture updates across `qa_automation.py`, `qa_config.py`, `qa_runtime.py`, `qa_workflow.py`
- Prompt contract changes affecting parser expectations (JSON-only or strict 3-line analysis output)

## Publishing a Docker Image (GHCR)

Only the repository maintainer publishes Docker images. Contributors open a pull request — the maintainer merges, tags, and publishes.

### How the workflow works

Pushing a version tag triggers `.github/workflows/publish-ghcr.yml` automatically:

```
git push origin v7.0.0
        |
        ▼
GitHub Actions
        ├── Checks out the code
        ├── Logs in to GHCR using GITHUB_TOKEN (no manual secret needed)
        ├── Builds the Docker image from Dockerfile
        └── Pushes to GHCR:
                                  ghcr.io/aiqualitylab/ai-natural-language-tests:v7.0.0  ← pinned
              ghcr.io/aiqualitylab/ai-natural-language-tests:latest   ← always current
```

### When to publish a new version

- A bug in test generation is fixed
- Support for a new LLM provider is added
- A dependency is updated (Python, Node, LangGraph, etc.)
- The `Dockerfile` or `docker-compose.yml` is changed
- Any change that affects how the tool behaves for end users

> Without publishing, users pulling `latest` would run an outdated image. Pinned tags let users stay on a specific release and upgrade deliberately.

### Steps to publish

```bash
# 1. Merge the PR and ensure main is clean
# 2. Tag the current commit
git tag v7.0.0

# 3. Push the tag — this triggers the publish workflow
git push origin v7.0.0
```

After ~2 minutes the image appears in the **Packages** tab of the repository.

## Architecture Contribution Notes

Starting in `v6.0.0`, keep contributions aligned to module responsibilities:

- `qa_automation.py`: CLI and command dispatch only
- `qa_config.py`: static configuration, prompt loading, model factory
- `qa_runtime.py`: external integrations (logging, tracing, persistence, replay, pattern store)
- `qa_workflow.py`: LangGraph state, nodes, and graph assembly
- `qa_refinement.py`: conversational refinement of generated tests

Current implementation notes:

- Keep structured LLM output handling in parser classes (`BaseOutputParser`) rather than ad-hoc string parsing.
- Keep workflow/app/CLI invocation wrappers in `RunnableLambda` when introducing new orchestration boundaries.
- Keep embeddings imports compatible with `langchain-huggingface` first, then fallback only when needed.
- Keep refinement logic isolated from heavy dependencies: `qa_refinement.py` imports only from `qa_config` (not `qa_workflow` or `qa_runtime`).

When adding features, prefer extending the relevant module over reintroducing monolithic logic into the CLI entry file.