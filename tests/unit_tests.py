"""
Tests core, dependency-free logic from qa_config, qa_workflow, and ragas_nlp_evaluator.
No network calls, no LLM API calls, no API keys required.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the modules under test
from qa_config import FRAMEWORK_CONFIG
from qa_workflow import CodeFenceParser, extract_code_fence, get_test_filepath


class TestFrameworkConfig:
    """Test framework configuration loading and mapping."""

    def test_framework_config_has_all_expected_frameworks(self):
        """Verify FRAMEWORK_CONFIG contains all required frameworks."""
        expected = {"cypress", "playwright", "webdriverio", "appium"}
        assert set(FRAMEWORK_CONFIG.keys()) == expected

    def test_framework_file_extensions_mapping(self):
        """Verify each framework maps to the correct file extension."""
        extensions = {
            "cypress": ".cy.js",
            "playwright": ".spec.ts",
            "webdriverio": ".spec.js",
            "appium": ".spec.js",
        }
        for framework, expected_ext in extensions.items():
            assert FRAMEWORK_CONFIG[framework]["file_ext"] == expected_ext

    def test_framework_default_output_directories(self):
        """Verify each framework has a default output directory defined."""
        for framework, config in FRAMEWORK_CONFIG.items():
            assert "default_output" in config
            assert isinstance(config["default_output"], str)
            assert len(config["default_output"]) > 0


class TestCodeFenceParser:
    """Test markdown code fence parsing."""

    def test_parser_extracts_javascript_code(self):
        """Parser should extract content between ```javascript markers."""
        parser = CodeFenceParser()
        text = '```javascript\nconst x = 42;\nconsole.log(x);\n```'
        result = parser.parse(text)
        assert result.strip() == "const x = 42;\nconsole.log(x);"

    def test_parser_extracts_typescript_code(self):
        """Parser should extract content between ```typescript markers."""
        parser = CodeFenceParser()
        text = '```typescript\nconst name: string = "test";\n```'
        result = parser.parse(text)
        assert result.strip() == 'const name: string = "test";'

    def test_parser_handles_js_shorthand(self):
        """Parser should handle ```js shorthand."""
        parser = CodeFenceParser()
        text = '```js\nfunction test() {}\n```'
        result = parser.parse(text)
        assert result.strip() == "function test() {}"

    def test_parser_fallback_when_no_fence_found(self):
        """Parser should return original text if no fence marker found."""
        parser = CodeFenceParser()
        text = "no code fence here"
        result = parser.parse(text)
        assert result == text

    def test_parser_handles_pretext_and_posttext(self):
        """Parser should ignore text before and after fence."""
        parser = CodeFenceParser()
        text = 'Here is code:\n```javascript\nconst x = 1;\n```\nEnd.'
        result = parser.parse(text)
        assert result.strip() == "const x = 1;"


class TestExtractCodeFence:
    """Test the extract_code_fence wrapper function."""

    def test_extract_code_fence_with_javascript(self):
        """extract_code_fence should use CodeFenceParser to extract JS code."""
        text = 'Here is JavaScript:\n```javascript\nconst result = 42;\n```'
        extracted = extract_code_fence(text)
        assert "const result = 42;" in extracted

    def test_extract_code_fence_returns_string(self):
        """extract_code_fence should always return a string."""
        text = '```javascript\ntest\n```'
        result = extract_code_fence(text)
        assert isinstance(result, str)


class TestGetTestFilepath:
    """Test test file path generation."""

    def test_filepath_uses_correct_extension_cypress(self):
        """Generated path should use correct extension for Cypress."""
        with patch("os.makedirs"):
            filepath, _, _ = get_test_filepath("cypress", "cypress/e2e", False, 1, "test requirement")
            assert filepath.endswith(".cy.js")

    def test_filepath_uses_correct_extension_playwright(self):
        """Generated path should use correct extension for Playwright."""
        with patch("os.makedirs"):
            filepath, _, _ = get_test_filepath("playwright", "tests", False, 1, "test requirement")
            assert filepath.endswith(".spec.ts")

    def test_filepath_includes_index_number(self):
        """Generated path should include test index number."""
        with patch("os.makedirs"):
            filepath, _, _ = get_test_filepath("cypress", "cypress/e2e", False, 5, "test requirement")
            assert "05_" in filepath

    def test_filepath_includes_generated_folder_when_not_prompt_mode(self):
        """Generated path should include 'generated' folder when not in prompt mode."""
        with patch("os.makedirs"):
            _, _, folder_name = get_test_filepath("cypress", "cypress/e2e", False, 1, "test")
            assert folder_name == "generated"

    def test_filepath_includes_prompt_powered_folder_when_prompt_mode(self):
        """Generated path should include 'prompt-powered' folder when in prompt mode."""
        with patch("os.makedirs"):
            _, _, folder_name = get_test_filepath("cypress", "cypress/e2e", True, 1, "test")
            assert folder_name == "prompt-powered"

    def test_filepath_includes_appium_folder_for_appium_prompt_mode(self):
        """Appium tests in prompt mode should use 'appium-tests' folder."""
        with patch("os.makedirs"):
            _, _, folder_name = get_test_filepath("appium", "webdriverio/tests", True, 1, "test")
            assert folder_name == "appium-tests"

    def test_filepath_returns_tuple_of_three(self):
        """get_test_filepath should return a tuple of (filepath, filename, folder_name)."""
        with patch("os.makedirs"):
            result = get_test_filepath("cypress", "cypress/e2e", False, 1, "test")
            assert isinstance(result, tuple)
            assert len(result) == 3
            filepath, filename, folder = result
            assert isinstance(filepath, str)
            assert isinstance(filename, str)
            assert isinstance(folder, str)


class TestScoreAverageCalculation:
    """Test the SCORE_AVERAGE lambda from ragas_nlp_evaluator."""

    def test_score_average_calculates_mean(self):
        """SCORE_AVERAGE should calculate the mean of a list."""
        from ragas_nlp_evaluator import SCORE_AVERAGE
        
        values = [0.8, 0.9, 1.0]
        result = SCORE_AVERAGE.invoke(values)
        assert result == 0.9

    def test_score_average_rounds_to_two_decimals(self):
        """SCORE_AVERAGE should round result to 2 decimal places."""
        from ragas_nlp_evaluator import SCORE_AVERAGE
        
        values = [0.85, 0.87, 0.88]
        result = SCORE_AVERAGE.invoke(values)
        assert isinstance(result, float)
        # Result should be rounded to 2 decimals
        assert len(str(result).split(".")[-1]) <= 2

    def test_score_average_handles_empty_list(self):
        """SCORE_AVERAGE should return 0.0 for empty list."""
        from ragas_nlp_evaluator import SCORE_AVERAGE
        
        result = SCORE_AVERAGE.invoke([])
        assert result == 0.0

    def test_score_average_handles_single_value(self):
        """SCORE_AVERAGE should return the value itself for single-element list."""
        from ragas_nlp_evaluator import SCORE_AVERAGE
        
        result = SCORE_AVERAGE.invoke([0.75])
        assert result == 0.75


class TestLoadSamples:
    """Test the load_samples function from ragas_nlp_evaluator (with mocking)."""

    def test_load_samples_parses_json(self):
        """load_samples should parse JSON from file."""
        from ragas_nlp_evaluator import load_samples
        
        # Create temp file with delete=False, then close before reading
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            test_data = [
                {"name": "test1", "response": "answer", "reference": "expected"},
                {"name": "test2", "response": "answer2", "reference": "expected2"},
            ]
            json.dump(test_data, f)
            temp_path = f.name
        
        try:
            result = load_samples(temp_path)
            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0]["name"] == "test1"
        finally:
            try:
                os.unlink(temp_path)
            except PermissionError:
                pass 

    def test_load_samples_preserves_structure(self):
        """load_samples should preserve the JSON structure."""
        from ragas_nlp_evaluator import load_samples
        
        # Create temp file with delete=False, then close before reading
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            test_data = {
                "samples": [
                    {"response": "test_response", "reference": "test_reference"}
                ]
            }
            json.dump(test_data, f)
            temp_path = f.name
        
        try:
            result = load_samples(temp_path)
            assert isinstance(result, dict)
            assert "samples" in result
        finally:
            try:
                os.unlink(temp_path)
            except PermissionError:
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
