"""Fetch hosted images and encode them as base64 data URLs for multimodal LLM calls."""

import base64
import logging
from typing import List, Optional

import httpx

logger = logging.getLogger(__name__)

# Keep multimodal payloads sane
MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_IMAGES_PER_CALL = 4

_MIME_BY_SUFFIX = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


def _guess_mime(url: str, content_type: Optional[str]) -> str:
    if content_type and content_type.startswith("image/"):
        return content_type.split(";")[0]
    lowered = url.lower().split("?")[0]
    for suffix, mime in _MIME_BY_SUFFIX.items():
        if lowered.endswith(suffix):
            return mime
    return "image/png"


async def fetch_images_as_data_urls(urls: List[str]) -> List[str]:
    """Download image URLs (e.g. Supabase public URLs) and return base64 data URLs.

    Gemini's OpenAI-compatible endpoint reliably accepts inline base64;
    remote URL fetching is not guaranteed. Failures are skipped, not fatal.
    """
    data_urls: List[str] = []
    async with httpx.AsyncClient(timeout=30) as client:
        for url in urls[:MAX_IMAGES_PER_CALL]:
            try:
                response = await client.get(url)
                response.raise_for_status()
                content = response.content
                if len(content) > MAX_IMAGE_BYTES:
                    logger.warning(f"Skipping oversized image ({len(content)} bytes): {url}")
                    continue
                mime = _guess_mime(url, response.headers.get("content-type"))
                encoded = base64.b64encode(content).decode("ascii")
                data_urls.append(f"data:{mime};base64,{encoded}")
            except Exception as e:
                logger.warning(f"Failed to fetch image for multimodal call: {url} ({e})")
    return data_urls
