import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from langchain_openai import ChatOpenAI

try:
    from langchain_anthropic import ChatAnthropic
except ImportError:
    ChatAnthropic = None

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None


PROMPT_SPEC_DIR = Path(__file__).parent / "prompt_specs"
VECTOR_DB_DIR = Path(__file__).parent / "vector_db"
HTML_DEBUG_DIR = VECTOR_DB_DIR / "html_analysis_debug"

LLM_CONFIG = {
    "openai": {"name": "OpenAI (ChatGPT)", "model": "gpt-4o-mini", "provider": "openai"},
    "anthropic": {"name": "Anthropic (Claude)", "model": "claude-3-5-sonnet-20241022", "provider": "anthropic"},
    "google": {"name": "Google (Gemini)", "model": "gemini-2.0-flash", "provider": "google"},
}

DEFAULT_LLM = "openai"

ALLOWED_FAILURE_CATEGORIES = {
    "SELECTOR",
    "TIMING",
    "ASSERTION",
    "NETWORK",
    "STATE",
    "NAVIGATION",
    "INTERACTION",
    "CONFIGURATION",
}

SYMBOLIC_RULES = """
SELECTOR CONVENTIONS (MANDATORY):
- ALWAYS prefer data-testid attributes: [data-testid="submit-button"]
- Use data-cy as second choice for Cypress-specific attributes: [data-cy="login-form"]
- Use aria-label or role-based selectors as third choice: [aria-label="Password"]
- Use CSS class or ID only when no semantic alternative exists
- NEVER use XPath selectors (//, .//tag[@attr])
- NEVER use :nth-child(), :nth-of-type(), or positional pseudo-selectors
- NEVER chain more than 2 CSS descendant combinators (e.g. .a .b .c is the limit)
- NEVER use inline style attribute selectors (e.g. [style="color: red"])

ASSERTION REQUIREMENTS (MANDATORY):
- Every test MUST have at least one explicit assertion (not just an action)
- Assertions must check observable outcomes: visibility, text content, URL change, or element state
- NEVER assert on implementation details such as CSS class names that carry no semantic meaning
- Use existence + visibility assertions together: .should('exist') and .should('be.visible') for Cypress
- For success flows: assert that a success indicator is visible OR the URL changed away from the action page
- For error flows: assert that an error indicator is visible with non-empty text
- NEVER leave an assertion as a TODO or placeholder comment
"""

FRAMEWORK_CONFIG = {
    "cypress": {
        "name": "Cypress",
        "file_ext": ".cy.js",
        "default_output": "cypress/e2e",
        "run_cmd": "npx cypress run --spec",
        "code_fence": "javascript",
        "prompt_file_standard": "test_generation_traditional.yaml",
        "prompt_file_prompt": "test_generation_prompt_powered.yaml",
        "supports_prompt_mode": True,
    },
    "playwright": {
        "name": "Playwright",
        "file_ext": ".spec.ts",
        "default_output": "tests",
        "run_cmd": "npx playwright test",
        "code_fence": "typescript",
        "prompt_file_standard": "test_generation_playwright.yaml",
        "supports_prompt_mode": False,
    },
    "webdriverio": {
        "name": "WebdriverIO",
        "file_ext": ".spec.js",
        "default_output": "webdriverio/tests",
        "run_cmd": "npx wdio run wdio.conf.js",
        "code_fence": "javascript",
        "prompt_file_standard": "test_generation_webdriverio.yaml",
        "supports_prompt_mode": False,
    },
}


def load_prompt_spec(filename: str, required_keys: Optional[List[str]] = None) -> Dict[str, Any]:
    logging.getLogger("ai-natural-language-tests").info(f"Loading prompt spec: {filename}")
    spec_path = PROMPT_SPEC_DIR / filename
    with open(spec_path, "r", encoding="utf-8") as file:
        spec = yaml.safe_load(file) or {}

    missing_required = [key for key in (required_keys or []) if key not in spec]
    if missing_required:
        raise ValueError(f"Prompt spec '{filename}' is missing required key '{missing_required[0]}'")

    for key in ("name", "version", "metadata"):
        if key not in spec:
            logging.getLogger("ai-natural-language-tests").warning(
                f"Prompt spec '{filename}' is missing recommended key '{key}'"
            )

    return spec


def load_prompt_template(filename: str, **variables: Any) -> str:
    spec = load_prompt_spec(filename, required_keys=["template"])
    template = str(spec.get("template", ""))
    return template.format(**variables)


def load_prompt_system(filename: str) -> str:
    spec = load_prompt_spec(filename)
    return str(spec.get("system", ""))


def _get_provider_constructor(provider: str) -> Any:
    providers = {
        "openai": lambda cfg: ChatOpenAI(model=cfg["model"], temperature=0),
        "anthropic": lambda cfg: ChatAnthropic(model=cfg["model"], temperature=0) if ChatAnthropic else None,
        "google": lambda cfg: ChatGoogleGenerativeAI(model=cfg["model"], temperature=0) if ChatGoogleGenerativeAI else None,
    }
    return providers.get(provider, lambda cfg: ChatOpenAI(model=cfg["model"], temperature=0))


def get_llm(provider: str = DEFAULT_LLM) -> Any:
    if provider not in LLM_CONFIG:
        logging.getLogger("ai-natural-language-tests").warning(
            f"Unknown provider '{provider}', using default {DEFAULT_LLM}"
        )
        provider = DEFAULT_LLM

    config = LLM_CONFIG[provider]
    ctor = _get_provider_constructor(provider)
    result = ctor(config)

    if result is None:
        logging.getLogger("ai-natural-language-tests").warning(
            f"{provider} not installed, falling back to OpenAI"
        )
        return ChatOpenAI(model=LLM_CONFIG[DEFAULT_LLM]["model"], temperature=0)

    return result