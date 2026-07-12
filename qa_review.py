"""AI-powered test code review module."""

import json
import logging
import re
from typing import Any, Dict

from qa_config import get_llm, load_prompt_template, load_prompt_system


SCORE_KEYS = ("assertions", "selectors", "structure", "determinism")
logger = logging.getLogger("ai-natural-language-tests")


def _extract_json(text: str) -> Dict[str, Any]:
    """
    Extract JSON from LLM response text.
    
    Tolerant parsing: strip whitespace, search for {..} block if not JSON-starting,
    handle code fences gracefully.
    
    Raises ValueError if no valid JSON found.
    """
    text = text.strip()
    
    if not text:
        raise ValueError("LLM response is empty.")
    
    # Try direct JSON parsing first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Search for {..} block in case it's wrapped in prose or code fences
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        json_text = match.group(0)
        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Found JSON block but failed to parse: {e}") from e
    
    raise ValueError(f"No valid JSON found in response: {text[:100]}...")


def _normalize(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize and defensively recompute the review verdict.
    
    - Clamps scores to 0–5.
    - RECOMPUTES verdict: "needs_work" if any score ≤ 2, else "approve".
    - Caps issues at 5.
    - Clears refinement_instruction if verdict is "approve".
    """
    if not isinstance(raw, dict):
        raise ValueError(f"Expected dict, got {type(raw)}")
    
    # Extract and clamp scores
    raw_scores = raw.get("scores", {})
    if not isinstance(raw_scores, dict):
        raw_scores = {}
    
    scores = {}
    for key in SCORE_KEYS:
        val = raw_scores.get(key)
        # Coerce to int, handle garbage
        try:
            score = int(val) if val is not None else 0
        except (ValueError, TypeError):
            score = 0
        # Clamp to 0–5
        scores[key] = max(0, min(5, score))
    
    # RECOMPUTE verdict: needs_work if any score ≤ 2
    verdict = "needs_work" if any(s <= 2 for s in scores.values()) else "approve"
    
    # Extract and cap issues
    issues = raw.get("issues", [])
    if not isinstance(issues, list):
        issues = []
    issues = [str(issue) for issue in issues[:5]]
    
    # Extract refinement instruction
    refinement = raw.get("refinement_instruction", "")
    if not isinstance(refinement, str):
        refinement = ""
    
    # Clear refinement if verdict is approve
    if verdict == "approve":
        refinement = ""
    
    return {
        "scores": scores,
        "verdict": verdict,
        "issues": issues,
        "refinement_instruction": refinement,
    }


def review_test(code: str, framework: str, llm_provider: str = "openai") -> Dict[str, Any]:
    """
    Review generated test code using LLM.
    
    Args:
        code: Generated test code (may contain multiple files with // FILE: headers).
        framework: Test framework (cypress, playwright, webdriverio, appium).
        llm_provider: LLM provider (openai, anthropic, google).
    
    Returns:
        Normalized review dictionary with scores, verdict, issues, and refinement_instruction.
    
    Raises:
        ValueError: If LLM response cannot be parsed.
    """
    if not code.strip():
        raise ValueError("Code is empty.")
    
    # Build prompt
    prompt_text = load_prompt_template("test_review.yaml", framework=framework, code=code)
    system_text = load_prompt_system("test_review.yaml")
    
    # Call LLM
    llm = get_llm(llm_provider)
    from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
    
    response: BaseMessage = llm.invoke([
        SystemMessage(content=system_text),
        HumanMessage(content=prompt_text),
    ])
    
    # Extract and normalize
    raw_result = _extract_json(response.content)
    normalized = _normalize(raw_result)
    
    logger.info(f"Review complete: {normalized['verdict']} ({normalized['scores']})")
    
    return normalized
