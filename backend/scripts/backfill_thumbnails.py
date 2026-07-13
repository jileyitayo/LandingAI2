"""
One-time backfill: capture dashboard thumbnails for projects that were
published before the thumbnail feature shipped.

Requires SCREENSHOTONE_ACCESS_KEY in the environment (and migration 028).

Usage (from backend/):
    python scripts/backfill_thumbnails.py
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.utils.supabase_client import get_supabase_client
from app.services.thumbnail_service import capture_thumbnail

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pause between ScreenshotOne calls to stay under rate limits
DELAY_BETWEEN_CAPTURES_S = 2.0


async def backfill_thumbnails():
    if not settings.screenshotone_access_key:
        logger.error("SCREENSHOTONE_ACCESS_KEY is not set; aborting")
        return

    supabase = get_supabase_client()

    response = (
        supabase.table("projects")
        .select("id, user_id, name, deployment_url")
        .not_.is_("deployment_url", "null")
        .is_("thumbnail_url", "null")
        .is_("deleted_at", "null")
        .execute()
    )
    projects = response.data or []
    logger.info(f"Found {len(projects)} published projects without a thumbnail")

    done = 0
    for project in projects:
        logger.info(f"Capturing thumbnail for {project['name']} ({project['id']})")
        # Sites are long-deployed, so no propagation delay is needed
        await capture_thumbnail(
            project_id=project["id"],
            user_id=project["user_id"],
            deployment_url=project["deployment_url"],
            delay_s=0,
        )
        done += 1
        if done < len(projects):
            await asyncio.sleep(DELAY_BETWEEN_CAPTURES_S)

    logger.info(f"Backfill complete: attempted {done} of {len(projects)} projects")


if __name__ == "__main__":
    asyncio.run(backfill_thumbnails())
