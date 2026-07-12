"""URL design ingestion: fetch a referenced site with httpx and extract its
design signals (colors, fonts, logo, copy, structure) for generation/edit prompts."""

from app.services.site_ingestion.models import DesignExtraction, ColorInfo, to_prompt_block
from app.services.site_ingestion.extractor import extract_site_design, WEAK_CONFIDENCE

__all__ = [
    "DesignExtraction",
    "ColorInfo",
    "to_prompt_block",
    "extract_site_design",
    "WEAK_CONFIDENCE",
]
