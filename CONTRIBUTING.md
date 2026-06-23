# Contributing Guide

Thank you for contributing to `ai-natural-language-tests`.

This project follows enterprise-style contribution standards to maintain reliability, security, and traceability.

## Table of Contents

1. Contribution Principles
2. Development Setup
3. Forking and Clone Strategy
4. Branching Strategy
5. Commit Standards
6. Pull Request Requirements
7. Testing Requirements
8. Documentation Requirements
9. Security Requirements
10. Observability Requirements
11. Code Review Checklist
12. Release Contribution Notes
13. Publishing a Docker Image (GHCR)

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

For `v5.1.0` and later, release notes should explicitly call out changes in these areas when applicable:

- HITL behavior (`--approve` flow and approval UX)
- Replay behavior (`--list-html-replays`, `--replay-html-analysis`)
- Architecture updates across `qa_automation.py`, `qa_config.py`, `qa_runtime.py`, `qa_workflow.py`
- Prompt contract changes affecting parser expectations (JSON-only or strict 3-line analysis output)

## Publishing a Docker Image (GHCR)

Only the repository maintainer publishes Docker images. Contributors open a pull request — the maintainer merges, tags, and publishes.

### How the workflow works

Pushing a version tag triggers `.github/workflows/publish-ghcr.yml` automatically:

```
git push origin v5.1.0
        |
        ▼
GitHub Actions
        ├── Checks out the code
        ├── Logs in to GHCR using GITHUB_TOKEN (no manual secret needed)
        ├── Builds the Docker image from Dockerfile
        └── Pushes to GHCR:
                                  ghcr.io/aiqualitylab/ai-natural-language-tests:v5.1.0  ← pinned
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
git tag v5.1.0

# 3. Push the tag — this triggers the publish workflow
git push origin v5.1.0
```

After ~2 minutes the image appears in the **Packages** tab of the repository.

## Architecture Contribution Notes

Starting in `v5.1.0`, keep contributions aligned to module responsibilities:

- `qa_automation.py`: CLI and command dispatch only
- `qa_config.py`: static configuration, prompt loading, model factory
- `qa_runtime.py`: external integrations (logging, tracing, persistence, replay, pattern store)
- `qa_workflow.py`: LangGraph state, nodes, and graph assembly

Current implementation notes:

- Keep structured LLM output handling in parser classes (`BaseOutputParser`) rather than ad-hoc string parsing.
- Keep workflow/app/CLI invocation wrappers in `RunnableLambda` when introducing new orchestration boundaries.
- Keep embeddings imports compatible with `langchain-huggingface` first, then fallback only when needed.

When adding features, prefer extending the relevant module over reintroducing monolithic logic into the CLI entry file.
