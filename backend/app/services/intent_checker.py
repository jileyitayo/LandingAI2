"""Pre-flight intent check for generation prompts.

One cheap structured LLM call that decides whether the prompt depends on
something the system cannot access (an unreadable URL, "use my logo" with
nothing attached, a contradictory/non-website request). Deliberately high
bar: plain vagueness must NEVER trigger a clarification — filling gaps
tastefully is the product's job.
"""

import logging
import re
from typing import List, Literal, Optional, Tuple

from pydantic import BaseModel, Field

from app.config import settings
from app.services.prompt_open_ai import PromptOpenAI

logger = logging.getLogger(__name__)

URL_RE = re.compile(r"https?://[^\s\"'<>)\]]+")

_REPLICA_WORDS = ("replica", "clone", "copy of", "copy it", "exact", "identical", "duplicate", "just like")
_ASSET_WORDS = ("logo", "photo", "image", "picture", "screenshot", "attach", "headshot")


class IntentCheckResult(BaseModel):
    needs_clarification: bool = False
    question: Optional[str] = None
    wants_attachment: bool = False
    url_refs: List[str] = Field(default_factory=list)
    fidelity: Literal["replica", "inspired", "none"] = "none"
    missing_deps: List[str] = Field(default_factory=list)


class _LLMIntentCheck(BaseModel):
    """Schema for the LLM call — url_refs are extracted deterministically, never by the LLM."""
    needs_clarification: bool
    question: Optional[str] = None
    wants_attachment: bool = False
    fidelity: Literal["replica", "inspired", "none"] = "none"
    missing_deps: List[str] = Field(default_factory=list)


_SYSTEM_PROMPT = """You review a user's website-generation prompt before generation starts.
Your ONLY job is to detect prompts that depend on something the system cannot access, and to
classify how faithfully a referenced website should be followed.

Set needs_clarification=true ONLY in these cases:
1. The prompt requires a specific user asset that was NOT provided — e.g. "use my logo",
   "with our team photos" — and has_attachments is false. Set wants_attachment=true and ask
   for the asset in one short, friendly question. EXCEPTION: when the asset belongs to a
   website the prompt references (e.g. "replicate this site with its logo and colors") and
   can_read_urls is true, do NOT ask — the system fetches it from that site.
2. The prompt is self-contradictory or clearly not a website request (e.g. "write me a poem").
3. can_read_urls is false AND the prompt depends on the content/design of a referenced URL.

NEVER set needs_clarification=true for:
- Vague prompts ("a site for my business") — vagueness is fine, generation fills the gaps.
- Missing business details, missing page lists, missing style preferences.
- A URL reference by itself when can_read_urls is true — the system will fetch it.

fidelity (only meaningful when the prompt references a URL):
- "replica": the user wants a faithful copy — words like replica, clone, copy, exact, identical, "just like".
- "inspired": the user wants something similar — words like like, similar to, inspired by, in the style of.
- "none": no URL referenced.

missing_deps: short slugs of what is missing (e.g. "logo", "product_photos"). Empty when nothing is missing.
The question, when present, must be ONE sentence, addressed to the user, ending in a question mark."""


def _templated_url_question(url: str) -> str:
    return (
        f"I couldn't read enough of {url} to copy its design — could you attach a "
        "screenshot of the site, or describe its colors, fonts and sections?"
    )


def check_generation_intent(
    prompt: str,
    has_attachments: bool,
    can_read_urls: bool = True,
) -> Tuple[IntentCheckResult, dict]:
    """Sync (PromptOpenAI is sync) — call via asyncio.to_thread. Returns (result, usage)."""
    url_refs = [u.rstrip(").,;\"'") for u in URL_RE.findall(prompt)]
    usage: dict = {}

    # URL ingestion disabled: deterministic clarify-only mode, no LLM needed.
    if url_refs and not can_read_urls:
        return (
            IntentCheckResult(
                needs_clarification=not has_attachments,
                question=_templated_url_question(url_refs[0]) if not has_attachments else None,
                wants_attachment=not has_attachments,
                url_refs=url_refs,
                fidelity=_keyword_fidelity(prompt),
                missing_deps=["reference_site_screenshot"] if not has_attachments else [],
            ),
            usage,
        )

    try:
        client = PromptOpenAI(is_google=True)
        client.set_max_completion_tokens(1000)
        user_prompt = (
            f'User prompt:\n"{prompt[:2000]}"\n\n'
            f"has_attachments: {has_attachments}\n"
            f"can_read_urls: {can_read_urls}\n"
            f"URLs referenced (extracted separately, do not repeat them): {len(url_refs)}"
        )
        llm_result, usage = client.call_openai_api_structured(
            _SYSTEM_PROMPT, user_prompt, _LLMIntentCheck, model=settings.analysis_model
        )
        result = IntentCheckResult(
            needs_clarification=llm_result.needs_clarification,
            question=llm_result.question,
            wants_attachment=llm_result.wants_attachment,
            url_refs=url_refs,
            fidelity=llm_result.fidelity,
            missing_deps=llm_result.missing_deps,
        )
    except Exception as e:
        # Fail open: intent check must never block generation.
        logger.warning(f"[PREFLIGHT] intent check failed, proceeding without: {e}")
        result = IntentCheckResult(url_refs=url_refs)

    # Deterministic guardrails against false positives.
    if result.needs_clarification:
        if has_attachments and result.wants_attachment:
            logger.info("[PREFLIGHT] guardrail: attachments present, dropping asset clarification")
            result.needs_clarification = False
            result.question = None
            result.wants_attachment = False
        elif not url_refs and not any(w in prompt.lower() for w in _ASSET_WORDS):
            # No URL and no asset language — distrust a clarify verdict unless the
            # prompt is a clear non-website request (keep those).
            if "non_website" not in result.missing_deps and "contradiction" not in result.missing_deps:
                logger.info(
                    f"[PREFLIGHT] guardrail: distrusting clarification for prompt without "
                    f"URLs/asset keywords (question was: {result.question!r})"
                )
                result.needs_clarification = False
                result.question = None
                result.wants_attachment = False
    if result.needs_clarification and not result.question:
        result.needs_clarification = False

    # A referenced URL always has a fidelity; default to the user's wording.
    if url_refs and result.fidelity == "none":
        result.fidelity = _keyword_fidelity(prompt)

    return result, usage


def _keyword_fidelity(prompt: str) -> Literal["replica", "inspired"]:
    lowered = prompt.lower()
    return "replica" if any(w in lowered for w in _REPLICA_WORDS) else "inspired"
