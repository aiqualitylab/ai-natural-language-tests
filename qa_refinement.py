"""Test code refinement module for conversational refinement of generated tests."""

import logging
from pathlib import Path
from typing import List, Optional, Tuple

from qa_config import SYMBOLIC_RULES, get_llm, load_prompt_template

logger = logging.getLogger("ai-natural-language-tests")

FILE_HEADER_PREFIX = "// FILE: "


def strip_code_fence(text: str) -> str:
    """
    Remove code fence markers from text.
    
    Recognizes markers: ```typescript, ```javascript, ```js, ```
    If no marker is found, returns the text unchanged (stripped).
    """
    fence_markers = ["```typescript", "```javascript", "```js", "```"]
    marker = next((item for item in fence_markers if item in text), None)
    if marker is None:
        return text.strip()
    return text.split(marker, 1)[1].split("```", 1)[0].strip()


def split_file_sections(code_text: str) -> List[Tuple[str, str]]:
    """
    Split code text into (filepath, code) tuples based on FILE_HEADER_PREFIX lines.
    
    Returns a list of (filepath, code) tuples in order.
    If no headers are found, returns an empty list (indicating bare snippet, not multi-file).
    """
    lines = code_text.splitlines(keepends=True)
    sections = []
    current_path = None
    current_code_lines = []

    for line in lines:
        if line.strip().startswith(FILE_HEADER_PREFIX):
            # Save previous section if exists
            if current_path is not None:
                current_code = "".join(current_code_lines).rstrip()
                sections.append((current_path, current_code))
            
            # Extract new path
            current_path = line.strip()[len(FILE_HEADER_PREFIX):].strip()
            current_code_lines = []
        else:
            if current_path is not None:
                current_code_lines.append(line)

    # Save last section
    if current_path is not None:
        current_code = "".join(current_code_lines).rstrip()
        sections.append((current_path, current_code))

    return sections


def join_file_sections(sections: List[Tuple[str, str]]) -> str:
    """
    Join (filepath, code) tuples back into a single code panel text.
    
    Reconstructs the format: FILE_HEADER_PREFIX + filepath + newline + code
    """
    chunks = []
    for filepath, code in sections:
        chunks.append(f"{FILE_HEADER_PREFIX}{filepath}\n{code}")
    return "\n\n".join(chunks)


def refine_tests(
    current_code: str,
    instruction: str,
    framework: str,
    llm_provider: str = "openai",
) -> Tuple[str, List[Tuple[str, bool]]]:
    """
    Refine generated test code based on a user instruction.
    
    Args:
        current_code: The current code panel text (may include FILE_HEADER_PREFIX lines).
        instruction: Natural language instruction describing the refinement.
        framework: The test framework ('cypress', 'playwright', 'webdriverio', 'appium').
        llm_provider: LLM provider to use ('openai', 'anthropic', 'google').
    
    Returns:
        Tuple of (revised_panel_text, files_written)
        - revised_panel_text: The updated code for the panel.
        - files_written: List of (filepath, success) tuples indicating which files were written.
    
    Raises:
        ValueError: If the refined output is invalid (missing files, empty sections, etc.).
    """
    if not current_code.strip():
        raise ValueError("No current code to refine. Generate tests first.")

    if not instruction.strip():
        raise ValueError("Instruction is empty. Describe the change you want.")

    # Parse original sections
    original_sections = split_file_sections(current_code)
    has_file_headers = len(original_sections) > 0

    # Build the refinement prompt
    prompt = load_prompt_template(
        "test_refinement.yaml",
        framework=framework,
        instruction=instruction,
        current_code=current_code,
        symbolic_rules=SYMBOLIC_RULES,
    )

    logger.info(f"Refining tests with instruction: {instruction[:100]}...")
    llm = get_llm(llm_provider)
    response = llm.invoke(prompt)
    response_content = response.content if hasattr(response, 'content') else str(response)

    # Extract code from fence
    revised_code = strip_code_fence(response_content)

    # Parse revised sections
    revised_sections = split_file_sections(revised_code)

    # SAFETY RULE 1: If original had file headers, revised must have same files in same order
    if has_file_headers:
        original_paths = [path for path, _ in original_sections]
        revised_paths = [path for path, _ in revised_sections]

        if original_paths != revised_paths:
            raise ValueError(
                f"Refinement error: File list mismatch. "
                f"Original: {original_paths}, Revised: {revised_paths}. "
                f"The LLM must not add, remove, or rename files."
            )

    # SAFETY RULE 2: No empty file sections
    for filepath, code in revised_sections:
        if not code.strip():
            raise ValueError(f"Refinement error: Empty code section for {filepath}. All files must have content.")

    # Write files to disk (if original had headers)
    files_written: List[Tuple[str, bool]] = []

    if has_file_headers:
        for filepath, code in revised_sections:
            file_path = Path(filepath)

            # SAFETY RULE 3: Only write to existing paths
            if not file_path.exists():
                logger.warning(f"File does not exist on disk, skipping write: {filepath}")
                files_written.append((filepath, False))
                continue

            try:
                file_path.write_text(code, encoding="utf-8")
                logger.info(f"Updated: {filepath}")
                files_written.append((filepath, True))
            except Exception as e:
                logger.error(f"Failed to write {filepath}: {e}")
                files_written.append((filepath, False))

    # Return revised panel text (reconstruct with headers if original had them)
    if has_file_headers:
        revised_panel_text = join_file_sections(revised_sections)
    else:
        # SAFETY RULE 4: Bare snippet (no headers) — return revision for panel only, no disk writes
        revised_panel_text = revised_code

    return revised_panel_text, files_written
