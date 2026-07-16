"""
Thumbnail Service
Captures a small preview screenshot of a deployed site (via ScreenshotOne)
and stores it in the project-media bucket for the dashboard cards.
"""

import asyncio
import logging
import time

import httpx

from app.config import settings
from app.utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

MEDIA_BUCKET = "project-media"
SCREENSHOT_API_URL = "https://api.screenshotone.com/take"

# 16:9 above-the-fold capture, resized down for the dashboard card
VIEWPORT_WIDTH = 1280
VIEWPORT_HEIGHT = 720
THUMBNAIL_WIDTH = 400
THUMBNAIL_HEIGHT = 225


async def capture_thumbnail(
    project_id: str,
    user_id: str,
    deployment_url: str,
    delay_s: float = 7.0,
) -> None:
    """
    Best-effort: screenshot the deployed site and save its public URL to
    projects.thumbnail_url. Never raises — a failed capture just leaves the
    dashboard placeholder in place until the next publish.

    delay_s gives a freshly deployed Vercel URL time to become reachable;
    the backfill script passes 0.
    """
    if not settings.screenshotone_access_key:
        logger.debug(
            f"SCREENSHOTONE_ACCESS_KEY not set; skipping thumbnail for project {project_id}"
        )
        return

    try:
        if delay_s > 0:
            await asyncio.sleep(delay_s)

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                SCREENSHOT_API_URL,
                params={
                    "access_key": settings.screenshotone_access_key,
                    "url": deployment_url,
                    "viewport_width": VIEWPORT_WIDTH,
                    "viewport_height": VIEWPORT_HEIGHT,
                    "image_width": THUMBNAIL_WIDTH,
                    "image_height": THUMBNAIL_HEIGHT,
                    "format": "jpg",
                    "block_cookie_banners": "true",
                },
            )

        if response.status_code != 200:
            logger.warning(
                f"Screenshot capture failed for project {project_id} "
                f"({deployment_url}): HTTP {response.status_code} {response.text[:200]}"
            )
            return

        supabase = get_supabase_client()

        # Stable per-project path (keeps the bucket's {user_id}/... convention);
        # overwritten on every publish so storage never grows
        storage_path = f"{user_id}/thumbnails/{project_id}.jpg"
        supabase.storage.from_(MEDIA_BUCKET).upload(
            path=storage_path,
            file=response.content,
            file_options={"content-type": "image/jpeg", "upsert": "true"},
        )

        public_url = supabase.storage.from_(MEDIA_BUCKET).get_public_url(storage_path)
        # Supabase appends a trailing '?' to public URLs sometimes; normalize
        public_url = public_url.rstrip("?")
        # The path never changes, so bust browser/CDN caches per publish
        thumbnail_url = f"{public_url}?v={int(time.time())}"

        supabase.table("projects").update({"thumbnail_url": thumbnail_url}).eq(
            "id", project_id
        ).execute()

        logger.info(f"Thumbnail captured for project {project_id}: {thumbnail_url}")

    except Exception as e:
        logger.warning(f"Thumbnail capture failed for project {project_id}: {e}")
