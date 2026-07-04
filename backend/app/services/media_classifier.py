"""Classify user-uploaded images for generation: logo, product photo, or style reference."""

import json
import logging
import re
from typing import Any, Dict, List, Optional

from app.config import settings
from app.services.prompt_open_ai import PromptOpenAI
from app.utils.image_loader import fetch_images_as_data_urls

logger = logging.getLogger(__name__)

VALID_KINDS = {"logo", "product_photo", "style_reference", "other"}


async def build_media_context(attachments: List[Dict[str, Any]], user_prompt: str) -> Optional[str]:
    """
    Classify attached images with one multimodal call and return a prompt block
    describing how generation should use each one. Returns None when there is
    nothing usable (classification failure falls back to generic asset handling).
    """
    urls = [a["url"] for a in attachments if a.get("url")]
    if not urls:
        return None

    images = await fetch_images_as_data_urls(urls)
    if not images:
        return None
    urls = urls[:len(images)]

    classifications = _classify(images, urls, user_prompt)

    lines = []
    for i, url in enumerate(urls):
        item = classifications[i] if i < len(classifications) else {}
        kind = item.get("kind", "other")
        description = item.get("description", "user-uploaded image")
        if kind == "logo":
            lines.append(f"{i+1}. LOGO: {url} — {description}. Use this EXACT URL as the site logo in the header/nav (and footer if a logo appears there).")
        elif kind == "product_photo":
            lines.append(f"{i+1}. PRODUCT/BRAND PHOTO: {url} — {description}. Use this EXACT URL in the most relevant section (hero, products, about).")
        elif kind == "style_reference":
            lines.append(f"{i+1}. STYLE REFERENCE (do NOT embed this URL anywhere): {description}. Match this style — colors, typography, layout, mood — across the site.")
        else:
            lines.append(f"{i+1}. IMAGE: {url} — {description}. Use this EXACT URL where it fits the content best.")

    return (
        "UPLOADED MEDIA (user-provided images, publicly hosted):\n"
        + "\n".join(lines)
        + "\nFor any image marked with a URL above, use that EXACT URL — do NOT substitute Unsplash or placeholder images for it. "
        "Unsplash remains fine for other imagery the site needs."
    )


def _classify(images: List[str], urls: List[str], user_prompt: str) -> List[Dict[str, Any]]:
    """One multimodal call returning [{kind, description}] per image, in order."""
    try:
        prompt_service = PromptOpenAI(is_google=True)
        response, usage = prompt_service.call_openai_api(
            system_prompt="You classify images a user uploaded while requesting a website. Respond with ONLY valid JSON.",
            user_prompt=f"""The user is generating a website with this request:
"{user_prompt[:500]}"

They attached {len(images)} image(s), shown in order. For EACH image return an object:
- "kind": one of "logo" | "product_photo" | "style_reference" | "other"
  (style_reference = a screenshot/design they want imitated, not embedded)
- "description": one sentence covering content, dominant colors, and mood

Respond with ONLY a JSON array of {len(images)} objects, in the same order as the images.""",
            model=settings.edit_model,
            images=images,
        )
        logger.info(f"[MEDIA CLASSIFIER] usage: {usage}")
        cleaned = re.sub(r"^```(?:json)?\n?|\n?```$", "", response.strip(), flags=re.MULTILINE).strip()
        parsed = json.loads(cleaned)
        if not isinstance(parsed, list):
            raise ValueError("expected a JSON array")
        result = []
        for item in parsed:
            kind = item.get("kind") if isinstance(item, dict) else None
            result.append({
                "kind": kind if kind in VALID_KINDS else "other",
                "description": (item.get("description") if isinstance(item, dict) else None) or "user-uploaded image",
            })
        return result
    except Exception as e:
        logger.warning(f"[MEDIA CLASSIFIER] classification failed, defaulting to generic assets: {e}")
        return [{"kind": "other", "description": "user-uploaded image"} for _ in images]
