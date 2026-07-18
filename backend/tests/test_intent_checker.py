"""Tests for the pre-flight intent checker (LLM mocked)."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.intent_checker import (
    IntentCheckResult,
    _LLMIntentCheck,
    _keyword_fidelity,
    check_generation_intent,
)


def _mock_llm(result: _LLMIntentCheck):
    client = MagicMock()
    client.call_openai_api_structured.return_value = (result, {"total_tokens": 100})
    return patch("app.services.intent_checker.PromptOpenAI", return_value=client)


# ---------------------------------------------------------------------------
# Deterministic URL extraction + fidelity
# ---------------------------------------------------------------------------

def test_url_regex_extraction():
    prompt = ("Create a comprehensive website just like this - https://joof-murex.vercel.app\n"
              "It should be a complete replica of it with the logo and the colors theme and font")
    with _mock_llm(_LLMIntentCheck(needs_clarification=False, fidelity="replica")):
        result, _ = check_generation_intent(prompt, has_attachments=False)
    assert result.url_refs == ["https://joof-murex.vercel.app"]
    assert result.fidelity == "replica"


def test_trailing_punctuation_stripped():
    with _mock_llm(_LLMIntentCheck(needs_clarification=False)):
        result, _ = check_generation_intent(
            "make it like (https://example.com/page).", has_attachments=False)
    assert result.url_refs == ["https://example.com/page"]


def test_keyword_fidelity():
    assert _keyword_fidelity("a complete replica of it") == "replica"
    assert _keyword_fidelity("just like this site") == "replica"
    assert _keyword_fidelity("something similar to stripe.com") == "inspired"


def test_url_with_none_fidelity_falls_back_to_wording():
    with _mock_llm(_LLMIntentCheck(needs_clarification=False, fidelity="none")):
        result, _ = check_generation_intent(
            "clone https://example.com for my shop", has_attachments=False)
    assert result.fidelity == "replica"


# ---------------------------------------------------------------------------
# Guardrails
# ---------------------------------------------------------------------------

def test_attachment_present_drops_asset_clarification():
    llm = _LLMIntentCheck(
        needs_clarification=True, question="Could you attach your logo?",
        wants_attachment=True, missing_deps=["logo"])
    with _mock_llm(llm):
        result, _ = check_generation_intent("use my logo everywhere", has_attachments=True)
    assert result.needs_clarification is False
    assert result.question is None


def test_missing_logo_without_attachment_asks():
    llm = _LLMIntentCheck(
        needs_clarification=True, question="Could you attach your logo?",
        wants_attachment=True, missing_deps=["logo"])
    with _mock_llm(llm):
        result, _ = check_generation_intent("use my logo everywhere", has_attachments=False)
    assert result.needs_clarification is True
    assert result.wants_attachment is True


def test_vague_prompt_clarification_distrusted():
    """LLM wrongly asks about a vague prompt with no URL/asset language — guardrail drops it."""
    llm = _LLMIntentCheck(
        needs_clarification=True, question="What kind of business is it?",
        wants_attachment=False, missing_deps=["business_type"])
    with _mock_llm(llm):
        result, _ = check_generation_intent("a website for my business", has_attachments=False)
    assert result.needs_clarification is False


def test_llm_failure_fails_open():
    client = MagicMock()
    client.call_openai_api_structured.side_effect = RuntimeError("api down")
    with patch("app.services.intent_checker.PromptOpenAI", return_value=client):
        result, _ = check_generation_intent(
            "replica of https://example.com please", has_attachments=False)
    assert result.needs_clarification is False
    assert result.url_refs == ["https://example.com"]
    assert result.fidelity == "replica"


# ---------------------------------------------------------------------------
# URL ingestion disabled (clarify-only mode) — no LLM call at all
# ---------------------------------------------------------------------------

def test_can_read_urls_false_asks_for_screenshot():
    with patch("app.services.intent_checker.PromptOpenAI") as mock_client:
        result, _ = check_generation_intent(
            "replica of https://example.com", has_attachments=False, can_read_urls=False)
    mock_client.assert_not_called()
    assert result.needs_clarification is True
    assert result.wants_attachment is True
    assert "https://example.com" in result.question
    assert "screenshot" in result.question


def test_can_read_urls_false_with_attachment_proceeds():
    with patch("app.services.intent_checker.PromptOpenAI") as mock_client:
        result, _ = check_generation_intent(
            "replica of https://example.com", has_attachments=True, can_read_urls=False)
    mock_client.assert_not_called()
    assert result.needs_clarification is False
    assert result.fidelity == "replica"


# ---------------------------------------------------------------------------
# Prompt polish
# ---------------------------------------------------------------------------

def test_polished_prompt_round_trips():
    llm = _LLMIntentCheck(
        needs_clarification=False,
        polished_prompt="Create a modern portfolio website...\n### Design System & Theme:\n- Dark mode")
    with _mock_llm(llm):
        result, _ = check_generation_intent("a modern portfolio website", has_attachments=False)
    assert result.polished_prompt.startswith("Create a modern portfolio website")


def test_empty_polished_prompt_normalized_to_none():
    with _mock_llm(_LLMIntentCheck(needs_clarification=False, polished_prompt="   ")):
        result, _ = check_generation_intent("a bakery site", has_attachments=False)
    assert result.polished_prompt is None


def test_clarification_response_included_in_llm_input():
    client = MagicMock()
    client.call_openai_api_structured.return_value = (
        _LLMIntentCheck(needs_clarification=False, polished_prompt="spec"), {})
    with patch("app.services.intent_checker.PromptOpenAI", return_value=client):
        check_generation_intent(
            "use my logo", has_attachments=True,
            clarification_response="here is the logo, make it blue")
    user_prompt = client.call_openai_api_structured.call_args[0][1]
    assert "here is the logo, make it blue" in user_prompt


def test_llm_failure_leaves_polished_prompt_none():
    client = MagicMock()
    client.call_openai_api_structured.side_effect = RuntimeError("api down")
    with patch("app.services.intent_checker.PromptOpenAI", return_value=client):
        result, _ = check_generation_intent("a portfolio site", has_attachments=False)
    assert result.polished_prompt is None


def test_clarify_only_mode_has_no_polish():
    with patch("app.services.intent_checker.PromptOpenAI"):
        result, _ = check_generation_intent(
            "replica of https://example.com", has_attachments=False, can_read_urls=False)
    assert result.polished_prompt is None
